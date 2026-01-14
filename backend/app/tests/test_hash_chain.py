import unittest
from decimal import Decimal
from datetime import date, datetime
from backend.app.persistence.models import LedgerEntryModel

class TestLedgerHashChain(unittest.TestCase):
    
    def test_hash_computation(self):
        """
        Test that hash computation includes prev_hash and is deterministic.
        """
        entry = LedgerEntryModel(
            event_id="evt-chain-1",
            source="CHAIN_TEST",
            external_reference="REF1",
            account="CASH",
            amount=Decimal("50.00"),
            prev_hash="GENESIS_HASH"
        )
        
        # Compute first hash
        h1 = entry.compute_hash()
        self.assertIsNotNone(h1)
        self.assertEqual(len(h1), 64) # SHA-256 hex length
        
        # Verify determinism
        h2 = entry.compute_hash()
        self.assertEqual(h1, h2)
        
        # Verify tampering changes hash
        entry.amount = Decimal("50.01")
        h3 = entry.compute_hash()
        self.assertNotEqual(h1, h3)
        
        # Verify changing prev_hash changes hash
        entry.amount = Decimal("50.00") # Reset amount
        entry.prev_hash = "OTHER_HASH"
        h4 = entry.compute_hash()
        self.assertNotEqual(h1, h4)

if __name__ == "__main__":
    unittest.main()
