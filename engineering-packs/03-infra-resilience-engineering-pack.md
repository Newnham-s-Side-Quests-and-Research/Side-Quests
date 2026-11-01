# 03: Infra Resilience: engineering pack

**Status:** proposed design for review; no implementation or results claimed. Read with the [common standard](00-engineering-pack-standard.md), [project plan](../plans/03-infra-resilience.md) and original [technical brief](../source/Engineering%20Portfolio/Project%2003%20Infra%20Resilience/02%20Technical%20Two%20Pager.pdf) and [case study](../source/Engineering%20Portfolio/Project%2003%20Infra%20Resilience/03%20Case%20Study.pdf).

## Purpose and boundaries
Rank plausible initiating faults from synthetic plant event streams and compare against threshold alarms. Scope is an offline conveyor/drive/sensor model; no PLC connection, protective action or certified industrial safety logic.

## Architecture and contracts
`plant` defines directed equipment dependencies and discrete PLC style state; `faults` injects motor, sensor, network and timing faults; `telemetry` emits schema versioned events `(event_id, event_time, asset, signal, value, quality)`; `baseline` raises threshold alarms; `diagnosis` ranks candidate causes with evidence and assumptions; `review` presents ranked results and uncertainty; `evaluation` joins predictions to independently planted ground truth. Missing or out of order telemetry is explicit, not treated as healthy.

## Requirements and verification
| ID | Requirement and acceptance | Verification |
| --- | --- | --- |
| IR 01 | Each seeded scenario records topology, injected fault and complete event trace. | Replay and check fault location/onset against scenario manifest. |
| IR 02 | Baseline and ranker process the same events with a stable ordering rule. | Feed identical streams including same timestamp events and missing quality flags. |
| IR 03 | Each ranked cause includes evidence IDs and declared confidence/ambiguity. | Check citations exist; ties and absent evidence return ambiguous or unknown. |
| IR 04 | Report top k diagnosis accuracy and false leads against ground truth, including unranked cases. | Hand calculated rankings; single, simultaneous, hidden and correlated fault fixtures. |
| IR 05 | No output controls plant equipment. | Interface inspection and tests showing no actuator/PLC adapter in first release. |

## Decisions and delivery
Freeze plant topology, fault catalogue, event granularity, causal assumptions, ranking rule, baseline and held out scenarios before scoring. Produce normal and faulted traces; implement baseline then dependency ranker; test missing events, clock skew and multiple faults; review incorrect explanations. Measure top 1/top k, time from first signal to ranked output and ambiguous cases with denominators. Choose sample size and uncertainty before campaign; do not mistake correlations for proof of causality.

## Original brief coverage
Drive, occupancy sensor and controller state modelling; multiple fault types; threshold baseline; dependency aware ranking and missing data ambiguity are required. Engineer review is a human evaluation step; live plant integration is excluded.
