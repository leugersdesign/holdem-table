# Stage 03 report: opponent realism

Scope: prompt 03. Complete for hold'em cash tables; the limits are listed at the end. Reference tables (traits, archetype priors, measured behavior) are in `docs/opponent-model.md`, generated from the code.

## What changed

- **Individual players.** `genTraits`, `trOf`, `archBot`: every opponent draws 27 documented traits from its archetype's averages. Four latent factors (looseness, aggression, stickiness, skill) load onto the traits so related ones move together, and contradictory combinations are repaired (`traitProblems`). `liveProf` applies the traits to every post-flop number; `botPre` applies them to the pre-flop paths.
- **Three new archetypes** from the pack: Recreational wildcard (`wild`, highest spread, inconsistent sizing), Thinking player (`thinker`, balanced, learns and notices more), Short-stack recreational (`shorty`, buys in at 25 to 40% of the normal stack, shoves or folds pre-flop). The existing eight are unchanged apart from being individualized.
- **Richer decisions** (`liveDecide`): second and third barrels after betting the previous street, check-raising, over-valuing one pair, a call cap (a hand at or above it keeps calling any bet), bet-size noise (`gauss`), and belief-based bluffing.
- **Limited observation** (`observeHand`, `belief`, `adaptCall`, `adaptBluff`, `adaptPre`, `sharkRead`): replaces the old behavior in which every opponent read the hero's whole-session stats for free (`heroImage`) plus a table-wide 30-hand bluff memory (`T.mem`). Each opponent now keeps Beta counts of what it noticed, regressed to population priors, with fading evidence and skill-dependent adaptation.
- **Observed-only mode** (`readOpp`, `modelKeyP`, `modelProfAt`, `viewLabel`, setting `oppInfo`): the sheet, the opponent list, the analysis, the range charts, and the advice text use an estimated type read from hero-visible stats, never the hidden type. **It is now the default.** Settings > Opponent info > Revealed restores the old behavior.
- **Pre-flop model refit** (`PFM`) on about 295,000 decisions from individualized bots, covering all 12 types at live and online tables, with a fallback to live-table cells instead of a flat prior.
- **Tools:** `tools/measure_archetypes.py`, `tools/summarize_archetypes.py`, `tools/make_opponent_doc.py`; `tools/record_preflop.py` now rebuilds the table every 300 hands.

## Tests (75 pass, 0 fail, 1 known failure)

`python3 tests/run_all.py` and `python3 tests/mutation_check.py`. New module `tests/test_opponents.py` (24 tests):

- every generated trait in range, none contradictory, every trait documented; archetype means preserved; individuals differ; wildcard varies most; correlations match the factor model;
- more than 217,000 decisions per type: types behave as designed, every pair distinguishable (closest pair 0.05 apart in rate space), folds rise with bet size, no type folds everything to a shove, no type is a universal bluff target (a bluff of 5x pot or more loses against all 12), barrels, check-raises, and pair over-valuation exist, the wildcard sizes far less consistently, the short stack shoves or folds;
- a new opponent knows nothing, one observation barely matters, 20 matter somewhat, skilled players adapt more, beliefs regress to the population, old evidence fades, players learn only from events they noticed (a player who already folded notices about 30% as much);
- **twin runs:** 240 seeded hands in each mode, rerun with the hero holding different cards while his actions stay the same: bot actions are identical, so no bot decision reads his hole cards;
- observed mode: the analysis is identical whether the hidden opponent is a maniac, a rock, or a station; the sheet shows no type name, skill dot, or tilt before a read exists;
- the reader: top-three accuracy at least 90% at 300 hands; declines to guess under 12 hands; default is Observed only.

**Mutation check:** 12 deliberate breakages, all caught. One was missed on the first pass (removing the call cap) because my test did not exercise the cap; a cap-specific test now catches it.

## Measured results

- **Reader accuracy** (81 players across three seatings): exact type first 47% / 58% / 64% after about 60 / 150 / 300 hands; true type in its top three 88% / 92% / 93%. Solid regular, weekend regular, thinking player, and (on most stats) shark look alike; the wildcard and the thinker are never its first pick.
- **Individual variation** (hero-visible stats, 28 individuals per type): VPIP spread (standard deviation) 3 to 10 points within a type; type averages range from 14% (rock) to 60% (gambler).
- **EV recommendation vs rollouts of the real engine** (512 spots, 6-seat mixed table, 30 playouts per option; paired bootstrap 95% intervals; positive favors the recommendation):

| | vs previous advice | vs the bots' own play | vs always check/call |
| --- | --- | --- | --- |
| Revealed (model knows each opponent) | +0.58 [-0.07, +1.22] | +1.26 [+0.45, +2.08] | +2.62 [+1.65, +3.60] |
| Observed only (model has only a hero's information) | +0.83 [-0.11, +1.84] | +1.47 [+0.35, +2.64] | +2.99 [+1.76, +4.20] |

  The recommendation still beats the bots' own play and always-check/call. **Its edge over the previous rule-based advice is no longer established:** the interval includes zero overall (it excluded zero against the previous, less realistic opponents in stage 02: +1.25 [+0.53, +1.96]). Observed-only mode costs nothing measurable. The river is the only street where the revealed interval excludes zero (+1.62 [+0.41, +3.30]).
- **Bot behavior** over a 1,500-hand seeded table of individuals: plays 30 to 50% of hands, raises pre-flop 5 to 16%, folds to 40 to 70% of bets, c-bets 40 to 85% (all asserted by a test).

## Defects found and fixed during this stage

- Size-model quadrature weights summed to 0.99999 (probabilities off by 1e-5): fixed.
- The online pre-flop model had no cells for two types because my recording runs omitted them, which silently gave a flat prior: more data recorded, and the lookup now falls back to live cells.
- Adaptation was too fast (a thinker reached its maximum adjustment after 20 observed bluffs): beliefs are now clipped and gains reduced; 5 bluffs barely matter and 20 matter somewhat.
- The "what they think of you" quotes and the opponent list hinted at the hidden type: neutral quotes and observed stats are used in Observed-only mode.
- The thinking player was nearly identical to the solid regular on every decision rate (distance 0.028): retuned to play more balanced (distance now 0.05 or more from every other type).
- Not an app defect: a browser crash in my measurement harness on very long single calls. I measured 4,000 hands on one table: heap flat at about 4 MB, saved state about 52 KB, no leak.

## Mistakes in my own tests (fixed, none were engine bugs)

A pair-bias spot where everyone called; a pot written without including the bet; HTML attributes searched with the wrong quote style; a twin-run that cleared the timer queue before the hand played; and a bound that excluded the correct expected value (0.65).

## Known limitations

1. **Pre-flop aggression of the regular types is low.** In casino mixes a solid regular plays 27% of hands and raises 8% (a live TAG is nearer 15%); the cause is the older pre-flop code in limp-heavy tables, not the new traits. For prompt 04.
2. **The EV engine needs recalibration** against the new opponents and a multi-street model (above): its edge over the previous advice is unproven.
3. **Observed-only mode covers hold'em.** The draw game's sheet still names types and tendencies.
4. **Type-flavored table talk remains** (chatter lines are by archetype, like real table talk), and the analysis in Observed-only mode assumes a typical player of the read type, ignoring an individual's deviations, tilt, and current beliefs about the hero.
5. **Adaptation is limited to five stats** (pre-flop play and raising, aggression, folds to bets, bluffs and value shown). No position-specific learning and no learning from bet-size tells.
6. **Tournament and older-path bots keep their previous behavior;** traits apply to cash-table bots.
7. **The universal-bluff check uses random hands,** not realistic calling ranges.
8. **Traits are generated at table creation** (and lazily, from the player's name, for saved tables and cast characters), so they are not carried between sessions.

## Data and migration

Bots gain `tr` (traits) and `obs` (beliefs), saved with the table; older saved tables generate traits lazily from the name. `S.settings.oppInfo` is new; absent means Observed only. The hand history gains `pa` and `xr` flags. No existing statistic changed meaning.
