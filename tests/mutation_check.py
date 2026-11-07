"""Mutation check: break the engine on purpose and confirm the suite notices. Each mutation must make at least one test fail.
Usage: python3 tests/mutation_check.py"""
import os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SRC = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
MUTS = [
 ('sampler ignores the importance weight (biased joint)', 'W*=A;used[r.c1[pick]]', 'used[r.c1[pick]]', 'test_equity'),
 ('call EV adds the call instead of paying it', 'return eq*rakeNet(pot+call,flop)*rho-call;}', 'return eq*rakeNet(pot+call,flop)*rho+call;}', 'test_ev'),
 ('flush ranked below a straight in the evaluator', 'return score(5,topBits(sm[i],5,[]));', 'return score(3,topBits(sm[i],5,[]));', 'test_evaluator'),
 ('rake not removed from the pot', 'var cut=Math.min(rkLeft,amt);amt-=cut;rkLeft-=cut;', 'var cut=0;', 'test_engine'),
 ('three-way tie scored as a half share', 'me===best?1/(1+tied):0', 'me===best?0.5:0', 'test_equity'),
 ('oversized bets can be recommended', 'var cand=opts.filter(function(o){return !o.extrap;});if(!cand.length)cand=opts;', 'var cand=opts;', 'test_ev'),
 ('a bot peeks at the hero hole cards', 'var d=liveDecide(P,hcInfo(s.cards,H.board),c,RNG),S=d[2];', 'var d=liveDecide(P,hcInfo(s.cards,H.board),Object.assign(c,{memAdj:(H.s[0].cards[0]>>2)*0.05-0.3}),RNG),S=d[2];', 'test_opponents'),
 ('no call cap: everything folds to a shove', 'need=Math.min(need,P.cap||99);', '', 'test_opponents'),
 ('adaptation without evidence', 'function beliefWt(p,k){var t=beliefTrials(p,k);return t/(t+20);}', 'function beliefWt(p,k){return 1;}', 'test_opponents'),
 ('observed mode secretly uses the true type', 'function modelKeyP(p){if(FORCE_KEY&&p&&!p.hero&&!p.human)return FORCE_KEY;if(!p||oppMode()==="revealed"||p.hero||p.human)return liveKey(p);', 'function modelKeyP(p){return liveKey(p);', 'test_opponents'),
 ('attention ignored', 'var a=trOf(p).attn,foldIdx=', 'var a=1,foldIdx=', 'test_opponents'),
 ('grading tolerance removed', 'tol=Math.max(0.15,1.5*se),sev=raw<tol?0:raw<1?1:raw<3?2:3,X=stratExtras(A,true)', 'tol=0,sev=raw<0.001?0:raw<1?1:raw<3?2:3,X=stratExtras(A,true)', 'test_coaching'),
 ('leaks named without a sample-size check', 'flag:C.N>=30&&e.n>=6&&100*ci.lo>=3', 'flag:true', 'test_coaching'),
 ('raise-size assumption removed', 'var SIZE_TILT=0.7,SIZE_GAMMA=1.2;', 'var SIZE_TILT=0,SIZE_GAMMA=0;', 'test_strategy'),
 ('rake ignored in the pre-flop call', 'cev=cq.eq*rakeNet(potCall,true)*rC-callAmt', 'cev=cq.eq*potCall*rC-callAmt', 'test_strategy'),
 ('overbets offered for any hand', '(st===3&&eqAll>=0.8?', '(st>=2?', 'test_strategy'),
 ('posterior ignores bet size', 'n+=sized?sizeProbs(P,d[2],d[1])[bk]:1;', 'n+=1;', 'test_ranges'),
]
bad = 0
for name, old, new, mod in MUTS:
    if SRC.count(old) != 1: print('SKIP (pattern not found once):', name); bad += 1; continue
    p = os.path.join(tempfile.gettempdir(), 'mut_index.html'); open(p, 'w', encoding='utf-8').write(SRC.replace(old, new))
    r = subprocess.run([sys.executable, os.path.join(HERE, 'run_all.py'), mod], env=dict(os.environ, HOLDEM_INDEX=p), capture_output=True, text=True)
    caught = r.returncode != 0
    fails = [l.split()[1] for l in r.stdout.splitlines() if l.startswith('FAIL')]
    print('%-55s %s %s' % (name, 'CAUGHT' if caught else 'MISSED', ', '.join(f.split('.')[1] for f in fails)[:90]))
    if not caught: bad += 1
sys.exit(1 if bad else 0)
