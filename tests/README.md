# Hold'em Table tests

Everything runs against the real app (`index.html`) in headless Chromium. Open the page with `?test=1` and a test hook is
exposed; all game randomness goes through `RNG()`, which tests seed with `seedRNG(n)`, so every run is reproducible.
In normal play the hook is absent and `RNG` is `Math.random`.

## Run

    pip install -r tests/requirements.txt && python3 -m playwright install chromium
    python3 tests/run_all.py                 # everything, about 30 seconds
    python3 tests/run_all.py test_equity     # one module
    python3 tests/mutation_check.py          # proves the suite can fail (see below)

`run_all.py` exits 1 on any failure. Known failures (documented defects not fixed yet) are listed and do not fail the run.
The files are also plain `pytest` tests.

## What is covered

| Module | Checks |
| --- | --- |
| `test_evaluator.py` | Hand ranking vs the independent `treys` library: all 2,598,960 five-card hands (must give exactly 7,462 classes), 300,000 random and 60,000 edge-case seven-card hands (seeded). Same class and same order, or fail. |
| `test_equity.py` | Equity vs exact enumeration (head-to-head, 3-way, flop, turn, river), weighted multiway ranges, heavily overlapping ranges, equity vs random hands, card removal, no-valid-assignment case, split-pot shares (1/2 and 1/3), seed reproducibility, error shrinks as 1/sqrt(n), reported standard error matches observed spread. |
| `test_ranges.py` | Range model: normalization, card removal, posterior = prior x likelihood, no underflow on long sequences, collapse falls back to the prior, bet size and raises as evidence, pre-flop prior ordering, size probabilities are proper distributions. |
| `test_ev.py` | EV accounting by hand arithmetic (fold = 0, sunk chips, refunds), rake arithmetic, all-in candidate, sizing table, fold frequency vs size, multiway vs heads-up, oversized-bet rule, stated assumptions and error. |
| `test_opponents.py` | Opponent realism: trait validity, individual variation and correlations, behavior of every type over 200,000+ decisions each, distinctness, no universal bluff target, barrels, check-raise, pair over-valuation, short stack, limited observation and gradual adaptation, twin runs proving bots never read the hero's hole cards, Observed-only mode hides the type, reader accuracy. |
| `test_engine.py` | Chip conservation over thousands of seeded hands (6 and 9 seats, short stacks, with rake), split pots, odd chips, side pots, rake from the main pot, card uniqueness, replay from a seed. |

## Tolerances

Equity tests pass when `|app - exact| <= 4 x reported standard error + 0.002` (0.001 for river multiway). Evaluator, accounting,
rake, and pot-split tests are exact. Simulation tests use fixed seeds and statistical tolerances, never a required single action.

## Reference fixtures

`tests/fixtures/reference_equities.json` holds answers the app shares no code with, computed by exhaustive enumeration with `treys`:
`python3 tests/make_fixtures.py` (about 8 minutes on one core), then `python3 tests/make_blocker_fixtures.py`. Hand-vs-hand
equities were also cross-checked three ways (treys, the app's own evaluator, and the app's sampler). There is no solver data in
this repo, so nothing here claims solver equivalence.

## Mutation check

`mutation_check.py` breaks the engine on purpose (drops the sampler's weight, flips an EV sign, mis-ranks a flush, removes rake,
scores three-way ties as a half, ignores bet size, allows oversized bets, lets a bot read the hero's cards, removes the call cap,
adapts without evidence, uses the true type in Observed-only mode, ignores attention) and requires the suite to fail each time. A test that
cannot fail is not a test: one mutation was missed on the first pass, which is why `test_heavily_overlapping_ranges_*` exists.

## Related tools

`tools/record_preflop.py` records pre-flop decisions from the real bots; `tools/fit_preflop.py` fits the pre-flop opponent model
(`PFM` in `index.html`) with shrinkage chosen on held-out data; `tools/measure_archetypes.py` and `tools/summarize_archetypes.py` produce the
hero-visible stats table (`ARCH_STATS`); `tools/calibrate_ev.py` and `tools/score_calibration.py` benchmark the EV recommendation;
`tools/make_opponent_doc.py` regenerates `docs/opponent-model.md`.
