# 07: Alpha Validity: engineering pack

**Status:** proposed design for review; no implementation or results claimed. Read with the [common standard](00-engineering-pack-standard.md), [project plan](../plans/07-alpha-validity.md) and original [technical brief](../source/Engineering%20Portfolio/Project%2007%20Alpha%20Validity/02%20Technical%20Two%20Pager.pdf) and [case study](../source/Engineering%20Portfolio/Project%2007%20Alpha%20Validity/03%20Case%20Study.pdf).

## Purpose and scope
Measure false discoveries and ability to detect a weak planted signal in synthetic market research. No live execution, capital allocation advice or claim of real world alpha. Begin with a null generator and leakage free benchmark; add weak signal and regime campaigns before claiming full original brief coverage.

## Modules and data contract
`generators` produce seeded time series with a documented null or planted signal and truth metadata; `strategies` expose a fixed parameter universe; `splits` create time ordered development, validation and untouched holdout windows; `validation` implements naive selection and predeclared more robust methods; `costs` applies documented fees and turnover; `experiment` logs every trial, selected candidate and seed; `statistics` computes estimates and uncertainty; `report` records unsuccessful studies. Each observation includes timestamp, instrument ID, features available at that time and simulated price; prevent future feature availability from entering earlier decisions.

## Requirements and verification
| ID | Requirement and acceptance | Verification |
| --- | --- | --- |
| AV 01 | Generated data reproduce for fixed version, seed and parameters; generator properties are validated. | Known seed replay and distribution checks with predeclared tolerances. |
| AV 02 | No feature, label or fit step sees information after its decision time. | Deliberately planted future variable and split boundary tests; reviewer inspect transformations. |
| AV 03 | All attempted strategies, selection criteria and costs are retained. | Compare trial manifest to predeclared universe; verify hand calculated costs. |
| AV 04 | Report null false discovery and weak signal detection/power with denominators and intervals. | Simulated known truth fixtures; independently recompute statistics. |
| AV 05 | Holdout and regime change outcomes include negative and failed runs. | Holdout access audit; change regime and no trade scenarios. |

## Decisions and delivery
Pre register generator assumptions, null and signal strength, hypothesis family, sample size, multiplicity correction, validation protocol, cost model and uncertainty method. A researcher reviews leakage and selection logic before scoring. Milestones: null generator and naive baseline; temporal validation; weak signals and power; regime/cost sensitivity; optional licensed historical data only with rights and survivorship controls. Synthetic outcomes are conditional on generator assumptions.
