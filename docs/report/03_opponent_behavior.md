# 03. Opponent behavior

Full report: `../stage-03-report.md`; generated reference tables: `../opponent-model.md`.

- 12 archetypes (3 new: recreational wildcard, thinking player, short-stack recreational) and 27 documented traits per individual, drawn from four latent factors, with contradictions repaired.
- Barrels, check-raises, one-pair over-valuation, a call cap, and noisy bet sizes.
- Limited observation: each opponent keeps its own noisy beliefs about the hero and adapts gradually, more if skilled. **Observed-only mode** (default) shows a type estimated from hero-visible stats, never the hidden type.
- **Smooth decisions (stage 06 fix).** The post-flop decision used a hard threshold, so for a fixed hand every type called about 100% up to a bet size and about 0% just beyond it (jumps of up to 75 points between neighbouring sizes). It now uses logistic noise: the largest jump is 30 points and the curves are monotonic. How each type plays changed by 5 points or less.
- Reader accuracy (hero-visible stats): exact type 47% / 58% / 64% after about 60 / 150 / 300 hands; true type in the top three 88% to 93%.
- Limits: the pre-flop raise rate of the regular types is low; simulated players fold to 3-bets more than most real players do.
