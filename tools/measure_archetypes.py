"""Measure each archetype's observable stats (what a hero could see in a heads-up display) by playing seeded hands with
freshly generated individuals. Output is the ARCH_STATS table used by the Observed-only opponent reader.

  python3 tools/measure_archetypes.py TABLES HANDS out.json     (e.g. 16 250)
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'tests'))
from harness import engine
TYPES = ['station', 'limper', 'whale', 'maniac', 'nit', 'weekend', 'tag', 'lag', 'shark', 'wild', 'thinker', 'shorty']
if __name__ == '__main__':
    tables, hands, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    code = open(os.path.join(HERE, 'measure_archetypes.js'), encoding='utf-8').read().strip().rstrip(';')
    rows = []
    for shift in (0, 4, 8):                      # three seatings so every type is measured in several mixes
        spec = [TYPES[(shift + k) % len(TYPES)] for k in range(8)]
        for chunk in range(0, tables, 2):        # small calls, a fresh page every few: very long single calls can crash the browser
            if chunk % 6 == 0: e = engine(fresh=True)
            r = e.js('(%s)(%d,%d,%d,%s)' % (code, 9000 + shift * 100 + chunk * 7, min(2, tables - chunk), hands, json.dumps(spec))); rows += r['rows']
        print('seating', shift, len(rows), 'players so far', flush=True)
    json.dump(rows, open(out, 'w')); print('wrote', out, len(rows))
