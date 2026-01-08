import unittest
from backend.app.domain.models import LedgerEntry
from datetime import date, datetime
from decimal import Decimal
import dataclasses

class TestCoreInvariants(unittest.TestCase):
    
    def test_domain_model_immutability(self):
        """
        Invariant: Domain models must be immutable (frozen).
        """
        entry = LedgerEntry(
            transaction_id="123",
            date=date.today(),
            amount=Decimal("100.00"),
            currency="USD",
            account="CASH",
            direction="DEBIT",
            description="Test",
            source="TEST",
            external_reference="REF1",
            created_at=datetime.utcnow()
        )
        
        # Attempt to mutate should fail if pydantic config frozen=True works
        with self.assertRaises(Exception):
            entry.amount = Decimal("200.00")
            
    def test_append_only_principle(self):
        """
        Invariant: There is no method to update an existing entry exposed in the logic.
        This is a structural check.
        """
        # Verify that there are no 'update' methods in the domain definition
        # This is a meta-test.
        from backend.app.domain import ledger
        
        methods = dir(ledger)
        update_methods = [m for m in methods if "update" in m.lower()]
        self.assertEqual(update_methods, [], "Ledger core must not expose update methods")

if __name__ == '__main__':
    unittest.main()
