"""Score calibration runs: regret (big blinds given up vs the best option, by realized rollout value) for the shipped
recommendation and for baselines, with paired bootstrap 95% intervals on the DIFFERENCES.

Absolute regret is inflated (taking the best of several noisy rollout means biases it upward), but the best option cancels
in a paired difference, so differences between policies are unaffected by that bias. Only the differences are reported as findings.
"""
import json, random, statistics as st, sys
random.seed(7)
spots = []
for f in sys.argv[1:]: spots += json.load(open(f))['spots']
spots = [s for s in spots if all(o['real'] is not None for o in s['opts']) and any(o.get('rec') for o in s['opts'])]
def pick(s, k):
    c = [o for o in s['opts'] if o['k'] == k] or [o for o in s['opts'] if o['k'] in ('check', 'fold')]
    return c[len(c) // 2] if len(c) > 1 else c[0]
ship = lambda s: next(o for o in s['opts'] if o.get('rec'))
adv = lambda s: pick(s, {'reraise': 'raise'}.get(s['adv'].lower(), s['adv'].lower()))
bot = lambda s: pick(s, s['bot'])
passive = lambda s: [o for o in s['opts'] if o['k'] in ('check', 'call')][0]
def gain(X, other):   # mean bb per decision the shipped recommendation gains over `other`, with paired bootstrap interval
    d = [ship(s)['real'] - other(s)['real'] for s in X]   # positive = the recommendation did better
    m = [st.mean(random.choices(d, k=len(d))) for _ in range(4000)]; m.sort()
    return st.mean(d), m[100], m[3899]
segs = [('all', lambda s: True), ('heads-up', lambda s: s['hu']), ('multiway', lambda s: not s['hu']),
        ('flop', lambda s: s['st'] == 1), ('turn', lambda s: s['st'] == 2), ('river', lambda s: s['st'] == 3)]
print('spots scored:', len(spots), '(%d heads-up, %d multiway)' % (sum(s['hu'] for s in spots), sum(not s['hu'] for s in spots)))
print('mean bb per decision the recommendation gains over each baseline, with 95% interval (positive = recommendation better)')
print('%-9s %5s | %-26s | %-26s | %-26s' % ('segment', 'n', 'vs previous advice', "vs the bots' own play", 'vs always check/call'))
for name, f in segs:
    X = [s for s in spots if f(s)]
    if len(X) < 8: continue
    def cell(o):
        m, lo, hi = gain(X, o); return '%+.2f [%+.2f, %+.2f]%s' % (m, lo, hi, '' if lo > 0 else ' (includes 0)')
    print('%-9s %5d | %-26s | %-26s | %-26s' % (name, len(X), cell(adv), cell(bot), cell(passive)))
over = sum(1 for s in spots if ship(s).get('extrap')); print('recommendations outside the modeled size range:', over)
