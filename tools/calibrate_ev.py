"""Benchmark the EV recommendation against rollouts of the real engine.

For each spot the real bots play, the hero is stopped at a post-flop decision. Every option the EV engine lists is then
played out M times (the same shuffled decks for every option) with the hero continuing as a standard regular, and the mean
result in big blinds is recorded next to the model's EV. Run in chunks, because very long single calls can exhaust the
browser's memory.

  python3 tools/calibrate_ev.py SPOTS ROLLOUTS "seat,types" out.json [chunk]       custom table, e.g. "shark,station,limper,whale,tag"
  python3 tools/calibrate_ev.py SPOTS ROLLOUTS "" out.json 10 casino12            built-in casino table
  (optional 7th argument: revealed (default) or observed, the opponent-info mode the model runs in)
Then:  python3 tools/score_calibration.py out.json [more.json ...]
"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'tests'))
from harness import engine

if __name__ == '__main__':
    total, M, spec, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3], sys.argv[4]
    chunk = int(sys.argv[5]) if len(sys.argv) > 5 else 16
    stake = sys.argv[6] if len(sys.argv) > 6 else 'x'
    mode = sys.argv[7] if len(sys.argv) > 7 else 'revealed'      # revealed: the model knows each opponent; observed: it only has what a hero could see
    code = open(os.path.join(HERE, 'calibrate_ev.js'), encoding='utf-8').read().strip().rstrip(';')
    spots = []; crashes = 0; e = engine(); e.js('S.settings.oppInfo="%s";1' % mode); t0 = time.time()
    while len(spots) < total and crashes < 6:
        try:
            r = json.loads(e.js('(%s)(%d,%d,"%s","%s")' % (code, chunk, M, stake, spec)))
            spots += r['spots']; print('%d/%d spots %.0fs' % (len(spots), total, time.time() - t0), flush=True)
        except Exception as ex:
            crashes += 1; print('crash %d: %s' % (crashes, str(ex)[:60])); e = engine(fresh=True); e.js('S.settings.oppInfo="%s";1' % mode)
    json.dump({'spots': spots}, open(out, 'w')); print('wrote', out, len(spots), 'spots')
