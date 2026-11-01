# 04: Proof AI

**Status:** planned; no implementation or measured result is claimed.

## Objective and inputs

Test whether independent checks and abstention reduce incorrect automatic acceptance of document fields.

Synthetic or openly licensed documents only; no payment execution, compliance certification or implied savings.

## First release and boundaries

Begin with deterministic fixtures and a stub extractor; external models and OCR are optional adapters with recorded versions.

## Proposed design

Document fixtures: extraction adapter: independent checks: accept/abstain decision: evidence and evaluation.

These are initial design choices, subject to an architecture decision record before implementation. Interfaces, validation, errors and persistence must be specified at the relevant boundary.

## Delivery sequence

1. Confirm inputs, assumptions and scope; record unanswered questions and the baseline.
2. Write the requirements, data contracts, failure cases and verification matrix.
3. Define field schema, ground truth and error taxonomy. Build baseline extraction and cross check rules, then a review queue and reproducible evaluation through project 12.
4. Review the implementation against the requirements, run the verification plan and preserve raw results.
5. Write the case study with results, negative cases, limits and an independent rerun guide.

## Verification and acceptance

Test missing and conflicting values, high confidence wrong answers, malformed inputs and checker failures. Compare unsafe acceptance and abstention against the same labelled holdout set.

The first release is accepted only when its documented requirements pass, a clean setup can run its checks and any failed or inconclusive checks are visible. Measurements are observations, not promised targets.

## Evidence and metrics

Incorrect automatic acceptance, field accuracy, abstention and review burden, with intervals and examples.

Keep inputs or their authorised references, configuration, versions, seeds where relevant, commands, outputs and environment details with each run. Link every claim to a test or source.

## Decisions and dependencies

Select source rights and decision thresholds before any real workflow use.

See [programme plan](../programme-plan.md) and [engineering standard](../engineering-standard.md). Original briefs and case studies are in [the source archive](../source/Engineering%20Portfolio/).


## Detailed engineering pack

See the [detailed engineering pack](../engineering-packs/04-proof-ai-engineering-pack.md) for requirements, module boundaries, decisions and verification.
