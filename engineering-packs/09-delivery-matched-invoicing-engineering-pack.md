# 09: Delivery Matched Invoicing: engineering pack

**Status:** proposed design for review; no implementation or results claimed. Read with the [common standard](00-engineering-pack-standard.md), [project plan](../plans/09-delivery-matched-invoicing.md) and original [technical brief](../source/Engineering%20Portfolio/Project%2009%20Delivery%20Matched%20Invoicing/02%20Technical%20Two%20Pager.pdf) and [case study](../source/Engineering%20Portfolio/Project%2009%20Delivery%20Matched%20Invoicing/03%20Case%20Study.pdf).

## Purpose and scope
Compare invoice quantities against synthetic purchase orders, delivery receipts and accepted goods, with a reviewable proposed credit. No automatic short payment, supplier messaging or actual recoveries. A human buyer approves any credit recommendation.

## Modules and contracts
`orders` stores supplier, product, agreed unit and ordered quantity; `receipts` records delivery, accept/reject events and evidence; `invoices` stores line references, quantity, price and currency; `matching` links the three sources using explicit identity and unit conversion rules; `credit` proposes quantities and amounts with source references; `review` captures approval or dispute; `audit` records immutable corrections and actors. Quantities use fixed precision and explicit units; money uses minor units or decimal. Ambiguous matches and missing evidence remain review states.

## Requirements and verification
| ID | Requirement and acceptance | Verification |
| --- | --- | --- |
| DM 01 | Every invoice match identifies order, receipt and accepted quantities or records why matching is unresolved. | Missing records, partial deliveries, duplicate lines and ambiguous product IDs. |
| DM 02 | Rejections and corrections retain event time, reason, source and history. | Replay late temperature/quality rejection, correction and duplicate events. |
| DM 03 | Credit amount uses agreed units and documented rounding, with no automatic financial action. | Independent hand calculated partial acceptance, conversions, price changes and invalid currency. |
| DM 04 | Buyer can approve or reject a proposed credit and the decision is auditable. | Verify state transitions and actor/reason; duplicate approval is idempotent. |
| DM 05 | Compare manual style checking, rules and optional free text extraction against labelled holdout. | Report credit precision/recall, potential short payment errors and approver edits with denominators. |

## Decisions and milestones
Agree supplier identity, item and unit mappings, tolerance, partial deliveries, returns and approval roles before implementation. Build fixture schema and deterministic matcher; add credit proposal and review; later compare manual style, rules only and model assisted extraction of free text rejection notes. Freeze labels and held out scenarios first. Photo evidence, verbal agreements and real supplier dispute behaviour remain outside the original synthetic study.
