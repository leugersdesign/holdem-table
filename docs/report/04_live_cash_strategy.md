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

## Version 44: the baseline is the solver, with no reads
Heads-up flop, turn, and river decisions are graded against a solver on your actual board; multiway pots by the price against chart-based ranges. Nothing in Solver mode's grading or baseline advice uses a read on a player: the typical-opponent fallback, the type-based cushions and live overrides after the flop, and the live pre-flop 3-bet table keyed to the opener's type (in chart mode) are gone from it. The read-based model stays on the Analysis sheet as the Exploit view. A Deviate button logs deliberate departures from the baseline separately. Details: `../solver.md`.

The raise box (version 44) adds quarter, third, two-thirds pot buttons, raise multiples, half and whole big-blind steps, and shows the chosen size as a share of the pot.

## Version 45: straddles
- **Your straddle (home games):** Table options, or the Straddle button between hands, sets Off, Under the gun, Button, or Both. You post 2 big blinds when you're in that seat with 4 or more players dealt in (one straddle per hand; a bot's under-the-gun straddle comes first). On the button the small blind acts first and you act last before the flop.
- **Advice and grading with a straddle on (anyone's):** sizes are counted in straddles (raise to 3 to 4 straddles plus 1 per limper; home tables use 4). Opens use the hand score: early and middle seats and the small blind add 1 to their seat number, the cutoff and button don't. Limped pots use the same rule with the same +1. The straddler is not counted as a limper, checks its option like a big blind, and defends a raise like one. The big blind facing a straddle calls cheaply with hands scoring 6 or more, any pair, or a suited hand scoring 6 or more, raises 9 or more, and folds the rest.
- **Solver ranges:** an opener's range over a straddle uses the same tightened rule, and the straddler's flat calls use the big blind's wider band.
- **Raise box:** over a straddle the presets are 3, 4, and 5 straddles (plus one per limper) and the amount shows how many straddles it is.
- **Why it changes:** a straddle doubles the stakes for the hand, so stacks play half as deep. Big pairs and strong high cards gain; small pairs and suited connectors lose, because set mining and draws need deep stacks to pay. The seat after the straddle is the new first to act. Straddling yourself under the gun is usually a losing play (a forced blind, out of position all hand); the button straddle is the better one if your game allows it.
- Tests: hero straddles under the gun and on the button, the button straddle's action order, chip conservation over 400 hands with straddles, the tightened open, the straddler's option, the big blind facing a straddle, and the raise box in straddles. Two new deliberate breakages are caught.
