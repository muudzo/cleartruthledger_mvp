import unittest
from decimal import Decimal
from sqlmodel import Session, select, text
from backend.app.db.database import engine
from backend.app.persistence.models import LedgerEntryModel

class TestInvariantsExpanded(unittest.TestCase):
    
    def setUp(self):
        from backend.app.db.init_db import init_db
        init_db()
        self.session = Session(engine)
        
    def tearDown(self):
        self.session.close()

    def test_global_zero_sum(self):
        """
        Invariant: The sum of ALL amounts in the ledger must be exactly zero per currency.
        This proves double-entry accounting is holding globally.
        """
        # Query sum by currency
        statement = text("SELECT currency, SUM(amount) FROM ledger_entries GROUP BY currency")
        results = self.session.exec(statement).all()
        
        for currency, total_amount in results:
            self.assertEqual(Decimal(str(total_amount)), Decimal("0"), f"Global ledger for {currency} is not balanced!")

    def test_idempotency_compliance_check(self):
        """
        Invariant: No duplicate (source, external_reference, account) tuples exist.
        This is enforced by DB constraint, but let's verify data integrity.
        """
        statement = text("""
            SELECT source, external_reference, account, COUNT(*) 
            FROM ledger_entries 
            GROUP BY source, external_reference, account 
            HAVING COUNT(*) > 1
        """)
        dupes = self.session.exec(statement).all()
        self.assertEqual(len(dupes), 0, "Found duplicate ledger entries!")

    def test_hash_chain_integrity_scan(self):
        """
        Invariant: Every entry's prev_hash matches the entry_hash of the previous entry by ID.
        This scans the entire chain.
        """
        # Fetch all entries ordered by ID
        entries = self.session.exec(select(LedgerEntryModel).order_by(LedgerEntryModel.id)).all()
        
        if not entries:
            return

        current_prev_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        
        for entry in entries:
            self.assertEqual(entry.prev_hash, current_prev_hash, f"Hash chain broken at ID {entry.id}")
            
            # Recompute hash to verify entry content wasn't mutated
            computed_hash = entry.compute_hash()
            self.assertEqual(entry.entry_hash, computed_hash, f"Entry content tampered at ID {entry.id}")
            
            current_prev_hash = entry.entry_hash

if __name__ == "__main__":
    unittest.main()
