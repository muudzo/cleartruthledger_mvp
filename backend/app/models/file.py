from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class File(SQLModel, table=True):
    """File model for screenshot uploads"""
    __tablename__ = "files"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    filename: str = Field(max_length=255)
    filepath: str = Field(max_length=500)
    file_size: int  # in bytes
    mime_type: str = Field(max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)
