from sqlmodel import SQLModel, Field, create_engine, Session
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

# Use postgresql:// - SQLAlchemy will auto-detect available psycopg driver
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://clearledger:clearledger@localhost:5432/clearledger_db")

# For psycopg3, we need to specify the dialect explicitly
# But first check if we can use the simpler approach
try:
    from psycopg import Connection
    # If psycopg3 is available, use it
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://")
except ImportError:
    # Fall back to default
    pass

engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    """Create all database tables"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get database session"""
    with Session(engine) as session:
        yield session
