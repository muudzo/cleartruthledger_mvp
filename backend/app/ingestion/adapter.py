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
    def ingest(raw_data: Dict[str, Any], last_hash: str = None, original_entries: List[LedgerEntryModel] = None) -> List[LedgerEntryModel]:
        """
        Takes raw input (e.g. from API or CSV), validates it,
        and translates it into a balanced set of LedgerEntries using the pure Ledger Core.
        
        Requires last_hash to build the tamper-evident chain.
        Requires original_entries if type is REVERSAL.
        """
        from backend.app import ledger_core
        from backend.app.ledger_core import CoreLedgerEntry
        from backend.app.domain.events import LedgerEvent, LedgerEventType
        from backend.app.constants import INITIAL_HASH

        if last_hash is None:
             last_hash = INITIAL_HASH
        
        # 1. Parse Core Event
        # This validates the raw input into a domain event
        try:
            event_type_str = raw_data.get("type", "POSTING")
            # Validate type eagerly
            if event_type_str not in [t.value for t in LedgerEventType]:
                 raise ValueError(f"Invalid event type: {event_type_str}")
                 
            event_args = {
                "source": raw_data.get("source", "MANUAL"),
                "external_reference": raw_data.get("reference", str(uuid.uuid4())),
                "type": LedgerEventType(event_type_str),
                "data": raw_data,
                "description": raw_data.get("description", "Manual Entry")
            }
            if "occurred_at" in raw_data:
                event_args["occurred_at"] = raw_data["occurred_at"]
            
            event = LedgerEvent(**event_args)
        except Exception as e:
             if "Invalid event type" in str(e):
                 raise e
             raise ValueError(f"Invalid event data: {str(e)}")

        # 2. Extract Data from Event
        raw_amount = Decimal(str(event.data.get("amount", 0)))
        currency = event.currency
        account_name = event.data.get("account", "CASH_ON_HAND")
        
        core_entries = []

        if event.type == LedgerEventType.REVERSAL:
            if "original_reference" not in event.data:
                raise ValueError("REVERSAL event must specify 'original_reference'")
            if not original_entries:
                 raise ValueError("Original entries not found for reversal")
            
            # Map LedgerEntryModel (Persistence) -> CoreLedgerEntry (Domain)
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
                reversal_reference=event.external_reference,
                description=event.description,
                last_hash=last_hash,
                created_at=event.occurred_at
            )

        else:
            # POSTING
            if raw_amount <= 0:
                raise ValueError("Amount must be positive")
            
            core_entries = ledger_core.create_posting(
                amount=raw_amount,
                currency=currency,
                source=event.source,
                external_reference=event.external_reference,
                description=event.description,
                account_name=account_name,
                last_hash=last_hash,
                transaction_date=event.occurred_at.date(), # Use event date!
                created_at=event.occurred_at
            )

        # Map pure CoreLedgerEntry back to Persistence LedgerEntryModel
        persistence_entries = []
        for c in core_entries:
            # simple mapping since fields match
            m = LedgerEntryModel(**c.model_dump())
            persistence_entries.append(m)
            
        return persistence_entries
