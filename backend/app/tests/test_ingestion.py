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

if __name__ == '__main__':
    unittest.main()
