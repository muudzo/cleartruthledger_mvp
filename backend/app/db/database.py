from sqlmodel import SQLModel, Field, create_engine, Session
from typing import Optional
from backend.app.config import settings

# Use settings for DB URL
DATABASE_URL = settings.DATABASE_URL

# Create engine - add connect_args only for SQLite
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    """Create all database tables"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get database session"""
    with Session(engine) as session:
        yield session
