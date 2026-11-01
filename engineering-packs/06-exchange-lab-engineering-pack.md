# 06: Exchange Lab: engineering pack

**Status:** proposed design for review; no implementation or results claimed. Read with the [common standard](00-engineering-pack-standard.md), [project plan](../plans/06-exchange-lab.md) and original [technical brief](../source/Engineering%20Portfolio/Project%2006%20Exchange%20Lab/02%20Technical%20Two%20Pager.pdf) and [case study](../source/Engineering%20Portfolio/Project%2006%20Exchange%20Lab/03%20Case%20Study.pdf).

## Purpose and scope
Implement a deterministic single threaded order book and compare optimised variants to a simple reference. First release has synthetic order flow, documented limit orders and cancellation, a journal and replay; excludes networking, clearing and production exchange claims.

## Modules and interfaces
C++ `order` and `types` define validated integer price ticks, quantity lots, IDs and sequence; `reference_book` prioritises price then arrival order; `candidate_book` implements the same pure command/event contract; `journal` records input commands and emitted fills/rejections; `replay` rebuilds state; `generator` creates seeded order streams; `benchmark` measures only validated variants; Python `analysis` summarises raw timing with machine/compiler metadata. Define order IDs, sequence assignment, overflow limits, time in force and cancellation semantics before code.

## Requirements and verification
| ID | Requirement and acceptance | Verification |
| --- | --- | --- |
| EL 01 | At a price, fills follow documented arrival priority and never exceed available quantity. | Hand calculated tie, partial fill and multiple level fixtures. |
| EL 02 | Invalid orders and cancels are rejected without corrupting the book. | Zero/negative values, unknown or duplicate IDs, integer limits and malformed sequence. |
| EL 03 | Reference and candidate emit identical ordered events and final book on equivalent input. | Differential tests over seeded, bursty, dense price and cancellation heavy streams; retain minimal counterexamples. |
| EL 04 | Execution conserves quantity and never produces negative remaining size. | Independent ledger invariants checked after each event. |
| EL 05 | Replay reconstructs events and state identically. | Rebuild from full input and from checkpoint if implemented; detect journal corruption. |
| EL 06 | Performance claims include raw samples, environment, warmup, workload and percentiles. | Validate measurement harness on a known workload; report p50, p99, p99.9, memory and variance, only after correctness passes. |

## Decisions and delivery
Document matching policy, integer representation, overflow behaviour, self trade and unsupported order types in ADRs. Build reference, invariant tests and journal before optimisation; then use a candidate with differential tests and stable benchmark environment. Original risk/sequence stage must reject malformed commands and assign deterministic sequence; broader market risk checks are later scope. Measurements depend on hardware and method; synthetic tests do not prove exchange readiness.
