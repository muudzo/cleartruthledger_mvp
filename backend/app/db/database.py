from sqlmodel import SQLModel, Field, create_engine, Session
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

# Explicitly use postgresql+psycopg:// for psycopg3
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://clearledger:clearledger@localhost:5432/clearledger_db")

# Create engine with psycopg3
engine = create_engine(DATABASE_URL, echo=True, future=True)


def create_db_and_tables():
    """Create all database tables"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get database session"""
    with Session(engine) as session:
        yield session
