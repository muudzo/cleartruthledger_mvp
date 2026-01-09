import unittest
from backend.app.ingestion.adapter import IngestionAdapter

class TestIngestionEventTypes(unittest.TestCase):
    
    def test_invalid_event_type(self):
        payload = {
            "amount": 100,
            "type": "INVALID_TYPE",
            "source": "TEST"
        }
        with self.assertRaises(ValueError) as cm:
            IngestionAdapter.ingest(payload)
        self.assertIn("Invalid event type", str(cm.exception))

    def test_reversal_requires_original_reference(self):
        payload = {
            "amount": 100,
            "type": "REVERSAL",
            "source": "TEST"
        }
        with self.assertRaises(ValueError) as cm:
            IngestionAdapter.ingest(payload)
        self.assertIn("REVERSAL event must specify 'original_reference'", str(cm.exception))

if __name__ == "__main__":
    unittest.main()
