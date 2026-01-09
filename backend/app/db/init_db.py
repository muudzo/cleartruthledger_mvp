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
        
        # 3. Create Views (Projections)
        
        # View: Account Balances
        create_view_balances = text("""
        CREATE VIEW IF NOT EXISTS view_account_balances AS
        SELECT 
            account,
            currency,
            SUM(amount) as balance,
            COUNT(*) as entry_count,
            MAX(transaction_date) as last_activity
        FROM ledger_entries
        GROUP BY account, currency;
        """)
        
        # View: Trial Balance (Should be zero globally per currency)
        create_view_trial = text("""
        CREATE VIEW IF NOT EXISTS view_trial_balance AS
        SELECT 
            currency,
            SUM(amount) as net_balance
        FROM ledger_entries
        GROUP BY currency;
        """)
        
        session.exec(create_view_balances)
        session.exec(create_view_trial)
        
        session.commit()
    print("Database triggers and views applied.")

if __name__ == "__main__":
    init_db()
