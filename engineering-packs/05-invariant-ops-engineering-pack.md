# 05: Invariant Ops: engineering pack

**Status:** proposed design for review; no implementation or results claimed. Read with the [common standard](00-engineering-pack-standard.md), [project plan](../plans/05-invariant-ops.md) and original [technical brief](../source/Engineering%20Portfolio/Project%2005%20Invariant%20Ops/02%20Technical%20Two%20Pager.pdf) and [case study](../source/Engineering%20Portfolio/Project%2005%20Invariant%20Ops/03%20Case%20Study.pdf).

## Purpose and first release
Model synthetic purchase orders, receipts and invoice approvals across unreliable delivery. Prove selected business invariants under specified duplicates, retries and crash points; do not assert exactly once transport or production readiness.

## Modules and data contracts
`domain` defines immutable IDs, order/receipt/invoice state and invariants; `commands` validates intent and authorisation; `store` persists records, transaction version and unique idempotency key; `outbox` atomically records pending effects with domain changes; `consumer` deduplicates `(source, event_id)` transactionally; `reconciliation` reports mismatches and proposed corrections; `audit` records actor, action, reason and before/after references. SQLite can exercise local mechanics; PostgreSQL integration tests are required before relying on concurrent transaction behaviour. No live ERP calls.

State transitions: orders draft to approved to closed; receipt corrections are new events, not silent overwrites; invoice pending to approved or exception to corrected/reviewed. These are proposed and require domain approval. A business posting must have one durable source identity, amount in currency minor units and audit record. Conflicting idempotency keys with different payloads fail explicitly.

## Requirements and verification
| ID | Requirement and acceptance | Verification |
| --- | --- | --- |
| IO 01 | State transitions and amount/quantity invariants are enforced at domain and storage boundaries. | Table driven valid/invalid transitions, currency and unit boundary cases. |
| IO 02 | Repeated event or command does not create a second business posting. | Repeat identical IDs concurrently and after restart; changed payload with same ID is conflict. |
| IO 03 | State update and outbox record commit atomically. | Inject crash before/after commit, acknowledgement and retry; inspect database after restart. |
| IO 04 | Late or out of order events produce explicit pending/exception state, not silent corruption. | Deliver permutations, missing predecessors and schema version mismatch. |
| IO 05 | Reconciliation identifies planted mismatches and correction creates a traceable record. | Compare synthetic ledger to independent expected totals; replay correction twice. |

## Decisions and delivery
Choose source authority, idempotency retention, transaction isolation, ordering, retry/dead letter policy and correction permissions before implementation. Threats include duplicate IDs, partial commits, stale reads and dropped messages; disclose uncovered scenarios. First build domain and local store; add atomic outbox/deduplication and crash harness; run PostgreSQL concurrency integration suite; publish event traces and recovery times. Original brief calls for synthetic legacy APIs and crash/ack/retry/schema/restart campaigns: add adapters and expanded campaigns after the local baseline; maintain the same invariants.
