from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from datetime import date
from backend.app.db.database import get_session
from backend.app.schemas.dashboard import DailyTruthResponse
from backend.app.services.aggregation import get_daily_totals, get_channel_breakdown

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/daily", response_model=DailyTruthResponse)
def get_daily_truth(
    target_date: date = Query(default_factory=date.today),
    session: Session = Depends(get_session)
):
    """Get daily truth dashboard data"""
    totals = get_daily_totals(1, target_date, session)
    channels = get_channel_breakdown(1, target_date, session)
    
    return {
        "date": target_date.isoformat(),
        "totals": totals,
        "channels": channels
    }
