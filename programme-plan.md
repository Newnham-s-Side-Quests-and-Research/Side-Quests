# Engineering portfolio programme

## Purpose and status

Turn the 12 supplied concepts into independently reviewable engineering projects. The drone is an existing build to recover; the other 11 are proposed research. None is represented as completed or measured by these plans. The source documents are in `source/Engineering Portfolio/`; the website is in `dist/`. Project plans link to this programme and the common standard.

## Decisions

- Keep the projects independent, with their own code, data, tests, documentation and evidence. Share a tool only after a real, documented need appears; avoid a premature common platform.
- Build the evaluation harness first because it can support the AI oriented projects. It is useful independently and does not block projects that do not use it.
- Start drone evidence recovery in parallel when the original files become available. Do not claim reconstructed code is historical hardware evidence.
- Use local, synthetic or openly licensed data by default. External APIs, live systems and hardware work require their own design and appropriate authorisation.
- The source documents describe scenarios, not verified customers, business outcomes or instructions to operate a live system.
- All estimates and technology choices are provisional until discovery. No completion date is promised without staffing, availability and an agreed scope.

## Proposed order

| Order | Project | Reason and relationship |
| --- | --- | --- |
| 1 | [12: Workflow Evaluation Harness](plans/12-workflow-evaluation-harness.md) | Establish a tested baseline for later workflow evaluation. |
| 2 | [01: Custom Autonomous Drone](plans/01-custom-autonomous-drone.md) | Recover existing evidence as soon as artefacts are available; its simulation depends on what is recovered. |
| 3 | [05: Invariant Ops](plans/05-invariant-ops.md) | Establish workflow state, idempotency and failure handling patterns. |
| 4 | [04: Proof AI](plans/04-proof-ai.md) | Exercises the harness on labelled document extraction and abstention. |
| 5 | [08: Freight Invoice Audit](plans/08-freight-invoice-audit.md) | Deterministic calculation and provenance before optional AI. |
| 6 | [09: Delivery Matched Invoicing](plans/09-delivery-matched-invoicing.md) | Related finance workflow; reuses lessons, not necessarily code. |
| 7 | [10: Maintenance Triage](plans/10-maintenance-triage.md) | Uses evaluation patterns, with conservative human escalation. |
| 8 | [11: Company Hub](plans/11-company-hub.md) | Adds retrieval, provenance and access checks; synthetic only. |
| 9 | [03: Infra Resilience](plans/03-infra-resilience.md) | Introduces simulation and diagnosis with known fault ground truth. |
| 10 | [02: Aegis Autonomy](plans/02-aegis-autonomy.md) | Adds control and fault monitor experiments; can draw on drone evidence without assuming it exists. |
| 11 | [06: Exchange Lab](plans/06-exchange-lab.md) | Independent C++ correctness and benchmarking track. |
| 12 | [07: Alpha Validity](plans/07-alpha-validity.md) | Independent statistical research track. |

This is an initial priority order, not a technical dependency chain. Project 12 is a useful optional evaluation tool for 04, 10 and 11; no project should be blocked solely to force reuse. Projects 01, 06 and 07 can progress independently when their inputs and capacity permit.

## Lifecycle and gates

1. **Discovery:** inventory source material and assumptions; identify missing inputs and rights.
2. **Specification:** define problem, scope, requirements, interfaces, threat/failure cases, baselines and a verification matrix. Record decisions and alternatives.
3. **Implementation:** make small, reviewable changes; use version control and meaningful tests; keep the system runnable.
4. **Verification:** run the documented tests and experiments, retain failures, independently reproduce where feasible and assess the original requirements.
5. **Release:** document results and limitations, review rights and sensitive material and update the portfolio only when supported by evidence. Human approval remains required for consequential decisions.

A project becomes “built and tested” only when its stated first release requirements are implemented, verified and documented. A partial implementation remains “in progress”. Simulation does not establish hardware safety and synthetic results do not establish real world performance.

## Workspace structure

Create code only when implementation begins, under `projects/<project-slug>/`. Each project will contain `README.md`, `docs/` (requirements, design, decisions and verification), `src/`, `tests/`, `data/` where appropriate and `results/` for reproducible records. Do not commit secrets, personal data, unlicensed material or large raw artefacts without an explicit storage decision. The plans are deliberately separate from the website deployment directory.

## Next concrete work

The first implementation candidate is project 12. Its initial specification is [here](plans/12-first-release-specification.md). Review that specification against actual usage during implementation; do not treat proposed thresholds or illustrative cases as results.

## Detailed engineering packs

Each project has an engineering pack covering modules, interfaces, requirements, verification, decisions and original brief coverage. Start with the [common engineering pack standard](engineering-packs/00-engineering-pack-standard.md) and follow each project plan to its pack. Design choices remain proposed until reviewed and blocking inputs are resolved.
