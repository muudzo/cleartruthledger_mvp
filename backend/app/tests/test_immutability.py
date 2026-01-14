import os
# Force in-memory DB for tests BEFORE importing engine
os.environ["DATABASE_URL"] = "sqlite://" 

import unittest
from decimal import Decimal
from sqlmodel import Session, select, text
from backend.app.db.database import engine
from backend.app.persistence.models import LedgerEntryModel
from datetime import date
import uuid

class TestImmutabilityTriggers(unittest.TestCase):
    
    def setUp(self):
        # Ensure we are using the main DB or a persistent one where we ran init_db
        # For testing, we might need to apply triggers to the test DB if it's in-memory.
        # But our init_db script used the imported engine. 
        # CAUTION: If the test runs against a fresh in-memory DB each time, 
        # we need to apply triggers in setUp.
        # Let's check if the engine is file-based or memory.
        # If file-based (default), it stays. 
        # To be safe and robust, let's re-apply triggers here or use the init_db function.
        from backend.app.db.init_db import init_db
        from backend.app.db.database import create_db_and_tables
        create_db_and_tables() # Ensure tables exist!
        init_db()
        self.session = Session(engine)

    def tearDown(self):
        self.session.close()

    def test_prevention_of_update(self):
        """
        Test that a raw SQL UPDATE on ledger_entries fails.
        """
        # 1. Create a dummy entry
        ref = str(uuid.uuid4())
        entry = LedgerEntryModel(
            event_id=f"evt-{ref}",
            source="TEST_IMMUTABILITY",
            external_reference=ref,
            account="TEST_ACC",
            amount=Decimal("100.00"),
            currency="USD",
            direction="DEBIT",
            description="Immutable Entry",
            transaction_date=date.today(),
            prev_hash="hash1",
            entry_hash="hash2"
        )
        self.session.add(entry)
        self.session.commit()
        
        # 2. Attempt Update
        # Using raw SQL to bypass any ORM safeguards if any
        try:
            self.session.exec(text(f"UPDATE ledger_entries SET amount = 200 WHERE external_reference = '{ref}'"))
            self.session.commit()
            self.fail("UPDATE should have failed due to trigger")
        except Exception as e:
            # We expect an OperationalError (SQLite) or IntegrityError
            # Check message
            self.assertIn("Ledger entries are append-only", str(e))

    def test_prevention_of_delete(self):
        """
        Test that a raw SQL DELETE on ledger_entries fails.
        """
        # 1. Create a dummy entry
        ref = str(uuid.uuid4())
        entry = LedgerEntryModel(
            event_id=f"evt-{ref}",
            source="TEST_IMMUTABILITY",
            external_reference=ref,
            account="TEST_ACC",
            amount=Decimal("100.00"),
            currency="USD",
            direction="DEBIT",
            description="Immutable Entry",
            transaction_date=date.today(),
            prev_hash="hash3",
            entry_hash="hash4"
        )
        self.session.add(entry)
        self.session.commit()
        
        # 2. Attempt Delete
        try:
            self.session.exec(text(f"DELETE FROM ledger_entries WHERE external_reference = '{ref}'"))
            self.session.commit()
            self.fail("DELETE should have failed due to trigger")
        except Exception as e:
            self.assertIn("Ledger entries are append-only", str(e))

if __name__ == "__main__":
    unittest.main()
