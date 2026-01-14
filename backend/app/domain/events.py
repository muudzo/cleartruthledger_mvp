from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
import uuid

from backend.app.constants import LedgerEventType

class LedgerEvent(BaseModel):
    """
    Represents an immutable business event that triggers ledger entries.
    Acts as the source of truth for 'what happened' before it is translated into 'accounting entries'.
    """
    model_config = ConfigDict(frozen=True)

    event_id: str = Field(default=None) # Required, but can be None to trigger deterministic generation

    def __init__(self, **data):
        super().__init__(**data)
        if not self.event_id:
            # Deterministically derive event_id if not provided
            # We use the domain normalization rules to ensure consistency
            from backend.app.domain.normalization import canonicalize_event_data
            import hashlib
            import json
            
            # We canonicalize the *data* portion mainly, but for the ID
            # we want to cover identity fields: source, type, ref, data.
            # Occurred_at is technically metadata but usually part of identity for "when it happened".
            
            # Construct a raw payload similar to what Adapter receives
            payload = {
                "source": self.source,
                "type": self.type.value,
                "external_reference": self.external_reference,
                # Use data items
                **self.data
            }
            # Note: explicit keys override data keys if conflict, which is safer for identity
            
            if "occurred_at" not in payload:
                payload["occurred_at"] = self.occurred_at
                
            canonical = canonicalize_event_data(payload)
            canonical_json = json.dumps(canonical, sort_keys=True)
            derived_id = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
            
            # Use object.__setattr__ because model is frozen
            object.__setattr__(self, "event_id", derived_id)
    source: str
    external_reference: str
    type: LedgerEventType = LedgerEventType.POSTING
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(default_factory=dict)
    
    # Optional metadata
    description: str = ""
    
    @property
    def amount(self) -> Any:
        return self.data.get("amount")
        
    @property
    def currency(self) -> str:
        return self.data.get("currency", "USD")
