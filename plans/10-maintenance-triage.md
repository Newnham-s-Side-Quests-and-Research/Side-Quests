# 10: Maintenance Triage

**Status:** planned; no implementation or measured result is claimed.

## Objective and inputs

Evaluate routing of synthetic maintenance reports, with safety reports escalated to a person.

Research prototype only; not a live safety system or certified triage service.

## First release and boundaries

No autonomous emergency decisions, real tenant data, automatic contractor dispatch or assumed transcription performance.

## Proposed design

Synthetic reports: conservative rule baseline: optional classifier: urgent escalation/review queue: audit and evaluation.

These are initial design choices, subject to an architecture decision record before implementation. Interfaces, validation, errors and persistence must be specified at the relevant boundary.

## Delivery sequence

1. Confirm inputs, assumptions and scope; record unanswered questions and the baseline.
2. Write the requirements, data contracts, failure cases and verification matrix.
3. Define safety categories and immediate human escalation policy. Create labelled synthetic cases, baseline rules and a review interface; use project 12 to compare candidates.
4. Review the implementation against the requirements, run the verification plan and preserve raw results.
5. Write the case study with results, negative cases, limits and an independent rerun guide.

## Verification and acceptance

Test gas, fire, flooding and safeguarding reports, ambiguous language, adversarial phrasing and unavailable classifier. Verify fail closed routing to a human and no silent drops.

The first release is accepted only when its documented requirements pass, a clean setup can run its checks and any failed or inconclusive checks are visible. Measurements are observations, not promised targets.

## Evidence and metrics

Safety category recall and missed cases, escalation delay in the test environment, false escalation and review burden; report uncertainty.

Keep inputs or their authorised references, configuration, versions, seeds where relevant, commands, outputs and environment details with each run. Link every claim to a test or source.

## Decisions and dependencies

A live deployment requires domain, safeguarding, privacy and legal review; synthetic tests cannot establish safety.

See [programme plan](../programme-plan.md) and [engineering standard](../engineering-standard.md). Original briefs and case studies are in [the source archive](../source/Engineering%20Portfolio/).


## Detailed engineering pack

See the [detailed engineering pack](../engineering-packs/10-maintenance-triage-engineering-pack.md) for requirements, module boundaries, decisions and verification.
