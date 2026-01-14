# Ledger Core Trust Boundaries & Invariants

This document defines the strict boundary between the **Ledger Core** (pure domain logic) and the **Outside World** (Adapter, API, Database).

## The Core Guarantee: "Garbage In, Immutable Garbage Out"
The Ledger Core is a passive, mathematical engine. It does not "verify" reality; it **record** assertions made by the outside world.

### 1. What the Core GUARANTEES
*   **Immutability**: Once an entry is hashed and chained, its content cannot be changed without breaking the cryptographic chain.
*   **Double-Entry Integrity**: Every POSTING event creates balanced Debits and Credits. Sum is always zero.
*   **Tamper Evidence**: If `prev_hash` does not match the previous entry's `entry_hash`, the chain is broken.
*   **Determinism**: The same Input + Same History = Identical Output.

### 2. What the Core ASSUMES (Non-Guarantees)
The Core relies on the **Ingestion Adapter** and **Persistence Layer** to enforce these truths:

*   **Uniqueness of IDs**: The Core assumes `event_id` is unique. If the Adapter passes a duplicate `event_id`, the Core will process it. *The Database Unique Constraint must catch this.*
*   **Monotonicity of Sequence**: The Core assumes `ingest_sequence` is strictly increasing. If the Adapter passes unsorted sequences, the Core will record them out of order. *The Ingestion Service must serialize writes.*
*   **Time Veracity**: The Core records the `occurred_at` timestamp provided. It does not check if the time is close to "now".
*   **Reference Validity**: The Core does not check if `external_reference` points to a real external object (e.g., a valid User ID or Invoice ID).

## The Trust Boundary
The **Adapter** is the gatekeeper.

| Responsibility | Component | Method |
| :--- | :--- | :--- |
| **Normalize Data** | Adapter | `canonicalize_event_data` |
| **Assign Event ID** | Adapter | SHA-256 Fingerprint |
| **Assign Sequence** | Service/DB | Atomic Counter |
| **Enforce Uniqueness** | Database | `UNIQUE(event_id)` |
| **Enforce Balance** | Core | `create_posting` |
| **Enforce Chain** | Core | `compute_entry_hash` |

## Failure Modes
*   **Double Spending**: Prevented by DB Unique Constraints on `event_id`.
*   **Retroactive Editing**: Prevented by Hash Chain verification (auditors).
*   **Lying Adapter**: If the Adapter creates a fake event `{"amount": 1M}`, the Core will validly process it. The **Auditor** is responsible for reconciling Ledger Entries with external reality (Bank Statements, etc.).
