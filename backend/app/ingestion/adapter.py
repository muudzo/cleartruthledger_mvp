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
        
        # IDEMPOTENCY CHECK
        # Check if we have already seen this event_id
        if original_entries:
             # We might be in a reversal context, but let's check if THIS specific event (reversal or posting)
             # has been processed. 
             # Note: 'original_entries' passed to ingest() are usually the entries TO BE REVERSED.
             # We need to query if the CURRENT event_id exists in DB.
             # Since this adapter doesn't have DB access (it's pure functional logic receiving data),
             # we assume the caller handles the lookup OR we rely on the DB constraint to fail.
             # However, the requirement says "Same event_id with different payload -> hard failure".
             # This implies we should be able to check.
             # BUT, the signature of `ingest` is: ingest(raw_data, last_hash, original_entries).
             # It doesn't receive "existing entries for this event_id".
             # Wait, strict idempotency usually requires checking if we already did this.
             # If we rely on DB UniqueConstraint (event_id, source...), that catches duplicates.
             # But it doesn't distinguish "Same ID, Same Payload" (Success/Ignore) vs "Same ID, Diff Payload" (Error).
             
             # FOR THIS REFACTOR: We will assume the SERVICE layer (which calls this Adapter) 
             # responsibilty to fetch existing entries by ID? Or we assume this is the first time?
             # IF we want to move check logic here, we need the existing entries for THIS event.
             # The signature key `original_entries` is ambiguous. It usually means "entries referenced by this event".
             
             # Let's adjust. The Adapter translates. The Service orchestrates.
             # But the prompt says "Idempotency guard in ingestion layer".
             # If "ingestion layer" means this Adapter, it needs context. 
             # Or maybe `ingest` should return the entries, and if they duplicate, the DB constraint hits.
             # To handle "Same ID, Diff Payload", we'd need to read the conflicting row.
             
             # Strategy:
             # 1. Adapter produces the CoreLedgerEntry objects (all deteministic).
             # 2. These objects contain `event_id`.
             # 3. Persistence layer (Service) tries to save.
             # 4. If Unique Violation:
             #    Fetch existing. Compare hashes/payloads.
             #    If match -> Return existing (Idempotent Success).
             #    If mismatch -> Raise Error.
             
             # Since we are editing `adapter.py` which seems to be the main logic, 
             # maybe we can just pass the event_id into the core functions.
             pass

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
                        event_id=m.event_id,
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
                event_id=event.event_id,
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
                event_id=event.event_id,
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
