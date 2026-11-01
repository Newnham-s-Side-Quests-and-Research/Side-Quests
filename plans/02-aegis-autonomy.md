# 02: Aegis Autonomy

**Status:** planned; no implementation or measured result is claimed.

## Objective and inputs

Compare fault monitors and degraded control under state estimation faults in simulation.

Simulation only; no claim of physical safety or certification.

## First release and boundaries

A reduced order model is the first baseline; six degree of freedom dynamics and adaptive monitoring are later options, not prerequisites.

## Proposed design

Seeded dynamics and sensors: estimator: interchangeable monitors: supervisory controller: experiment runner and reports.

These are initial design choices, subject to an architecture decision record before implementation. Interfaces, validation, errors and persistence must be specified at the relevant boundary.

## Delivery sequence

1. Confirm inputs, assumptions and scope; record unanswered questions and the baseline.
2. Write the requirements, data contracts, failure cases and verification matrix.
3. Specify state, units, fault models and safety boundary. Implement plain controller and fixed threshold baseline, then innovation monitor and bounded fallback. Freeze development and held out seed sets before comparison.
4. Review the implementation against the requirements, run the verification plan and preserve raw results.
5. Write the case study with results, negative cases, limits and an independent rerun guide.

## Verification and acceptance

Test deterministic dynamics and fault timing; replay configurations; run healthy and faulted cases, including correlated faults and miscalibrated covariance. Compare all methods on identical held out cases and retain failures.

The first release is accepted only when its documented requirements pass, a clean setup can run its checks and any failed or inconclusive checks are visible. Measurements are observations, not promised targets.

## Evidence and metrics

Detection delay, healthy run false alarms, trajectory error, boundary violations and completion, with uncertainty and seed level results.

Keep inputs or their authorised references, configuration, versions, seeds where relevant, commands, outputs and environment details with each run. Link every claim to a test or source.

## Decisions and dependencies

Choose model, boundary and fault range during design; no numerical performance claim until measured.

See [programme plan](../programme-plan.md) and [engineering standard](../engineering-standard.md). Original briefs and case studies are in [the source archive](../source/Engineering%20Portfolio/).


## Detailed engineering pack

See the [detailed engineering pack](../engineering-packs/02-aegis-autonomy-engineering-pack.md) for requirements, module boundaries, decisions and verification.
