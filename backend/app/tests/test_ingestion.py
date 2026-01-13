import unittest
from decimal import Decimal
from sqlmodel import Session, SQLModel, create_engine
from backend.app.ingestion.adapter import IngestionAdapter
from backend.app.persistence.models import LedgerEntryModel

class TestIngestion(unittest.TestCase):
    
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        SQLModel.metadata.create_all(self.engine)
        self.session = Session(self.engine)
        
    def tearDown(self):
        self.session.close()

    def test_adapter_produces_balanced_entries(self):
        """
        Invariant: Computed entries must sum to zero (Debits = Credits).
        """
        payload = {
            "amount": 100,
            "currency": "USD",
            "source": "TEST_SRC",
            "reference": "REF_001",
            "account": "CASH"
        }
        
        entries = IngestionAdapter.ingest(payload)
        
        total = sum(e.amount for e in entries)
        self.assertEqual(total, Decimal("0"), "Double entry must sum to zero")
        self.assertEqual(len(entries), 2, "Must produce at least 2 legs")

    def test_idempotency_constraint(self):
        """
        Invariant: Re-ingesting the same event implies saving duplicate keys,
        which must be rejected by the persistence layer.
        """
        payload = {
            "amount": 50,
            "source": "TEST_IDEM",
            "reference": "REF_DUPE",
            "account": "CASH"
        }
        
        entries1 = IngestionAdapter.ingest(payload)
        for e in entries1:
            self.session.add(e)
        self.session.commit()
        
        # Ingest again (same ref, same source)
        entries2 = IngestionAdapter.ingest(payload)
        for e in entries2:
            self.session.add(e)
            
        # Expect unique constraint violation
        from sqlalchemy.exc import IntegrityError
        with self.assertRaises(IntegrityError):
            self.session.commit()

    def test_reversal_success(self):
        """
        Test that a valid reversal request produces negating entries.
        """
        # 1. Ingest Original
        payload_orig = {
            "amount": 100,
            "currency": "USD",
            "source": "TEST_REV",
            "reference": "REF_REV_001",
            "account": "CASH"
        }
        original_entries = IngestionAdapter.ingest(payload_orig)
        for e in original_entries:
            self.session.add(e)
        self.session.commit()
        
        # 2. Ingest Reversal
        # We must provide original entries manually to adapter? 
        # Integration logic: The Service/Caller is responsible for fetching originals.
        # Here we mock that fetch by passing the list we just created.
        
        payload_rev = {
            "type": "REVERSAL",
            "source": "TEST_REV",
            "reference": "REV_001",
            "original_reference": "REF_REV_001",
            "description": "Correction"
        }
        
        # Adapter requires original_entries list
        reversal_entries = IngestionAdapter.ingest(payload_rev, original_entries=original_entries)
        
        for e in reversal_entries:
            self.session.add(e)
        self.session.commit()
        
        self.assertEqual(len(reversal_entries), 2)
        total_rev = sum(e.amount for e in reversal_entries)
        self.assertEqual(total_rev, Decimal("0"))
        
        # Check Net Balance
        all_entries = original_entries + reversal_entries
        net_balance = sum(e.amount for e in all_entries)
        self.assertEqual(net_balance, Decimal("0"), "Reversal must negate original entries")

    def test_reversal_missing_original(self):
        """
        Test failure when original entries are not provided or found.
        """
        payload_rev = {
            "type": "REVERSAL",
            "source": "TEST_FAIL",
            "reference": "REV_FAIL",
            "original_reference": "REF_MISSING"
        }
        
        with self.assertRaises(ValueError) as cm:
            IngestionAdapter.ingest(payload_rev, original_entries=None)
            
        self.assertIn("Original entries not found", str(cm.exception))

if __name__ == '__main__':
    unittest.main()
