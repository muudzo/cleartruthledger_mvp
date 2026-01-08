from typing import List, Dict
from decimal import Decimal
from backend.app.domain.models import IngestionEvent, LedgerEntry

def normalize_event(event: IngestionEvent) -> List[LedgerEntry]:
    """
    Converts a raw ingestion event into a list of balanced ledger entries.
    Must be idempotent and deterministic.
    """
    raise NotImplementedError("Ledger core normalization not implemented yet")

def compute_balance(entries: List[LedgerEntry]) -> Dict[str, Decimal]:
    """
    Derives account balances from a history of ledger entries.
    """
    raise NotImplementedError("Ledger core balance computation not implemented yet")
