# 01: Custom Autonomous Drone: engineering pack

**Status:** proposed design for review; no implementation or results claimed. Read with the [common standard](00-engineering-pack-standard.md), [project plan](../plans/01-custom-autonomous-drone.md) and original [technical brief](../source/Engineering%20Portfolio/Project%2001%20Custom%20Autonomous%20Drone/02%20Technical%20Two%20Pager.pdf) and [case study](../source/Engineering%20Portfolio/Project%2001%20Custom%20Autonomous%20Drone/03%20Case%20Study.pdf).

## Purpose, scope and stakeholders
Recover the original aircraft engineering record and if the preserved controller can be run, reproduce its behaviour in software in the loop (SIL). The builder owns historical attribution and publication; an independent embedded reviewer challenges assumptions. First release covers inventory, claims, diagrams and a conditional SIL harness. It excludes physical flight, modifications, airworthiness claims and reconstruction presented as history.

## Design and module boundaries
- `inventory`: ingest a copy of each authorised artefact; immutable content hash, original path, acquisition date, inferred version and rights status. Preserve originals separately.
- `claims`: link an assertion to artefact IDs and classify it as flown, bench tested, simulated, conceptual or unsupported; classification has reviewer, date and rationale.
- `architecture`: map power, airframe, PCB, sensors, controller, telemetry and app interfaces to source evidence; distinguish inferred interfaces.
- `sil-adapter`: wrap recovered controller only after its version, toolchain, inputs, outputs, units and timing are established; fixture plant and logger are replaceable.
- `report`: generate evidence register, missing evidence list and publication pack; release files individually after rights and safety review.

## Contracts and failure handling
Artefact record: ID, SHA 256, source, revision, date confidence, rights state and storage reference. Claim record: ID, text, status, evidence IDs, assessor, review date and caveat. SIL run: controller hash, harness version, timestep, input trace, seed if applicable, outputs and environment. Reject duplicate IDs, broken references and invalid status transitions; quarantine corrupted or unverifiable files. Never manufacture timestamps or flight logs.

## Requirements and verification
| ID | Requirement and acceptance | Verification |
| --- | --- | --- |
| DR 01 | Every recovered in scope file has an ID, hash, source and rights state. | Inventory fixture with duplicates, missing metadata and changed bytes; report each explicitly. |
| DR 02 | Every published historical claim has an evidence link and classification or is labelled unsupported. | Independently trace ten claims where available, including at least one negative or missing item. |
| DR 03 | Interface map cites supporting artefacts and identifies inferred links. | Reviewer follows each interface to source; mark unresolvable links unknown. |
| DR 04 | If controller and toolchain are recoverable, fixed input yields documented SIL output with reproducible settings. | Clean environment replay; compare outputs under stated numeric tolerances and retain divergence. |
| DR 05 | Publication includes only individually cleared assets. | Test rights denied and unknown assets are omitted; builder reviews manifest. |

## Decisions, hazards and delivery
Decide source of truth firmware, board revision, timebase, fixed point versus float, input replay, tolerances and supported toolchain only after recovery. Physical hardware, propellers, batteries and flight operations require separate domain specific safety and regulatory review; no autonomous physical testing is authorised by this plan. Milestones: inventory and permissions; classify claims; map interfaces; assess SIL feasibility; build and verify SIL if feasible; independent review and cleared release. If assets are unavailable, deliver the gaps register and mark DR 04 blocked, not passed.

## Original brief coverage
Airframe/power, firmware, estimation/control and vision/telemetry/app are represented in the architecture map; only existing evidence supports claims. Original bench and flight log recovery is a discovery task; new flight activity is out of scope. Original SIL regression is conditional on recovered code. Metrics: traceable claims / published claims, inventory gaps and independent rerun outcome. No historical measurement is inferred.
