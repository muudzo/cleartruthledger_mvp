from sqlmodel import SQLModel, Field, Enum as SQLEnum
from typing import Optional
from datetime import datetime, date
from enum import Enum


class Channel(str, Enum):
    """Payment channel options"""
    ECOCASH = "EcoCash"
    ZIPIT = "ZIPIT"
    BANK = "Bank"
    PAYNOW = "Paynow"
    CASH = "Cash"
    OTHER = "Other"


class Direction(str, Enum):
    """Transaction direction"""
    INCOMING = "Incoming"
    OUTGOING = "Outgoing"


class Status(str, Enum):
    """Transaction status"""
    EXPECTED = "Expected"
    RECEIVED = "Received"
    PENDING = "Pending"
    MISSING = "Missing"


class Transaction(SQLModel, table=True):
    """Transaction model for manual logging"""
    __tablename__ = "transactions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    
    # Required fields
    amount: float = Field(gt=0)  # Must be positive
    channel: Channel
    direction: Direction
    status: Status
    reference: str = Field(max_length=500)
    transaction_date: date = Field(default_factory=date.today)
    
    # Optional fields
    screenshot_id: Optional[int] = Field(default=None, foreign_key="files.id")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
