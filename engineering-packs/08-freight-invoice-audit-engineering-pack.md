# 08: Freight Invoice Audit: engineering pack

**Status:** proposed design for review; no implementation or results claimed. Read with the [common standard](00-engineering-pack-standard.md), [project plan](../plans/08-freight-invoice-audit.md) and original [technical brief](../source/Engineering%20Portfolio/Project%2008%20Freight%20Invoice%20Audit/02%20Technical%20Two%20Pager.pdf) and [case study](../source/Engineering%20Portfolio/Project%2008%20Freight%20Invoice%20Audit/03%20Case%20Study.pdf).

## Purpose and scope
Recalculate synthetic carrier invoices from versioned contract rates and shipment events, then route evidence backed differences to finance. No actual disputes, payment or recovery claims. Begin with a limited, explicit tariff language and deterministic calculations.

## Components and contracts
`contracts` parses validated rate cards with effective dates, currency, zones, weight bands and rounding; `shipments` records dimensions, weights and timestamped delivery facts; `invoices` imports line IDs, charge type, amount and source; `rating` is a pure calculator producing charge components and rule references; `matching` joins carrier lines to shipments, retaining unmatched/ambiguous cases; `review` shows proposed discrepancies and supports human accept/reject; `audit` records decisions. Money is fixed point/integer minor units and tariffs never silently default across missing periods.

## Requirements and verification
| ID | Requirement and acceptance | Verification |
| --- | --- | --- |
| FA 01 | Rate selection uses correct carrier, service, zone and effective date; ambiguity goes to review. | Boundary dates, overlapping rate cards, missing zone and unknown service. |
| FA 02 | Base, fuel and accessorial charges apply documented order and rounding. | Independently hand calculated cases including weight band edges, negative adjustments and multi currency rejection. |
| FA 03 | Each discrepancy links to the tariff clause, shipment fact and invoice line. | Trace every output to fixture IDs; missing events result in unresolved status. |
| FA 04 | No duplicate invoice line or shipment is silently counted twice. | Duplicate IDs, conflicting imports and partial batches. |
| FA 05 | Compare manual style sampling, rules only and optional extraction assisted method on same held out set. | Ground truth with planted overcharges; report variance recall, exact amount accuracy, false disputes and reviewer effort. |

## Decisions and milestones
Approve tariff schema and contract interpretation, fuel calculation, volumetric weight, precision, evidence policy and review authority. Implement hand calculated reference; produce synthetic batch and deterministic rating; add review queue; then compare sampling and optional model reading of unstructured clauses. Rate ambiguity is not resolved silently. Unknown carrier dispute behaviour, synthetic simplicity and review time measurement limits remain in report.
