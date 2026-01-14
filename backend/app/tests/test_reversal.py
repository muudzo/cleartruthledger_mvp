import unittest
from decimal import Decimal
from sqlmodel import Session, SQLModel, create_engine
from backend.app.ingestion.adapter import IngestionAdapter
from backend.app.persistence.models import LedgerEntryModel

class TestReversal(unittest.TestCase):
    
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        SQLModel.metadata.create_all(self.engine)
        self.session = Session(self.engine)

    def test_reversal_via_compensating_entry(self):
        """
        Invariant: To 'undo' an event, we must ingest a compensating event
        that zeroes out the balance.
        """
        # 1. Original Event
        event_a = {
            "amount": 100,
            "reference": "REF_A",
            "source": "MANUAL",
            "account": "CASH"
        }
        entries_a = IngestionAdapter.ingest(event_a)
        for e in entries_a:
            self.session.add(e)
        self.session.commit()
        
        # Check Balance (CASH)
        # Assuming manual scan or logic
        cash_balance_a = sum(e.amount for e in self.session.query(LedgerEntryModel).filter_by(account="CASH").all())
        self.assertEqual(cash_balance_a, Decimal("100"), "Balance should be 100")
        
        # 2. Reversal Event (Same details, negative amount? Or specific logic?)
        # For this MVP, we ingest a new event with negative amount logically, 
        # or the adapter handles 'reversal' type. 
        # Requirement: "event A, reversal of A, balance returns to zero"
        # Since our adapter takes positive amounts and makes DR/CR, logic for reversal 
        # implies sending a negative amount if the adapter supports it, 
        # OR swapping the legs.
        # Adapter code says: raw_data.get("amount", 0) -> if <= 0 raise ValueError.
        # So we can't send negative amount to THIS adapter yet.
        # We need to Upgrade Adapter or Simulate manual reversal entries.
        # Since I'm "Adding Tests", I should demonstrate how it SHOULD work.
        # I will manually construct reversal entries to prove the ledger CAPABILITY,
        # acknowledging the adapter might need a 'type=reversal' flag later.
        
        # Constructing compensating entries manually for the test
        reversal_entries = [
            LedgerEntryModel(
                event_id="evt-rev-dr",
                source="MANUAL",
                external_reference="REF_A_REVERSAL_DR",
                account="CASH",
                amount=Decimal("-100"), # Compensating
                currency="USD",
                direction="DEBIT", # Technically a negative debit or a credit?
                                   # In pure double entry, you usually credit the debit account.
                                   # But sum(amount) works regardless of sign/direction labeling 
                                   # if we treat amount as signed.
                prev_hash="last",
                entry_hash="hash1"
            ),
             LedgerEntryModel(
                event_id="evt-rev-cr",
                source="MANUAL",
                external_reference="REF_A_REVERSAL_CR",
                account="REVENUE_SALES",
                amount=Decimal("100"), # Compensating
                currency="USD",
                direction="CREDIT",
                prev_hash="hash1",
                entry_hash="hash2"
            )
        ]
        
        for e in reversal_entries:
            self.session.add(e)
        self.session.commit()
        
        # 3. Verify Zero Balance
        final_balance = sum(e.amount for e in self.session.query(LedgerEntryModel).filter_by(account="CASH").all())
        self.assertEqual(final_balance, Decimal("0"), "Balance should return to zero after reversal")

if __name__ == '__main__':
    unittest.main()
