# 01: Custom Autonomous Drone

**Status:** planned; no implementation or measured result is claimed.

## Objective and inputs

Recover and verify the existing aircraft build, then add a software in the loop regression route where recovered material permits.

Original source, firmware revisions, schematics, CAD, photos, dated logs and permission to publish are external inputs; inventory their absence rather than reconstructing history as fact.

## First release and boundaries

No physical flights, hardware modifications or airworthiness claims in the first release. Do not replace unavailable historical evidence with new simulations.

## Proposed design

Artefact inventory with hashes: claim/evidence register: subsystem and interface map: preserved controller simulation harness: reviewed publication pack.

These are initial design choices, subject to an architecture decision record before implementation. Interfaces, validation, errors and persistence must be specified at the relevant boundary.

## Delivery sequence

1. Confirm inputs, assumptions and scope; record unanswered questions and the baseline.
2. Write the requirements, data contracts, failure cases and verification matrix.
3. Inventory available files and classify each claim as flown, bench tested, simulated, conceptual or unsupported; map firmware and board versions. Define interfaces from evidence. Build a reproducible simulation only after controller and execution environment are understood.
4. Review the implementation against the requirements, run the verification plan and preserve raw results.
5. Write the case study with results, negative cases, limits and an independent rerun guide.

## Verification and acceptance

Trace each published claim to dated evidence or label it unsupported; sample ten claims where available. Re run any recovered controller simulation from a clean setup with recorded configuration. Confirm images and flight claims have provenance.

The first release is accepted only when its documented requirements pass, a clean setup can run its checks and any failed or inconclusive checks are visible. Measurements are observations, not promised targets.

## Evidence and metrics

Completeness of inventory; claim traceability and gaps; independent rerun outcome. Hardware validation remains separate.

Keep inputs or their authorised references, configuration, versions, seeds where relevant, commands, outputs and environment details with each run. Link every claim to a test or source.

## Decisions and dependencies

Recover original artefacts and identify publication rights before implementation decisions.

See [programme plan](../programme-plan.md) and [engineering standard](../engineering-standard.md). Original briefs and case studies are in [the source archive](../source/Engineering%20Portfolio/).


## Detailed engineering pack

See the [detailed engineering pack](../engineering-packs/01-custom-autonomous-drone-engineering-pack.md) for requirements, module boundaries, decisions and verification.
