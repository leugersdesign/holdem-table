# 02. Math and EV engine

Full report: `../stage-02-report.md`.

- **Reproducible randomness.** All 94 uses of `Math.random` go through `RNG()`; tests call `seedRNG(n)`. Real play is unchanged.
- **Equity.** Sequential importance sampling with no dropped samples, a three-way tie counted as one third each, and a standard error plus effective sample size reported with every estimate. Checked against exact enumeration.
- **Ranges.** Prior, likelihood, and posterior are separate; probabilities are accumulated in log space with an underflow guard and a collapse fallback; bet size is evidence (four size buckets, with noise handled by quadrature). Weights are now relative, so a rare action sequence cannot empty a range (found and fixed in stage 06).
- **EV accounting.** Rake (percent, cap, drop, no flop no drop), all-in as a candidate, refund of unmatched chips, per-option standard error, and oversized bets flagged and never recommended.
- **Evaluator.** Exhaustive five-card check and random seven-card cross-check against an independent Python implementation: `tests/test_evaluator.py`.
- **Limits.** EV is a one-street estimate with judgment-set realization factors; multiway EV treats opponents as independent and ignores side pots; opponents are simulated players, not people; no solver comparison.
