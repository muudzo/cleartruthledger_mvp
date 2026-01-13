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

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
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
