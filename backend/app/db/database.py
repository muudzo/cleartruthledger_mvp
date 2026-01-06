from sqlmodel import SQLModel, Field, create_engine, Session
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

# Use MySQL for database
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root@localhost:3306/clearledger_db")

# Create engine
engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    """Create all database tables"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get database session"""
    with Session(engine) as session:
        yield session
