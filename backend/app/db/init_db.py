from sqlmodel import Session, text
from backend.app.db.database import engine

def init_db():
    print("Initializing database triggers...")
    with Session(engine) as session:
        # SQLite doesn't support REVOKE, so we use Triggers to prevent mutation.
        
        # 1. Prevent UPDATE
        # Note: SQLite triggers are created on the table.
        # RAISE(ABORT, 'message') aborts the operation.
        
        create_update_trigger = text("""
        CREATE TRIGGER IF NOT EXISTS prevent_ledger_update
        BEFORE UPDATE ON ledger_entries
        BEGIN
            SELECT RAISE(ABORT, 'Ledger entries are append-only. UPDATE is not allowed.');
        END;
        """)
        
        # 2. Prevent DELETE
        create_delete_trigger = text("""
        CREATE TRIGGER IF NOT EXISTS prevent_ledger_delete
        BEFORE DELETE ON ledger_entries
        BEGIN
            SELECT RAISE(ABORT, 'Ledger entries are append-only. DELETE is not allowed.');
        END;
        """)
        
        session.exec(create_update_trigger)
        session.exec(create_delete_trigger)
        session.commit()
    print("Database triggers applied.")

if __name__ == "__main__":
    init_db()
