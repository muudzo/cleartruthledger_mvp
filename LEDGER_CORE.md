# Ledger Core Invariants & Intent

## Core Invariants
1. **Append-Only**: The ledger represents a history of facts. Facts cannot be changed, only appended to.
2. **No Mutation**: Existing entries are immutable. Corrections are made via compensating entries (reversals).
3. **Derived Balances**: Balances are not stored as the source of truth; they are derived from the summation of ledger entries.
4. **Idempotency**: Uniqueness is guaranteed by the composite key (source, external_reference, account). This prevents double-counting upon re-ingestion.

## Refactor Intent
The goal of this refactor is to eliminate entropy and enforce separation of concerns. The persistence layer becomes a dumb sink, logic moves to a pure domain layer, and ingestion handles the translation of external chaos into clean double-entry records.

This document serves as a contract to prevent future rationalization of bad architectural decisions.
