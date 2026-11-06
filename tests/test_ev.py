"""Expected-value accounting and recommendation structure.

EV convention (see evAnalyze): chips gained from now on, relative to folding now (fold = 0). Chips already in the pot are
sunk: they are chips the hero can win, never a loss. Only chips added from now on are costs. Unmatchable chips are refunded.
Hand-computed expectations below are exact arithmetic, not simulation.
"""
from harness import engine, known_failure

def test_rake_arithmetic():
    e = engine()
    r = e.run('''T={room:{rake:{pct:0.05,cap:300,drop:0}}};var a=rakeOf(1000,true),b=rakeOf(10000,true),c=rakeOf(1000,false);
      T.room.rake.drop=100;var d=rakeOf(1000,true),f=rakeOf(50,true);T.room.rake.noFlopNoDrop=false;var g=rakeOf(1000,false);T.room=undefined;return {a:a,b:b,c:c,d:d,f:f,g:g,off:rakeOf(1000,true)};''')
    assert r['a'] == 50 and r['b'] == 300          # 5% of 1000, then the cap
    assert r['c'] == 0                              # no flop, no drop
    assert r['d'] == 150                            # 5% plus a 100 drop
    assert r['f'] == 50                             # rake never exceeds the pot
    assert r['g'] == 150 and r['off'] == 0          # with the no-flop-no-drop rule off, rake applies to every pot; no rake configured = none

def test_ev_formulas_match_hand_arithmetic():
    e = engine()
    r = e.run('''T={};return {
      call:evCallPure(0.4,100,20,1,true),                 /* 0.4*(100+20) - 20 */
      callRho:evCallPure(0.4,100,20,0.9,true),            /* 0.4*120*0.9 - 20 */
      check:evCheckDown(0.5,100,1,true),                  /* half the pot */
      allFold:evAggressHU({pot:100,eb:50,ocE:50,f:1,c:0,r:0,eqC:0.5,eqR:0,rho:1,flop:true,reraise:"fold",rr:0}),   /* wins the pot, bet returned */
      allCall:evAggressHU({pot:100,eb:50,ocE:50,f:0,c:1,r:0,eqC:0.6,eqR:0,rho:1,flop:true,reraise:"fold",rr:0}),   /* 0.6*200 - 50 */
      reraiseFold:evAggressHU({pot:100,eb:50,ocE:50,f:0,c:0,r:1,eqC:0,eqR:0.9,rho:1,flop:true,reraise:"fold",rr:150}), /* give up: lose the bet */
      reraiseCall:evAggressHU({pot:100,eb:50,ocE:50,f:0,c:0,r:1,eqC:0,eqR:0.9,rho:1,flop:true,reraise:"callOrFold",rr:150}), /* 0.9*(100+300) - 150 */
      mixed:evAggressHU({pot:100,eb:50,ocE:50,f:0.5,c:0.5,r:0,eqC:0.6,eqR:0,rho:1,flop:true,reraise:"fold",rr:0})};''')
    assert abs(r['call'] - 28) < 1e-9 and abs(r['callRho'] - 23.2) < 1e-9 and abs(r['check'] - 50) < 1e-9
    assert abs(r['allFold'] - 100) < 1e-9 and abs(r['allCall'] - 70) < 1e-9
    assert abs(r['reraiseFold'] + 50) < 1e-9 and abs(r['reraiseCall'] - 210) < 1e-9
    assert abs(r['mixed'] - (0.5 * 100 + 0.5 * 70)) < 1e-9

def test_rake_lowers_ev_by_the_expected_amount():
    e = engine()
    r = e.run('''T={room:{rake:{pct:0.10,cap:0,drop:0}}};var withRake=evCallPure(0.5,100,20,1,true),noFlop=evCallPure(0.5,100,20,1,false);T.room=undefined;return {w:withRake,n:noFlop,none:evCallPure(0.5,100,20,1,true)};''')
    assert abs(r['w'] - (0.5 * (120 - 12) - 20)) < 1e-9    # rake of 10% of the 120 chip pot comes out of the winner's share
    assert abs(r['n'] - r['none']) < 1e-9                  # no rake configured: no change

def test_default_analysis_is_unchanged_by_a_zero_rake_room():
    e = engine()
    def run(room):
        return e.run('''__t.spot({hero:"AhQd",board:"Ks7d2c9h4s",opps:[{arch:"station"}],pot:40,seed:5%s});var A=evAnalyze();return A.opts.map(function(o){return [o.lab,o.ev];});''' % room)
    assert run('') == run(',rake:{pct:0,cap:0,drop:0}')

def test_rake_lowers_every_option_that_can_win_the_pot():
    e = engine()
    a = e.run('''__t.spot({hero:"AhQd",board:"Ks7d2c9h4s",opps:[{arch:"station"}],pot:40,seed:5});return evAnalyze().opts.map(function(o){return [o.k,o.ev];});''')
    b = e.run('''__t.spot({hero:"AhQd",board:"Ks7d2c9h4s",opps:[{arch:"station"}],pot:40,seed:5,rake:{pct:0.10,cap:0,drop:0}});return evAnalyze().opts.map(function(o){return [o.k,o.ev];});''')
    for (k, x), (k2, y) in zip(a, b):
        assert k == k2
        if k == 'fold': assert x == y == 0
        else: assert y < x, (k, x, y)

def test_fold_is_zero_and_call_uses_the_stated_formula():
    e = engine()
    r = e.run('''__t.spot({hero:"AhQd",board:"Ks7d2c9h4s",opps:[{arch:"weekend"}],pot:60,toCall:20,seed:3});var A=evAnalyze(),f=A.opts.find(function(o){return o.k==="fold";}),c=A.opts.find(function(o){return o.k==="call";});
      return {fold:f.ev,call:c.ev,expect:evCallPure(A.eqAll,A.pot,A.toCall,1,true),odds:A.potOdds,pot:A.pot,toCall:A.toCall};''')
    assert r['pot'] == 80 and r['toCall'] == 20             # the spot's pot (60) plus the 20 bet being called
    assert r['fold'] == 0                                    # sunk chips are never a loss for folding
    assert abs(r['call'] - r['expect']) < 1e-9               # river: realization is 1, so EV is exactly eq*(pot+call)-call
    assert abs(r['odds'] - 20 / 100) < 1e-12                 # call 20 to win 100

def test_all_in_is_a_candidate_and_risks_the_whole_stack():
    e = engine()
    r = e.run('''__t.spot({hero:"AhQd",board:"Ks7d2c9h4s",opps:[{arch:"station",stack:2000}],pot:40,heroStack:300,seed:3});var A=evAnalyze();var a=A.opts.find(function(o){return o.allIn;});return {has:!!a,amt:a&&a.amt,eb:a&&a.eb};''')
    assert r['has'] and r['amt'] == 300 and r['eb'] == 300

def test_chips_the_opponent_cannot_match_are_refunded_not_risked():
    e = engine()
    r = e.run('''__t.spot({hero:"AhQd",board:"Ks7d2c9h4s",opps:[{arch:"station",stack:30}],pot:80,heroStack:500,seed:3});var A=evAnalyze();
      return A.opts.filter(function(o){return o.k==="bet";}).map(function(o){return [o.amt,o.eb];});''')
    for amt, eb in r:
        assert eb == min(amt, 30), (amt, eb)

def test_fold_frequency_does_not_fall_as_the_bet_gets_bigger():
    e = engine()
    for arch in ('station', 'nit', 'weekend', 'tag'):
        r = e.run('''__t.spot({hero:"8h8d",board:"Ks7d2c9h4s",opps:[{arch:"%s"}],pot:60,seed:3,history:[{i:1,st:3,a:"check",toCall:0,pot:60}]});var A=evAnalyze();
          return A.opts.filter(function(o){return o.k==="bet"&&!o.allIn;}).sort(function(a,b){return a.amt-b.amt;}).map(function(o){return o.fe;});''' % arch)
        assert len(r) >= 3
        assert all(r[i] <= r[i + 1] + 0.02 for i in range(len(r) - 1)), (arch, r)

def test_multiway_bluffs_work_less_often_than_heads_up():
    e = engine()
    def allfold(opps):
        return e.run('''__t.spot({hero:"Jc8c",board:"Ks7d2c9h4s",opps:[%s],pot:60,seed:3,history:[{i:1,st:3,a:"check",toCall:0,pot:60}]});var A=evAnalyze();return A.opts.find(function(o){return o.lab==="Bet 75%% pot";}).fe;''' % opps)
    hu = allfold('{arch:"weekend"}'); mw = allfold('{arch:"weekend"},{arch:"weekend"},{arch:"weekend"}')
    assert mw < hu - 0.10, (hu, mw)

def test_sizing_table_reports_price_continuing_range_and_spr():
    e = engine()
    r = e.run('''__t.spot({hero:"AhQd",board:"Ks7d2c9h4s",opps:[{arch:"weekend"}],pot:60,seed:3,history:[{i:1,st:3,a:"check",toCall:0,pot:60}]});var A=evAnalyze();
      return A.opts.filter(function(o){return o.k==="bet"&&!o.allIn;}).sort(function(a,b){return a.amt-b.amt;}).map(function(o){return {amt:o.amt,price:o.price,cont:o.cont,fe:o.fe,spr2:o.spr2};});''')
    for o in r:
        assert 0 <= o['price'] <= 0.5 and abs(o['cont'] + o['fe'] - 1) < 1e-9 and o['spr2'] >= 0
    prices = [o['price'] for o in r]; sprs = [o['spr2'] for o in r]
    assert prices == sorted(prices) and sprs == sorted(sprs, reverse=True)   # bigger bet: worse price for them, lower SPR left

def test_analysis_states_its_assumptions_and_uncertainty():
    e = engine()
    r = e.run('''__t.spot({hero:"AhQd",board:"Ks7d2c",opps:[{arch:"weekend"}],pot:20,seed:3,history:[{i:1,st:1,a:"bet",f:0.5,toCall:0,pot:20}]});var A=evAnalyze();
      return {text:A.assumptions.join(" "),se:A.eqSE,hasSE:A.opts.every(function(o){return typeof o.seBB==="number";}),horizon:A.horizon};''')
    assert 'Future betting is not modeled' in r['text'] and 'not from real people' in r['text']
    assert r['hasSE'] and r['se'] > 0 and 'realization' in r['horizon']      # flop equity is sampled, so it carries an error

def test_high_equity_does_not_always_mean_bet():
    """Against a player who only continues with better hands, a thin value hand does better checking, even with >50% raw equity."""
    e = engine()
    r = e.run('''__t.spot({hero:"KcQc",board:"Ks7d2c9h4s",opps:[{arch:"nit"}],pot:60,seed:3,history:[{i:1,st:3,a:"check",toCall:0,pot:60}]});var A=evAnalyze();
      var chk=A.opts.find(function(o){return o.k==="check";}),bet=A.opts.filter(function(o){return o.k==="bet"&&!o.allIn;}).map(function(o){return o.ev;});
      return {eq:A.eqAll,chk:chk.ev,bestBet:Math.max.apply(null,bet)};''')
    assert r['eq'] > 0.5 and r['chk'] >= r['bestBet'], r

def test_oversized_bets_are_shown_but_never_recommended():
    """The opponent response model is only built for sizes up to 2x the pot. Larger ones are flagged and never chosen,
    even when the simulated opponents (who saturate there) would make them look profitable."""
    e = engine()
    for arch in ('station', 'limper', 'nit', 'weekend', 'tag'):
        r = e.run('''__t.spot({hero:"7h2d",board:"Ks9d4c",opps:[{arch:"%s"}],pot:10,seed:3,history:[{i:1,st:1,a:"check",toCall:0,pot:10}]});var A=evAnalyze(),pot=A.pot;
          return {best:A.best.lab,bestExtrap:!!A.best.extrap,flags:A.opts.map(function(o){return [o.k,o.eb/pot>2,!!o.extrap];}),assume:A.assumptions.join(" ")};''' % arch)
        assert not r['bestExtrap'], (arch, r['best'])
        for k, over, flag in r['flags']:
            assert flag == (over and k in ('bet', 'raise')), (arch, k, over, flag)
        assert 'twice the pot' in r['assume']

def test_grading_a_huge_overbet_uses_the_nearest_modeled_size():
    e = engine()
    r = e.run('''__t.spot({hero:"7h2d",board:"Ks9d4c",opps:[{arch:"limper"}],pot:10,seed:3,history:[{i:1,st:1,a:"check",toCall:0,pot:10}]});var A=evAnalyze(),pick=evPick(A,["raise",495]);
      return {extrap:!!pick.extrap,amt:pick.amt,pot:A.pot,ratio:pick.eb/A.pot};''')
    assert not r['extrap'] and r['ratio'] <= 2

def test_a_higher_ev_oversized_bet_is_overridden_by_the_size_rule():
    """Full house against a limp-caller: the shove has the highest raw EV here (the simulated player folds almost always
    to a 50x pot bet), yet the recommendation stays inside the modeled range."""
    e = engine()
    r = e.run('''__t.spot({hero:"7h2d",board:"7c7d2s",opps:[{arch:"limper"}],pot:10,seed:3,history:[{i:1,st:1,a:"check",toCall:0,pot:10}]});var A=evAnalyze();
      var top=A.opts.slice().sort(function(x,y){return y.ev-x.ev;})[0];return {topExtrap:!!top.extrap,topEV:top.ev,bestEV:A.best.ev,bestExtrap:!!A.best.extrap,best:A.best.lab};''')
    assert r['topExtrap'] and r['topEV'] > r['bestEV'], r      # the oversized option really is the raw maximum
    assert not r['bestExtrap'], r                               # ...and is still not recommended
