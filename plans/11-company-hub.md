# 11: Company Hub

**Status:** planned; no implementation or measured result is claimed.

## Objective and inputs

Build a source linked briefing prototype with access controlled retrieval and reviewable entity links.

Synthetic firm and local data only initially; real organisational connectors and personal data are excluded.

## First release and boundaries

Start with a deterministic extractive briefing and keyword baseline. Optional model integration follows the repository model gateway; no source access or outbound action by a model.

## Proposed design

Source records: access filter: provenance store and entity review: sourced briefing: review and audit.

These are initial design choices, subject to an architecture decision record before implementation. Interfaces, validation, errors and persistence must be specified at the relevant boundary.

## Delivery sequence

1. Confirm inputs, assumptions and scope; record unanswered questions and the baseline.
2. Write the requirements, data contracts, failure cases and verification matrix.
3. Define source offsets, record versions, roles, access checks and reversible entity links. Build synthetic fixtures and a reviewable briefing before considering an integration.
4. Review the implementation against the requirements, run the verification plan and preserve raw results.
5. Write the case study with results, negative cases, limits and an independent rerun guide.

## Verification and acceptance

Test source traceability, stale versions, wrong merges, missing sources and tamper detection. Exercise role based and adversarial access cases before retrieval and in output.

The first release is accepted only when its documented requirements pass, a clean setup can run its checks and any failed or inconclusive checks are visible. Measurements are observations, not promised targets.

## Evidence and metrics

Claim traceability, obligation recall, entity precision/recall and observed access leakage on the synthetic dataset.

Keep inputs or their authorised references, configuration, versions, seeds where relevant, commands, outputs and environment details with each run. Link every claim to a test or source.

## Decisions and dependencies

Real deployment requires data owner approval, access design and data protection assessment; a hash chain does not prove truth.

See [programme plan](../programme-plan.md) and [engineering standard](../engineering-standard.md). Original briefs and case studies are in [the source archive](../source/Engineering%20Portfolio/).


## Detailed engineering pack

See the [detailed engineering pack](../engineering-packs/11-company-hub-engineering-pack.md) for requirements, module boundaries, decisions and verification.
