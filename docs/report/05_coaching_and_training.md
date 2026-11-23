# 05. Coaching and training

Full report: `../stage-04-05-report.md`.

- Post-flop grading uses the model's EV for the chosen option against the best option, never the result. By default it grades against a typical opponent rather than the read (Settings > Post-flop grading), and each graded decision shows the price math. Limped pots are graded by the memorable limper rule (see 04). Pre-flop grading uses the opening charts and existing rules by default; the EV model is an option in Settings > Pre-flop grading (and the Analysis sheet shows it either way). The hand result is stored and shown separately.
- Tolerance is max(0.15 bb, 1.5 x the estimate's noise); a choice inside it is not a mistake. The record also keeps the loss against a typical player and a confidence label.
- Leak categories come from the EV comparison. The Coach tab (Career) shows EV lost per 100 decisions with a 95% interval by position, street, pot type, opponent, and effective stack. No pattern is named below 30 decisions and 6 examples. Everything is labelled as simulated performance.
- Personalized practice maps the top flagged pattern to an existing drill. A new reading drill trains the same read Observed-only mode uses.
- Tests: `tests/test_coaching.py` (15) and `tests/test_adversarial.py` (won hand with a bad decision, lost hand with a good one, close-EV alternatives, small samples, adjusting versus failing to adjust).
- Limits: coaching data starts at version 2 of the saved data; drills reuse the existing ones; no engine-backed generic drill.

## Version 44
Decisions made before the solver finishes are graded when it lands (the chip shows "..." until then) and are not counted anywhere before that. Decisions marked with Deviate are shown against the solver but kept out of accuracy, leaks, coaching stats, and redo, and logged on the Coach tab. The Rules card adds the minimum-defense row (how much of your range has to continue against each bet size).

## Version 46: the hand routine
- **Routine button** beside Deviate on every decision. It opens a flowchart for the spot (folded to you, limpers, one raise, a re-raise, your free option, after the flop facing a bet, after the flop checked to you) with this decision's path lit and its numbers on each box: hand score and seat number, the limper rule's target, equity against the opener's range and the playability-adjusted price, board texture, hand tier and pot budget, price, SPR, equity, and whether a normal bet or raise fits the budget.
- The routine restates the baseline's own rules as fixed steps. It never changes advice or grades. Where its short form and the baseline differ (the score rule versus the chart on about 10% of opens, or a live-table adjustment), the sheet says so and gives the baseline's reason. In 70 seeded hands it matches the baseline on at least 90% of decisions (tested).
- **Routine drill** (Settings > Table feel, off by default): before the buttons show, one or two questions from the routine. Facing a bet after the flop: the equity the price needs, then your equity band against their range. Limped pots: the score the limper rule needs. Facing a raise or re-raise: your equity band against their range. Skip is always there. Answers are kept on the Coach tab (exact, and one band off for equity) and never touch the grade.
- **Coach tab:** a "Your hand routine" card with the order of steps, a math table (price, bluff break-even, minimum defense, outs x 2 and x 4, SPR bands, pot budget), and all seven charts.
- Hidden in live mode when helpers are off. Tests: `tests/test_routine.py` (8).
