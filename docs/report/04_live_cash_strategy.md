# 04. Live cash strategy

Full report: `../stage-04-05-report.md`.

- Room settings (rake, drop, open and 3-bet sizes) are table settings; $1/$3 added; three example rake presets in the table builder.
- Pre-flop EV analysis from the same opponent model as the range charts: limpers and isolation, large raises, 3-bets and limp-reraises, short stacks, rake, multiway.
- Raise size matters through explicit, switchable live-room assumptions (not something the simulated players do).
- Every recommendation is shown against a typical player (baseline) and against a rock, station, and maniac ("what could change it"), with the opponent evidence and a computed confidence: Clear, Close, Opponent-dependent, or Low-information.
- Overbets only on the river and only with a hand that beats at least 80% of the range.
- Scenario tests: `tests/test_strategy.py` (16) and `tests/test_adversarial.py` (10). Each changes one thing and checks the direction of the result.
- Limits: the opponents are simulated (fold to 3-bets about 75 to 80% of the time); several constants are judgment, not measurement (listed in the report); multiway EV treats opponents as independent.

## Version 42: rules a player can remember

- **Opening:** the charts still decide opens. The same thing as one rule: open if your hand score (Chen formula) is at least your seat number. 9-handed: UTG 9, early and middle 8, hijack 7, cutoff 6, button 5, small blind 6. 6-handed: 7, 7, 6, 5, 5. It matches the charts on at least 90% of hand combos at every seat (tested).
- **Limped pots:** raise if the score is at least your seat number plus 1 for each limper after the first (to about 4 big blinds plus 1 per limper); limp behind or complete with any pair or any suited hand that scores 6 or more; fold the rest. This one rule now drives the advice and grading on every table and the course's isolation lessons and limp drill (the big blind keeps its own logic). It matches the app's previous limped-pot logic on 92% of hand combos. It is standard live practice written as a formula, not a solver result, and not fitted to the EV analyzer, which is unreliable here (its simulated limpers fold too much to raises and it ignores implied odds).
- **After the flop:** grading is against a typical opponent by default (Settings > Post-flop grading: Typical opponent or Read-based), and every graded decision states the math: the price, your equity against the likely range, and what share of the range must continue against that bet size, or how often a bet must work as a bluff.
- **Where to find it:** the Coach tab opens with a "Rules to remember" card (scoring, seat numbers, the limper rule, and the price table).

## Version 43: river solver
Heads-up river decisions are now graded against a solver run on your actual board (CFR, no hand abstraction, exact card removal), and the Analysis sheet shows the solver's mix for your hand and the value of each action. It reproduces the textbook river equilibrium in tests. Flop and turn are not solved yet, and the ranges entering the river are built from the charts and board-aware rules rather than solved. Details: `../solver.md`. Settings > Post-flop grading: Solver (default), Typical opponent, or Read-based.
