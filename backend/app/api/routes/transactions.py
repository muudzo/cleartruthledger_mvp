from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from typing import List
from datetime import date, datetime, timedelta
from backend.app.db.database import get_session
from backend.app.models.user import User
from backend.app.models.transaction import Transaction
from backend.app.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionResponse
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create a new transaction"""
    new_transaction = Transaction(
        user_id=current_user.id,
        **transaction_data.model_dump()
    )
    
    session.add(new_transaction)
    session.commit()
    session.refresh(new_transaction)
    
    return new_transaction


@router.patch("/{transaction_id}", response_model=TransactionResponse)
def update_transaction_status(
    transaction_id: int,
    update_data: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update transaction status"""
    statement = select(Transaction).where(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    )
    transaction = session.exec(statement).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    transaction.status = update_data.status
    transaction.updated_at = datetime.utcnow()
    
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    
    return transaction


@router.get("", response_model=List[TransactionResponse])
def get_transactions(
    transaction_date: date = Query(default_factory=date.today),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get transactions for a specific date"""
    statement = select(Transaction).where(
        Transaction.user_id == current_user.id,
        Transaction.transaction_date == transaction_date
    ).order_by(Transaction.created_at.desc())
    
    transactions = session.exec(statement).all()
    return transactions
