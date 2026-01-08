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
        # 1. Adapt/Translate
        entries = IngestionAdapter.ingest(event_payload)
        
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

