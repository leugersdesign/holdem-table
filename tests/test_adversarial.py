"""Adversarial recommendation and coaching tests (prompt 07). Each spot is built so that an obvious-but-wrong rule would fail it."""
import json, re
from harness import engine as _engine
from test_strategy import post, pre, call_ev, BARREL

class engine:
    def run(self, js):
        return _engine().run('S.settings.oppInfo="revealed";S.settings.preModel=true;' + js)

def ev(r, k, only_ok=True):
    return [o['bb'] for o in r['opts'] if o['k'] == k and not o.get('extrap')]

def test_high_raw_equity_does_not_make_a_bet_profitable():
    r = post(dict(hero='KhJd', board='Ks7d2c9h4s', opps=[{'arch': 'maniac'}], pot=40, seed=5))
    assert r['eq'] > 0.8 and r['bestK'] == 'check'                           # a strong hand that should check to a maniac who bets for you
    assert [o for o in r['opts'] if o['k'] == 'check'][0]['bb'] > max(ev(r, 'bet'))

def test_a_bluff_is_profitable_despite_low_showdown_equity():
    r = post(dict(hero='Jc8c', board='Ks7d2c', opps=[{'arch': 'weekend'}], pot=20, seed=5))
    chk = [o for o in r['opts'] if o['k'] == 'check'][0]['bb']
    assert r['eq'] < 0.4 and r['bestK'] == 'bet' and max(ev(r, 'bet')) > chk + 1

def test_a_small_bet_beats_a_large_one_when_the_big_bet_only_folds_out_worse_hands():
    r = post(dict(hero='Jc8c', board='Ks7d2c', opps=[{'arch': 'weekend'}, {'arch': 'weekend'}], pot=30, seed=5))
    by = {o['lab']: o['bb'] for o in r['opts']}
    assert by['Bet 33% pot'] > by['Bet 100% pot'] + 1 and by['Bet 33% pot'] > by['Bet 75% pot']

def test_a_call_is_profitable_against_one_range_and_not_another():
    run = lambda arch: post(dict(hero='KhJd', board='Ks7d2c9h4s', opps=[{'arch': arch}], pot=117, toCall=29, seed=5, history=BARREL))
    assert call_ev(run('maniac')) > 5 and call_ev(run('tag')) < -2

def test_one_observation_does_not_justify_an_exploit():
    r = engine().run('''__t.spot({hero:"KhJd",board:"Ks7d2c9h4s",opps:[{arch:"station"}],pot:40,seed:5});S.settings.oppInfo="observed";var nm=T.players[1].name,run=function(h){T.hud={};if(h)T.hud[nm]={h:h,vp:Math.round(h*0.04),pr:Math.round(h*0.04),agg:Math.round(h*0.5),call:Math.round(h*0.1),fbO:Math.round(h*0.3),fb:Math.round(h*0.3)};
        H._ar={};H.evA=null;RESP_MEMO={};seedRNG(5);var A=evAnalyze();return {key:modelKeyP(T.players[1]),best:A.best.lab,evs:A.opts.map(function(o){return Math.round(o.ev*100)/100;})};};
      return {none:run(0),three:run(3),eleven:run(11),many:run(200)};''')
    assert r['three'] == r['none'] and r['eleven'] == r['none']             # up to 11 hands of very odd stats change nothing: no read exists yet
    assert r['many']['key'] != r['none']['key']                              # with a real sample the estimate does move

def test_similar_ev_options_get_monotonic_grades_and_the_best_option_is_never_penalized():
    spots = ['{hero:"KhJd",board:"Ks7d2c9h4s",opps:[{arch:"weekend"}],pot:40,seed:5}', '{hero:"Jc8c",board:"Ks7d2c",opps:[{arch:"weekend"}],pot:20,seed:5}',
             '{hero:"AhKd",board:"Ks7d2c",opps:[{arch:"station"}],pot:20,seed:5}', '{hero:"QhQd",board:"Ks7d2c9h",opps:[{arch:"tag"}],pot:30,seed:5}']
    for sp in spots:
        r = engine().run('''__t.spot(%s);var A=evGet(true),rows=A.opts.filter(function(o){return !o.extrap;}).map(function(o){var rec={st:H.street,nOpp:1},g=coachGrade(rec,A,o);return {lab:o.lab,ev:o.ev/T.bb,sev:g.G.sev,raw:g.fields.raw,tol:g.fields.tol,best:o===A.best};});return rows;''' % sp)
        r.sort(key=lambda x: -x['ev'])
        sevs = [x['sev'] for x in r]
        assert sevs == sorted(sevs), (sp, r)                                  # worse EV never gets a better grade
        assert r[0]['sev'] == 0 and all(x['sev'] == 0 for x in r if x['raw'] < x['tol']), (sp, r)

def test_explanations_only_state_numbers_the_calculation_produced():
    spots = ['__t.preSpot({hero:"KhQd",pos:"BTN",opps:[{arch:"station",pos:"UTG"},{arch:"tag",pos:"SB"},{arch:"tag",pos:"BB"}],actions:[{i:1,a:"call"}]});var A=preAnalyze(),txt=preExplain(A);',
             '__t.preSpot({hero:"KhJd",pos:"BB",opps:[{arch:"tag",pos:"UTG"},{arch:"nit",pos:"SB"}],actions:[{i:1,a:"raise",to:6}]});var A=preAnalyze(),txt=preExplain(A);',
             '__t.preSpot({hero:"As5s",pos:"BTN",opps:[{arch:"nit",pos:"CO"},{arch:"tag",pos:"SB"},{arch:"tag",pos:"BB"}],actions:[{i:1,a:"raise",to:3}]});var A=preAnalyze(),txt=preExplain(A);',
             '__t.spot({hero:"Jc8c",board:"Ks7d2c",opps:[{arch:"weekend"}],pot:20,seed:5});var A=evAnalyze(),txt=evExplain(A);',
             '__t.spot({hero:"KhJd",board:"Ks7d2c9h4s",opps:[{arch:"nit"}],pot:40,seed:5});var A=evAnalyze(),txt=evExplain(A);',
             '__t.spot({hero:"KhJd",board:"Ks7d2c9h4s",opps:[{arch:"maniac"}],pot:117,toCall:29,seed:5,history:%s});var A=evAnalyze(),txt=evExplain(A);' % json.dumps(BARREL)]
    for sp in spots:
        r = engine().run(sp + '''var nums={};function add(x){if(typeof x==="number"&&isFinite(x)){nums[Math.round(x*100)]=1;nums[Math.round((1-x)*100)]=1;}}
          add(A.eqAll);add(A.potOdds);add(A.eqRand);A.opts.forEach(function(o){add(o.fe);add(o.cont);add(o.eqC);add(o.price);add(o.pr4);add(o.pc);add(o.eqB);add(o.callP);});
          return {txt:txt,nums:Object.keys(nums).map(Number)};''')
        pcts = [int(x) for x in re.findall(r'(\d+)%', re.sub(r'\d+% pot', '', r['txt']))]      # a bet-size label such as '50% pot' is a definition, not a computed probability
        bad = [p for p in pcts if p not in r['nums']]
        assert not bad, (r['txt'], bad, sorted(r['nums']))

def test_a_won_hand_with_a_bad_decision_and_a_lost_hand_with_a_good_one_are_graded_on_the_decision():
    def play(act, net):
        return engine().run('''__t.preSpot({hero:"KhQd",pos:"BTN",opps:[{arch:"station",pos:"UTG"},{arch:"tag",pos:"SB"},{arch:"tag",pos:"BB"}],actions:[{i:1,a:"call"}]});S.coach=blankCoach();
          recordDecision(%s);var rec=H.dec[0];H.done=false;saveHandRecord(%d);return {sev:rec.sev,res:rec.res,html:coachLinesHTML(rec),leak:rec.leak};''' % (act, net))
    bad_won = play('["fold"]', 100)                                         # folded a hand worth raising, and the table happened to hand the hero chips anyway
    good_lost = play('["raise",12]', -60)                                   # raised, and lost
    assert bad_won['sev'] >= 1 and bad_won['res'] == 50 and 'Hand result:</b> +50' in bad_won['html'] and bad_won['leak'] == 'ev_pre_tight'
    assert good_lost['sev'] == 0 and good_lost['res'] == -30 and 'Hand result:</b> -30' in good_lost['html'] and good_lost['leak'] is None

def test_twenty_nine_bad_decisions_do_not_make_a_leak_but_thirty_can():
    r = engine().run('''S.coach=blankCoach();var C=S.coach;C.N=29;C.sum=29*2;C.sum2=29*5;C.cats.ev_fold={n:20,sum:58,sum2:160};var a=leakReport()[0].flag;
      C.N=30;C.sum=60;C.sum2=150;C.cats.ev_fold={n:20,sum:60,sum2:160};var b=leakReport()[0];return {a:a,b:b.flag,per100:b.per100,lo:b.lo};''')
    assert r['a'] is False and r['b'] is True and r['lo'] >= 3

def test_a_choice_that_fails_to_adjust_and_one_that_adjusts_are_told_apart():
    r = engine().run('''__t.table({seats:6});var bb=T.bb,real=altView,Ab={opts:[{lab:"Check",k:"check",ev:9*bb,seBB:0.1},{lab:"Bet 100% pot",k:"bet",ev:6*bb,seBB:0.1}]};Ab.best=Ab.opts[0];
      altView=function(A,k){return {key:k,best:Ab.best.lab,A:Ab,differs:true,gap:3};};
      var mk=function(){var A={opts:[{lab:"Check",k:"check",ev:8*bb,seBB:0.1},{lab:"Bet 100% pot",k:"bet",ev:9*bb,seBB:0.1}],opps:[]};A.best=A.opts[1];return A;};
      var out={};try{var A1=mk(),g1=coachGrade({st:3,nOpp:1},A1,A1.opts[1]);var A2=mk(),g2=coachGrade({st:3,nOpp:1},A2,A2.opts[0]);
        out={adapt:g1.fields.tags,adaptSev:g1.G.sev,baseLossAdapt:g1.fields.base,noadj:g2.fields.tags,noadjSev:g2.G.sev,baseLossNo:g2.fields.base};}finally{altView=real;}return out;''')
    assert 'good_adjust' in r['adapt'] and r['adaptSev'] == 0 and r['baseLossAdapt'] >= 2          # fine against this player, a mistake against a typical one
    assert 'no_adjust' in r['noadj'] and r['noadjSev'] >= 1 and r['baseLossNo'] == 0               # fine against a typical player, but this player called for more
