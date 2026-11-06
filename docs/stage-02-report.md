# Stage 02 report: math, equity, ranges, and EV

Scope: prompt 02 (work packages WP0 and WP1, plus the EV structure). The multi-street EV calibration is deliberately deferred until after the opponent and strategy stages (see "Not done").

## Files and functions changed (index.html unless noted)

- **Randomness:** `RNG`, `seedRNG` (new), `rndC`; all 94 `Math.random` uses now call `RNG()`. Seeding is only reachable with `?test=1`.
- **Equity:** `eqVsRangesD` rewritten (sequential importance sampling), `eqRandomD` (adds standard error), `EQ_TRACE` (test hook, off).
- **Range model:** `priorRange`, `rangeLogLik`, `rangePosterior` (new); `actionRange` is now a wrapper; `sizeBucket`, `sizeProbs`, `liveLikeHi` (bet size as evidence); `liveProf` (adds sizing habit); `PFM` (pre-flop model refit).
- **Hand history (additive fields only):** `f` (bet size as a fraction of the pot), `la` (last aggressor), `lf` (last bet size); `H.lastBetF`.
- **EV:** `roomRake`, `rakeOf`, `rakeNet`, `evCallPure`, `evCheckDown`, `evAggressHU`, `evAggressMW`, `evStdErr` (new); `evAnalyze` restructured; `evPick`, `evExplain`, `evLowHTML` updated; `EV_MAX_SIZE`.
- **Engine:** `showdown` and `winUncontested` take rake (off unless `T.room.rake` is set).
- **New in the repo:** `tests/`, `tools/`, `docs/`, `.github/workflows/tests.yml`.

## Definitions and conventions

- **Equity** = (wins + tie shares) / valid trials. A tie with n opponents is a share of 1/(1+n) (a three-way tie is one third, not one half; this corrects the previous multiway behavior).
- **Hand-strength percentile** (`comboPct`) is a different quantity and is never used as equity. **Realization** is not inferred from showdown equity; it is an assumed constant (`EV_REAL`).
- **Joint opponent hands** follow P(h1..hk) proportional to the product of each range's weights over card-disjoint tuples. Method: sequential importance sampling; each opponent is drawn from his range restricted to free cards and the trial is weighted by the product of the available mass (computed by inclusion-exclusion). No sample is rejected or dropped. Reported: valid trials, effective sample size, standard error (ratio estimator).
- **Range posterior** = prior x product of P(action | hand, context). The prior is the pre-flop model; the likelihood is accumulated as a log, nothing is pruned; a collapsed posterior returns the prior and sets `collapsed`. Bet size enters the likelihood through four buckets (<40%, 40 to 60%, 60 to 85%, 85%+ of pot).
- **EV** = expected chips gained from now on, measured against folding now (fold = 0). Chips already in the pot are sunk and are only ever chips the hero can win. Chips an opponent cannot match are refunded (heads-up). Rake comes out of the pot the hero wins; no flop, no drop; default is no rake.
- **Oversized bets:** the opponent response model only covers sizes up to 2x the pot. Larger sizes are listed, marked, never recommended, and a hero choice there is graded against the largest modeled size.

## Tests (51 pass, 0 fail, 1 known failure; about 25 seconds)

Commands: `python3 tests/run_all.py`, `python3 tests/mutation_check.py`. Details in `tests/README.md`.

- **Evaluator** vs `treys`: all 2,598,960 five-card hands (exactly 7,462 classes), 300,000 random and 60,000 edge-case seven-card hands. 0 discrepancies.
- **Equity** vs exact enumeration (independent evaluator): 8 pre-flop head-to-head, 2 pre-flop three-way, 16 flop and turn spots, 5 river multiway range spots, 5 heavily overlapping range spots, 8 vs-random hands. Tolerance: 4 x standard error + 0.002.
- **Hand-strength and sampling properties:** card removal, no valid assignment (n = 0), split-pot shares, seed reproducibility, error shrinks as 1/sqrt(n), reported error matches observed spread (ratio within 0.7 to 1.4).
- **Ranges, EV, engine:** normalization, identity, underflow, collapse, bet-size direction, hand-computed EV arithmetic, rake arithmetic, refunds, all-in, size rule, chip conservation (6 and 9 seats, short stacks, with rake), side pots, odd chips, replay from a seed.
- **Mutation check:** 7 deliberate breakages, all caught. The first pass missed one (dropping the sampler weight): my multiway fixtures were too forgiving, so I added overlap-heavy fixtures where the naive sampler is off by 25 to 30 points.
- **Test setup errors I made and fixed (not engine bugs):** four expectations were wrong (a rake case, a pot size, an opponent seat, and a profile assumption). Two range-test assertions were changed after investigation and the reasons are in the history.
- **Known failure:** `act()` accepts illegal actions (for example checking while facing a bet). Deferred to prompt 06.

## Benchmark results

**Sampler bias** (exact enumeration reference), three opponents with a tight mixed range, hero TT: exact 3.92%; previous sampler 4.29% (+0.37, standard error 0.07); now 3.91% (+0.00, standard error 0.05). Other spots were within noise before and after.

**Pre-flop model:** fit on 90,242 recorded bot decisions, shrinkage chosen on a held-out 20%. Held-out log-loss 0.2295 to 0.2267 overall; in sparse cells (7.2% of held-out decisions) 0.3423 to 0.3261. It also fixed an ordering error caused by a cell with 16 decisions.

**Bot behavior check** (2,500 hands, casino 1/2, unchanged by this work): 38% of hands played, 9% pre-flop raise, 55% c-bet, 39% fold to a river bet, 0.08% river bluff-raise.

**EV recommendation vs rollouts of the real engine** (30 playouts per option, same decks for every option, hero continues as a standard regular, 512 spots on a 6-seat mixed table and 300 on the 9-seat casino table, none seen during development). Mean big blinds per decision gained by the recommendation, with paired bootstrap 95% intervals (a paired difference cancels the upward bias that picking the best of several noisy rollouts causes):

| | vs previous advice | vs the bots' own play | vs always check/call |
| --- | --- | --- | --- |
| 6-seat, all | +1.25 [+0.53, +1.96] | +2.42 [+1.38, +3.55] | +5.32 [+4.06, +6.58] |
| 6-seat flop | +0.72 [+0.11, +1.35] | +1.43 | +3.41 |
| 6-seat turn | +2.04 [+0.32, +3.81] | +2.46 | +4.58 |
| 6-seat river | +1.57 [-0.62, +3.58] | +4.98 | +11.38 |
| 6-seat heads-up | +1.04 [-0.38, +2.31] | +3.11 | +6.92 |
| 6-seat multiway | +1.38 [+0.60, +2.20] | +1.99 | +4.31 |
| casino, all | +1.85 [+0.07, +3.68] | +3.66 [+1.55, +6.11] | +8.84 |
| casino multiway | +1.51 [-0.68, +3.66] | +2.35 | +7.56 |

Intervals that include zero: 6-seat heads-up and river; casino multiway, turn, and river. These are not findings of "no effect"; the samples are small for those segments.

**Latency** (desktop headless Chromium, one core, 24 spots each): flop heads-up 37 ms mean, flop three-way 57 ms (p95 75 ms), turn 12 to 20 ms, river 2 to 5 ms. Not measured on a phone.

## Known approximations and unresolved defects

1. **EV is a one-street estimate.** The rest of the hand is approximated by scaling showdown equity with fixed realization factors (`EV_REAL`), which were set by judgment, not fit. The panel states this. Fixing it is the multi-street work after prompts 03 and 04.
2. **Opponent responses come from the simulated players' own decision rules.** The benchmark therefore measures agreement with those simulated players, not real people, and no solver comparison exists (no solver data in the repo). The model must be recalibrated after the opponent changes.
3. **The simulated players are exploitable at the extremes:** they fold 99%+ to a 50x-pot bet because their response saturates at 2x the pot. The size rule hides this from recommendations; the cause is prompt 03's work.
4. **Bet-size evidence is very strong in this model.** A player who sizes outside his habitual band can only have used the strength-based branch, so a very large or very small bet is nearly conclusive. Real players are noisier. Prompt 03 must soften this.
5. **Multiway EV** treats opponents as folding independently and ignores side pots. Refunds are modeled heads-up only.
6. **Rake** is applied to the final pot of each line; no time charge or jackpot drop.
7. **Pre-flop model** is fit on simulated decisions and sparse cells are shrunk toward the pooled fit; open-versus-limp ordering is not asserted by a test.
8. **Flop equity** uses 150 sampled runouts with a standard error from a 5-fold split; turn and river are exact for the modeled range.
9. **The older (non-live) bot path** does not use bet size as evidence.
10. **Not changed here:** grading thresholds (0.2, 1, 3 bb) and leak labels still come from the old rules (prompt 05); pre-flop advice thresholds (prompt 04); illegal-action rejection and replay (prompt 06).

## Data and migration

No saved-data migration was needed: new history fields exist only in memory during a hand, and the optional room and rake fields default to off. Existing statistics keep their meaning. The one change that affects reported numbers is the three-way tie share (1/3 instead of 1/2), which corrects equity in rare multiway ties.
