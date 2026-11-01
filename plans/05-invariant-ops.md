# 05: Invariant Ops

**Status:** planned; no implementation or measured result is claimed.

## Objective and inputs

Demonstrate procurement workflow correctness under duplicate, delayed and interrupted messages.

Synthetic orders, receipts and invoices; no production ledger or claim of exactly once transport.

## First release and boundaries

Start as a local service and database; no external ERP integration in the first release.

## Proposed design

Command/API: durable state and event log: idempotent handlers: reconciliation and correction: audit trail.

These are initial design choices, subject to an architecture decision record before implementation. Interfaces, validation, errors and persistence must be specified at the relevant boundary.

## Delivery sequence

1. Confirm inputs, assumptions and scope; record unanswered questions and the baseline.
2. Write the requirements, data contracts, failure cases and verification matrix.
3. Specify order, receipt and invoice state machines and invariants. Implement a simple baseline then durable idempotency and replay; document transaction boundaries and recovery.
4. Review the implementation against the requirements, run the verification plan and preserve raw results.
5. Write the case study with results, negative cases, limits and an independent rerun guide.

## Verification and acceptance

Inject duplicates, out of order delivery, concurrent requests and process interruption around commits. Verify invariants, no duplicate business posting and replay/reconciliation from recorded events.

The first release is accepted only when its documented requirements pass, a clean setup can run its checks and any failed or inconclusive checks are visible. Measurements are observations, not promised targets.

## Evidence and metrics

Invariant violations, recovery outcomes and replay reproducibility; report scenario coverage and unhandled failure modes.

Keep inputs or their authorised references, configuration, versions, seeds where relevant, commands, outputs and environment details with each run. Link every claim to a test or source.

## Decisions and dependencies

Select transaction boundary and correction semantics before implementation.

See [programme plan](../programme-plan.md) and [engineering standard](../engineering-standard.md). Original briefs and case studies are in [the source archive](../source/Engineering%20Portfolio/).


## Detailed engineering pack

See the [detailed engineering pack](../engineering-packs/05-invariant-ops-engineering-pack.md) for requirements, module boundaries, decisions and verification.
