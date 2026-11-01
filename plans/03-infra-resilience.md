# 03: Infra Resilience

**Status:** planned; no implementation or measured result is claimed.

## Objective and inputs

Investigate whether evidence based diagnosis can distinguish an initiating fault from downstream alarms.

Synthetic material handling plant and fault scenarios only; no certified protection function.

## First release and boundaries

Conveyor and sensor model first; real PLC integration and live plant controls are excluded.

## Proposed design

Plant simulator: timestamped event stream: causal/diagnostic model: ranked explanations: benchmark report.

These are initial design choices, subject to an architecture decision record before implementation. Interfaces, validation, errors and persistence must be specified at the relevant boundary.

## Delivery sequence

1. Confirm inputs, assumptions and scope; record unanswered questions and the baseline.
2. Write the requirements, data contracts, failure cases and verification matrix.
3. Define plant topology, event schema and injected faults. Build an alarm only baseline and a ranked diagnosis method using the same event data. Freeze fault scenarios and hold out seeds.
4. Review the implementation against the requirements, run the verification plan and preserve raw results.
5. Write the case study with results, negative cases, limits and an independent rerun guide.

## Verification and acceptance

Check event ordering and planted root causes; run single faults, simultaneous faults, missing events and ambiguous signatures; compare ranked outputs and explanations to ground truth.

The first release is accepted only when its documented requirements pass, a clean setup can run its checks and any failed or inconclusive checks are visible. Measurements are observations, not promised targets.

## Evidence and metrics

Top k root cause accuracy, time to diagnosis, false leads and coverage, reported per fault type.

Keep inputs or their authorised references, configuration, versions, seeds where relevant, commands, outputs and environment details with each run. Link every claim to a test or source.

## Decisions and dependencies

Record causal assumptions; correlation alone does not establish cause.

See [programme plan](../programme-plan.md) and [engineering standard](../engineering-standard.md). Original briefs and case studies are in [the source archive](../source/Engineering%20Portfolio/).


## Detailed engineering pack

See the [detailed engineering pack](../engineering-packs/03-infra-resilience-engineering-pack.md) for requirements, module boundaries, decisions and verification.
