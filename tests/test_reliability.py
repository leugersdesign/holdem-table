"""Reliability (prompt 06): invalid actions are rejected, a refresh cannot lose chips, bots always get a legal action, the idle
precompute is transparent, long sessions stay consistent, and the session summary keeps results and decision quality apart."""
from harness import engine as _engine

class engine:
    def run(self, js):
        return _engine().run('S.settings.oppInfo="revealed";' + js)

START = 'seedRNG(%d);__t.table({seats:4});H=null;startHand();__t.q.length=0;var who=H.toAct,L=legal(who),snap=function(){return JSON.stringify([(H.hist||[]).length,H.cur,T.players[who].stack,potTotal(),H.s[who].sb]);};'

def test_illegal_actions_change_nothing():
    r = engine().run(START % 1 + '''var s0=snap(),out={};
      out.check=L.toCall>0?act(who,"check"):act(who,"call");           // checking into a bet, or calling when there is nothing to call
      out.nan=act(who,"raise",NaN);out.undef=act(who,"raise");out.notAbove=act(who,"raise",H.cur);out.unknown=act(who,"limp");
      out.belowMin=(L.minTo>H.cur+1&&L.maxTo>H.cur+1)?act(who,"raise",H.cur+1):false;       // a raise smaller than the minimum that is not an all-in
      out.unchanged=snap()===s0;H.s[who].folded=true;out.afterFold=act(who,"call");H.s[who].folded=false;H.done=true;out.afterDone=act(who,"fold");H.done=false;return out;''')
    assert r['unchanged'] and all(v is False for k, v in r.items() if k != 'unchanged'), r

def test_legal_actions_are_accepted_each_from_a_fresh_hand():
    cases = {'fold': 'act(who,"fold")', 'call': 'L.toCall>0?act(who,"call"):act(who,"check")', 'min raise': 'act(who,"raise",L.minTo)', 'all in': 'act(who,"raise",L.maxTo)'}
    for name, call in cases.items():
        r = engine().run(START % 2 + 'var n0=(H.hist||[]).length;var res=%s;return {ok:res!==false,grew:(H.hist||[]).length===n0+1};' % call)
        assert r['ok'] and r['grew'], (name, r)

def test_a_bot_that_asks_for_something_illegal_gets_the_nearest_legal_action_and_the_hand_finishes():
    for bogus in ('["check"]', '["raise",NaN]', '["call"]', '["raise",1]'):
        r = engine().run('''seedRNG(5);__t.table({seats:6});T.illegal=0;var oPre=botPre,oPost=botPost;botPre=function(i){return %s;};botPost=function(i){return %s;};
          var o;try{o=__t.play(30);}finally{botPre=oPre;botPost=oPost;}return {hands:o.hands,errors:o.errors,drift:o.drift,dup:o.dupCards,illegal:T.illegal};''' % (bogus, bogus))
        assert r['hands'] == 30 and r['errors'] == 0 and r['drift'] == 0 and r['dup'] == 0, (bogus, r)
        assert r['illegal'] > 0 or bogus == '["call"]'                      # the fallback was used (a bare call is legal whenever someone is facing a bet, so it may never be needed)

def test_a_refresh_in_the_middle_of_a_hand_voids_the_hand_and_loses_no_chips():
    r = engine().run('''seedRNG(8);__t.table({seats:6});var before=__t.chipsTotal();H=null;startHand();__t.q.length=0;      // blinds are posted, the hand is in progress
      var inPlay=__t.chipsTotal()+potTotal(),cur=T.players.map(function(p){return p.stack;});save();
      var saved=JSON.parse(localStorage.getItem(KEY)).cash.players.map(function(p){return p.stack;}),after=T.players.map(function(p){return p.stack;});
      var sum=function(a){return a.reduce(function(x,y){return x+y;},0);};
      H.done=true;save();var done=JSON.parse(localStorage.getItem(KEY)).cash.players.map(function(p){return p.stack;});
      return {before:before,inPlay:inPlay,savedSum:sum(saved),memoryUnchanged:JSON.stringify(cur)===JSON.stringify(after),pot:potTotal(),savedAfterHand:JSON.stringify(done)===JSON.stringify(after)};''')
    assert r['pot'] > 0 and r['inPlay'] == r['before']                      # the chips in the pot are real
    assert r['savedSum'] == r['before'], r                                   # a refresh restores everyone's hand-start stack: nothing lost, nothing created
    assert r['memoryUnchanged'] and r['savedAfterHand'], r                   # saving does not disturb the live hand, and between hands the current stacks are saved

def test_the_idle_precompute_is_transparent_and_makes_the_grade_a_cache_hit():
    r = engine().run('''var n=0,o=evAnalyze;evAnalyze=function(){n++;return o.apply(this,arguments);};
      try{__t.spot({hero:"AhKd",board:"Ks7d2c",opps:[{arch:"weekend"}],pot:20,seed:5});S.coach=blankCoach();
        var cold=(function(){n=0;H.dec=[];recordDecision(["check"]);return n;})();
        __t.spot({hero:"AhKd",board:"Ks7d2c",opps:[{arch:"weekend"}],pot:20,seed:5});prewarmNow();var warm0=n;H.dec=[];recordDecision(["check"]);var warm=n-warm0;var rec=H.dec[0];
        __t.spot({hero:"AhKd",board:"Ks7d2c",opps:[{arch:"weekend"}],pot:20,seed:5});n=0;prewarm();H.id=H.id+1000;__t.drain();var stale=n;
        return {cold:cold,warm:warm,stale:stale,graded:!!rec.model&&rec.tol>0&&!!rec.conf};}finally{evAnalyze=o;}''')
    assert r['cold'] >= 2 and r['warm'] == 0, r                              # without it, grading runs the analysis twice; with it, nothing new
    assert r['stale'] == 0 and r['graded'], r                                # a precompute for a hand that has moved on does nothing

def test_the_session_summary_keeps_the_result_and_decision_quality_apart():
    r = engine().run('''__t.preSpot({hero:"KhQd",pos:"BTN",opps:[{arch:"station",pos:"UTG"},{arch:"tag",pos:"SB"},{arch:"tag",pos:"BB"}],actions:[{i:1,a:"call"}]});S.coach=blankCoach();T.sess=null;
      recordDecision(["fold"]);var s=T.sess;s.hands=20;s.bbNet=-12;var html=evLostHTML(s);return {n:s.modelN,raw:s.rawBB,html:html};''')
    assert r['n'] == 1 and r['raw'] > 0
    assert '-12.0 bb' in r['html'] and 'a good session can lose and a poor one can win' in r['html'] and 'not a real-world win rate' in r['html']

def test_the_review_keeps_the_alternatives_and_the_typical_player_comparison():
    r = engine().run('''__t.preSpot({hero:"KhQd",pos:"BTN",opps:[{arch:"station",pos:"UTG"},{arch:"tag",pos:"SB"},{arch:"tag",pos:"BB"}],actions:[{i:1,a:"call"}]});S.coach=blankCoach();
      recordDecision(["call"]);var rec=H.dec[0];return {alts:rec.alts,base:rec.baseBest,html:coachLinesHTML(rec),json:JSON.stringify(rec).length};''')
    assert len(r['alts']) >= 3 and r['base'] and 'Options (estimated EV' in r['html'] and 'Against a typical player' in r['html']
    assert r['json'] < 4000                                                   # a stored decision stays small

def test_long_sessions_stay_consistent_on_every_table_type():
    for cfg in ('{seats:9,bi:0,depth:100,spec:["station","nit","maniac","tag","weekend","lag","shark","whale"],rake:{pct:0.10,cap:6,drop:1,noFlopNoDrop:true}}',
                '{seats:6,bi:1,depth:100,spec:["wild","thinker","shorty","limper","tag"]}', '{seats:2,bi:0,depth:60,spec:["maniac"]}', '{seats:9,bi:0,depth:25,spec:["maniac","station","lag","limper","whale","nit","tag","weekend"]}'):
        r = engine().run('''seedRNG(77);__t.table(%s);T.illegal=0;var log=[],f0=actFix;actFix=function(i,d){if(!actLegal(i,d[0],d[1])){var L=legal(i);log.push({arch:T.players[i].arch,asked:d,cur:H.cur,sb:H.s[i].sb,stack:T.players[i].stack,toCall:L.toCall,canRaise:L.canRaise,minTo:L.minTo,maxTo:L.maxTo,st:H.street,raises:H.raises});}return f0(i,d);};
          var o;try{o=__t.play(500);}finally{actFix=f0;}return {hands:o.hands,errors:o.errors,drift:o.drift,dup:o.dupCards,illegal:T.illegal,log:log.slice(0,4)};''' % cfg)
        assert {k: r[k] for k in ('hands', 'errors', 'drift', 'dup', 'illegal')} == {'hands': 500, 'errors': 0, 'drift': 0, 'dup': 0, 'illegal': 0}, (cfg[:30], r)
