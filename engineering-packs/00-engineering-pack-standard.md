# Engineering pack standard

**Status:** design baseline for review, not evidence of implementation or independent professional approval. Each project pack must be read with its original technical brief and case study and the corresponding project plan.

## Engineering workflow and ownership

1. Discover inputs, rights, stakeholders, constraints and existing assets. Mark each statement as evidence, assumption, decision or open question. Do not claim missing artefacts exist.
2. Agree the first release boundary, requirements and acceptance thresholds. Where numerical targets are unknown, set them with the accountable domain owner before measuring; preserve an immutable test protocol. A threshold is a target, not a result.
3. Review the proposed architecture and data contracts against realistic failure modes. Record material decisions with context, alternatives, consequences and owner. Reject unactioned unknowns that could invalidate the release.
4. Build the smallest vertical slice in reviewable changes. Domain logic has no dependency on UI or infrastructure; adapters implement explicit interfaces. Validate at system boundaries. Never expose side effects behind a read operation.
5. Verify using the project matrix, independently calculated examples and adversarial cases. Keep test fixtures distinct from tuning data. Run the same checks from a clean checkout, preserve failures and have a reviewer inspect the evidence.
6. Release only after open blocking decisions are resolved, requirements are verified or explicitly deferred, rights are reviewed and a human records the release decision. No simulation result implies physical certification or an unqualified production safety guarantee.

## Common structure and boundaries

A project owns `README.md`, `docs/requirements.md`, `docs/architecture.md`, `docs/decisions/`, `docs/verification.md`, `src/`, `tests/`, `fixtures/` and `results/` as needed. Compiled projects also have their own build configuration. Use a `domain` core for business rules, `application` for use cases, `adapters` for persistence, files and external services and a thin `interfaces` layer for CLI/API/UI. These are responsibilities, not mandatory empty directories. Each project builds and runs independently. A common package is justified only by a reviewed, concrete reuse case.

Use typed, versioned records at boundaries. Validate required fields, units, ranges, uniqueness and incompatible schema versions. Return explicit errors; distinguish invalid input, missing data, infrastructure failures and domain conflicts. Do not silently substitute a default for a missing value. Stable IDs link records and evidence. Timestamps are UTC with time zone offsets and source event time is separate from processing time. Money uses integer minor units or fixed point decimals with currency and explicit rounding, never floating point. Identity and permissions must be checked server side when a UI is added.

## Reliability, security and operations

Local offline operation and synthetic fixtures are the default. Keep personal, client, licensed and secret data out of source control and public deployments. Log correlation IDs and error categories; avoid secret values and document contents. Limit input sizes and reject malformed or unsupported files. Document retention and deletion. Only use actual credentials, integrations, databases or hosting after a specific design and permission decision; model calls must use the repository gateway when applicable. Read only demos are separate from systems with real side effects.

Where persistence is used, define transaction boundaries, uniqueness constraints, migrations, atomicity and recovery. Database constraints enforce durable invariants. External calls can fail, time out or repeat; assume at least once delivery unless a stronger contract is proven. Record before/after state, actor and reason for consequential human decisions. A hash chain detects some alterations but cannot prove an original record is true or prevent deletion without an independently held checkpoint.

## Verification and evidence contract

Every requirement has a stable ID and at least one independent verification method and pass criterion in its project pack. Unit tests check domain boundaries and known answers; integration tests exercise real storage or interfaces when those are in scope. Property, differential, adversarial, fault injection and performance tests apply where relevant. The run manifest records code revision, input/data version or hash, tool and dependency versions, config, random seeds when applicable, UTC time, environment and results. Preserve raw outcomes, failed and inconclusive cases, exclusions and reviewer decisions. Reproduction instructions include commands, expected outputs and known platform constraints.

For comparisons, specify population, units, baseline, data split, metrics, denominators, uncertainty method, stopping rule and excluded cases before tuning. Run baseline and candidate on equivalent inputs. Never infer savings or performance from plans. A release requires each first release requirement to have a recorded pass or a named, approved deferral with impact. "No known safety failures" is not a proof of safety.

## Common acceptance gates

- **G0:** Confirm scope, original brief mapping, inputs, authorities and rights; unresolved blockers are recorded.
- **G1:** Requirements and interface contracts reviewed; architecture, hazard/failure analysis and decision records approved by the responsible reviewer.
- **G2:** Deterministic, network free first slice works from a clean environment and meaningful tests cover normal, boundary and failure cases.
- **G3:** Complete verification matrix, raw run artefacts and limitations are reviewed; unsuccessful or inconclusive cases remain visible.
- **G4:** An accountable human accepts the release and publication scope. Real world operations, safety critical use and public source release require separate domain and rights review where applicable.

The proposed stacks and interfaces are design choices for review, not commitments to install infrastructure before it is needed. If a brief calls for a broader research method than the first release, the project pack records it as a later milestone rather than claiming it has been completed.
