# 04: Proof AI: engineering pack

**Status:** proposed design for review; no implementation or results claimed. Read with the [common standard](00-engineering-pack-standard.md), [project plan](../plans/04-proof-ai.md) and original [technical brief](../source/Engineering%20Portfolio/Project%2004%20Proof%20Ai/02%20Technical%20Two%20Pager.pdf) and [case study](../source/Engineering%20Portfolio/Project%2004%20Proof%20AI/03%20Case%20Study.pdf).

## Purpose and boundaries
Evaluate whether independently checked document extraction plus abstention reduces incorrect automatic acceptance on labelled synthetic or licensed documents. No payment, real finance data, regulatory certification or claimed savings.

## Components and contracts
`fixtures` stores document and ground truth with rights and data split; `extractor` returns fields, source spans, model/version and confidence or a typed error; `checks` applies independent arithmetic, identity, duplicate and source consistency rules; `decision` returns accept/review/reject with rule evidence; `review` records human decision; `evaluation` runs model only, rules only and hybrid methods on identical labelled inputs. Optional OCR/model adapters are replaceable; deterministic stubs permit offline execution. Field values carry units, source IDs and missing/uncertain states. Version rules and thresholds.

## Requirements and verification
| ID | Requirement and acceptance | Verification |
| --- | --- | --- |
| PA 01 | Every fixture has rights, label, split and ground truth; development and holdout IDs do not overlap. | Schema checks and duplicate/hash leakage tests. |
| PA 02 | Extractor errors, missing fields and unavailable checks cannot produce automatic acceptance. | Inject timeout, invalid JSON, missing field and failed rule execution. |
| PA 03 | Model only, rules only and hybrid decisions retain field and source evidence. | Hand labelled normal, conflicting and consistent but wrong fixtures; verify decision trace. |
| PA 04 | Decisions are replayable with pinned rule, prompt/model and input versions. | Replay deterministic adapter; label nondeterministic output and retain individual trials. |
| PA 05 | Report incorrect acceptance, abstention, field accuracy and confidence calibration with denominators. | Independently calculated confusion tables; report ambiguous labels and uncertainty. |

## Decisions, risks and milestones
Freeze document schema, allowable source licences, acceptance criteria, baseline methods, split, sampling and threshold selection before scoring. Explicitly test OCR noise, duplicate invoices, wrong totals, identity mismatch and mutually consistent incorrect fields; rules cannot prove truth. First release: labelled fixtures, stub, rules and review state; later: OCR and optional model, model only/rules only/hybrid comparisons, calibration and adversarial holdout evaluation. Provider calls need gateway review, cost limits and no unapproved data transmission.

## Original brief coverage
All three baselines, calibration and abstention are planned for the full research milestone; deterministic offline mechanics come first. Review states and provenance remain human controlled.
