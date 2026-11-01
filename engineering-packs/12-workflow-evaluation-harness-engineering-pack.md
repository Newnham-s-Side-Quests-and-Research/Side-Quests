# 12: Workflow Evaluation Harness: engineering pack

**Status:** an initial local implementation has passed synthetic mechanism tests. This design remains subject to review. No real world accuracy or safety result is claimed. Read with the [common standard](00-engineering-pack-standard.md), [project plan](../plans/12-workflow-evaluation-harness.md) and original [technical brief](../source/Engineering%20Portfolio/Project%2012%20Workflow%20Evaluation%20Harness/02%20Technical%20Two%20Pager.pdf) and [case study](../source/Engineering%20Portfolio/Project%2012%20Workflow%20Evaluation%20Harness/03%20Case%20Study.pdf).

## Purpose and first release
Provide a local, deterministic replay runner for labelled cases and baseline/candidate workflow adapters. Produce transparent scores and gate decisions for human review. It never makes or executes a deployment decision. The [first release specification](../plans/12-first-release-specification.md) is authoritative for R1 R7 and is extended here.

## Modules and contracts
`case_library` loads schema versioned JSON: case ID, input, expected fields, expected abstention, category, split and source rights; `adapters` expose `run(input, settings) -> structured output | typed error` and stable version identity; `runner` submits the identical ordered case set to both versions; `scoring` contains pure field/abstention scorers with explicit missing output policy; `gates` evaluates versioned rules and minimum sample sizes as pass/fail/incomplete; `report` writes machine readable manifest, per case outcomes and human readable summary. Default fixtures and deterministic adapters require no network or external model.

## Requirements and verification
| ID | Requirement and acceptance | Verification |
| --- | --- | --- |
| EH 01 | Reject invalid schema, duplicate case IDs and unrecognised versions before execution. | Malformed, duplicate and mismatched version cases, with actionable errors. |
| EH 02 | Baseline and candidate receive identical case identities and settings; errors remain visible. | Recording adapter verifies ordered inputs; inject timeout, exception and invalid result. |
| EH 03 | Field accuracy and abstention scores include explicit denominators and case failures. | Hand calculated confusion table, missing values, wrong fields and both abstention errors. |
| EH 04 | Gate evaluation gives pass, fail or incomplete; missing evidence never passes. | Threshold boundary, insufficient cases, absent metric and error handling fixtures. |
| EH 05 | Report contains case set hash, adapter versions, settings, results, errors and gate version. | Replay from clean checkout and independently recompute a known report. |
| EH 06 | Defective candidates and sound changes are both represented. | Inject wrong field, false accept and false abstain defects; measure caught defects and false blocks. |
| EH 07 | No gate triggers deployment; a person records the outcome. | Inspect interfaces and verify no external release action; reviewer decision record required. |

## Decisions and delivery
Decide canonical JSON hashing, adapter timeout, missing field scoring, minimum cases, threshold approval and exit codes. Build schema/loader; deterministic runner; independent scorers; gates; reports and planted defect tests; conduct clean environment review. Later add repeat trials and uncertainty, latency/cost accounting, model settings and gateway backed adapters. Original brief's regression detection, false block rate, latency/cost and variance comparisons are full research milestones, not claims of the first deterministic slice.
