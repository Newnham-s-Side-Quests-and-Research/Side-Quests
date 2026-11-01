# 07: Alpha Validity

**Status:** planned; no implementation or measured result is claimed.

## Objective and inputs

Measure how research validation methods can mistake chance for skill on synthetic markets.

Synthetic results do not establish tradable alpha; no live trading or investment recommendations.

## First release and boundaries

Begin with a known null generator and simple strategies; historical data and brokerage connectivity are later decisions.

## Proposed design

Seeded market generators: candidate strategies: validation protocols: cost model: statistical report.

These are initial design choices, subject to an architecture decision record before implementation. Interfaces, validation, errors and persistence must be specified at the relevant boundary.

## Delivery sequence

1. Confirm inputs, assumptions and scope; record unanswered questions and the baseline.
2. Write the requirements, data contracts, failure cases and verification matrix.
3. Pre register generators, strategy search space, baselines and holdout splits. Compare naive selection with leakage resistant validation and transaction cost assumptions.
4. Review the implementation against the requirements, run the verification plan and preserve raw results.
5. Write the case study with results, negative cases, limits and an independent rerun guide.

## Verification and acceptance

Verify no look ahead across splits, generator reproducibility and cost accounting. Run repeated null experiments and inspect selection bias and regime shifts.

The first release is accepted only when its documented requirements pass, a clean setup can run its checks and any failed or inconclusive checks are visible. Measurements are observations, not promised targets.

## Evidence and metrics

False discovery and selection rates, out of sample performance distributions and sensitivity to costs, with uncertainty.

Keep inputs or their authorised references, configuration, versions, seeds where relevant, commands, outputs and environment details with each run. Link every claim to a test or source.

## Decisions and dependencies

Choose sample sizes and confidence method before running; retain all tested strategies.

See [programme plan](../programme-plan.md) and [engineering standard](../engineering-standard.md). Original briefs and case studies are in [the source archive](../source/Engineering%20Portfolio/).


## Detailed engineering pack

See the [detailed engineering pack](../engineering-packs/07-alpha-validity-engineering-pack.md) for requirements, module boundaries, decisions and verification.
