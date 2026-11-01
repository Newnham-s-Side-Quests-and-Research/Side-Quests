# 02: Aegis Autonomy: engineering pack

**Status:** proposed design for review; no implementation or results claimed. Read with the [common standard](00-engineering-pack-standard.md), [project plan](../plans/02-aegis-autonomy.md) and original [technical brief](../source/Engineering%20Portfolio/Project%2002%20Aegis%20Autonomy/02%20Technical%20Two%20Pager.pdf) and [case study](../source/Engineering%20Portfolio/Project%2002%20Aegis%20Autonomy/03%20Case%20Study.pdf).

## Purpose and first release
Compare whether a monitor detects loss of state trust while limiting nuisance alarms in a controlled simulation. First release uses a reproducible reduced order vehicle, simple estimator, no monitor baseline and a fixed/innovation monitor. Degraded behaviour is bounded in the simulation model. No hardware control or certified safety claim.

## Architecture and interfaces
- `dynamics`: step `(state, command, dt, scenario)` to next state; declare coordinate frame, units, timestep, integration method and numerical limits.
- `sensors`: seeded IMU/position observations, bias, noise, delay and dropout, with fault onset and truth independent of monitor output.
- `estimator`: observation and previous estimate to state estimate, covariance and innovations; report invalid covariance or unobservable conditions.
- `monitor`: fixed threshold and innovation implementations share `evaluate(estimate, residual, covariance) -> decision, score, reason`.
- `supervisor`: explicit nominal, degraded and terminal states; transitions and bounded commands recorded with cause and time.
- `campaign`: locked scenario grid and separated development/held out seeds; write trace, inputs, versions and metrics for every run.

## Requirements and verification
| ID | Requirement and acceptance | Verification |
| --- | --- | --- |
| AA 01 | Identical deterministic scenario and seed reproduce state and sensor trace within documented tolerance. | Repeat and clean environment replay; verify units and fault onset against hand computed cases. |
| AA 02 | Baseline and each monitor receive identical scenarios and comparable seeds. | Assert input manifest equality and record all runs, including crashes. |
| AA 03 | State changes occur only on declared transition conditions; degraded commands stay inside declared model bounds. | Transition table, boundary and malformed estimate tests. |
| AA 04 | Score healthy false alarms and fault detection delay, including missed detections. | Hand labelled traces; test no fault, dropout, bias and undetectable faults. |
| AA 05 | Report trajectory error, boundary violations and completion by scenario and uncertainty; no dropped failures. | Recompute from trace fixtures and audit campaign counts. |

## Decisions, risks and milestones
Before coding choose motion equations, timestep, sensor units and noise, estimator, fault classes, safety boundary, degraded controller and numerical tolerances in ADRs. Before campaign freeze thresholds, development/held out seeds, sample size and confidence method; report false alarms per simulated hour and censor undetected faults explicitly. Model mismatch and correlated faults are mandatory negative cases. Milestones: model and estimator; baseline; monitor and state machine; held out campaign; review and report.

## Original brief coverage
Reduced order dynamics, fixed threshold and innovation monitors, plain controller comparison and required metrics are first release. Adaptive monitoring, six degree of freedom dynamics and larger correlated fault sensitivity campaigns are later milestones. No result certifies physical flight.
