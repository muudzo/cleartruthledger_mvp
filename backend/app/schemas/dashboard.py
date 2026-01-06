from pydantic import BaseModel
from typing import List


class ChannelBreakdown(BaseModel):
    """Channel breakdown data"""
    channel: str
    count: int
    total: float


class DailyTruthResponse(BaseModel):
    """Daily truth dashboard data"""
    date: str
    totals: dict
    channels: List[ChannelBreakdown]
