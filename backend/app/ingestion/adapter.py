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
    def ingest(raw_data: Dict[str, Any], last_hash: str = "0000000000000000000000000000000000000000000000000000000000000000", original_entries: List[LedgerEntryModel] = None) -> List[LedgerEntryModel]:
        """
        Takes raw input (e.g. from API or CSV), validates it,
        and translates it into a balanced set of LedgerEntries using the pure Ledger Core.
        
        Requires last_hash to build the tamper-evident chain.
        Requires original_entries if type is REVERSAL.
        """
        from backend.app import ledger_core
        from backend.app.ledger_core import CoreLedgerEntry
        
        # 1. Extract core fields
        raw_amount = Decimal(str(raw_data.get("amount", 0)))
        currency = raw_data.get("currency", "USD")
        source = raw_data.get("source", "MANUAL")
        ref = raw_data.get("reference", str(uuid.uuid4()))
        description = raw_data.get("description", "Manual Entry")
        account_name = raw_data.get("account", "CASH_ON_HAND") # Default to cash
        
        event_type = raw_data.get("type", "POSTING")
        if event_type not in ["POSTING", "REVERSAL"]:
             raise ValueError(f"Invalid event type: {event_type}")

        core_entries = []

        if event_type == "REVERSAL":
            if "original_reference" not in raw_data:
                raise ValueError("REVERSAL event must specify 'original_reference'")
            if not original_entries:
                 raise ValueError("Original entries not found for reversal")
            
            # Map LedgerEntryModel (Persistence) -> CoreLedgerEntry (Domain)
            # This is necessary because Core expects its own pure types
            domain_originals = []
            for m in original_entries:
                domain_originals.append(
                    CoreLedgerEntry(
                        source=m.source,
                        external_reference=m.external_reference,
                        account=m.account,
                        amount=m.amount,
                        currency=m.currency,
                        description=m.description,
                        direction=m.direction,
                        transaction_date=m.transaction_date,
                        created_at=m.created_at,
                        prev_hash=m.prev_hash,
                        entry_hash=m.entry_hash
                    )
                )

            core_entries = ledger_core.create_reversal(
                original_entries=domain_originals,
                reversal_reference=ref,
                description=description,
                last_hash=last_hash,
                created_at=datetime.utcnow()
            )

        else:
            # POSTING
            if raw_amount <= 0:
                raise ValueError("Amount must be positive")
            
            core_entries = ledger_core.create_posting(
                amount=raw_amount,
                currency=currency,
                source=source,
                external_reference=ref,
                description=description,
                account_name=account_name,
                last_hash=last_hash,
                transaction_date=datetime.utcnow().date(),
                created_at=datetime.utcnow()
            )

        # Map pure CoreLedgerEntry back to Persistence LedgerEntryModel
        persistence_entries = []
        for c in core_entries:
            # simple mapping since fields match
            m = LedgerEntryModel(**c.model_dump())
            persistence_entries.append(m)
            
        return persistence_entries
