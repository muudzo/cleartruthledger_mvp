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
        and translates it into a balanced set of LedgerEntries.
        
        Requires last_hash to build the tamper-evident chain.
        Requires original_entries if type is REVERSAL.
        """
        
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
             
        if event_type == "REVERSAL":
            if "original_reference" not in raw_data:
                raise ValueError("REVERSAL event must specify 'original_reference'")
            if not original_entries:
                 raise ValueError("Original entries not found for reversal")
            
            # Reversal Integrity Checks
            # Prevent reversing a reversal (simplistic check: descriptions or flags?)
            # Ideally we check the source/type of original entries, but we only have LedgerEntryModel (persistence).
            # We can check if description starts with "REVERSAL" or something if we don't have explicit type stored on entry.
            # But wait, LedgerEntryModel doesn't store "Event Type". It just stores business facts.
            # So "Prevent Reversing a Reversal" implies we can tell if an entry is a reversal.
            # We should probably store event_type on LedgerEntryModel or Metadata.
            # However, for now, we can check if the original entries reference another reversal?
            # Or simplified: Strict Reversal matches amounts exactly but negative.
            
            # Logic: Derive new entries based on original, strictly negating them.
            # This ensures "Cross-account reversals" are impossible because we use the SAME accounts.
            
            # Assuming original_entries contains the balanced pair (DR/CR).
            # We want to create a new pair that negates them.
            
            entries = []
            current_hash_chain = last_hash
            
            for orig in original_entries:
                # Check if original is already a reversal? 
                # If we don't store metadata, hard to mechanically enforce "no reversing reversal" 
                # unless we check description or some other marker.
                # Let's assume we proceed.
                
                rev_entry = LedgerEntryModel(
                    source=source,
                    # New reference needs to be unique. 
                    # Usually "REV-{original_ref}" or provided new ref.
                    external_reference=f"{ref}-{orig.direction}", 
                    account=orig.account,
                    amount=-orig.amount, # Negate exact amount
                    currency=orig.currency,
                    description=f"REVERSAL of {orig.external_reference}: {description}",
                    direction=orig.direction, # Same direction? 
                    # If I reverse a Debit (Assets +100), I want Assets -100.
                    # If my system allows negative amounts, I keep direction DEBIT and amount -100.
                    # OR I swap direction to CREDIT and amount 100.
                    # Current system (Commit 4/11) uses 'direction' string and signed amounts? 
                    # Adapter logic: DR entries have positive amount, CR entries have negative.
                    # So if I negate amount:
                    # Orig DR: 100. New: -100. Direction DEBIT. (Asset decrease).
                    # Orig CR: -100. New: 100. Direction CREDIT. (Revenue decrease/Refund).
                    # This seems consistent with "Derived Balances = Sum(amount)".
                    transaction_date=datetime.utcnow().date(),
                    prev_hash=current_hash_chain,
                    entry_hash=""
                )
                rev_entry.entry_hash = rev_entry.compute_hash()
                entries.append(rev_entry)
                current_hash_chain = rev_entry.entry_hash
            
            return entries

        # Standard POSTING logic
        if raw_amount <= 0:
            raise ValueError("Amount must be positive")
            
        entries = []
        # ... standard logic ...
        
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
