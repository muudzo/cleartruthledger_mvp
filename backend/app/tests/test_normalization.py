
import pytest
from decimal import Decimal
import json
from backend.app.domain.normalization import canonicalize_event_data
from backend.app.ingestion.adapter import IngestionAdapter

def test_canonicalize_sorts_keys():
    """Test that keys are sorted alphabetically."""
    data1 = {"b": 2, "a": 1}
    data2 = {"a": 1, "b": 2}
    
    canon1 = canonicalize_event_data(data1)
    canon2 = canonicalize_event_data(data2)
    
    # JSON string comparison to prove stability
    assert json.dumps(canon1) == json.dumps(canon2)
    # Order in dict keys (Python 3.7+) is insertion order, so we need to check iteration order
    keys1 = list(canon1.keys())
    assert keys1 == ["a", "b"]

def test_canonicalize_currency_and_precision():
    """Test currency normalization and amount precision."""
    data = {
        "currency": "usd",
        "amount": 100
    }
    canon = canonicalize_event_data(data)
    assert canon["currency"] == "USD"
    assert canon["amount"] == "100.00"
    
    data_float = {"amount": 100.001} # Extra precision
    canon_float = canonicalize_event_data(data_float)
    assert canon_float["amount"] == "100.00"

def test_recursive_canonicalization():
    """Test nested dictionaries."""
    data = {"meta": {"b": 1, "a": 2}, "list": [{"d": 4, "c": 3}]}
    canon = canonicalize_event_data(data)
    
    assert list(canon["meta"].keys()) == ["a", "b"]
    assert list(canon["list"][0].keys()) == ["c", "d"]

def test_adapter_fingerprint_stability():
    """Test that adapter generates same event_id for shuffled inputs."""
    raw1 = {"source": "TEST", "b": 2, "a": 1, "currency": "usd", "amount": 100}
    raw2 = {"amount": 100.0, "currency": "USD", "source": "TEST", "a": 1, "b": 2}
    
    # We can inspect the internal event creation using mocks, OR
    # checking the returned entries if they carry the event_id.
    # But event_id is on LedgerEntryModel now!
    
    entries1 = IngestionAdapter.ingest(raw1, last_hash="0001")
    entries2 = IngestionAdapter.ingest(raw2, last_hash="0002") # Diff hash shouldn't affect event_id derived from payload
    
    assert entries1[0].event_id == entries2[0].event_id
    
    # Ensure event_id is NOT just random UUID
    assert len(entries1[0].event_id) == 64 # SHA256 hex length
