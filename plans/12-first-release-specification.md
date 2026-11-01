# Workflow Evaluation Harness: first release specification

**Status:** proposed; not implemented. This is the first implementation candidate under the [programme](../programme-plan.md).

## Goal

A local command line tool compares a baseline and candidate workflow against a versioned set of synthetic cases. It records outputs, scores, gate decisions and the information needed to repeat a run. A human owns any release decision.

## Requirements

- **R1:** Load a versioned case set with unique IDs, input, expected output and failure category; reject malformed or duplicate cases with a useful error.
- **R2:** Run baseline and candidate adapters against the same selected cases and record per case success or failure. Initial adapters are deterministic and local.
- **R3:** Score exact field matches and expected abstention separately, including missing and invalid output. Publish denominators and individual failures.
- **R4:** Apply explicit versioned gate rules to aggregate scores; distinguish pass, fail and incomplete when a run or required score is missing. A gate does not deploy or authorise release.
- **R5:** Write a machine readable run record and a readable report with case set identity, adapter versions, configuration, timestamps, scores, errors and gate decisions. Preserve per case outputs and avoid claiming seeded determinism for external services.
- **R6:** Provide a documented clean setup and a single test command; operate without network access for the initial fixture set.
- **R7:** Include deliberately defective candidates to demonstrate detection of at least a wrong field, an inappropriate acceptance and an inappropriate abstention; include a sound candidate to exercise a non regression path.

## Design to validate before coding

Use Python with a small CLI and standard library facilities where practical. Proposed boundaries: case loader and validation; adapter protocol; runner; pure scoring functions; gate evaluator; report writer. JSON is the initial interchange format. Store fixtures in source control; write generated run outputs to an ignored local directory. Decide schema versioning, canonical dataset hashing, exit codes and error policy in an architecture decision record before implementation.

A case contains `id`, `input`, `expected` and `category`. An adapter returns structured fields plus an explicit abstention flag or a recorded error. The initial scorer compares the configured expected fields exactly; normalization must be explicit and tested. A run level execution error cannot silently become an ordinary incorrect answer. Gate rules use explicit thresholds and minimum sample counts; if requirements are missing, the result is incomplete.

## Verification matrix

| Requirement | Verification |
| --- | --- |
| R1 | Valid fixture loads; duplicate IDs, missing fields and unsupported versions fail clearly. |
| R2 | Recording adapters prove both versions receive identical ordered cases; an adapter failure is retained per case. |
| R3 | Hand calculated cases cover correct/wrong/missing fields and both abstention errors. |
| R4 | Boundary values, insufficient data and scorer errors yield the documented pass/fail/incomplete state. |
| R5 | Read report and JSON from a known run; verify identity, configuration, case outcomes and errors are present. |
| R6 | Follow README from a clean environment and run all tests without network access. |
| R7 | Run the planted defect suite and sound candidate against reviewed fixture expectations; report both catches and false blocks. |

## Scope and decisions

No live model, provider SDK, dashboard, database, real customer data, automatic deployment or statistical claim is needed for the first release. The case schema and gate thresholds are design inputs and should be reviewed; a small synthetic suite demonstrates mechanics, not real world accuracy. Later work can add repeat trials, confidence intervals and provider adapters after the local baseline is trustworthy.
