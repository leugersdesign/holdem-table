# 01. Prioritized engineering plan: what was planned, what was done

Order followed: math first (everything else depends on it), then opponents, then strategy, coaching, product and reliability, then independent validation.

| Stage | Goal | Status | Where the detail is |
| --- | --- | --- | --- |
| 02 | Math and EV engine | Done | `02_math_and_ev_engine.md`, `../stage-02-report.md` |
| 03 | Opponent behavior | Done for hold'em cash tables | `03_opponent_behavior.md`, `../stage-03-report.md`, `../opponent-model.md` |
| 04 | Live $1/$2 and $1/$3 strategy | Done for hold'em cash tables | `04_live_cash_strategy.md`, `../stage-04-05-report.md` |
| 05 | Coaching and training | Done, with the gaps listed there | `05_coaching_and_training.md`, `../stage-04-05-report.md` |
| 06 | Product, sessions, performance, reliability | Reliability and performance done; some product items deferred | `06_product_and_simulation.md` |
| 07 | Independent validation | Done; release gate assessed | `07_independent_validation.md` |

Deferred on purpose (each needs real design work, and none is required for the app to be correct):

1. Replay of a past hand with a different opponent assumption (needs a full hand-state snapshot). What exists instead: every graded decision keeps its alternatives, its confidence label, and the typical-player comparison.
2. A manual notebook for live-table observations. The app records the stats a player could see automatically, and Observed-only mode keeps hidden types hidden.
3. A generic engine-backed multiway drill, and a solver comparison.
4. A Web Worker. The measured worst case is handled by computing ahead during the player's thinking time (see 06).
5. Re-tuning the regular opponent types' pre-flop raise rates (they raise less than live regulars).
