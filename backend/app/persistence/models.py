from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from sqlmodel import SQLModel, Field, UniqueConstraint

class LedgerEntryModel(SQLModel, table=True):
    """
    Persistence model for the ledger.
    Acts as a dumb sink for immutable facts.
    """
    __tablename__ = "ledger_entries"
    __table_args__ = (
        UniqueConstraint("source", "external_reference", "account", name="uq_ledger_entry_idempotency"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Core Identity
    source: str = Field(index=True)
    external_reference: str = Field(index=True)
    account: str = Field(index=True)
    
    # Value
    amount: Decimal = Field(default=0, decimal_places=2)
    currency: str = Field(default="USD", max_length=3)
    
    # Metadata
    transaction_date: date = Field(default_factory=date.today)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # No user_id
    # No screenshot_id
    # No update_at (Immutable)
