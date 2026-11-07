# 07. Independent validation

## Honest scope

This was done by the same agent that built the app, so it is not independent in the strict sense. What substitutes for independence: references written separately from the app code (an exhaustive and random cross-check of the hand evaluator in Python, exact enumeration for equity), mutation checks that break the app on purpose to see whether the tests notice, statistical tolerances instead of exact bot actions, fixed seeds, and scenarios whose expected direction was written down from poker logic before looking at the output where possible. A person should still review the strategic claims.

## How to reproduce

```
python3 tests/run_all.py                 # 126 tests, about 1 minute; each test sets its own seed with seedRNG(n)
python3 tests/mutation_check.py          # 23 deliberate breakages, about 8 minutes
python3 tools/benchmark.py               # performance profile, writes docs/performance.json
python3 tools/calibrate_ev.py 500 30 "shark,station,limper,whale,tag" out.json 16 x revealed && python3 tools/score_calibration.py out.json
python3 tools/make_opponent_doc.py       # regenerates docs/opponent-model.md
```

## Results

| Area | Tests | Result |
| --- | --- | --- |
| Hand evaluation, ties, kickers | test_evaluator (3) | Pass: exhaustive five-card check, random seven-card cross-check |
| Equity, card removal, multiway, convergence, sampling bias | test_equity (12) | Pass against exact enumeration; standard error and effective sample size reported |
| Range conditioning, normalization, bet-size evidence | test_ranges (11) | Pass |
| Pot odds, EV accounting, rake, all-in, refunds, oversized bets | test_ev (16) | Pass |
| Engine: chips, cards, side pots, rake, long sessions | test_engine (10) | Pass, no known failures |
| Opponent simulation | test_opponents (25) | Pass: distinct types, individual variation, size and street effects, gradual skill-dependent adaptation, no access to hidden cards (twin runs), **smooth response to bet size** |
| Strategy scenarios ($1/$2 and $1/$3 style spots) | test_strategy (16) | Pass: each changes one tendency, size, stack, or the rake and checks the direction |
| Adversarial recommendations | test_adversarial (10) | Pass: high equity but check, bluff with low equity, small beats large, call good against one range and bad against another, one observation does not justify an exploit, similar-EV options graded monotonically, explanations contain only computed numbers |
| Coaching | test_coaching (15) + test_adversarial | Pass: result separate from decision, tolerance, leak categories, no leak from small samples, adjusting versus failing to adjust |
| Reliability | test_reliability (8) | Pass: illegal actions rejected, bots always legal, refresh loses no chips, precompute transparent, 4 table types x 500 hands |
| Mutation checks | 23 | All caught (0 missed, 0 skipped) |
| UI scripts (phone viewport) | 9 plus 2 refresh checks | Pass (the draw-game script is intermittent in v39 as well, see 06) |

Total: 126 tests, 0 failed, 0 known failures. Test tolerances were not loosened to pass; where a test encoded an assumption that changed (a call-cap threshold written for the old hard threshold), the test was rewritten to check the intended relationship, and a mutation check confirms it still catches the defect.

## Defects found during validation

Refresh loses the pot; no action validation; duplicate bot actions; hard-threshold bot decisions that made every type exploitable by betting just under a size (largest jump 75 points, now 30); empty ranges on rare sequences; a pre-flop analyzer that ignored raise size; overbets recommended for medium hands by exploiting thresholds; a function-name collision with the live coach box. Several of my own tests were wrong and were fixed (bad pots, missing betting history, state leaking between tests, an assertion tuned to the old noise).

## EV recommendation versus rollouts (512 spots, 30 playouts per option, simulated opponents, revealed mode)

| | vs previous advice | vs the bots' own play | vs always check/call |
| --- | --- | --- | --- |
| all | +1.58 [+0.83, +2.44] | +2.53 [+1.47, +3.68] | +3.80 [+2.68, +5.02] |
| flop only | +0.82 [+0.19, +1.51] | +0.63 [-0.21, +1.51] | +1.87 [+0.85, +2.87] |

(bb per decision; 95% paired-bootstrap intervals.) Stage 03 measured +0.58 [-0.07, +1.22] against the previous advice. Several things changed in between (smooth thresholds, overbet candidates, engine fixes), so the improvement is not attributed to any one of them. These are results against simulated players only.

## Release gate

| Criterion | Assessment |
| --- | --- |
| Critical correctness tests pass | Met: 126 of 126; 23 of 23 mutations caught |
| Known failures documented | Met: none open in the suite; limitations below |
| Core scenarios behave in the expected direction | Met within the modelled opponents; two caveats below |
| No material regression | Met for behavior (type stats moved 5 points or less), the UI scripts, and the EV benchmark (re-run above) |
| Usable through a full session | Met in simulation: 3,000 hands on four table types, 0 errors, flat memory; refresh safe. Not tested on a physical phone |
| Limitations and unverified claims disclosed | See below |

Assessment: the app passes this gate **for its stated scope, a training simulator with simulated opponents**. I do not claim the advice is correct against real players, that it shows any real-world edge, or that it is solver quality.

## Limitations and unverified claims

1. The opponents are simulated. They fold to 3-bets about 75 to 80% of the time (more than most real players), so pre-flop 3-bet advice leans aggressive for real live games; against a simulated nit that bets every street the model can find a bluff-raise (flagged Opponent-dependent, with a warning).
2. Pre-flop equity realization, the raise-size assumptions, and the 7% per extra opponent discount are judgment values, not measured.
3. The regular types raise less pre-flop than live regulars.
4. Multiway EV treats opponents as independent and ignores side pots and squeezes behind a caller.
5. No solver comparison; no study against real players.
6. Mobile testing is emulated (viewport and CPU throttle).
7. Replay under a different assumption and a manual observation notebook are not built.
8. A refresh voids the hand instead of resuming it.
9. Pre-flop grading uses the opening charts by default. The EV model for pre-flop is optional and has not been validated as a grader against the charts (the two can disagree; the report does not claim either is better).
