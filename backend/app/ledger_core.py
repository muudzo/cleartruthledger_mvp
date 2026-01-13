"""
Ledger Core Module
==================

This module contains the pure, functional core of the ClearLedger accounting system.
It strictly enforces the Append-Only and Double-Entry invariants.

Invariants:
1.  **Append-Only**: Facts cannot be changed. Logic here produces NEW entries, never modifies existing ones.
2.  **Double-Entry**: Every POSTING event produces at least two entries (Debits = Credits).
3.  **Immutability**: Reversals are compensating entries, not deletions.
4.  **Hashing**: Every entry is cryptographically chained to the previous one (Tamper-Evident).

This module contains NO database dependencies.
"""

import hashlib
import json
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Any, Dict

# We will use the domain model for inputs/outputs if possible, 
# or simple dicts/dataclasses if the domain model is not yet rich enough.
# For now, we redefine a pure CoreEntry to be precise, or use the one from domain if it fits.
# Given the "Pure Python" requirement, let's define the shape here or import.

from backend.app.domain.models import LedgerEntry as DomainLedgerEntry
# We need a model that includes hashes. DomainLedgerEntry currently doesn't have checks.
# We will define a CoreLedgerEntry for this module's output.

from pydantic import BaseModel, ConfigDict, Field

class CoreLedgerEntry(BaseModel):
    """
    Represents a fully formed ledger entry ready for persistence.
    Includes protocol-level fields like hashes.
    """
    model_config = ConfigDict(frozen=True)

    source: str
    external_reference: str
    account: str
    amount: Decimal
    currency: str
    description: str
    direction: str  # "DEBIT" or "CREDIT"
    transaction_date: date
    created_at: datetime
    
    # Chain/Audit
    prev_hash: str
    entry_hash: str

from backend.app.constants import INITIAL_HASH

def compute_entry_hash(entry_data: Dict[str, Any]) -> str:
    """
    Computes the SHA-256 hash of the canonical JSON representation of an entry.
    The dictionary MUST contain:
    - source, external_reference, account, amount, currency, description, direction, 
      transaction_date, created_at, prev_hash.
    
    It MUST NOT contain 'entry_hash' (circular).
    """
    # Enforce canonical order and formatting
    # Amount needs to be stringified to avoid float precision issues in JSON
    # Dates need isoformat
    
    clean_data = {
        "source": entry_data["source"],
        "external_reference": entry_data["external_reference"],
        "account": entry_data["account"],
        "amount": str(entry_data["amount"]),
        "currency": entry_data["currency"],
        "description": entry_data["description"],
        "direction": entry_data["direction"],
        "transaction_date": entry_data["transaction_date"].isoformat() if isinstance(entry_data["transaction_date"], date) else entry_data["transaction_date"],
        "created_at": entry_data["created_at"].isoformat() if isinstance(entry_data["created_at"], datetime) else entry_data["created_at"],
        "prev_hash": entry_data["prev_hash"]
    }
    
    canonical_json = json.dumps(clean_data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()

def create_posting(
    amount: Decimal,
    currency: str,
    source: str,
    external_reference: str,
    description: str,
    account_name: str,
    last_hash: str,
    transaction_date: Optional[date] = None,
    created_at: Optional[datetime] = None
) -> List[CoreLedgerEntry]:
    """
    Pure function to create a double-entry posting (Debit + Credit).
    
    Logic:
    1. Validate inputs (Amount > 0).
    2. Create Debit (Asset Increase) for the specified account.
    3. Create Credit (Revenue/Equity) for the offset account (Hardcoded REVENUE_SALES for MVP).
    4. Chain hashes: Last -> Debit -> Credit.
    """
    if amount <= 0:
        raise ValueError("Posting amount must be positive. Use Reversal for corrections.")

    if not transaction_date:
        transaction_date = date.today()
    if not created_at:
        created_at = datetime.utcnow()

    # 1. Debit Entry
    dr_data = {
        "source": source,
        "external_reference": f"{external_reference}-DR",
        "account": account_name,
        "amount": amount,
        "currency": currency,
        "description": description,
        "direction": "DEBIT",
        "transaction_date": transaction_date,
        "created_at": created_at,
        "prev_hash": last_hash
    }
    dr_hash = compute_entry_hash(dr_data)
    dr_entry = CoreLedgerEntry(**dr_data, entry_hash=dr_hash)

    # 2. Credit Entry
    cr_data = {
        "source": source,
        "external_reference": f"{external_reference}-CR",
        "account": "REVENUE_SALES", # MVP logic
        "amount": -amount,          # Credits are negative in summation model
        "currency": currency,
        "description": description,
        "direction": "CREDIT",
        "transaction_date": transaction_date,
        "created_at": created_at,
        "prev_hash": dr_hash        # Chains from the Debit
    }
    cr_hash = compute_entry_hash(cr_data)
    cr_entry = CoreLedgerEntry(**cr_data, entry_hash=cr_hash)

    return [dr_entry, cr_entry]

def create_reversal(
    original_entries: List[CoreLedgerEntry],
    reversal_reference: str, # UUID for the reversal event
    description: str,
    last_hash: str,
    created_at: Optional[datetime] = None
) -> List[CoreLedgerEntry]:
    """
    Pure function to create compensating entries that negate original entries.
    
    Logic:
    1. Iterate through original entries.
    2. Create a new entry with NEGATED amount for each.
    3. Chain hashes sequentially.
    """
    if not original_entries:
        raise ValueError("No entries to reverse.")
        
    if not created_at:
        created_at = datetime.utcnow()
        
    reversal_entries = []
    current_hash = last_hash
    
    # Sort original entries to ensure deterministic Reversal order?
    # Usually we reverse in reverse order? Or same order? 
    # For hash chaining, order matters. Let's process in the order provided (assuming it's the transaction order).
    
    for orig in original_entries:
        # Prevent reversing a reversal? 
        # Ideally checked by caller, but we can check if description implies reversal?
        # For now, we trust the caller (Adapter) to select correct targets.
        
        # New Reference: {reversal_uuid}-{original_suffix or index}
        # To identify which leg is being reversed. 
        # Orig Ref: "txn1-DR". Reversal Ref: "rev1-txn1-DR"
        new_ref = f"{reversal_reference}-{orig.external_reference}"

        rev_data = {
            "source": orig.source,
            "external_reference": new_ref,
            "account": orig.account,
            "amount": -orig.amount, # Negate!
            "currency": orig.currency,
            "description": f"REVERSAL: {description} (Ref: {orig.external_reference})",
            "direction": orig.direction, # Direction stays same, amount negates? (Debit -100 vs Credit 100) -> Yes, stays same per MVP logic.
            "transaction_date": date.today(), # Reversal happens TODAY, not in the past
            "created_at": created_at,
            "prev_hash": current_hash
        }
        
        rev_hash = compute_entry_hash(rev_data)
        rev_entry = CoreLedgerEntry(**rev_data, entry_hash=rev_hash)
        
        reversal_entries.append(rev_entry)
        current_hash = rev_hash
        
    return reversal_entries
