# 10: Maintenance Triage: engineering pack

**Status:** proposed design for review; no implementation or results claimed. Read with the [common standard](00-engineering-pack-standard.md), [project plan](../plans/10-maintenance-triage.md) and original [technical brief](../source/Engineering%20Portfolio/Project%2010%20Maintenance%20Triage/02%20Technical%20Two%20Pager.pdf) and [case study](../source/Engineering%20Portfolio/Project%2010%20Maintenance%20Triage/03%20Case%20Study.pdf).

## Purpose and scope
Evaluate conservative triage of synthetic property reports, with safety and safeguarding reports escalated promptly to a person. It is a research prototype, not a live safety service and cannot guarantee no harm. No real tenants, automatic contractor dispatch or emergency response.

## Modules and contracts
`intake` validates synthetic report ID, timestamp, unit and text; `rules` detects specified risk language and returns reason; `classifier` is an optional replaceable adapter; `policy` routes urgent, routine, ambiguous and system error cases; `queue` stores a durable escalation record; `review` captures a person's decision; `evaluation` scores labelled held out cases and records time. Safety escalation takes precedence over grouping and classification. A classifier timeout, malformed output, uncertain case or unavailable dependency routes to an explicitly monitored human review queue; if persistence itself fails, return a hard failure rather than claiming escalation occurred.

## Requirements and verification
| ID | Requirement and acceptance | Verification |
| --- | --- | --- |
| MT 01 | Every accepted report receives a durable ID and auditable routing outcome or an explicit intake failure. | Simulate queue/storage failure, duplicate input and recovery; no successful acknowledgement before durable write. |
| MT 02 | Defined urgent patterns escalate without waiting for classifier or deduplication. | Gas, fire, flood and safeguarding fixtures including mixed routine text. |
| MT 03 | Unknown, failed and low confidence predictions route to human review. | Timeout, invalid result, missing text and boundary confidence tests. |
| MT 04 | Duplicate grouping cannot suppress urgent records or erase links to originals. | Cross unit duplicates, multi unit incident and urgent/routine conflict. |
| MT 05 | Compare rules only, model only and combined approaches on frozen held out cases; report every missed safety case. | Compute category recall, false escalation, simulated elapsed time and reviewer burden with denominators and intervals. |

## Decisions, risks and milestones
A domain owner must define hazard categories, escalation recipient, clock start/stop, queue monitoring, failure response, realistic workload and review thresholds. Build synthetic intake and deterministic safety policy first; later add optional classifier, duplicate grouping and comparative study. Inject unclear phrasing and unavailable services. The original question's guarantee cannot be established from synthetic tests; live deployment requires independent safety, safeguarding, privacy and legal review.
