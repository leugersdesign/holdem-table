"""Record pre-flop decisions from the real bots, as input for tools/fit_preflop.py.

  python3 tools/record_preflop.py HANDS STYLE SEATS out.json
  e.g.  python3 tools/record_preflop.py 2300 casino "station,limper,whale,maniac,nit,weekend,tag,lag" /tmp/q1.json

STYLE is casino, home or online. Each record is [type, situation, position group, hand code, action (f|c|r), in opening chart, live].
The hero seat is played by a bot too, so hands run unattended. Hand counts of about 2,300 per run, four runs, gave the 90,000
decisions the current model was fit on (see index.html, PFM).
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'tests'))
from harness import engine
if __name__ == '__main__':
    n, style, seats, out = int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
    code = open(os.path.join(HERE, 'preflop_recorder.js'), encoding='utf-8').read()
    r = json.loads(engine().js('(%s)(%d,"%s","%s")' % (code.strip().rstrip(';'), n, style, seats)))
    json.dump(r['rec'], open(out, 'w')); print(out, 'errors', r['errs'], 'decisions', len(r['rec']))
