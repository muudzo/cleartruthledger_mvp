import unittest
from decimal import Decimal
from datetime import datetime
from backend.app.persistence.models import LedgerEntryModel
from backend.app.ingestion.adapter import IngestionAdapter

class TestOrdering(unittest.TestCase):
    
    def test_explicit_sequence_ordering(self):
        """
        Verify that entries with identical timestamps can be ordered by ingest_sequence.
        """
        now = datetime.utcnow()
        
        # Create raw events (identical content, same time)
        event_a = {
            "source": "ORDER_TEST",
            "reference": "REF_A",
            "type": "POSTING",
            "amount": 100,
            "currency": "USD",
            "occurred_at": now
        }
        event_b = {
            "source": "ORDER_TEST",
            "reference": "REF_B",
            "type": "POSTING",
            "amount": 200,
            "currency": "USD",
            "occurred_at": now
        }
        
        # Ingest with explicit sequence
        entries_a = IngestionAdapter.ingest(event_a, ingest_sequence=1, last_hash="0001")
        entries_b = IngestionAdapter.ingest(event_b, ingest_sequence=2, last_hash=entries_a[-1].entry_hash)
        
        all_entries = entries_a + entries_b
        
        # define sorting key: (occurred_at, ingest_sequence)
        sorted_entries = sorted(all_entries, key=lambda x: (x.transaction_date, x.ingest_sequence))
        
        # Verify order
        self.assertEqual(sorted_entries[0].external_reference, "REF_A-DR")
        self.assertEqual(sorted_entries[2].external_reference, "REF_B-DR")
        
        # Verify sequence persistence
        self.assertEqual(entries_a[0].ingest_sequence, 1)
        self.assertEqual(entries_b[0].ingest_sequence, 2)

    def test_sequence_affects_hash(self):
        """
        Verify that changing the sequence changes the hash (tamper evidence).
        """
        event = {
            "source": "HASH_TEST",
            "reference": "REF_X",
            "amount": 100
        }
        entries_1 = IngestionAdapter.ingest(event, ingest_sequence=1, last_hash="0000")
        entries_2 = IngestionAdapter.ingest(event, ingest_sequence=2, last_hash="0000")
        
        self.assertNotEqual(entries_1[0].entry_hash, entries_2[0].entry_hash)
        self.assertNotEqual(entries_1[0].to_canonical_json(), entries_2[0].to_canonical_json())

if __name__ == "__main__":
    unittest.main()
