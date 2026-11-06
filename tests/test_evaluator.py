"""Hand evaluator vs the independent `treys` library.

Pass criterion: treys and the app must group hands into exactly the same strength classes in exactly the same
order (same class <-> same app score, and a strictly better treys class always has a strictly higher app score).
"""
import os, random, itertools, subprocess, tempfile
import numpy as np
from harness import ROOT, TESTS, INDEX

RK = '23456789TJQKA'; ST = 'shdc'
_NODE = os.path.join(tempfile.gettempdir(), 'holdem_eval_node.js')

def _build_node_script():
    h = open(INDEX, encoding='utf-8').read()
    i = h.index('function strHigh('); j = h.index('\n', h.index('function catOf('))
    src = 'var P13=371293;\n' + h[i:j] + '''
const fs=require('fs');const buf=fs.readFileSync(process.argv[2]);const k=+process.argv[3];const n=buf.length/k;const out=new Int32Array(n);
for(let i=0;i<n;i++){const cs=[];for(let j=0;j<k;j++)cs.push(buf[i*k+j]);out[i]=evaluate(cs);}
fs.writeFileSync(process.argv[4],Buffer.from(out.buffer));
'''
    open(_NODE, 'w').write(src)

def _compare(hands, k):
    from treys import Card, Evaluator
    ev = Evaluator(); tc = [Card.new(RK[c >> 2] + ST[c & 3]) for c in range(52)]
    d = tempfile.gettempdir(); fin = os.path.join(d, 'hev_in.bin'); fout = os.path.join(d, 'hev_out.bin')
    np.array(hands, dtype=np.uint8).tofile(fin)
    _build_node_script()
    subprocess.check_call(['node', _NODE, fin, str(k), fout])
    js = np.fromfile(fout, dtype=np.int32)
    ref = np.array([ev.evaluate([], [tc[c] for c in h]) if k == 5 else ev.evaluate([tc[c] for c in h[:2]], [tc[c] for c in h[2:]]) for h in hands])
    order = np.lexsort((js, ref)); refs = ref[order]; jss = js[order]
    uref, idx = np.unique(refs, return_index=True)
    groups = np.split(jss, idx[1:])
    split = sum(1 for g in groups if g.min() != g.max())
    reps = np.array([g[0] for g in groups])
    order_bad = int(np.sum(reps[1:] >= reps[:-1]))
    return len(uref), split, order_bad

def test_exhaustive_five_card_hands():
    hands = [list(c) for c in itertools.combinations(range(52), 5)]
    assert len(hands) == 2598960
    classes, split, bad = _compare(hands, 5)
    assert classes == 7462, classes          # the known number of distinct five-card hand strengths
    assert split == 0 and bad == 0, (split, bad)

def test_random_seven_card_hands():
    rnd = random.Random(20251106)
    hands = [rnd.sample(range(52), 7) for _ in range(300000)]
    classes, split, bad = _compare(hands, 7)
    assert split == 0 and bad == 0, (split, bad)

def test_targeted_seven_card_edge_cases():
    rnd = random.Random(7)
    out = []
    while len(out) < 60000:
        kind = rnd.choice(['trips2', 'threepair', 'wheel', 'quadtrip', 'sf', 'pairboard', 'flush'])
        if kind == 'trips2':
            a, b = rnd.sample(range(13), 2)
            cs = [a * 4 + s for s in rnd.sample(range(4), 3)] + [b * 4 + s for s in rnd.sample(range(4), 3)] + [rnd.choice([c for c in range(52) if c >> 2 not in (a, b)])]
        elif kind == 'threepair':
            r = rnd.sample(range(13), 3)
            cs = [x * 4 + s for x in r for s in rnd.sample(range(4), 2)] + [rnd.choice([c for c in range(52) if c >> 2 not in r])]
        elif kind == 'wheel':
            cs = [r * 4 + rnd.randrange(4) for r in (12, 0, 1, 2, 3)]; cs += rnd.sample([c for c in range(52) if c not in cs], 2)
        elif kind == 'quadtrip':
            a, b = rnd.sample(range(13), 2); cs = [a * 4 + s for s in range(4)] + [b * 4 + s for s in rnd.sample(range(4), 3)]
        elif kind == 'sf':
            s = rnd.randrange(4); lo = rnd.randrange(-1, 9)
            rs = [(lo + i) % 13 if lo >= 0 else (12 if i == 0 else i - 1) for i in range(5)]
            cs = [r * 4 + s for r in rs]; cs += rnd.sample([c for c in range(52) if c not in cs], 2)
        elif kind == 'pairboard':
            r = rnd.randrange(13); cs = [r * 4 + s for s in rnd.sample(range(4), 2)] + rnd.sample([c for c in range(52) if c >> 2 != r], 5)
        else:
            s = rnd.randrange(4); fl = rnd.sample([r * 4 + s for r in range(13)], 5); cs = fl + rnd.sample([c for c in range(52) if c not in fl], 2)
        if len(set(cs)) == 7: out.append(cs)
    classes, split, bad = _compare(out, 7)
    assert split == 0 and bad == 0, (split, bad)
