
import pytest
from datetime import datetime
from decimal import Decimal
import uuid
import json
import hashlib
from backend.app.domain.events import LedgerEvent, LedgerEventType
from backend.app.persistence.models import LedgerEntryModel
from backend.app.ledger_core import CoreLedgerEntry, compute_entry_hash, create_posting
from backend.app.ingestion.adapter import IngestionAdapter

def test_deterministic_event_id():
    """Test that event_id is deterministically derived from payload if not provided"""
    data_1 = {
        "source": "TEST",
        "type": "POSTING",
        "external_reference": "ref-123",
        "occurred_at": datetime(2023, 1, 1).isoformat(),
        "data": {"amount": 100, "currency": "USD"}
    }
    
    event1 = LedgerEvent(**data_1)
    event2 = LedgerEvent(**data_1)
    
    assert event1.event_id is not None
    assert event1.event_id == event2.event_id
    
    # Check that changing data changes ID
    data_2 = data_1.copy()
    data_2["data"] = {"amount": 200, "currency": "USD"}
    event3 = LedgerEvent(**data_2)
    assert event1.event_id != event3.event_id

def test_explicit_event_id():
    """Test that provided event_id is respected"""
    explicit_id = "custom-id-123"
    data = {
        "event_id": explicit_id,
        "source": "TEST",
        "type": "POSTING",
        "external_reference": "ref-123",
         "occurred_at": datetime(2023, 1, 1).isoformat(),
    }
    event = LedgerEvent(**data)
    assert event.event_id == explicit_id

def test_core_entry_hashing_includes_event_id():
    """Test that entry hash changes if event_id changes"""
    base_data = {
        "source": "TEST",
        "external_reference": "ref-1",
        "account": "CASH",
        "amount": Decimal("100.00"),
        "currency": "USD",
        "description": "Test",
        "direction": "DEBIT",
        "transaction_date": datetime(2023, 1, 1).date(),
        "created_at": datetime(2023, 1, 1),
        "prev_hash": "0000"
    }
    
    data1 = {**base_data, "event_id": "id-1"}
    data2 = {**base_data, "event_id": "id-2"}
    
    hash1 = compute_entry_hash(data1)
    hash2 = compute_entry_hash(data2)
    
    assert hash1 != hash2

def test_adapter_propagates_event_id():
    """Test that adapter passes event_id to core entries"""
    raw_event = {
        "source": "TEST_ADAPTER",
        "reference": "ref-adapter-1",
        "occurred_at": datetime.utcnow(),
        "amount": 50,
        "account": "BANK"
    }
    
    entries = IngestionAdapter.ingest(raw_event, last_hash="0000")
    
    assert len(entries) == 2
    assert entries[0].event_id is not None
    assert entries[0].event_id == entries[1].event_id
    
    # Verify the event_id matches the fingerprint of the raw event (as per Adapter logic)
    # import logic to verify
    from backend.app.domain.normalization import canonicalize_event_data
    canon = canonicalize_event_data(raw_event)
    expected_id = hashlib.sha256(json.dumps(canon, sort_keys=True).encode("utf-8")).hexdigest()
    
    assert entries[0].event_id == expected_id

