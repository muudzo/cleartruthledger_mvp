import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Phase 0: SQLite MVP
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./clearledger.db")
    
    # Feature Flags
    POSTGRES_ENABLED = False
    
    # Core settings
    # Ensure strict append-only by default? Handled by DB triggers.

settings = Config()
