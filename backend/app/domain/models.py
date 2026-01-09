from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict

from enum import Enum

class EventType(str, Enum):
    POSTING = "POSTING"
    REVERSAL = "REVERSAL"

class LedgerEntry(BaseModel):
    """
    Represents a double-entry ledger record.
    Pure domain model, no database concerns.
    """
    model_config = ConfigDict(frozen=True)

    transaction_id: str
    date: date
    amount: Decimal
    currency: str
    account: str
    direction: str  # 'debit' or 'credit'
    description: str
    source: str
    external_reference: str
    created_at: datetime

class IngestionEvent(BaseModel):
    """
    Represents a raw event from an external system.
    """
    model_config = ConfigDict(frozen=True)

    source: str
    external_reference: str
    raw_data: dict
    type: EventType = EventType.POSTING
    occurred_at: datetime
