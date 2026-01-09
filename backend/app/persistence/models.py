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
    
    # Hash Chain
    prev_hash: str = Field(index=True)
    entry_hash: str = Field(index=True)

    def to_canonical_json(self) -> str:
        """
        Produces a deterministic, canonical JSON representation of the entry.
        Used for hashing and audit.
        Excludes hash fields themselves to avoid circular dependency.
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
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "prev_hash": self.prev_hash # Include previous hash in the body to chain it
        }
        # Sort keys to ensure determinism
        return json.dumps(data, sort_keys=True, separators=(',', ':'))

    def compute_hash(self) -> str:
        """
        Computes the SHA-256 hash of the canonical JSON.
        """
        import hashlib
        canonical = self.to_canonical_json()
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
    
    # No user_id
    # No screenshot_id
    # No update_at (Immutable)
