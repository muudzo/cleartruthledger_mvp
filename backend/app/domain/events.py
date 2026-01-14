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
            # We use the "canonical" representation of the event data key variables
            # to ensure that the same logical event produces the same ID.
            # Using source, type, external_reference usually ensures uniqueness,
            # but to be safe against payload changes, we should hash the data too?
            # Instructions say: "hash of canonicalized event payload".
            # For now, let's use a hash of source + type + external_reference + data.
            import hashlib
            import json
            
            payload = {
                "source": self.source,
                "type": self.type.value,
                "external_reference": self.external_reference,
                "occurred_at": self.occurred_at.isoformat(),
                "data": self.data
            }
            # robust canonical serialization
            payload_str = json.dumps(payload, sort_keys=True, default=str)
            derived_id = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
            
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
