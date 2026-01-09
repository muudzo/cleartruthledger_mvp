from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import Dict, Any
from backend.app.db.database import get_session
from backend.app.ingestion.adapter import IngestionAdapter
from backend.app.persistence.models import LedgerEntryModel

router = APIRouter(prefix="/api/ingest", tags=["ingestion"])

@router.post("", status_code=status.HTTP_201_CREATED)
def ingest_event(
    event_payload: Dict[str, Any],
    session: Session = Depends(get_session)
):
    """
    Ingest a raw event and persist it as ledger entries.
    Idempotency is enforced by the database.
    """
    try:
        # 0. Get Last Hash (Genesis if empty)
        from sqlmodel import select
        last_entry = session.exec(select(LedgerEntryModel).order_by(LedgerEntryModel.id.desc())).first()
        last_hash = last_entry.entry_hash if last_entry else "0000000000000000000000000000000000000000000000000000000000000000"
        
        # 0.5. Get Original Entries (if Reversal)
        original_entries = None
        if event_payload.get("type") == "REVERSAL":
             orig_ref = event_payload.get("original_reference")
             # How to query? We stored "external_reference" as "{ref}-DR" and "{ref}-CR".
             # So we need to find entries where external_reference LIKE "{orig_ref}-%".
             # Or we expect orig_ref to be the base reference? 
             # Logic in adapter: `external_reference=f"{ref}-DR"`.
             # So if user passes "some-uuid", we look for "some-uuid-DR" and "some-uuid-CR".
             # Or we look for source matching? Ideally idempotency key was (source, ref, account).
             # Let's search by containing string or expected suffix?
             # Safer: Select where external_reference IN (...) ?
             # But we don't know the suffixes strictly (adapter implementation detail).
             # Let's try `startswith`.
             from sqlmodel import col
             statement = select(LedgerEntryModel).where(col(LedgerEntryModel.external_reference).contains(orig_ref))
             original_entries = session.exec(statement).all()
        
        # 1. Adapt/Translate
        entries = IngestionAdapter.ingest(event_payload, last_hash, original_entries)
        
        # 2. Persist
        for entry in entries:
            session.add(entry)
            
        session.commit()
        
        return {"status": "accepted", "entries_created": len(entries)}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Check for integrity error (idempotency)
        if "integrity" in str(e).lower():
             raise HTTPException(status_code=409, detail="Duplicate entry detected (Idempotency)")
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

