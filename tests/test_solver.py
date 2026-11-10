"""The river solver: textbook equilibrium, convergence, board dependence, card removal, grading, and that it never blocks a decision."""
import json
from harness import engine as _engine

def run(js):
    return _engine().run('S.settings.oppInfo="revealed";S.settings.postGrade="solver";' + js)

TOY = '''var board=__t.cards("KsQsJd4c2h");function range(list){var cards=[],rank=[],w=[];list.forEach(function(h){var c=__t.cards(h);cards.push(c);rank.push(evaluate(c.concat(board)));w.push(1);});return {cards:cards,rank:rank,w:w};}
  var ip=range(["AhTh","AdTd","AcTc","AhTd","AdTh","AcTh","7h6d","7d6h","7c6h","7h6c","7d6c","7c6d"]),oop=range(["Qh9h","Qd9d","Qc9c","Qh9d","Qd9h","Qc9h","Qh9c","Qd9c","Qc9d"]),P=100,ST=100;'''

def test_the_solver_reproduces_the_textbook_river_equilibrium():
    """Polarized range (nuts or air) against bluff-catchers, one pot-sized bet: bet all the nuts, bluff half the air (one bluff per two value bets), and the bluff-catcher calls half."""
    r = run(TOY + '''var T2=rvTree(P,ST,[1.0],[],[]),R=[oop,ip],res=rvSolveCore(P,R,T2,2000);
      var n=T2.nodes.find(function(x){return x.hist==="x"&&x.pl===1;}),s=rvStrat(n,12,true),b=n.acts.findIndex(function(a){return a.kind==="bet";}),nuts=0,air=0;for(var i=0;i<6;i++){nuts+=s[b][i]/6;air+=s[b][i+6]/6;}
      var f=T2.nodes.find(function(x){return x.hist==="xb100"&&x.pl===0;}),so=rvStrat(f,9,true),c=f.acts.findIndex(function(a){return a.kind==="call";}),call=0;for(i=0;i<9;i++)call+=so[c][i]/9;
      var q=rvQuery(P,R,T2,"x",1,6);return {expl:res.expl,nuts:nuts,air:air,call:call,airEVs:q.acts.map(function(a){return a.ev;})};''')
    assert r['expl'] < 0.001 and r['nuts'] > 0.99 and abs(r['air'] - 0.5) < 0.03 and abs(r['call'] - 0.5) < 0.03, r
    assert abs(r['airEVs'][0] - r['airEVs'][1]) < 1.0, r                    # a bluff is indifferent between betting and checking

def test_exploitability_falls_as_the_solver_runs():
    r = run(TOY + 'var out=[];[20,100,500].forEach(function(n){out.push(rvSolveCore(P,[oop,ip],rvTree(P,ST,[0.5,1.0],[],[]),n).expl);});return out;')
    assert r[0] > r[1] > r[2] and r[2] < 0.005, r

def test_card_removal_is_exact():
    r = run('''var mk=function(list){return {cards:list.map(function(h){return __t.cards(h);}),rank:list.map(function(){return 1;}),w:list.map(function(){return 1;})};};
      var R=rvPrep([mk(["AhKh","QdJd"]),mk(["AhQs","KhQs","QdJd","2c3c"])]),out=new Float64Array(2);rvCompat(R,0,R[1].w,out);return [out[0],out[1]];''')
    assert r == [2, 3], r          # AhKh blocks two of the four, QdJd blocks only its own duplicate

def solve(hero, board, hist, pot, to_call, ip=True):
    return run('__t.spot({hero:"%s",board:"%s",opps:[{arch:"weekend"}],pot:%d,toCall:%d,seed:5,ip:%s,history:%s});H.rv=null;var r=rvGet(true);return r?r.acts.map(function(a){return [a.lab,a.kind,a.freq,a.ev];}):null;' % (hero, board, pot, to_call, 'true' if ip else 'false', json.dumps(hist)))

CHK = [{'i': 1, 'st': 1, 'a': 'check', 'toCall': 0, 'pot': 20}, {'i': 0, 'st': 1, 'a': 'check', 'toCall': 0, 'pot': 20}, {'i': 1, 'st': 2, 'a': 'check', 'toCall': 0, 'pot': 20}, {'i': 0, 'st': 2, 'a': 'check', 'toCall': 0, 'pot': 20}, {'i': 1, 'st': 3, 'a': 'check', 'toCall': 0, 'pot': 20}]

def test_the_board_drives_the_answer():
    blank = solve('AhQh', 'Kh7h2c9d4s', CHK, 40, 0)
    flush = solve('AhQh', 'Kh7h2c9d3h', CHK, 40, 0)
    bet = lambda r: sum(f for _, k, f, _ in r if k == 'bet')
    assert bet(blank) < 0.2 and bet(flush) > 0.6, (blank, flush)             # same hand, same story: only the river card changed

def test_solver_frequencies_are_a_distribution_over_the_legal_actions():
    for hero, board in (('KhJd', 'Ks7d2c9h4s'), ('7c6c', 'Ks7d2c9h4s')):
        r = solve(hero, board, CHK, 40, 0)
        assert abs(sum(f for _, _, f, _ in r) - 1) < 1e-6 and {k for _, k, _, _ in r} <= {'check', 'bet'}, r

def test_grading_uses_the_solver_when_ready_never_waits_and_never_punishes_a_mixed_action():
    import time
    base = '__t.spot({hero:"7c6c",board:"Ks7d2c9h4s",opps:[{arch:"weekend"}],pot:40,seed:5,history:%s});S.coach=blankCoach();H.dec=[];' % json.dumps(CHK)
    cold = run(base + 'H.rv=null;H.rvS={};recordDecision(["check"]);var g=H.dec[0];window.__cold=g;return {pending:!!g.pend,vs:g.gradedVs||null,sev:g.sev};')
    assert cold == {'pending': True, 'vs': None, 'sev': 0}, cold            # the solve was not ready: no waiting and no fallback model, the decision waits
    for _ in range(40):
        time.sleep(0.5)
        landed = _engine().js('(function(){var g=window.__cold;return {pending:!!g.pend,vs:g.gradedVs||null,leaks:H.pend?H.pend.length:0};})()')
        if not landed['pending']:
            break
    assert landed['vs'] == 'solver' and not landed['pending'], landed     # graded by the solver once it landed
    warm = run(base + '''H.rv=null;var r=rvGet(true),mix=r.acts.filter(function(a){return a.freq>=0.1;}).map(function(a){return a.kind==="check"?["check"]:["raise",a.amt];});
      var out=mix.map(function(d){H.dec=[];recordDecision(d);var g=H.dec[0];return {vs:g.gradedVs,sev:g.sev,why:g.why};});return out;''')
    assert len(warm) >= 2 and all(x['vs'] == 'solver' and x['sev'] == 0 and x['why'].startswith('The solver plays your hand') for x in warm), warm

def test_ranges_exclude_the_board_and_contain_the_heros_hand():
    r = run('__t.spot({hero:"KhJd",board:"Ks7d2c9h4s",opps:[{arch:"weekend"}],pot:40,seed:5,history:%s});var I=rvSpotInput(10),b=H.board,bad=0;I.R.forEach(function(R){R.cards.forEach(function(c){if(b.indexOf(c[0])>=0||b.indexOf(c[1])>=0)bad++;});});return {bad:bad,idx:I.idx,hp:I.hp,n:[I.R[0].cards.length,I.R[1].cards.length]};' % json.dumps(CHK))
    assert r['bad'] == 0 and r['idx'] >= 0 and min(r['n']) > 20, r

def test_a_bet_ranges_narrows_toward_hands_that_connect_with_the_board():
    BET = [{'i': 1, 'st': 1, 'a': 'bet', 'f': 0.5, 'toCall': 0, 'pot': 20}, {'i': 0, 'st': 1, 'a': 'call', 'toCall': 10, 'pot': 30}, {'i': 1, 'st': 2, 'a': 'bet', 'f': 0.6, 'toCall': 0, 'pot': 40}, {'i': 0, 'st': 2, 'a': 'call', 'toCall': 24, 'pot': 64}]
    js = '__t.spot({hero:"KhJd",board:"Ks7d2c9h4s",opps:[{arch:"weekend"}],pot:88,seed:5,ip:true,history:%s});var R=rvRange(1,H.board,null),s=0,t=0;R.cards.forEach(function(c,i){var S=hcInfo(c,H.board).S;s+=S*R.w[i];t+=R.w[i];});return s/t;'
    assert run(js % json.dumps(BET)) > run(js % json.dumps(CHK)) + 0.5        # a player who bet twice holds stronger hands than one who checked twice
