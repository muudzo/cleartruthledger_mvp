import unittest
from decimal import Decimal
from datetime import date
from backend.app.ingestion.adapter import IngestionAdapter
from backend.app.persistence.models import LedgerEntryModel

class TestReversalIntegrity(unittest.TestCase):
    
    def test_reversal_requires_original_entries(self):
        payload = {
            "type": "REVERSAL",
            "original_reference": "MISSING_REF",
            "amount": 100 # Should be ignored
        }
        with self.assertRaises(ValueError) as cm:
            IngestionAdapter.ingest(payload, original_entries=[])
        self.assertIn("Original entries not found", str(cm.exception))

    def test_reversal_negates_original_entries(self):
        # 1. Create Mock Original Entries
        orig_dr = LedgerEntryModel(
            event_id="evt-orig",
            source="MANUAL",
            external_reference="REF-DR",
            account="CASH",
            amount=Decimal("100.00"),
            currency="USD",
            direction="DEBIT",
            prev_hash="",
            entry_hash="HASH-DR"
        )
        orig_cr = LedgerEntryModel(
            event_id="evt-orig",
            source="MANUAL",
            external_reference="REF-CR",
            account="SALES",
            amount=Decimal("-100.00"),
            currency="USD",
            direction="CREDIT",
            prev_hash="",
            entry_hash="HASH-CR"
        )
        
        payload = {
            "type": "REVERSAL",
            "original_reference": "REF",
            "reference": "REV-REF",
            "description": "Correction"
        }
        
        # 2. Ingest Reversal
        rev_entries = IngestionAdapter.ingest(payload, last_hash="LAST_HASH", original_entries=[orig_dr, orig_cr])
        
        # 3. Verify
        self.assertEqual(len(rev_entries), 2)
        
        # Check logic: Each original entry should have a counterpart with negated amount
        rev_dr_candidates = [e for e in rev_entries if e.account == "CASH"]
        self.assertEqual(len(rev_dr_candidates), 1)
        rev_dr = rev_dr_candidates[0]
        self.assertEqual(rev_dr.amount, Decimal("-100.00"), "Must negate original DEBIT amount")
        self.assertEqual(rev_dr.direction, "DEBIT", "Must preserve direction label")
        
        rev_cr_candidates = [e for e in rev_entries if e.account == "SALES"]
        self.assertEqual(len(rev_cr_candidates), 1)
        rev_cr = rev_cr_candidates[0]
        self.assertEqual(rev_cr.amount, Decimal("100.00"), "Must negate original CREDIT amount")

if __name__ == "__main__":
    unittest.main()
