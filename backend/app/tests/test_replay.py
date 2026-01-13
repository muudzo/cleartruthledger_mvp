import unittest
from decimal import Decimal
from sqlmodel import Session, SQLModel, create_engine, select
from backend.app.ingestion.adapter import IngestionAdapter
from backend.app.persistence.models import LedgerEntryModel
import uuid

class TestReplay(unittest.TestCase):
    
    def setUp(self):
        # Use in-memory DB for replay test
        self.engine = create_engine("sqlite:///:memory:")
        SQLModel.metadata.create_all(self.engine)
        self.session = Session(self.engine)
        
    def tearDown(self):
        self.session.close()

    def test_replay_determinism(self):
        """
        Verify that replaying a sequence of events produces 
        the exact same ledger state (hashes, amounts, balances).
        """
        
        # 1. Define Event Stream
        fixed_time = "2026-01-01T12:00:00"
        
        events = [
            # Event 1: Initial Capital
            {
                "source": "BANK_STMT",
                "reference": "REF-001",
                "type": "POSTING",
                "amount": "1000.00",
                "currency": "USD",
                "description": "Initial Capital",
                "account": "CASH",
                "occurred_at": fixed_time
            },
            # Event 2: Sale
            {
                "source": "POS",
                "reference": "REF-002",
                "type": "POSTING",
                "amount": "50.00",
                "currency": "USD",
                "description": "Sale of Goods",
                "account": "CASH",
                "occurred_at": fixed_time
            },
            # Event 3: Expense (Payment from Cash) 
             {
                "source": "POS",
                "reference": "REF-003",
                "type": "POSTING",
                "amount": "25.00",
                "currency": "USD",
                "description": "More Sales",
                "account": "CASH",
                "occurred_at": fixed_time
            },
            # Event 4: Reversal of Event 2
            {
                "source": "POS",
                "reference": "REV-001",
                "type": "REVERSAL",
                "original_reference": "REF-002",
                "description": "Refund for Sale",
                "occurred_at": fixed_time
                # raw_data passed to adapter needs original_reference
            }
        ]
        
        # 2. Run Phase 1 (Original Run)
        last_hash_1 = "0000000000000000000000000000000000000000000000000000000000000000"
        
        # Helper to ingest stream
        def process_stream(session, start_hash):
            current_hash = start_hash
            entries_accumulated = []
            
            for evt in events:
                # If Reversal, we need to find original entries IN THIS SESSION
                orig_entries = []
                if evt["type"] == "REVERSAL":
                    # Find original by reference
                    # Adapter expects List[LedgerEntryModel]
                    # We query the session
                    # Original reference matches 'external_reference' prefix?
                    # The adapter constructs e_ref = {ref}-DR / {ref}-CR.
                    # We need to find all entries where external_reference LIKE '{orig_ref}-%'
                    # SQLite 'LIKE' works.
                     stmt = select(LedgerEntryModel).where(LedgerEntryModel.external_reference.like(f"{evt['original_reference']}-%"))
                     orig_entries = session.exec(stmt).all()
                
                new_entries = IngestionAdapter.ingest(evt, last_hash=current_hash, original_entries=orig_entries)
                
                for entry in new_entries:
                    session.add(entry)
                    # Use session.commit() or flush to ensure IDs and such if needed?
                    # But hashes depend on previous entry hash.
                    # We update current_hash from the last entry in the batch
                    if entry.entry_hash:
                         current_hash = entry.entry_hash
                    entries_accumulated.append(entry)
                
                # Commit per event to simulate real time?
                session.commit()
            
            return entries_accumulated

        entries_1 = process_stream(self.session, last_hash_1)
        state_1_hashes = [e.entry_hash for e in entries_1]
        
        # 3. Wipe and Reset
        SQLModel.metadata.drop_all(self.engine)
        SQLModel.metadata.create_all(self.engine)
        session_2 = Session(self.engine)
        
        # 4. Run Phase 2 (Replay)
        # Should be identical
        entries_2 = process_stream(session_2, last_hash_1)
        state_2_hashes = [e.entry_hash for e in entries_2]
        
        # 5. Assertions
        self.assertEqual(len(entries_1), len(entries_2))
        self.assertEqual(state_1_hashes, state_2_hashes, "Replay produced different hash chain!")
        
        # Verify Reversal Effect (Balance Check)
        # 1000 + 50 + 25 - 50 = 1025
        cash_entries = session_2.exec(select(LedgerEntryModel).where(LedgerEntryModel.account == "CASH")).all()
        cash_balance = sum(e.amount for e in cash_entries)
        # Why?
        # Event 1: +1000 (DR Cash)
        # Event 2: +50 (DR Cash)
        # Event 3: +25 (DR Cash)
        # Event 4: Reversal of Event 2: -50 (DR Cash negated) implies adding -50 to DR Cash?
        # Ledger Core Reversal: Creates new entry with amount = -orig.amount.
        # Orig (Evt 2) Cash entry: Amount 50.
        # Reversal Entry: Amount -50.
        # Total = 1000 + 50 + 25 - 50 = 1025.
        
        self.assertEqual(cash_balance, Decimal("1025.00"))

if __name__ == "__main__":
    unittest.main()
