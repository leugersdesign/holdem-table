# 06. Product experience, live sessions, performance, reliability

## What changed

- **Sessions:** $1/$2 and $1/$3, seats 2 to 9, stack depth, rake presets (settings, not casino facts), opponent mix with individual variation (stage 03). Hands are not made artificially interesting: the usual limped, raised, and multiway pots occur at their natural rates.
- **Observations:** the app records what a player could see at a table (hands seen, voluntary participation, raise rate, aggression, folds to bets, showdowns). In Observed-only mode, the default, hidden opponent types stay hidden everywhere (sheet, list, analysis, charts, advice text). A manual notebook is not built.
- **Session review:** the summary now shows the result and the model's estimated EV given up side by side, with an explicit note that luck over a few hundred hands outweighs the difference, and that these are simulated estimates. Leak counts and drills come from the Coach tab (stage 05).
- **Review of decisions:** each graded decision keeps its estimated EV for every option, the typical-player best play, the confidence label and its reason, and the hand result (stored separately). Replaying a hand under a different opponent assumption is not built; the pre-flop and post-flop analysis sheets show the what-if view live during play.
- **Interface:** the new screens (pre-flop analysis, Coach tab, rake presets, reading drill) were checked on a 390 px wide phone viewport with no sideways overflow.

## Reliability fixes

| Defect | Evidence | Fix |
| --- | --- | --- |
| A refresh in the middle of a hand lost every chip in the pot (and the draw game has the same code pattern) | 13 of 1,200 chips gone after a reload | The saved state uses the hand-start stacks; a refresh voids the hand. Verified 0 lost in hold'em and draw |
| `act()` accepted illegal actions (check into a bet, raise below the minimum, act after folding) | The known failing test | Rejected without changing anything; bots get the nearest legal action and the count is kept |
| The same bot decision was sometimes scheduled twice in one hand, and the stale-action guard compared a token that is the same for every hand | 2 duplicate actions in 500 hands (9-max, 10% rake) | Per-hand serial number, and an action is dropped if play has moved on since it was scheduled |
| Ranges could be emptied by a rare action sequence (NaN EV) | Pre-flop limp-reraise from a maniac | Relative weight thresholds |
| A function name collided with the live coach box | Empty coach tab in a test | Renamed before release |

## Performance (python3 tools/benchmark.py; headless Chromium; medians; CPU throttle 4x is a stand-in for a mid-range phone, not a measurement of one)

| | normal CPU | CPU throttled 4x |
| --- | --- | --- |
| 7-card hand evaluations per second | 4.2 million | 0.9 million |
| EV analysis, flop heads-up / three-way / river | 28 / 83 / 3 ms | 125 / 397 / 11 ms |
| Grading a decision when you tap, before the change: flop heads-up / three-way / river / pre-flop | 74 / 125 / 6 / 14 ms | 283 / 578 / 31 / 61 ms |
| Grading a decision when you tap, **after** precomputing during your thinking time | 7 / 2.5 / 1.5 / 1.1 ms | 19 / 12 / 7 / 5 ms |
| Opening the analysis sheet (adds three what-if runs), pre-flop / flop | 29 / 129 ms | 137 / 644 ms |
| 3,000-hand session | 6.0 s, 0 errors, 0 chip drift, 0 duplicate cards | 28.2 s, same |
| Heap after a forced collection | 3.97 MB to 4.40 MB | 3.97 MB to 4.40 MB |
| Saved state | 47 KB | 47 KB |

Profiling showed one hot spot: grading ran two EV analyses synchronously at the moment of the tap. A Web Worker was not needed: the same work now runs when the hero's turn begins, and the tap finds it cached (a precompute for a hand that has moved on does nothing). Opening the analysis sheet on a three-way flop at 4x still takes about 0.6 s, on demand only.

## Known limitations

- The precompute occupies the main thread for up to about 0.6 s at 4x throttle right after the controls appear on a three-way flop; a tap in that window waits for it.
- Mobile behavior was emulated (viewport and CPU throttle), not tested on a physical phone.
- Not built: replay under a different assumption, a manual observation notebook.
- The existing draw-game browser script is intermittent in both v39 and this build (it assumes the raise slider is on screen); the cause is in the script, not the game.
