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
 ('illegal actions accepted', 'if(!actLegal(i,a,to))return false;   /* illegal actions change nothing */', '', 'test_reliability'),
 ('a refresh mid-hand loses the pot', 'if(sn&&sn.players&&sn.players.length===T.players.length)swaps.push([T.players,', 'if(false)swaps.push([T.players,', 'test_reliability'),
 ('stale bot action allowed to fire', 'H.sn!==tok||H.done||(H.hist||[]).length!==hl)return;', 'H.sn!==tok||H.done)return;', 'test_reliability'),
 ('players decide with a hard threshold again', 'S=hi.S+THRESH_S*Math.log(u/(1-u))', 'S=hi.S+(u*0.4-0.2)', 'test_opponents'),
 ('idle precompute does not warm the grade', 'if(A&&(A.pre||A.hu||MODEL_MW))stratExtras(A,true);', 'if(A&&(A.pre||A.hu||MODEL_MW)){}', 'test_reliability'),
 ('the EV model silently replaces the opening charts for pre-flop grading', 'S.settings.preModel===true){MA=preGet(true);', 'S.settings.preModel!==false){MA=preGet(true);', 'test_coaching'),
 ('limped pots ignore the rule', '      else if(limpersIn()>0){var LR=limpRule(code,pos,limpersIn());', '      else if(false){var LR=limpRule(code,pos,limpersIn());', 'test_rules'),
 ('course and drill keep their own limper logic', 'isoDecide=function(code,ip,n){if(ip==="BB")return', 'isoDecide=function(code,ip,n){return _isoDecideOld(code,ip,n);if(ip==="BB")return', 'test_rules'),
 ('post-flop graded against the read by default', 'if(S.settings.postGrade!=="read"){var X0=stratExtras(MA,true);', 'if(false){var X0=stratExtras(MA,true);', 'test_rules'),
 ('solver ignores card removal', 'for(var i=0;i<me.cards.length;i++){c=me.cards[i];out[i]=tot-tC[c[0]]-tC[c[1]]+(me.same[i]>=0?r[me.same[i]]:0);}return out;}', 'for(var i=0;i<me.cards.length;i++){out[i]=tot;}return out;}', 'test_solver'),
 ('solver ignores the board', 'rh.rank=rank(rh);rv.rank=rank(rv);', 'rh.rank=rh.cards.map(function(c){return EQ[codeOf(c)];});rv.rank=rv.cards.map(function(c){return EQ[codeOf(c)];});', 'test_solver'),
 ('river grading bypasses the solver', 'var rk=rvKey(),r=rvGet(false);if(!r){', 'var rk=rvKey(),r=null;if(false){', 'test_solver'),
 ('ranges ignore the flop and turn action', 'if(e.a==="bet"||e.a==="raise")wt*=Math.min(1,Math.max(0.08,rvSig((S2-3.8)/0.45)+(o>=8?0.45:o>=4?0.15:0)));', 'if(false)wt*=1;', 'test_solver'),
 ('chance nodes ignore card removal', 'for(i=0;i<bo.length;i++)ro[bo[i]]=0;', '', 'test_gt'),
 ('flop and turn grading bypass the solver', 'var g=gtFor(heroSizeStd(d)?null:{k:H.cur===0?"bet":"raise",amt:d[1]},false);', 'var g=null;', 'test_gt'),
 ('a decision before the solve lands gets a fallback grade', 'else if(g&&g.pending)pend={kind:"gt",key:g.pending,hist:g.hist};', 'else if(g&&g.pending)solverFallback(rec,"x");', 'test_gt'),
 ('solved play does not narrow the next street', 'if(M){var m=M[k];wt*=(m===undefined?0:m);continue;}', 'if(false){}', 'test_gt'),
 ('deliberate deviations counted in the stats', '  if(rec.dev){var D=devOf()', '  if(false){var D=devOf()', 'test_gt'),
 ('multiway baseline uses player reads', 'Rg=opp.map(gtOn()?neutralRange:actionRange);', 'Rg=opp.map(actionRange);', 'test_gt'),
 ('live 3-bet advice by the openers type in charts mode', '&&S.settings.preModel===true){var op=T.players[H.preAgg]', '){var op=T.players[H.preAgg]', 'test_gt'),
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
