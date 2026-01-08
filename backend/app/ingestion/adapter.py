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
    def ingest(raw_data: Dict[str, Any]) -> List[LedgerEntryModel]:
        """
        Takes raw input (e.g. from API or CSV), validates it,
        and translates it into a balanced set of LedgerEntries.
        
        Note: This returns persistence models ready for the DB.
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
        entries.append(LedgerEntryModel(
            source=source,
            external_reference=f"{ref}-DR", # Append suffix to make unique per leg
            account=account_name,
            amount=amount,
            currency=currency,
            description=description,
            direction="DEBIT",
            transaction_date=datetime.utcnow().date()
        ))
        
        # 3. Create Credit Entry (Revenue Increase)
        # e.g. Sales Revenue
        entries.append(LedgerEntryModel(
            source=source,
            external_reference=f"{ref}-CR",
            account="REVENUE_SALES", # Hardcoded offset for MVP
            amount=-amount, # Credits are negative in some systems, or just positive magnitude? 
                           # Ledger Core Invariant 3 says "Derived Balances". 
                           # Usually Debits + Credits = 0.
                           # Let's assume signed convention: Assets Positive, Revenue Negative (Credit).
            currency=currency,
            description=description,
            direction="CREDIT",
            transaction_date=datetime.utcnow().date()
        ))
        
        return entries
