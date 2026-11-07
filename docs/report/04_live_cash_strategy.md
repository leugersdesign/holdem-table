# 04. Live cash strategy

Full report: `../stage-04-05-report.md`.

- Room settings (rake, drop, open and 3-bet sizes) are table settings; $1/$3 added; three example rake presets in the table builder.
- Pre-flop EV analysis from the same opponent model as the range charts: limpers and isolation, large raises, 3-bets and limp-reraises, short stacks, rake, multiway.
- Raise size matters through explicit, switchable live-room assumptions (not something the simulated players do).
- Every recommendation is shown against a typical player (baseline) and against a rock, station, and maniac ("what could change it"), with the opponent evidence and a computed confidence: Clear, Close, Opponent-dependent, or Low-information.
- Overbets only on the river and only with a hand that beats at least 80% of the range.
- Scenario tests: `tests/test_strategy.py` (16) and `tests/test_adversarial.py` (10). Each changes one thing and checks the direction of the result.
- Limits: the opponents are simulated (fold to 3-bets about 75 to 80% of the time); several constants are judgment, not measurement (listed in the report); multiway EV treats opponents as independent.
