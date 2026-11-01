# 06: Exchange Lab

**Status:** planned; no implementation or measured result is claimed.

## Objective and inputs

Build a deterministic matching engine and assess optimisations without changing matching outcomes.

Synthetic order flow; single threaded first version; no networking, clearing or production exchange readiness.

## First release and boundaries

Price time priority and supported order types must be written down before implementation; optimise only after a correct reference exists.

## Proposed design

Reference order book: matching and sequencing: event ledger: replay/differential tests: benchmark harness.

These are initial design choices, subject to an architecture decision record before implementation. Interfaces, validation, errors and persistence must be specified at the relevant boundary.

## Delivery sequence

1. Confirm inputs, assumptions and scope; record unanswered questions and the baseline.
2. Write the requirements, data contracts, failure cases and verification matrix.
3. Specify order lifecycle, price time priority, matching and accounting. Implement a simple reference and C++ candidate, replay identical order streams, then benchmark controlled changes.
4. Review the implementation against the requirements, run the verification plan and preserve raw results.
5. Write the case study with results, negative cases, limits and an independent rerun guide.

## Verification and acceptance

Test FIFO ties, partial fills, cancels, invalid orders and conservation. Differentially compare every emitted event and final book for seeded workloads; benchmark only passing versions.

The first release is accepted only when its documented requirements pass, a clean setup can run its checks and any failed or inconclusive checks are visible. Measurements are observations, not promised targets.

## Evidence and metrics

Exact event equivalence and invariant failures; latency distribution and throughput with machine, compiler, workload and methodology recorded.

Keep inputs or their authorised references, configuration, versions, seeds where relevant, commands, outputs and environment details with each run. Link every claim to a test or source.

## Decisions and dependencies

Set supported order types, numeric representation and benchmark environment during design.

See [programme plan](../programme-plan.md) and [engineering standard](../engineering-standard.md). Original briefs and case studies are in [the source archive](../source/Engineering%20Portfolio/).


## Detailed engineering pack

See the [detailed engineering pack](../engineering-packs/06-exchange-lab-engineering-pack.md) for requirements, module boundaries, decisions and verification.
