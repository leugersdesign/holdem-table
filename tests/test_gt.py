"""The flop and turn solver: chance nodes and card removal against exact enumeration, convergence, board dependence,
ranges narrowed by solved play, grading that waits for the solve, multiway pots graded with no reads, the live pre-flop
baseline, deliberate deviations, and the settings migration."""
import json, time
from harness import engine as _engine

def run(js):
    return _engine().run('S.settings.oppInfo="revealed";delete S.settings.postGrade;GT_ITERS={1:24,2:30};GT_BUDGET={1:20000,2:20000};' + js)

def test_card_weights_count_every_pair_of_hands_exactly_once():
    """Every card dealt is weighted so that, for any two hands, the cards that can still come add up to one; the suit-stratified sample keeps each suit's total."""
    r = run('''var b=__t.cards("Ks7d2c9h"),all=gtCards(b,0),smp=gtCards(b,16),tot=function(l){var t=0;l.forEach(function(x){t+=x.w;});return t;},su=function(l,s){var t=0;l.forEach(function(x){if((x.c&3)===s)t+=x.w;});return t;};
      return {all:tot(all),smp:tot(smp),n:smp.length,suitsAll:[0,1,2,3].map(function(s){return su(all,s);}),suitsSmp:[0,1,2,3].map(function(s){return su(smp,s);})};''')
    assert abs(r['all'] - 48 / 44) < 1e-9 and abs(r['smp'] - r['all']) < 1e-9 and 14 <= r['n'] <= 18, r
    assert all(abs(a - b) < 1e-9 for a, b in zip(r['suitsAll'], r['suitsSmp'])), r

def test_a_check_down_matches_exact_equity_card_removal_included():
    """With no betting the solver's value for a hand is its share of the pot over the runouts. Checked against brute-force enumeration with the app's evaluator, including hands that block each other."""
    r = run('''var board=__t.cards("Ah8h3c"),list0=["KhQh","JcTc","5d4d","AsKd"],list1=["QsQd","8c7c","KhJh","2s2d"];
      var mk=function(l){return {cards:l.map(function(h){return __t.cards(h);}),w:l.map(function(){return 1;})};},R=[mk(list0),mk(list1)];
      var plan=[{sizes:[],raises:0,allinMax:0},null,null],I={P:100,S:200,board:board,plan:plan,sample:[0,0],R:R,hp:0,idx:0,iters:2,ranks:null,noExpl:true};
      var G=gtTree(I.P,I.S,board,plan,[0,0]);gtPrep(G,R,null);gtSolveCore(G,2);var v=gtEV(G,G.root,0,R[1].w),cmp=gtCompat(G,0,R[1].w),out=[];
      for(var i=0;i<4;i++){var h=R[0].cards[i],win=0,n=0;R[1].cards.forEach(function(o){if(o.some(function(c){return h.indexOf(c)>=0||board.indexOf(c)>=0;}))return;
          for(var t=0;t<52;t++)for(var u=t+1;u<52;u++){var used=board.concat(h,o);if(used.indexOf(t)>=0||used.indexOf(u)>=0)continue;var bd=board.concat([t,u]),a=evaluate(h.concat(bd)),b=evaluate(o.concat(bd));win+=a>b?1:a===b?0.5:0;n++;}});
        out.push([v[i]/cmp[i],100*win/n]);}
      return out;''')
    assert all(abs(a - b) < 1e-6 for a, b in r), r

def test_the_flop_solvers_sampled_cards_stay_within_the_noise_the_grade_allows():
    """The turn solve deals every river. The flop solve deals a sample of turn cards; its average error per hand, checked against
    dealing every card on 12 random boards, stays inside the extra tolerance (GT_NOISE) the flop grade gives it."""
    r = run('''seedRNG(3);var errs=[];
      for(var trial=0;trial<12;trial++){var deck=[];for(var c=0;c<52;c++)deck.push(c);for(var i=51;i>0;i--){var j=Math.floor(RNG()*(i+1)),t=deck[i];deck[i]=deck[j];deck[j]=t;}
        var board=deck.slice(0,4),R=[{cards:[],w:[]},{cards:[],w:[]}];for(var h=0;h<24;h++){R[h%2].cards.push([deck[4+2*h],deck[5+2*h]]);R[h%2].w.push(1);}
        var f=function(smp){var plan=[{sizes:[],raises:0,allinMax:0},null],G=gtTree(100,200,board,plan,[smp]);gtPrep(G,R,null);gtSolveCore(G,1);var v=gtEV(G,G.root,0,R[1].w),cc=gtCompat(G,0,R[1].w);return Array.from(v).map(function(x,i){return x/cc[i];});};
        var ex=f(0),sm=f(GT_SAMPLE[1][0]),e=0;for(var k=0;k<ex.length;k++)e+=Math.abs(sm[k]-ex[k]);errs.push(e/ex.length);}
      var m=0;errs.forEach(function(x){m+=x;});return {mean:m/errs.length,noise:GT_NOISE[1]*100,turnRivers:GT_SAMPLE[2][0]};''')
    assert r['turnRivers'] == 0 and r['mean'] < r['noise'] + 0.5, r

def turn_spot(hero, board, hist=None, ip=False, opps=None):
    return '__t.spot({hero:"%s",board:"%s",opps:%s,pot:20,seed:5,ip:%s,history:%s});' % (hero, board, json.dumps(opps or [{'arch': 'weekend'}]), 'true' if ip else 'false', json.dumps(hist or []))

def test_exploitability_falls_as_the_turn_solver_runs():
    r = run(turn_spot('AhJd', 'Ks7d2c9h') + 'var I=gtSpotInput(null,true),out=[];[4,16,48].forEach(function(n){var G=gtTree(I.P,I.S,I.board,I.plan,I.sample);gtPrep(G,I.R,I.ranks);gtSolveCore(G,n);out.push(gtExpl(G));});return out;')
    assert r[0] > r[1] > r[2] and r[2] < 0.04, r

def test_the_turn_card_drives_the_answer():
    blank = run(turn_spot('AhQh', 'Kh7h2c9d', ip=True, hist=[{'i': 1, 'a': 'check'}]) + 'var g=gtFor(null,true);return g.acts.map(function(a){return [a.kind,a.freq];});')
    flush = run(turn_spot('AhQh', 'Kh7h2c3h', ip=True, hist=[{'i': 1, 'a': 'check'}]) + 'var g=gtFor(null,true);return g.acts.map(function(a){return [a.kind,a.freq];});')
    bet = lambda r: sum(f for k, f in r if k == 'bet')
    assert bet(flush) > bet(blank) + 0.3 and bet(flush) > 0.6, (blank, flush)   # a made nut flush bets far more than the same hand with only a draw

def test_turn_grading_uses_the_solver_and_never_punishes_a_mixed_action():
    r = run(turn_spot('Td9d', 'Ks7d2c8h') + '''S.coach=blankCoach();var g=gtFor(null,true),mix=g.acts.filter(function(a){return a.freq>=0.1;}).map(function(a){return a.kind==="check"?["check"]:["raise",a.amt];});
      return mix.map(function(d){H.dec=[];recordDecision(d);var x=H.dec[0];return {vs:x.gradedVs,sev:x.sev,why:x.why};});''')
    assert len(r) >= 1 and all(x['vs'] == 'solver' and x['sev'] == 0 and x['why'].startswith('The solver plays your hand') for x in r), r

def test_a_decision_made_before_the_solve_lands_waits_and_is_then_graded_by_the_solver():
    cold = run(turn_spot('AhJd', 'Ks7d2c9h') + 'S.coach=blankCoach();H.dec=[];var n0=S.leaks?S.leaks.n:0;recordDecision(["check"]);var g=H.dec[0];window.__g=g;window.__n0=n0;return {pend:!!g.pend,vs:g.gradedVs||null,counted:(S.leaks?S.leaks.n:0)-n0};')
    assert cold == {'pend': True, 'vs': None, 'counted': 0}, cold          # nothing is counted until the grade exists
    for _ in range(60):
        time.sleep(0.5)
        g = _engine().js('(function(){var g=window.__g;return {pend:!!g.pend,vs:g.gradedVs||null,counted:(S.leaks?S.leaks.n:0)-window.__n0};})()')
        if not g['pend']:
            break
    assert g == {'pend': False, 'vs': 'solver', 'counted': 1}, g

def test_an_off_tree_bet_size_is_solved_with_that_size():
    r = run(turn_spot('KhKd', 'Ks7d2c9h', ip=True, hist=[{'i': 1, 'a': 'check'}]) + 'gtFor(null,true);var before=Object.keys(H.gtS).length;GT_WORKER=false;H.dec=[];recordDecision(["raise",11]);var g=H.dec[0];return {keys:Object.keys(H.gtS),before:before,vs:g.gradedVs,sol:g.solver};')
    assert r['before'] == 1 and len(r['keys']) == 2 and any(k.endswith('|11|') for k in r['keys']) and r['vs'] == 'solver', r
    assert any(lab.startswith('Bet 55%') for lab, _, _ in r['sol']), r     # the 11-chip bet (55% of the pot) is in the tree it was graded on

def test_the_next_street_starts_from_the_ranges_the_solver_played():
    """After the flop is solved and the line is bet-call, the turn ranges are the flop ranges times each hand's own probability of that line, not the board rule."""
    r = run(turn_spot('AhJd', 'Ks7d2c', ip=True) + '''GT_WORKER=false;var g=gtFor(null,true);var key=H.gtLast[1],E=H.gtS[key];
      H.hist.push({i:1,st:1,a:"check",toCall:0,pot:20},{i:0,st:1,a:"bet",to:15,toCall:0,pot:20},{i:1,st:1,a:"call",toCall:15,pot:35});H.board.push(__t.card("4h"));H.street=2;
      var narrowed=gtNarrowFor(1),N=H.gtN[1],v=1,Rv=gtRangeW(v,2,H.board,null,0),sol=0,rule=0,L=E.res.lines.find(function(l){return l.seq.length===3&&l.seq[1].k==="bet";});
      var kQ=ckey(__t.cards("KhQd")),k72=ckey(__t.cards("7c2h"));H.gtN={1:null};var Rr=gtRangeW(v,2,H.board,null,0);
      var w=function(R,k){var i=R.cards.findIndex(function(x){return ckey(x)===k;});return i<0?0:R.w[i];};
      return {narrowed:narrowed,has:!!(N&&N[0]&&N[v]),nl:E.res.lines.length,diff:Rv.w.length===Rr.w.length?Rv.w.reduce(function(a,x,i){return a+Math.abs(x-Rr.w[i]);},0):-1};''')
    assert r['narrowed'] and r['has'] and r['diff'] > 1, r

def test_multiway_pots_are_graded_by_the_price_with_no_reads():
    js = '__t.spot({hero:"QhJh",board:"Kh7d2c",opps:[{arch:"%s"},{arch:"%s"}],pot:30,toCall:10,seed:5});S.coach=blankCoach();H.dec=[];recordDecision(["call"]);var g=H.dec[0];return {vs:g.gradedVs,adv:g.advice,eq:Math.round(g.eq*100)};'
    a = run(js % ('station', 'nit'))
    b = run(js % ('maniac', 'lag'))
    assert a['vs'] == 'price' and b['vs'] == 'price' and a['adv'] == b['adv'] and abs(a['eq'] - b['eq']) <= 4, (a, b)   # who the players are does not change the baseline

def test_solver_mode_advice_uses_no_player_reads_after_the_flop():
    js = '__t.spot({hero:"KhJd",board:"Ks7d2c9h4s",opps:[{arch:"%s"}],pot:40,toCall:30,seed:5});T.live=true;T.mode="cash";var A=adviseHero(false);return {adv:A.advice,why:A.why};'
    a = run(js % 'station')
    b = run(js % 'nit')
    assert a['adv'] == b['adv'] and 'Sizing read' not in a['why'] and 'Sizing read' not in b['why'], (a, b)

def test_live_preflop_against_a_raise_uses_the_equity_baseline_not_the_openers_type():
    js = '__t.preSpot({hero:"Ah5h",pos:"BTN",opps:[{arch:"%s",pos:"CO"}],actions:[{i:1,a:"raise",to:3}]});T.live=true;var L=legal(0),lv=liveAdvice(codeOf(H.s[0].cards),H.pos[0],[1],L,H.s[0]);return lv?lv[0]:null;'
    assert run(js % 'station') is None and run(js % 'nit') is None
    assert run('S.settings.preModel=true;' + (js % 'station')) is not None   # the read-based table stays available when grading by the EV model

def test_a_deliberate_deviation_is_logged_and_kept_out_of_the_stats():
    r = run(turn_spot('AhJd', 'Ks7d2c9h') + '''GT_WORKER=false;S.coach=blankCoach();S.devs={n:0,list:[]};var n0=(S.leaks||{n:0}).n,r0=(S.redo||[]).length;gtFor(null,true);H.dec=[];H.devNext=true;recordDecision(["raise",100*T.bb]);var g=H.dec[0];
      return {dev:!!g.dev,next:!!H.devNext,logged:S.devs.list.length,leaks:(S.leaks||{n:0}).n-n0,redo:(S.redo||[]).length-r0,coach:S.coach.N,card:devCardHTML().indexOf("1</b> logged")>=0,vs:g.gradedVs,chip:gcIcon(g).charAt(0)};''')
    assert r == {'dev': True, 'next': False, 'logged': 1, 'leaks': 0, 'redo': 0, 'coach': 0, 'card': True, 'vs': 'solver', 'chip': 'D'}, r

def test_a_saved_typical_opponent_setting_goes_back_to_the_solver_once():
    r = run('''var a=migrateS({version:2,stats:{},settings:{postGrade:"typical"}}),b=migrateS({version:2,stats:{},settings:{postGrade:"read"}}),c=migrateS({version:3,stats:{},settings:{postGrade:"typical"}});
      return [a.settings.postGrade||"solver",b.settings.postGrade,c.settings.postGrade,a.version];''')
    assert r == ['solver', 'read', 'typical', 3], r                          # read-based stays; a choice made after the update stays

def test_the_raise_box_has_pot_fractions_and_half_and_whole_big_blind_steps():
    r = run(turn_spot('AhJd', 'Ks7d2c9h') + '''$("g-controls").innerHTML="<div id='c-rb'></div>";var L=legal(0);openRaise(L);var rb=$("c-rb"),labs=[].map.call(rb.querySelectorAll(".presets button"),function(b){return b.textContent;});
      var amt=function(){return $("c-amt").textContent;},click=function(sel){rb.querySelector(sel).click();return amt();};
      var half=click("[data-d='"+(T.bb/2)+"']"),one=click("[data-d='"+T.bb+"']"),back=click("[data-d='"+(-T.bb)+"']"),pot=click("[data-to='"+Math.round(potTotal())+"']");
      return {labs:labs,steps:[].map.call(rb.querySelectorAll(".steps button"),function(b){return b.textContent;}),bb:T.bb,first:labs[0],half:half,one:one,back:back,pot:pot,pct:$("c-amtp").textContent};''')
    assert r['labs'] == ['\u00bc pot', '\u2153 pot', '\u00bd pot', '\u2154 pot', '\u00be pot', 'Pot', 'All in'], r
    assert r['steps'] == ['\u2212 1 BB', '\u2212 \u00bd BB', '+ \u00bd BB', '+ 1 BB'] and '100% pot' in r['pct'], r
    q, bb = 5, r['bb']                                                       # a quarter of the 20 pot, then +half, +one, -one big blind
    want = [round(q + bb / 2 + 1e-9), round(q + bb * 1.5 + 1e-9), round(q + bb / 2 + 1e-9)]
    assert [int(r[k][1:]) for k in ('half', 'one', 'back')] == want and r['pot'] == '$20', r

def straddle_hand(pref, want, tries=400):
    """Deal home-game hands until the hero is in the seat the straddle setting covers, with a human hero and the real timers queued."""
    return run('''S.customCfg={bi:1,depth:100,seats:9,style:"home",spec:["station","limper","weekend","tag","nit","lag","station","limper"],table:"classic",atm:"vegas"};
      seedRNG(4);T=makeCash(customStake());T.home=true;S.cash=T;T.noLeave=true;S.settings.straddle="%s";var got=null;
      for(var k=0;k<%d&&!got;k++){T.players.forEach(function(p){if(p.stack<T.bb*20)p.stack=T.buy;});H=null;startHand();__t.q.length=0;
        if(H.straddle===0&&H.straddleKind==="%s")got={kind:H.straddleKind,cur:H.cur/T.bb,heroIn:H.s[0].sb/T.bb,toAct:H.toAct,sbI:H.sbI,bbI:H.bbI,button:H.button,pos:H.pos[0],log:H.log.join(" ")};
        else if(H.straddle===0)got={wrong:H.straddleKind};}
      return got;''' % (pref, tries, want))

def test_the_hero_can_straddle_under_the_gun():
    r = straddle_hand('utg', 'utg')
    assert r and r['kind'] == 'utg' and r['cur'] == 2 and r['heroIn'] == 2 and r['toAct'] not in (0, r['sbI'], r['bbI']) and 'You straddle' in r['log'], r

def test_a_button_straddle_lets_the_small_blind_act_first_and_the_hero_last():
    r = straddle_hand('btn', 'btn')
    assert r and r['kind'] == 'btn' and r['button'] == 0 and r['toAct'] == r['sbI'] and 'small blind' in r['log'], r

def test_no_straddle_when_the_setting_is_off():
    r = straddle_hand('off', 'utg', tries=60)
    assert r is None, r

STR_SPOT = '''__t.preSpot({hero:"%s",pos:"%s",opps:[{arch:"weekend",pos:"UTG"},{arch:"weekend",pos:"SB"},{arch:"weekend",pos:"BB"}],actions:[]});T.home=true;
  if(%s){H.s[1].sb=2*T.bb;H.s[1].tot=2*T.bb;T.players[1].stack-=2*T.bb;H.cur=2*T.bb;H.minR=2*T.bb;H.straddle=1;}
  var A=adviseHero(false);return {adv:A.advice,why:A.why,lim:limpersIn()};'''

def test_a_straddle_tightens_early_seats_but_not_the_button():
    # Q9s scores 7: an open from the hijack (seat 7) without a straddle, a fold from the hijack with one, still an open from the button
    no = run(STR_SPOT % ('Qh9h', 'HJ', 'false'))
    yes = run(STR_SPOT % ('Qh9h', 'HJ', 'true'))
    btn = run(STR_SPOT % ('Qh9h', 'BTN', 'true'))
    assert no['adv'] == 'Raise' and yes['adv'] == 'Fold' and btn['adv'] == 'Raise', (no, yes, btn)
    assert yes['lim'] == 0 and 'straddle' in yes['why'] and 'straddles (' in btn['why'], (yes, btn)   # the straddler is not a limper; sizes are in straddles

def test_the_straddler_checks_its_option_and_the_big_blind_no_longer_sees_a_free_flop():
    opt = run('''__t.preSpot({hero:"7h2c",pos:"UTG",opps:[{arch:"weekend",pos:"HJ"},{arch:"weekend",pos:"SB"},{arch:"weekend",pos:"BB"}],actions:[]});T.home=true;
      H.s[0].sb=2*T.bb;H.s[0].tot=2*T.bb;H.cur=2*T.bb;H.straddle=0;H.s[1].sb=2*T.bb;H.s[1].tot=2*T.bb;var A=adviseHero(false);return {adv:A.advice,why:A.why};''')
    bb = run('''__t.preSpot({hero:"7h2c",pos:"BB",opps:[{arch:"weekend",pos:"UTG"},{arch:"weekend",pos:"BTN"},{arch:"weekend",pos:"SB"}],actions:[]});T.home=true;
      H.s[1].sb=2*T.bb;H.s[1].tot=2*T.bb;H.cur=2*T.bb;H.straddle=1;H.s[0].sb=T.bb;var A=adviseHero(false);return {adv:A.advice,why:A.why};''')
    assert opt['adv'] == 'Check' and 'option' in opt['why'], opt
    assert bb['adv'] == 'Fold' and 'free' not in bb['why'], bb

def test_the_raise_box_counts_opens_in_straddles():
    r = run(STR_SPOT.replace('var A=adviseHero(false);return {adv:A.advice,why:A.why,lim:limpersIn()};', '''$("g-controls").innerHTML="<div id='c-rb'></div>";openRaise(legal(0));
      return {labs:[].map.call($("c-rb").querySelectorAll(".presets button"),function(b){return b.textContent;}),amt:$("c-amt").textContent,u:$("c-amtp").textContent,bb:T.bb};''') % ('AhKh', 'HJ', 'true'))
    assert r['labs'][:3] == ['3 str', '4 str', '5 str'] and r['amt'] == '$%d' % (6 * r['bb']) and '3 straddles' in r['u'], r

def test_hands_with_the_heros_straddle_play_out_and_conserve_chips():
    r = run('''seedRNG(9);__t.table({seats:9,style:"home"});T.home=true;S.settings.straddle="both";var n=0,btn=0,last=null,orig=startHand;
      var o=__t.play(400);return {hands:o.hands,errors:o.errors,drift:o.drift,dup:o.dupCards};''')
    assert r['hands'] >= 380 and r['errors'] == 0 and r['drift'] == 0 and r['dup'] == 0, r

def test_a_button_straddler_gets_the_last_word_before_the_flop():
    r = run('''seedRNG(4);__t.table({seats:6,style:"home"});T.home=true;S.settings.straddle="btn";var seen=0,lastOk=0;
      for(var k=0;k<300&&seen<5;k++){T.players.forEach(function(p){if(p.stack<T.bb*20)p.stack=T.buy;});H=null;startHand();__t.drain();
        if(H.straddleKind==="btn"){seen++;var pre=H.hist.filter(function(e){return e.st===0;});var allFold=pre.every(function(e){return e.a==="fold";});if(pre.length&&pre[0].i===H.sbI&&(pre[pre.length-1].i===0||pre.some(function(e){return e.a==="raise";})||allFold))lastOk++;}}
      return {seen:seen,ok:lastOk};''')
    assert r['seen'] >= 3 and r['ok'] == r['seen'], r
