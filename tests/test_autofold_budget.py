"""Auto-fold, the free-check fold guard, and the pot budget meter.

Auto-fold only fires when the action folds to the hero and the opening chart says fold; anything with a limp or raise in
front, the big blind, the hero's own straddle, and a free check all stay the hero's decision. The pot budget is checked
against hand arithmetic, and only over-budget bets and raises count as playing a hand too strong."""
from harness import engine

def _play(style, seats, n, seed):
    return engine().run('''var t=window.__t;seedRNG(%d);S.settings.autoFold=true;S.settings.straddle="off";
      t.table({seats:%d,style:"%s"});T.players[0].hero=true;T.players[0].arch=undefined;
      var o={hands:0,af:0,afBad:0,missed:0,drift:0,errs:0};
      for(var h=0;h<%d;h++){T.players.forEach(function(p){if(p.stack<T.bb*20)p.stack=T.buy;});var before=t.chipsTotal(),rk0=T.rakePaid||0;
        H=null;try{startHand();var g=0;while(H&&!H.done&&g<60){t.drain();g++;
          if(H&&!H.done&&H.toAct===0&&canAct(0)&&!H.autoFold){var L=legal(0),A=adviseHero(false);
            if(H.street===0&&H.raises===0&&limpersIn()===0&&H.pos[0]!=="BB"&&H.straddle!==0&&L.toCall>0&&A.advice==="Fold")o.missed++;
            heroDo(L.toCall>T.bb*8?["fold"]:L.toCall>0?["call"]:["check"]);}}}catch(e){o.errs++;continue;}
        if(H.autoFold){o.af++;var mine=H.hist.filter(function(e){return e.i===0;});if(mine.length!==1||mine[0].a!=="fold"||mine[0].raises!==0)o.afBad++;}
        o.hands++;if(t.chipsTotal()+((T.rakePaid||0)-rk0)!==before)o.drift++;}
      return o;''' % (seed, seats, style, n))

def test_auto_fold_only_folds_unopened_off_chart_hands_and_misses_none():
    for style, seats, seed in (('online', 6, 5), ('casino', 9, 6), ('home', 8, 7)):
        o = _play(style, seats, 50, seed)
        assert o['hands'] == 50 and o['errs'] == 0 and o['drift'] == 0, (style, o)
        assert o['af'] > 5 and o['afBad'] == 0 and o['missed'] == 0, (style, o)

def test_auto_fold_leaves_limped_raised_big_blind_and_free_spots_alone():
    r = engine().run('''var out={};S.settings.autoFold=true;
      function spot(pos,raises,limp,str,toCall){__t.preSpot({hero:"7h2c",pos:pos,opps:[{arch:"tag",pos:"BB"},{arch:"station",pos:"UTG"}],actions:[]});
        H.pos[0]=pos;H.raises=raises;H.straddle=str;H.toAct=0;var orig=limpersIn;limpersIn=function(){return limp;};var o=legal;legal=function(i){var L=o(i);if(i===0)L.toCall=toCall;return L;};
        try{return autoFoldWhy();}finally{limpersIn=orig;legal=o;}}
      out.unopened=spot("CO",0,0,-1,2);out.raised=spot("CO",1,0,-1,6);out.limped=spot("CO",0,1,-1,2);
      out.bb=spot("BB",0,0,-1,0);out.myStraddle=spot("UTG",0,0,0,0);out.free=spot("CO",0,0,-1,0);
      S.settings.autoFold=false;out.off=spot("CO",0,0,-1,2);return out;''')
    assert r['unopened'] and r['unopened']['code'] == '72o', r
    assert all(r[k] is None for k in ('raised', 'limped', 'bb', 'myStraddle', 'free', 'off')), r

def test_the_hero_cannot_fold_when_checking_is_free():
    r = engine().run('''__t.spot({hero:"7h2c",board:"KsQd9h",opps:[{arch:"tag"}],pot:20,toCall:0});var n=H.hist.length;
      heroDo(["fold"]);var a={folded:H.s[0].folded,grew:H.hist.length!==n};heroDo(["check"]);a.checked=H.hist.length===n+1;return a;''')
    assert r == {'folded': False, 'grew': False, 'checked': True}, r

def test_pot_budget_matches_hand_arithmetic():
    # flop pot 20, hero put 10 in pre-flop, 100 behind each. Top pair good kicker heads-up, dry board: 2 streets.
    r = engine().run('''__t.spot({hero:"AsJd",board:"Jh7c2s",opps:[{arch:"tag",stack:90}],pot:20,heroStack:90,toCall:0});H.flopPot=20;H.pfInv=10;
      var P=pbPlan();return {N:P.N,B:P.B,eff:P.eff,tier:P.tier,lab:P.lab};''')
    want = (10 + 20 * ((7 / 3) ** 2 - 1) / 2) / 100
    assert r['N'] == 2 and abs(r['B'] - want) < 1e-9 and r['eff'] == 100 and r['tier'] == 'Medium', r
    assert r['lab'] == 'Top pair, good kicker', r

def test_pot_budget_adjustments_stack_and_monsters_are_worth_stacks():
    r = engine().run('''var o={};
      __t.spot({hero:"AsJd",board:"Jh7h2h",opps:[{arch:"tag"},{arch:"station"},{arch:"nit"}],pot:30});o.wet=pbPlan().N;   // 2 - 1 (4 players) - 1/2 (flush possible)
      __t.spot({hero:"7s7d",board:"Jh7c2s",opps:[{arch:"tag"}],pot:20});var P=pbPlan();o.set=[P.N,P.B];
      __t.spot({hero:"9s8d",board:"KhQc2s",opps:[{arch:"tag"}],pot:20});o.air=pbPlan().air;
      __t.spot({hero:"AsJd",board:"Jh7c2s",opps:[{arch:"tag"}],pot:20,history:[{i:0,a:"bet"},{i:1,a:"raise",la:0}]});o.raised=pbPlan().N;
      return o;''')
    assert r['wet'] == 0.5 and r['set'] == [4, 1] and r['air'] is True and r['raised'] == 1, r

def test_only_over_budget_bets_count_as_too_strong():
    r = engine().run('''var o={};function fresh(){__t.spot({hero:"Ts9s",board:"Jh9c4d",opps:[{arch:"station"}],pot:20,toCall:0});H.flopPot=20;H.pfInv=10;T.sess=null;}
      fresh();var P=pbPlan();heroDo(["raise",Math.round(P.B*P.eff*3)]);o.big=JSON.stringify(sess().pb);o.flash=H.pbFlash&&H.pbFlash.t.indexOf("Too strong")===0;
      fresh();heroDo(["check"]);o.check=JSON.stringify(sess().pb);
      __t.spot({hero:"Ts9s",board:"Jh9c4d",opps:[{arch:"station"}],pot:20,toCall:150});H.flopPot=20;H.pfInv=10;T.sess=null;heroDo(["call"]);o.call=JSON.stringify(sess().pb);
      fresh();H.devNext=true;P=pbPlan();heroDo(["raise",Math.round(P.B*P.eff*3)]);o.dev=JSON.stringify(sess().pb);
      return o;''')
    assert r['big'] == '{"hands":1,"over":1,"calls":0}' and r['flash'], r
    assert r['check'] == '{"hands":1,"over":0,"calls":0}', r
    assert r['call'] == '{"hands":1,"over":0,"calls":1}', r     # a big call is flagged, not counted as too strong
    assert r['dev'] == '{"hands":0,"over":0,"calls":0}', r      # a deliberate deviation stays out of the tally
