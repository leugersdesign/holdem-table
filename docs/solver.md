# River solver

## What it does
On a heads-up river, the app solves the spot on your actual board and grades your decision against the result. It is a game-theory equilibrium for both players' whole ranges, not a read of one opponent.

## Method
- Counterfactual regret minimization (CFR+, linear averaging, alternating updates), 250 iterations in the game.
- No hand abstraction: every two-card hand is its own strategy, ranked against the real five-card board. Card removal is exact (a hand that shares a card with an opponent's hand never meets it).
- Bet sizes: one third and three quarters of the pot, all in, plus any size actually used on this street. One raise (pot size, all in, or the size actually used). Rake is applied to the pot the winner collects.
- The solve runs from the start of the river; your current spot is found by following the river action so far, so the opponent's range at your decision is shaped by the equilibrium itself, not by a guess.
- It runs in a background worker as soon as it is your turn on the river. If you act before it finishes, that decision is graded against a typical opponent and says so.

## Validation (tests/test_solver.py)
- **Textbook equilibrium:** a polarized range (nuts or air) against bluff-catchers with one pot-sized bet. Theory: bet all the nuts, bluff half the air, call half. Solver: 100%, 50.1%, 50.0%, exploitability 0.02% of the pot.
- Exploitability falls as it runs (20, 100, 500 iterations).
- Exact card removal on a hand-checked example.
- The board drives the answer: the same hand and story with only the river card changed (A-Q of hearts, blank versus flush-completing river) goes from checking almost always to betting or shoving most of the time.
- Grading uses the solver when the solve is ready, never waits for it, and never penalizes an action the solver itself takes 10% of the time or more.
- Four deliberate breakages (no card removal, board ignored, grading bypassing the solver, ranges ignoring the earlier action) are each caught.

## The assumption that matters: the ranges at the start of the river
The river solve is exact for the ranges it is given. Those ranges are not solved; they are built:
1. **Pre-flop:** from the charts and rules. Opened: the seat's opening chart. Flatted a raise: hands with 42 to 57% equity against the opener's range (36 to 57% from the big blind). 3-bet: premiums and hands with 57% or more against the opener's range, plus some small suited aces. Called a 3-bet: strong hands from the opening chart. Limped: hand score 4 or more. Big blind check: everything, with premiums reduced.
2. **Flop and turn:** each hand is weighted by how it connects with that street's board (the app's made-hand strength score S and its count of outs) and the action taken:
   - bet or raise: weight x clamp(sigmoid((S - 3.8) / 0.45) + draw bonus (0.45 with 8+ outs, 0.15 with 4+), 0.08, 1)
   - call: weight x clamp(sigmoid((S - 2.7) / 0.45) + draw bonus (0.7 with 8+ outs, 0.35 with 4+), 0.03, 1)
   - check: weight x (1 - 0.55 x sigmoid((S - 4.6) / 0.4))
   These parameters are judgment, not solved. A player who bet twice is tested to hold clearly stronger hands than one who checked twice.

## Speed
About 1.2 seconds in the background at normal desktop CPU, about 3.5 seconds with the CPU throttled 4x (a rough stand-in for a phone). The page stays responsive while it runs.

## Limits
- River only, heads-up only. Flop and turn decisions and multiway pots use the model (typical opponent by default). Solving the flop and turn is the next stage.
- The ranges entering the river come from the rules above, not from solving the earlier streets.
- Two bet sizes plus all in, and one raise: a real solver can use more sizes.
- The solver plays the equilibrium; it does not exploit a specific opponent. That is deliberate (it is the baseline), and reads can still justify deviating.
