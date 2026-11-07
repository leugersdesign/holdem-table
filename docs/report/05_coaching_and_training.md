# 05. Coaching and training

Full report: `../stage-04-05-report.md`.

- Grading uses the model's EV for the chosen option against the best option, never the result. The hand result is stored and shown separately.
- Tolerance is max(0.15 bb, 1.5 x the estimate's noise); a choice inside it is not a mistake. The record also keeps the loss against a typical player and a confidence label.
- Leak categories come from the EV comparison. The Coach tab (Career) shows EV lost per 100 decisions with a 95% interval by position, street, pot type, opponent, and effective stack. No pattern is named below 30 decisions and 6 examples. Everything is labelled as simulated performance.
- Personalized practice maps the top flagged pattern to an existing drill. A new reading drill trains the same read Observed-only mode uses.
- Tests: `tests/test_coaching.py` (13) and `tests/test_adversarial.py` (won hand with a bad decision, lost hand with a good one, close-EV alternatives, small samples, adjusting versus failing to adjust).
- Limits: coaching data starts at version 2 of the saved data; drills reuse the existing ones; no engine-backed generic drill.
