from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from sqlmodel import SQLModel, Field, UniqueConstraint
import json
from decimal import Decimal

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
    description: str = Field(default="")
    direction: str = Field(default="DEBIT") 
    
    # Metadata
    transaction_date: date = Field(default_factory=date.today)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def to_canonical_json(self) -> str:
        """
        Produces a deterministic, canonical JSON representation of the entry.
        Used for hashing and audit.
        """
        data = {
            "source": self.source,
            "external_reference": self.external_reference,
            "account": self.account,
            "amount": str(self.amount), # Decimals to string to avoid float precision issues
            "currency": self.currency,
            "description": self.description,
            "direction": self.direction,
            "transaction_date": self.transaction_date.isoformat(),
            # created_at is excluded from canonical hash if it's considered metadata that might vary lightly? 
            # Or should it be included? 'created_at' is usually system generated. 
            # Ideally, the hash represents the business fact.
            # But let's include it if we want strict history. 
            # However, prompt says "Canonical Serialization for Ledger Entries". 
            # Let's include everything that defines the fact.
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        # Sort keys to ensure determinism
        return json.dumps(data, sort_keys=True, separators=(',', ':'))
    
    # No user_id
    # No screenshot_id
    # No update_at (Immutable)
