# 11: Company Hub: engineering pack

**Status:** proposed design for review; no implementation or results claimed. Read with the [common standard](00-engineering-pack-standard.md), [project plan](../plans/11-company-hub.md) and original [technical brief](../source/Engineering%20Portfolio/Project%2011%20Company%20Hub/02%20Technical%20Two%20Pager.pdf) and [case study](../source/Engineering%20Portfolio/Project%2011%20Company%20Hub/03%20Case%20Study.pdf).

## Purpose and scope
Build a synthetic firm research prototype that creates source linked briefings with access filtered retrieval and human reviewed entity links. First release is local, synthetic and read only with respect to sources; no personal data, actual Workspace connector or automatic external publication.

## Modules and contracts
`ingest` stores immutable source ID, version, content hash, origin and access labels; `access` authorises a principal before retrieval; `entities` proposes person, organisation and contract matches; `review` records reversible merge decisions; `retrieval` returns only authorised passages with stable offsets; `briefing` initially assembles extractive sourced statements and later supports a gated model adapter; `audit` records reads and approvals with tamper evident chain and independent checkpoint. Source records and derived interpretations are separate. Claims contain statement ID, source version, passage location and confidence/status. Never allow a derived answer to bypass source access.

## Requirements and verification
| ID | Requirement and acceptance | Verification |
| --- | --- | --- |
| CH 01 | Every displayed factual statement cites an authorised, existing source passage or is withheld. | Broken offsets, stale source versions, no source and cross role tests. |
| CH 02 | Access filtering occurs before retrieval and applies again on source display. | Adversarial role matrix, prompt injection strings and revoked permissions; assert restricted fixture text never reaches adapter. |
| CH 03 | Entity merges require human review, can be reversed and preserve provenance. | Planted duplicates, false positive match, undo and role denied cases. |
| CH 04 | Record and audit alteration is detectable relative to an independently retained checkpoint. | Modify, reorder and delete fixture records; document detection limits and checkpoint protection. |
| CH 05 | Compare keyword baseline and source linked briefing on labelled synthetic firm. | Measure claim traceability, obligation recall and entity precision/recall; report all observed access leaks. |

## Decisions and milestones
Define source versioning, access policy, entity match threshold, retention, checkpoint authority and safe citation semantics. Build synthetic corpus and keyword baseline; add provenance/permissions and review; then optional model and synthetic read only connectors under gateway policy. Real connectors and personal data require explicit authority, legal basis, data protection assessment and access testing. Hashes prove consistency against a trusted reference, not truth or completeness.
