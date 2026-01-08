from pydantic import BaseModel, Field, field_validator
from datetime import date, datetime
from typing import Optional
from backend.app.models.transaction import Channel, Direction, Status


class TransactionCreate(BaseModel):
    """Schema for creating a transaction"""
    amount: float = Field(gt=0, description="Amount must be positive")
    channel: Channel
    direction: Direction
    status: Status
    reference: str = Field(max_length=500)
    transaction_date: date = Field(default_factory=date.today)
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v


class TransactionUpdate(BaseModel):
    """Schema for updating transaction status"""
    status: Status


class TransactionResponse(BaseModel):
    """Schema for transaction in responses"""
    id: int
    user_id: int
    amount: float
    channel: Channel
    direction: Direction
    status: Status
    reference: str
    transaction_date: date
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
