import unittest
from decimal import Decimal
from datetime import date, datetime
from backend.app.persistence.models import LedgerEntryModel

class TestCanonicalSerialization(unittest.TestCase):
    
    def test_serialization_determinism(self):
        """
        Test that serializing the same entry twice yields identical output,
        regardless of key order in dictionary construction.
        """
        now = datetime.utcnow()
        entry = LedgerEntryModel(
            source="TEST_SRC",
            external_reference="REF123",
            account="CASH",
            amount=Decimal("100.50"),
            currency="USD",
            direction="DEBIT",
            description="TestSerialization",
            transaction_date=date(2023, 1, 1),
            created_at=now
        )
        
        json1 = entry.to_canonical_json()
        json2 = entry.to_canonical_json()
        
        self.assertEqual(json1, json2, "Serialization must be deterministic")
        
        # Verify strict format (no spaces)
        self.assertNotIn(" ", json1, "Canonical JSON should be compact (no spaces)")
        self.assertIn('"amount":"100.50"', json1, "Decimals must be serialized as strings")
        
    def test_different_entries_produce_different_json(self):
        entry1 = LedgerEntryModel(source="A", external_reference="A", account="A")
        entry2 = LedgerEntryModel(source="B", external_reference="A", account="A")
        
        self.assertNotEqual(entry1.to_canonical_json(), entry2.to_canonical_json())

if __name__ == "__main__":
    unittest.main()
