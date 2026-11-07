# Stages 04 and 05 report: live strategy, coaching, and training

Scope: prompts 04 and 05, for hold'em cash tables. What is not done is listed at the end.

## Stage 04: live strategy

- **Room economics are settings.** Rake (percent, cap, drop, no flop no drop) and live sizing (open size, 3-bet multiple) belong to the table. The custom table builder has three example rake presets (none, light, standard) and a new $1/$3 blind level. Presets are examples, not facts about any casino. The analysis states the room assumptions it used.
- **Pre-flop EV analysis** (`preAnalyze`). Fold, call or limp, raise sizes, and the shove when short or facing a 3-bet, valued from the same opponent model as the range charts: each opponent's range comes from what they did this hand, their response comes from a model fit to simulated pre-flop decisions by type, position, and situation. It covers limpers and isolation, 3-bets, 4-bets and limp-reraises, rake, effective stack, and multiway pots (at most three continuing opponents).
- **Raise size matters.** A raise bigger than the usual size is assumed to be stronger and to fold out more hands. These are explicit live-room assumptions (`SIZE_TILT`, `SIZE_GAMMA`, per-room settings, 0 turns them off), not something the simulated players do. A test shows the 12 big blind result changes when they are off.
- **Baseline and adjustment.** Every analysis is also run against a typical player ("baseline") and against a calling station, a rock, and a maniac ("what could change it"). The panel shows baseline, adjustment, which opponent evidence drives it (and whether it is a player-specific read or a population assumption), and a confidence label.
- **Confidence is computed**: Clear, Close, Opponent-dependent, or Low-information, from the EV gap against the estimate's noise, whether the best play changes with the opponent's type, and how many hands have been seen.
- **River overbets** (150% and 200% pot) are candidates only on the river and only with a hand that beats at least 80% of the opponent's range.
- **Multiway** pots are analyzed as multiway: the same flop air hand bets heads-up and checks three-way.
- **Pure bluff-raises** carry an explicit warning.

## Stage 05: coaching

- **Decision quality is separate from the result.** Grading uses the model's EV for the chosen option against the best option and never looks at opponents' cards. The hand result is stored separately (in big blinds) after the hand and shown beside, not inside, the grade.
- **Tolerance, not exact matching.** A choice within max(0.15 bb, 1.5 x the estimate's noise) of the best option is not a mistake. The grade also records the loss against the typical-player baseline, the confidence label, and whether the player failed to adjust.
- **Pre-flop decisions in cash games are now graded from the EV model** (they used fixed thresholds before). Setting `S.settings.preModel=false` restores the old pre-flop grading (there is no screen for it).
- **Leak categories come from the EV comparison** (folding too much, calling too wide, missed value, bluffing too much, overplaying medium hands, bet size, and three pre-flop patterns), not from a guess after the fact.
- **Coach tab** (Career): EV lost per 100 decisions with a 95% interval overall and by position, street, pot type, opponent, and effective stack. No pattern is named under 30 decisions, a pattern needs at least 6 examples and a clearly positive loss, and every table states that this is simulated performance, not a real-world win rate.
- **Personalized drills:** a "Practice" button maps the top flagged pattern to one of the existing drills. A new reading drill shows a player's stats after 40, 60, or 90 hands and asks for the type; it uses the same reader as Observed-only mode.
- **Saved data version 2** adds the coaching store and moves a saved table-builder blind index to match the new $1/$3 entry. Nothing else changes, and migration is safe to run twice (tested).

## Tests

`python3 tests/run_all.py`: 104 pass, 0 fail, 1 known failure (illegal action acceptance, planned for prompt 06). New: `tests/test_strategy.py` (16) and `tests/test_coaching.py` (13). Each strategy scenario changes one thing and checks the direction of the result: large raises, isolation, opener type and 3-bet folds, limp-reraises, short stacks, rake flipping a marginal call, multiway c-bets, thin value, under-bluffed river aggression, river overbets, and the four confidence labels. Mutation checks now cover 17 deliberate breakages, including the grading tolerance, the sample-size rule, the size assumption, rake in the pre-flop call, and unrestricted overbets.

## Mistakes caught during the work

- A new function named `coachHTML` silently replaced the existing in-game coach box's function of the same name. Found by a test returning an empty string and renamed before release.
- The pre-flop analyzer ignored raise size, gave NaN on rare action sequences (an absolute weight cutoff emptied the range; the post-flop prior had the same flaw), and was too pessimistic about how much equity hands collect after the flop. All fixed and tested.
- My first overbet candidates were being recommended for medium hands by exploiting the simulated players' sharp thresholds. They are now limited to nutted river hands.
- Some early test spots had no betting history, so the opponent's range was not narrowed and the results meant nothing. Fixed in the spots.
- A test left the page in Observed-only mode and later tests inherited it. Every test now sets its own mode.

## Known limitations

1. **The opponents are simulated players.** They fold to 3-bets about 75 to 80% of the time, more than most real players, so pre-flop 3-bet advice leans aggressive for real live games. Against a simulated nit that bets every street, the model finds a bluff-raise because those nits fold everything below a set to a raise. The sensitivity view marks such spots Opponent-dependent and the panel warns on pure bluff-raises, but the numbers are still about simulated opponents.
2. **Some constants are judgment, not measurement:** the pre-flop equity realization values, the raise-size assumptions, and the 7% per extra opponent discount.
3. **Regular types still raise too little pre-flop** (carried over from stage 03).
4. **Multiway EV treats opponents as independent** and ignores side pots and squeezes behind a caller.
5. **No re-benchmark of the pre-flop recommendations against rollouts** of the real engine, and no solver comparison. Post-flop EV is the stage-02 engine with the opponent changes from stage 03.
6. **Coaching data starts at this version.** Earlier hands are not graded retroactively. The Coach tab counts only decisions the model graded (cash tables, hold'em).
7. **Drills reuse existing drills** for personalization, and the only new mode is the reading drill. There is no generic engine-backed multiway drill yet.
8. **Cost:** each hero decision now runs two analyses (about 90 ms on a desktop browser each pre-flop; a phone will be slower).
