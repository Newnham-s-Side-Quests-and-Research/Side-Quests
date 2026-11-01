# 12: Workflow Evaluation Harness

**Status:** planned; no implementation or measured result is claimed.

## Objective and inputs

Build a reusable replay and scoring harness for comparing AI workflow changes before human release decisions.

Synthetic or openly licensed cases; a passing gate informs a person and does not prove safety.

## First release and boundaries

Start with deterministic local adapters and a CLI; external models, dashboards and automatic deployment are not required.

## Proposed design

Versioned case library: candidate/baseline adapters: replay runner: scorers: configurable gate and human readable report.

These are initial design choices, subject to an architecture decision record before implementation. Interfaces, validation, errors and persistence must be specified at the relevant boundary.

## Delivery sequence

1. Confirm inputs, assumptions and scope; record unanswered questions and the baseline.
2. Write the requirements, data contracts, failure cases and verification matrix.
3. Define versioned case, run and result schemas. Implement deterministic replay, field and abstention scorers, baseline comparisons and gate configuration. Add repeat trials for nondeterministic adapters.
4. Review the implementation against the requirements, run the verification plan and preserve raw results.
5. Write the case study with results, negative cases, limits and an independent rerun guide.

## Verification and acceptance

Use known fixtures and deliberately defective candidates to test score calculations and gate behaviour; check malformed cases, missing outputs and reproducible runs. Measure false blocks as well as caught defects.

The first release is accepted only when its documented requirements pass, a clean setup can run its checks and any failed or inconclusive checks are visible. Measurements are observations, not promised targets.

## Evidence and metrics

Planted defect detection, false blocks, score variance, case coverage and recorded latency/cost where available.

Keep inputs or their authorised references, configuration, versions, seeds where relevant, commands, outputs and environment details with each run. Link every claim to a test or source.

## Decisions and dependencies

Review gate thresholds and dataset splits before using results for any release decision.

See [programme plan](../programme-plan.md) and [engineering standard](../engineering-standard.md). Original briefs and case studies are in [the source archive](../source/Engineering%20Portfolio/).


## Detailed engineering pack

See the [detailed engineering pack](../engineering-packs/12-workflow-evaluation-harness-engineering-pack.md) for requirements, module boundaries, decisions and verification.
