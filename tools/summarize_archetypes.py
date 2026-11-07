"""Summarize tools/measure_archetypes.py output into the ARCH_STATS table and embed it in index.html.

  python3 tools/summarize_archetypes.py rows.json [--embed]
Prints each type's observable stats (and the spread between individuals), and with --embed rewrites `var ARCH_STATS=` in index.html.
"""
import json, os, re, statistics as st, sys
HERE = os.path.dirname(os.path.abspath(__file__))
TYPES = ['station', 'limper', 'whale', 'maniac', 'nit', 'weekend', 'tag', 'lag', 'shark', 'wild', 'thinker', 'shorty']
rows = json.load(open(sys.argv[1])); out = {}
def rate(rs, a, b):
    n = sum(r[b] for r in rs); return sum(r[a] for r in rs) / n if n else 0.5
print('%-8s %3s | VPIP (sd)  | PFR (sd)   | bet share (sd) | fold to bet (sd)' % ('type', 'n'))
for t in TYPES:
    rs = [r for r in rows if r['k'] == t]
    if not rs: continue
    sd = lambda a, b: st.pstdev([r[a] / r[b] for r in rs if r[b] >= 8] or [0])
    sda = st.pstdev([r['agg'] / (r['agg'] + r['call']) for r in rs if r['agg'] + r['call'] >= 8] or [0])
    vp, pr = rate(rs, 'vp', 'h'), rate(rs, 'pr', 'h')
    agg = sum(r['agg'] for r in rs) / max(1, sum(r['agg'] + r['call'] for r in rs)); cb = rate(rs, 'cb', 'cbO'); fb = rate(rs, 'fb', 'fbO')
    print('%-8s %3d | %.2f (%.2f) | %.2f (%.2f) | %.2f (%.2f)    | %.2f (%.2f)' % (t, len(rs), vp, sd('vp', 'h'), pr, sd('pr', 'h'), agg, sda, fb, sd('fb', 'fbO')))
    out[t] = [round(vp, 3), round(pr, 3), round(agg, 3), round(cb, 3), round(fb, 3)]
if '--embed' in sys.argv:
    p = os.path.join(HERE, '..', 'index.html'); s = open(p, encoding='utf-8').read()
    m = re.search(r'var ARCH_STATS=\{[^;]*\};', s); assert m
    s = s[:m.start()] + 'var ARCH_STATS=' + json.dumps(out, separators=(',', ':')) + ';' + s[m.end():]
    open(p, 'w', encoding='utf-8').write(s); print('embedded ARCH_STATS into index.html')
