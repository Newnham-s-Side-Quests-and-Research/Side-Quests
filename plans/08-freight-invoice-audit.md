# 08: Freight Invoice Audit

**Status:** planned; no implementation or measured result is claimed.

## Objective and inputs

Reconstruct synthetic carrier charges from contracts and shipment events and explain discrepancies.

Synthetic contracts, invoices and events; no actual dispute submission or recovery claim.

## First release and boundaries

Start with one explicit rate card format and a limited set of accessorials; ambiguous clauses require review.

## Proposed design

Versioned tariffs and shipment facts: rating engine: invoice reconciliation: evidence backed exception queue.

These are initial design choices, subject to an architecture decision record before implementation. Interfaces, validation, errors and persistence must be specified at the relevant boundary.

## Delivery sequence

1. Confirm inputs, assumptions and scope; record unanswered questions and the baseline.
2. Write the requirements, data contracts, failure cases and verification matrix.
3. Define money rounding, tariff effective dates and event provenance. Build a reference rate calculator and reconciliation pipeline on labelled batches; add reviewable explanations.
4. Review the implementation against the requirements, run the verification plan and preserve raw results.
5. Write the case study with results, negative cases, limits and an independent rerun guide.

## Verification and acceptance

Use hand calculated examples, boundary weights, date changes, fuel surcharges, duplicate lines and missing events; verify each discrepancy traces to tariff and fact.

The first release is accepted only when its documented requirements pass, a clean setup can run its checks and any failed or inconclusive checks are visible. Measurements are observations, not promised targets.

## Evidence and metrics

Charge accuracy, discrepancy precision/recall, unexplained cases and review effort on the labelled set.

Keep inputs or their authorised references, configuration, versions, seeds where relevant, commands, outputs and environment details with each run. Link every claim to a test or source.

## Decisions and dependencies

Agree contract interpretation and dispute authority; real carrier behaviour is outside the simulation.

See [programme plan](../programme-plan.md) and [engineering standard](../engineering-standard.md). Original briefs and case studies are in [the source archive](../source/Engineering%20Portfolio/).


## Detailed engineering pack

See the [detailed engineering pack](../engineering-packs/08-freight-invoice-audit-engineering-pack.md) for requirements, module boundaries, decisions and verification.
