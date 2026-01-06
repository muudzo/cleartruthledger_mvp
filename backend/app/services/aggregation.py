from sqlmodel import Session, select, func
from datetime import date
from typing import Dict, List
from backend.app.models.transaction import Transaction, Status, Channel, Direction


def get_daily_totals(user_id: int, target_date: date, session: Session) -> Dict:
    """Get daily totals grouped by status"""
    totals = {
        "expected": 0.0,
        "received": 0.0,
        "pending": 0.0,
        "missing": 0.0
    }
    
    # Query transactions for the date
    statement = select(Transaction).where(
        Transaction.user_id == user_id,
        Transaction.transaction_date == target_date,
        Transaction.direction == Direction.INCOMING  # Only incoming for daily truth
    )
    
    transactions = session.exec(statement).all()
    
    for txn in transactions:
        if txn.status == Status.EXPECTED:
            totals["expected"] += txn.amount
        elif txn.status == Status.RECEIVED:
            totals["received"] += txn.amount
        elif txn.status == Status.PENDING:
            totals["pending"] += txn.amount
        elif txn.status == Status.MISSING:
            totals["missing"] += txn.amount
    
    return totals


def get_channel_breakdown(user_id: int, target_date: date, session: Session) -> List[Dict]:
    """Get transaction breakdown by channel"""
    statement = select(Transaction).where(
        Transaction.user_id == user_id,
        Transaction.transaction_date == target_date,
        Transaction.direction == Direction.INCOMING
    )
    
    transactions = session.exec(statement).all()
    
    # Group by channel
    channel_data = {}
    for txn in transactions:
        channel_name = txn.channel.value
        if channel_name not in channel_data:
            channel_data[channel_name] = {
                "channel": channel_name,
                "count": 0,
                "total": 0.0
            }
        channel_data[channel_name]["count"] += 1
        channel_data[channel_name]["total"] += txn.amount
    
    return list(channel_data.values())
