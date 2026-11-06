"""Add 'multiway_blockers' to reference_equities.json: multiway river spots chosen because opponents' ranges overlap
heavily, so sampling that ignores card removal between opponents is badly biased. For each candidate we compute, by
exhaustive enumeration with treys, (a) the exact equity and (b) the equity a naive sequential sampler converges to
(each opponent drawn from his own range restricted to free cards, with no correction). We keep the spots where they
differ most, so a sampler that loses the correction fails the test.   Run: python3 tests/make_blocker_fixtures.py"""
import json, os, random, itertools
import make_fixtures as m
random.seed(99)
pool = [r * 4 + s for r in (12, 11, 10) for s in range(4)]           # A K Q in every suit
allc = list(itertools.combinations(pool, 2))
board = m.cards('2c7d9h4s3c'); hero = m.hand('JhJd')
def rank(c): return m.rank7(list(c) + board)
hv = m.rank7(hero + board)
def analyse(ranges):
    rv = [[(cb, w, rank(cb)) for cb, w in r] for r in ranges]
    exact = [0.0, 0.0]; naive = [0.0, 0.0]
    def go(i, used, wt, qwt, best, nb):
        if i == len(rv):
            share = 1.0 if hv < best else (1.0 / (1 + nb) if hv == best else 0.0)
            exact[0] += wt; exact[1] += wt * share; naive[0] += qwt; naive[1] += qwt * share; return
        avail = [(cb, w, r) for cb, w, r in rv[i] if cb[0] not in used and cb[1] not in used]
        A = sum(w for _, w, _ in avail)
        for cb, w, r in avail:
            nb2, nn = (r, 1) if r < best else ((best, nb + 1) if r == best else (best, nb))
            go(i + 1, used | {cb[0], cb[1]}, wt * w, qwt * w / A, nb2, nn)
    go(0, frozenset(), 1.0, 1.0, 10 ** 9, 0)
    return exact[1] / exact[0], naive[1] / naive[0]
cands = []
for _ in range(400):
    k = random.choice([2, 3]); rs = []
    for _ in range(k):
        sub = random.sample(allc, random.randint(3, 6)); rs.append([(cb, float(random.randint(1, 4))) for cb in sub])
    ex, nv = analyse(rs)
    cands.append((abs(ex - nv), ex, nv, rs))
cands.sort(key=lambda x: -x[0])
fx = json.load(open(m.os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures', 'reference_equities.json')))
fx['multiway_blockers'] = [{'name': 'overlapping A/K/Q ranges, %d opps (naive sampler off by %.1f pts)' % (len(rs), d * 100), 'hero': hero, 'board': board,
                            'ranges': [[[list(cb), w] for cb, w in r] for r in rs], 'eq': ex, 'naive': nv} for d, ex, nv, rs in cands[:5]]
for b in fx['multiway_blockers']: print(b['name'], 'exact %.2f naive %.2f' % (b['eq'] * 100, b['naive'] * 100))
json.dump(fx, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures', 'reference_equities.json'), 'w'))
