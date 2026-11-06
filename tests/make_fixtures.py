"""Generate the reference fixtures the equity tests compare against.

Everything here is computed by EXHAUSTIVE enumeration with the independent `treys` evaluator, so the app's
Monte Carlo and importance-sampling code is checked against answers it shares no code with.
Card ids follow the app: id = rank*4 + suit, rank 0..12 = 2..A, suit 0..3.

Run:  python3 tests/make_fixtures.py        (about 10 minutes on one core; the output is committed)
"""
import itertools, json, os, sys, time, random
from multiprocessing import Pool
from treys import Card, Evaluator
RK = '23456789TJQKA'; ST = 'shdc'
ev = Evaluator()
TC = [Card.new(RK[c >> 2] + ST[c & 3]) for c in range(52)]
def cid(s): return RK.index(s[0]) * 4 + ST.index(s[1])
def rank7(cards): return ev.evaluate([TC[c] for c in cards[:2]], [TC[c] for c in cards[2:]])  # lower = better

def outcome(hands, board):
    r = [rank7(h + board) for h in hands]
    best = min(r)
    win = [1.0 / r.count(best) if x == best else 0.0 for x in r]
    return win

def exact_equity(hands, board):
    """Hero (hands[0]) equity against fixed opponent hands, enumerating every runout."""
    used = set(c for h in hands for c in h) | set(board)
    rest = [c for c in range(52) if c not in used]
    need = 5 - len(board)
    tot = 0.0; n = 0
    for run in itertools.combinations(rest, need):
        tot += outcome(hands, board + list(run))[0]; n += 1
    return tot / n, n

def job(args):
    hands, board, first = args
    used = set(c for h in hands for c in h) | set(board)
    rest = [c for c in range(52) if c not in used]
    need = 5 - len(board)
    tot = 0.0; n = 0
    for run in itertools.combinations([c for c in rest if c != first] if False else rest, need):
        if run[0] != first: continue          # split the enumeration by the first runout card
        tot += outcome(hands, board + list(run))[0]; n += 1
    return tot, n

def exact_parallel(pool, hands, board):
    used = set(c for h in hands for c in h) | set(board)
    rest = [c for c in range(52) if c not in used]
    if 5 - len(board) < 3: return exact_equity(hands, board)
    parts = pool.map(job, [(hands, board, f) for f in rest])
    return sum(p[0] for p in parts) / sum(p[1] for p in parts), sum(p[1] for p in parts)

def hand(s): return [cid(s[0:2]), cid(s[2:4])]
def cards(s): return [cid(s[i:i + 2]) for i in range(0, len(s), 2)] if s else []

def river_multiway(hero, board, ranges):
    """Exact hero equity vs several weighted ranges on a complete board.
    ranges = list of [(combo, weight)]. Opponents must hold disjoint cards; the joint weight is the product of the
    weights. Hero's share of the pot is 1 if best, 1/(1+n) if tied with n opponents, else 0."""
    dead = set(hero) | set(board)
    hv = rank7(hero + board)
    rv = [[(cb, w, rank7(list(cb) + board)) for cb, w in r if not (set(cb) & dead)] for r in ranges]
    acc = [0.0, 0.0]
    def go(i, used, wt, best_rank, n_best):
        if i == len(rv):
            acc[0] += wt
            acc[1] += wt * (1.0 if hv < best_rank else (1.0 / (1 + n_best) if hv == best_rank else 0.0))
            return
        for cb, w, r in rv[i]:
            if cb[0] in used or cb[1] in used: continue
            if r < best_rank: nb, nn = r, 1
            elif r == best_rank: nb, nn = best_rank, n_best + 1
            else: nb, nn = best_rank, n_best
            go(i + 1, used | {cb[0], cb[1]}, wt * w, nb, nn)
    go(0, frozenset(), 1.0, 10 ** 9, 0)
    return acc[1] / acc[0]

def combos_of(code):
    hi = 'AKQJT98765432'
    r1, r2 = 12 - hi.index(code[0]), 12 - hi.index(code[1])
    out = []
    if r1 == r2:
        for s1, s2 in itertools.combinations(range(4), 2): out.append((r1 * 4 + s1, r1 * 4 + s2))
    elif code[2] == 's':
        for s in range(4): out.append((r1 * 4 + s, r2 * 4 + s))
    else:
        for s1 in range(4):
            for s2 in range(4):
                if s1 != s2: out.append((r1 * 4 + s1, r2 * 4 + s2))
    return out
def rng(codes, wts): return [(cb, w) for c, w in zip(codes, wts) for cb in combos_of(c)]

if __name__ == '__main__':
    t0 = time.time(); fx = {'about': 'Exact equities from exhaustive enumeration with treys. hero is the first hand.', 'spots': []}
    with Pool() as pool:
        pre = [('AsAh', 'KdKc'), ('AsKs', 'QdQc'), ('AsKd', 'QhQc'), ('JsTs', '2d2c'), ('7d2c', 'AsAh'), ('TsTh', 'AdQc'),
               ('5s5h', 'AdKc'), ('8s8h', '7d6d')]
        for a, b in pre:
            eq, n = exact_parallel(pool, [hand(a), hand(b)], [])
            fx['spots'].append({'name': f'preflop {a} vs {b}', 'hero': hand(a), 'opps': [hand(b)], 'board': [], 'eq': eq, 'boards': n}); print(fx['spots'][-1]['name'], round(eq * 100, 3), n, f'{time.time()-t0:.0f}s', flush=True)
        for a, b, c in [('AsAh', 'KdKc', 'QhQd'), ('AsKs', 'JdJc', '5h5d')]:
            eq, n = exact_parallel(pool, [hand(a), hand(b), hand(c)], [])
            fx['spots'].append({'name': f'preflop {a} vs {b} vs {c}', 'hero': hand(a), 'opps': [hand(b), hand(c)], 'board': [], 'eq': eq, 'boards': n}); print(fx['spots'][-1]['name'], round(eq * 100, 3), n, flush=True)
    post = [('AsKs', 'QdQc', '2d7hTs'), ('9h9d', 'AsKs', 'Qs7s2c'), ('JhTh', 'AdAc', '9h8d2c'), ('KcQc', 'AhAd', 'Jc2c9d'), ('7s7d', 'AcKd', '7c5h2d'),
            ('AdQd', 'KsKh', 'KdJd3s'), ('6h5h', 'AsAd', '4h3c2d'), ('QsJs', '9h9d', 'Td8c2s'),
            ('AsKs', 'QdQc', '2d7hTs3c'), ('9h9d', 'AsKs', 'Qs7s2c4d'), ('JhTh', 'AdAc', '9h8d2cQs'), ('KcQc', 'AhAd', 'Jc2c9dTs'),
            ('AdQd', 'KsKh', 'KdJd3s4h'), ('QsJs', '9h9d', 'Td8c2s7h')]
    for a, b, bd in post:
        eq, n = exact_equity([hand(a), hand(b)], cards(bd))
        fx['spots'].append({'name': f'{ {3:"flop",4:"turn"}[len(bd)//2] } {a} vs {b} on {bd}', 'hero': hand(a), 'opps': [hand(b)], 'board': cards(bd), 'eq': eq, 'boards': n})
    for a, b, c, bd in [('Ac5d', 'AsKs', 'QhQc', '2d7hTs'), ('KsKh', 'AdAc', 'JcTc', '9c8c2d')]:
        eq, n = exact_equity([hand(a), hand(b), hand(c)], cards(bd))
        fx['spots'].append({'name': f'flop 3-way {a} vs {b} vs {c} on {bd}', 'hero': hand(a), 'opps': [hand(b), hand(c)], 'board': cards(bd), 'eq': eq, 'boards': n})
    mw = []
    B = cards('2c7d9h4s3c')
    for name, hero, rs in [
        ('2 opps {AA,KK,JJ,TT}, hero QQ', 'QhQd', [(['AA', 'KK', 'JJ', 'TT'], [1, 1, 1, 1])] * 2),
        ('2 opps skewed AA:8 KK:4 QQ:2 JJ:1 TT:1, hero JJ', 'JhJd', [(['AA', 'KK', 'QQ', 'JJ', 'TT'], [8, 4, 2, 1, 1])] * 2),
        ('3 opps tight mix, hero TT', 'ThTd', [(['AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', 'AKs', 'AKo', 'AQs'], [3, 3, 3, 2, 2, 1, 1, 2, 2, 1])] * 3),
        ('3 opps pairs 55+, hero 88', '8h8d', [(['AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55'], [1] * 10)] * 3),
        ('2 opps different ranges, hero AKo', 'AhKd', [(['AA', 'KK', 'QQ', 'AKs', 'AQs', 'JJ', 'TT'], [2, 2, 2, 1, 1, 1, 1]), (['QQ', 'JJ', 'TT', '99', '88', '77', '66', 'AQo', 'KQs'], [1, 1, 2, 2, 2, 2, 2, 1, 1])])]:
        h = hand(hero)
        mw.append({'name': name, 'hero': h, 'board': B, 'ranges': [[[list(cb), w] for cb, w in rng(c, w)] for c, w in rs],
                   'eq': river_multiway(h, B, [rng(c, w) for c, w in rs])}); print(name, round(mw[-1]['eq'] * 100, 3), flush=True)
    fx['multiway_river'] = mw
    # equity vs random opponents: high-sample Monte Carlo in an independent code path (seeded)
    random.seed(1234); rr = []
    for hero, nopp in [('AsAh', 1), ('KsKh', 1), ('AsKs', 1), ('7d2c', 1), ('JsTs', 1), ('AsAh', 3), ('7d2c', 3), ('QsQh', 2)]:
        h = hand(hero); N = 250000; w = 0.0; w2 = 0.0
        for _ in range(N):
            deck = [c for c in range(52) if c not in h]; random.shuffle(deck)
            opp = [[deck[2 * k], deck[2 * k + 1]] for k in range(nopp)]; bd = deck[2 * nopp:2 * nopp + 5]
            x = outcome([h] + opp, bd)[0]; w += x; w2 += x * x
        m = w / N; rr.append({'hero': h, 'name': hero, 'nopp': nopp, 'eq': m, 'se': ((w2 / N - m * m) / N) ** 0.5, 'n': N}); print(hero, nopp, round(m * 100, 2), flush=True)
    fx['vs_random'] = rr
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures', 'reference_equities.json')
    json.dump(fx, open(out, 'w')); print('wrote', out, f'{time.time()-t0:.0f}s')
