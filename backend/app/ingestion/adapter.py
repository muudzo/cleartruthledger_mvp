from datetime import datetime
from typing import List, Dict, Any
from decimal import Decimal
import uuid
from backend.app.domain.models import LedgerEntry
from backend.app.persistence.models import LedgerEntryModel

class IngestionAdapter:
    """
    Translates external chaos into clean double-entry ledger records.
    """
    
    @staticmethod
    def ingest(raw_data: Dict[str, Any], last_hash: str = "0000000000000000000000000000000000000000000000000000000000000000") -> List[LedgerEntryModel]:
        """
        Takes raw input (e.g. from API or CSV), validates it,
        and translates it into a balanced set of LedgerEntries.
        
        Requires last_hash to build the tamper-evident chain.
        """
        
        # 1. Extract core fields
        amount = Decimal(str(raw_data.get("amount", 0)))
        currency = raw_data.get("currency", "USD")
        source = raw_data.get("source", "MANUAL")
        ref = raw_data.get("reference", str(uuid.uuid4()))
        description = raw_data.get("description", "Manual Entry")
        account_name = raw_data.get("account", "CASH_ON_HAND") # Default to cash
        
        if amount <= 0:
            raise ValueError("Amount must be positive")

        entries = []
        
        # 2. Create Debit Entry (Asset Increase)
        # e.g. Cash received
        dr_entry = LedgerEntryModel(
            source=source,
            external_reference=f"{ref}-DR", # Append suffix to make unique per leg
            account=account_name,
            amount=amount,
            currency=currency,
            description=description,
            direction="DEBIT",
            transaction_date=datetime.utcnow().date(),
            prev_hash=last_hash,
            entry_hash="" # Computed below
        )
        dr_entry.entry_hash = dr_entry.compute_hash()
        entries.append(dr_entry)
        
        # Update last_hash for the next entry in the batch
        current_hash = dr_entry.entry_hash
        
        # 3. Create Credit Entry (Revenue Increase)
        # e.g. Sales Revenue
        cr_entry = LedgerEntryModel(
            source=source,
            external_reference=f"{ref}-CR",
            account="REVENUE_SALES", # Hardcoded offset for MVP
            amount=-amount, 
            currency=currency,
            description=description,
            direction="CREDIT",
            transaction_date=datetime.utcnow().date(),
            prev_hash=current_hash,
            entry_hash="" # Computed below
        )
        cr_entry.entry_hash = cr_entry.compute_hash()
        entries.append(cr_entry)
        
        return entries
