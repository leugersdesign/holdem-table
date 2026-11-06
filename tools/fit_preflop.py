"""Fit the pre-flop opponent model (PFM) from recorded bot decisions.

Input: JSON files of records [type, situation, positionGroup, handCode, action(f|c|r), inChart, live]
produced by tools/record_preflop.py (the real bots playing seeded hands). Output: the PFM object embedded in index.html.

Model: for each (live?, type, situation, position group) cell, two logistic regressions on
  [1, (equity-50)/10, in opening chart, pocket pair, suited]
  P(play) and P(raise | play). Sparse cells are shrunk toward the type's pooled fit:
  theta = (n * theta_cell + K * theta_pooled) / (n + K), with K chosen to minimise held-out log-loss.
"""
import json, math, re, sys, random
import numpy as np

def feats(EQ, code, ch):
    return [1.0, (EQ[code] - 50) / 10.0, float(ch), 1.0 if len(code) == 2 else 0.0, 1.0 if code.endswith('s') else 0.0]

def ridge_logit(F, Y, lam=0.3):
    A = np.array(F, float); y = np.array(Y, float)
    if len(y) < 40 or y.min() == y.max():
        s = y.sum(); return [math.log((s + .5) / (len(y) - s + .5))] + [0.0] * (A.shape[1] - 1)
    a = np.zeros(A.shape[1])
    for _ in range(80):
        p = 1 / (1 + np.exp(-(A @ a))); g = A.T @ (y - p) - lam * a
        H = -(A.T * (p * (1 - p))) @ A - lam * np.eye(A.shape[1]); a = a - np.linalg.solve(H, g)
    return [float(x) for x in a]

def fit(records, EQ, K):
    cells = {}
    for k, sit, pg, code, a, ch, lv in records:
        for key in ((lv, k, sit, pg), (lv, k, sit, '*')):
            cells.setdefault(key, []).append((feats(EQ, code, ch), a))
    raw = {}
    for key, v in cells.items():
        play = [0 if a == 'f' else 1 for _, a in v]; F = [f for f, _ in v]
        pv = [(f, 1 if a == 'r' else 0) for f, a in v if a != 'f']
        raw[key] = (ridge_logit(F, play), ridge_logit([f for f, _ in pv], [y for _, y in pv]) if len(pv) >= 40 else None, len(v), len(pv))
    out = {}
    for (lv, k, sit, pg), (tp, tr, n, nr) in raw.items():
        if pg != '*' and K > 0:
            pp, pr, _, _ = raw[(lv, k, sit, '*')]
            w = n / (n + K); tp = [w * a + (1 - w) * b for a, b in zip(tp, pp)]
            if pr is not None:
                wr = nr / (nr + K); base = tr if tr is not None else pr
                tr = [wr * a + (1 - wr) * b for a, b in zip(base, pr)]
        if tr is None:
            tr = raw[(lv, k, sit, '*')][1] or [-2.0, 0, 0, 0, 0]
        out.setdefault(str(lv), {}).setdefault(k, {}).setdefault(sit, {})[pg] = [[round(x, 3) for x in tp], [round(x, 3) for x in tr]]
    return out

def logloss(model, records, EQ):
    tot = 0.0; n = 0
    for k, sit, pg, code, a, ch, lv in records:
        cell = model.get(str(lv), {}).get(k, {}).get(sit, {})
        c = cell.get(pg) or cell.get('*')
        if not c: continue
        x = feats(EQ, code, ch)
        pp = 1 / (1 + math.exp(-sum(w * v for w, v in zip(c[0], x)))); pr = 1 / (1 + math.exp(-sum(w * v for w, v in zip(c[1], x))))
        p = (1 - pp) if a == 'f' else pp * (pr if a == 'r' else 1 - pr)
        tot += -math.log(max(p, 1e-6)); n += 1
    return tot / n

if __name__ == '__main__':
    html = open(sys.argv[1], encoding='utf-8').read()
    EQ = json.loads(re.search(r'var EQ=(\{[^}]*\})', html).group(1))
    recs = []
    for f in sys.argv[3:]: recs += json.load(open(f))
    random.seed(1); idx = list(range(len(recs))); random.shuffle(idx)
    cut = int(len(recs) * 0.8); train = [recs[i] for i in idx[:cut]]; test = [recs[i] for i in idx[cut:]]
    print('records', len(recs), 'train', len(train), 'held-out', len(test))
    best = None
    for K in (0, 25, 75, 150, 300, 600):
        ll = logloss(fit(train, EQ, K), test, EQ); print('K=%-4d held-out log-loss %.4f' % (K, ll))
        if best is None or ll < best[1]: best = (K, ll)
    print('chosen K =', best[0])
    json.dump(fit(recs, EQ, best[0]), open(sys.argv[2], 'w'), separators=(',', ':'))
