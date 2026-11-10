# Solver (flop, turn, and river, heads-up)

## Version 44 in one paragraph
Solver mode (the default) now grades every heads-up post-flop decision against a solver run on your actual board: flop, turn, and river. No grade or piece of baseline advice after the flop uses a read on the player any more. Multiway pots have no solver; they are graded by the price against chart-based ranges, also with no reads. A decision you make before the solve finishes waits for it (the chip shows "..." and fills in when the solve lands) instead of being graded against a fallback model. The flop and turn sections below describe the new solver; the river section is unchanged from version 43 except that its ranges now come from the solved earlier streets.

## What changed and why (the audit)
Before version 44, "Solver" covered only heads-up rivers. Everything else was graded against a "typical opponent", which in the code was the weekend recreational player type, so flop and turn grades rewarded exploiting a recreational player rather than solver play. Other places the baseline used reads:
- River decisions made before the river solve finished fell back to the same typical-opponent model.
- Post-flop Tools advice compared your equity against ranges built from each player's type, with a cushion for aggressive players.
- On live tables, river thin value and decisions facing a raise were chosen by the opponent's type, and a sizing read was added to the advice.
- Pre-flop facing a raise on live tables, the advice (and so the chart-mode grade) picked 3-bet or call by whether the opener read as loose or tight.
- The Analysis sheet led with the read-based model on the flop and turn.
- Ranges entering the river were narrowed by hand-tuned rules rather than by solved play.
All of these now use the solver or the type-free baseline in Solver mode. The read-based model is still shown on the Analysis sheet, labelled "Exploit view", so you can see what a read would change. A saved "Typical opponent" setting from version 42 is moved back to Solver once (version 3 of the saved data); choosing it again afterwards sticks.

## Flop and turn solver
- Same method as the river: discounted CFR, every two-card hand its own strategy, exact card removal, money counted from the start of the street.
- **Turn:** turn betting, then every river card (exact), then river betting (three quarters of the pot, plus all in when the stack is no more than 1.5 pots). After a turn raise is called, the river is checked down (the stack left is small by then).
- **Flop:** flop betting, then 16 turn cards spread evenly through the deck by rank and reweighted so each suit counts exactly as often as it really comes, then turn betting, then a sampled river with no more betting. The flop grade gets an extra tolerance of 3% of the pot for the card sampling (GT_NOISE); the test suite checks the sampling error stays inside it.
- **Bet sizes on the street being graded:** one third and three quarters of the pot, all in, plus any size actually used; one raise (pot size or all in). If you bet a size the tree doesn't have, the spot is solved again with your size before it is graded.
- **Raise box:** post-flop bets have one quarter, one third, one half, two thirds, three quarters, and pot; raises have 2.5x, 3x, and the same pot fractions; pre-flop opens have 2.5x to 5x. Below them, steps of minus and plus one big blind and half a big blind. The amount shows its size as a share of the pot (or in big blinds for a pre-flop open), hidden when the live pot-counting setting is on. Deviate is also in the raise box, so you can flag a sized bet without closing it.
- **Speed (reference machine, the same one where the river takes about 1.2 s):** turn about 4.4 s, flop about 4.8 s, both converged to about 2.3% of the pot. Solves start in a background worker as soon as a street is dealt, so most are ready by your turn.
- **Ranges:** pre-flop charts and rules, then each solved street multiplies every hand's weight by how often the equilibrium took the actions that were actually taken. If an earlier street could not be solved (or was multiway), the board-aware rule below stands in for that street only.

## Deliberate deviations
Tap **Deviate** under the action buttons before acting when a read says to leave the baseline. The decision is still shown against the solver (its chip carries a D), but it is kept out of accuracy, the leak finder, coaching stats, and the redo list, and logged on the Coach tab with the baseline's cost estimate and the hand result.

## River solver (version 43)

### What it does
On a heads-up river, the app solves the spot on your actual board and grades your decision against the result. It is a game-theory equilibrium for both players' whole ranges, not a read of one opponent.

## Method
- Counterfactual regret minimization (CFR+, linear averaging, alternating updates), 250 iterations in the game.
- No hand abstraction: every two-card hand is its own strategy, ranked against the real five-card board. Card removal is exact (a hand that shares a card with an opponent's hand never meets it).
- Bet sizes: one third and three quarters of the pot, all in, plus any size actually used on this street. One raise (pot size, all in, or the size actually used). Rake is applied to the pot the winner collects.
- The solve runs from the start of the river; your current spot is found by following the river action so far, so the opponent's range at your decision is shaped by the equilibrium itself, not by a guess.
- It runs in a background worker as soon as it is your turn on the river. If you act before it finishes, the decision waits for it (version 44; before that it was graded against a typical opponent).

### Validation (tests/test_solver.py)
- **Textbook equilibrium:** a polarized range (nuts or air) against bluff-catchers with one pot-sized bet. Theory: bet all the nuts, bluff half the air, call half. Solver: 100%, 50.1%, 50.0%, exploitability 0.02% of the pot.
- Exploitability falls as it runs (20, 100, 500 iterations).
- Exact card removal on a hand-checked example.
- The board drives the answer: the same hand and story with only the river card changed (A-Q of hearts, blank versus flush-completing river) goes from checking almost always to betting or shoving most of the time.
- Grading uses the solver when the solve is ready, never waits for it, and never penalizes an action the solver itself takes 10% of the time or more.
- Four deliberate breakages (no card removal, board ignored, grading bypassing the solver, ranges ignoring the earlier action) are each caught.

### The assumption that matters: the ranges at the start of the river
The river solve is exact for the ranges it is given. Since version 44 the flop and turn parts of those ranges come from the flop and turn solves when they exist. The fallback rules, used only for a street that was not solved:
1. **Pre-flop:** from the charts and rules. Opened: the seat's opening chart. Flatted a raise: hands with 42 to 57% equity against the opener's range (36 to 57% from the big blind). 3-bet: premiums and hands with 57% or more against the opener's range, plus some small suited aces. Called a 3-bet: strong hands from the opening chart. Limped: hand score 4 or more. Big blind check: everything, with premiums reduced.
2. **Flop and turn (fallback only):** each hand is weighted by how it connects with that street's board (the app's made-hand strength score S and its count of outs) and the action taken:
   - bet or raise: weight x clamp(sigmoid((S - 3.8) / 0.45) + draw bonus (0.45 with 8+ outs, 0.15 with 4+), 0.08, 1)
   - call: weight x clamp(sigmoid((S - 2.7) / 0.45) + draw bonus (0.7 with 8+ outs, 0.35 with 4+), 0.03, 1)
   - check: weight x (1 - 0.55 x sigmoid((S - 4.6) / 0.4))
   These parameters are judgment, not solved. A player who bet twice is tested to hold clearly stronger hands than one who checked twice.

### Speed
About 1.2 seconds in the background at normal desktop CPU, about 3.5 seconds with the CPU throttled 4x (a rough stand-in for a phone). The page stays responsive while it runs.

## Limits
- Heads-up only. Multiway pots are graded by the price against chart-based ranges.
- The flop solve samples turn and river cards and checks the river down; the turn solve checks the river down after a raised turn.
- Pre-flop ranges come from the charts and rules, not from a pre-flop solve.
- Two bet sizes plus all in, and one raise: a real solver can use more sizes.
- The solver plays the equilibrium; it does not exploit a specific opponent. That is deliberate (it is the baseline), and reads can still justify deviating.

## Validation of the flop and turn solver (tests/test_gt.py)
- With no betting, the solver's value for each hand equals its exact equity over every runout, checked by brute force with the app's evaluator, including hands that block each other. This pins down the chance nodes and card removal.
- Card weights: for any two hands the cards that can still come add up to one; the suit-stratified sample keeps every suit's total.
- The flop's card sampling: average error per hand on 12 random boards stays inside the flop grade's extra tolerance.
- Exploitability falls as the turn solver runs (4, 16, 48 iterations).
- The board drives the answer: the same hand bets far more when the turn completes its flush.
- Turn grading uses the solver and never penalizes an action the solver takes 10% of the time or more.
- A decision made before the solve lands is not counted anywhere until the grade exists, then is graded by the solver.
- An off-tree bet size is solved again with that size before grading.
- The turn ranges after a solved flop line differ from the board rule (they come from the solve).
- Multiway: changing who the opponents are does not change the baseline grade. Solver-mode advice after the flop is the same against a station and a nit. Live pre-flop advice facing a raise no longer depends on the opener's type in chart mode.
- Deviations are logged and kept out of every stat. The saved-setting migration moves "Typical opponent" to Solver once.
- Seven new deliberate breakages in tests/mutation_check.py (chance nodes without card removal, grading bypassing the flop and turn solver, a fallback grade before the solve lands, solved play not narrowing the next street, deviations counted, multiway reads, the live 3-bet type table) must each be caught.
