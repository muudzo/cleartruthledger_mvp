# Ledger Core Invariants & Architecture (Phase 1)

## Core Invariants
1. **Append-Only**: The ledger represents a history of facts. Facts cannot be changed, only appended to. Enforced by DB triggers.
2. **Double-Entry**: All value movement is represented by paired `DEBIT` and `CREDIT` entries summing to zero.
3. **Immutability**: Reversals are compensating entries, not deletions.
4. **Tamper-Evident**: Every entry contains a cryptographic hash (`entry_hash`) linking to `prev_hash`.

## Architecture

### 1. Ingestion Adapter (`backend/app/ingestion/adapter.py`)
- **Role**: Validation & I/O.
- **Responsibility**: 
    - Accepts raw/chaotic input (Dicts, API payloads).
    - Converts input to `LedgerEvent`.
    - Fetches state (`last_hash`, `original_entries`) from DB.
    - Delegated accounting logic to **Ledger Core**.
    - Maps Core results to Persistence models.

### 2. Ledger Core (`backend/app/ledger_core.py`)
- **Role**: Pure Domain Logic.
- **Responsibility**:
    - **No Dependencies**: Pure Python, no DB, no API.
    - **Invariants**: Enforces positive amounts, double-entry balancing, hash chaining.
    - **Determinism**: Given same inputs (including time), produces identical outputs.

### 3. Persistence (`backend/app/persistence/models.py`)
- **Role**: Storage.
- **Responsibility**:
    - Stores `LedgerEntryModel`.
    - DB Triggers prevent `UPDATE` and `DELETE`.

## Technical Debt & Limitations (Phase 1)
- **SQLite**: Used for MVP. Triggers are primitive. Migration to PostgreSQL required for production concurrency.
- **Replayability**: Relies on input stream containing `occurred_at`. Adapter defaults to `utcnow()` if missing, breaking strict replay if raw logs lack timestamps.
- **Account Types**: Currently "CASH" and "REVENUE_SALES" are hardcoded or loosely typed strings.
- **Frontend**: None. API-only.

## Next Steps
- Migrate to PostgreSQL.
- Implement strict Account Registry.
- Build Read-Model Projections (Balances).
