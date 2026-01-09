import unittest
from decimal import Decimal
from sqlmodel import Session, text
from backend.app.db.database import engine
from backend.app.persistence.models import LedgerEntryModel
from datetime import date
import uuid

class TestProjections(unittest.TestCase):
    
    def setUp(self):
        # Apply views
        from backend.app.db.init_db import init_db
        init_db()
        self.session = Session(engine)
        
    def tearDown(self):
        self.session.close()

    def test_account_balances_view(self):
        # 1. Clean DB (Delete existing entries to test clean state? Triggers prevent delete!)
        # So we must verify DELTAS.
        # Get current balance
        initial_res = self.session.exec(text("SELECT balance FROM view_account_balances WHERE account = 'VIEW_TEST_CASH'")).first()
        initial_balance = Decimal(initial_res) if initial_res else Decimal(0)
        
        # 2. Insert Entries
        ref = str(uuid.uuid4())
        self.session.add(LedgerEntryModel(
            source="VIEW_TEST",
            external_reference=ref,
            account="VIEW_TEST_CASH",
            amount=Decimal("100.00"),
            currency="ESD", # Experimental Dollar
            direction="DEBIT",
            prev_hash="",
            entry_hash=""
        ))
        self.session.commit()
        
        # 3. Query View
        res = self.session.exec(text("SELECT balance FROM view_account_balances WHERE account = 'VIEW_TEST_CASH'")).first()
        new_balance = Decimal(res)
        
        self.assertEqual(new_balance - initial_balance, Decimal("100.00"), "View should reflect inserted delta")

    def test_trial_balance_zero(self):
        # Insert a balanced pair
        ref = str(uuid.uuid4())
        self.session.add(LedgerEntryModel(
            source="VIEW_TEST",
            external_reference=f"{ref}-DR",
            account="TRIAL_CASH",
            amount=Decimal("50.00"),
            currency="TZD", # Test Zero Dollar
            direction="DEBIT", prev_hash="", entry_hash=""
        ))
        self.session.add(LedgerEntryModel(
            source="VIEW_TEST",
            external_reference=f"{ref}-CR",
            account="TRIAL_REV",
            amount=Decimal("-50.00"),
            currency="TZD",
            direction="CREDIT", prev_hash="", entry_hash=""
        ))
        self.session.commit()
        
        # Query Trial Balance View
        res = self.session.exec(text("SELECT net_balance FROM view_trial_balance WHERE currency = 'TZD'")).first()
        self.assertEqual(Decimal(res), Decimal("0.00"), "Trial balance must be zero")

if __name__ == "__main__":
    unittest.main()
