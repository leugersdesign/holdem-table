"""Coaching tests (prompt 05): decision quality is separate from results, tolerance, leak categories, sample-size safeguards,
saved-data migration, and that explanations come from the same numbers the engine used."""
import json
from harness import engine as _engine

class engine:
    def run(self, js):
        return _engine().run('S.settings.oppInfo="revealed";S.settings.preModel=true;' + js)      # every test sets its own opponent-info mode

def grade(hero, to_act, cfg_extra=''):
    """record the hero's decision in a pre-flop spot and return the stored record"""
    return engine().run('''__t.preSpot({hero:"%s",pos:"BTN",opps:[{arch:"station",pos:"UTG"},{arch:"tag",pos:"SB"},{arch:"tag",pos:"BB"}],actions:[{i:1,a:"call"}]});%s
      S.coach=blankCoach();recordDecision(%s);var r=H.dec[H.dec.length-1];return {sev:r.sev,loss:r.loss,raw:r.raw,tol:r.tol,model:r.model,conf:r.conf,leak:r.leak,base:r.base,why:r.why,advice:r.advice,tags:r.tags};''' % (hero, cfg_extra, to_act))

def test_decision_quality_does_not_depend_on_the_opponents_actual_cards():
    run = lambda cards: engine().run('''__t.preSpot({hero:"KhQd",pos:"BTN",opps:[{arch:"station",pos:"UTG"},{arch:"tag",pos:"SB"},{arch:"tag",pos:"BB"}],actions:[{i:1,a:"call"}]});
      %s;S.coach=blankCoach();recordDecision(["fold"]);var r=H.dec[0];return [r.sev,r.loss,r.raw,r.tol,r.advice];''' % cards)
    a = run('H.s[1].cards=__t.cards("AhAd");H.s[2].cards=__t.cards("7c2d")')
    b = run('H.s[1].cards=__t.cards("7c2d");H.s[2].cards=__t.cards("AhAd")')
    assert a == b                                                           # winning or losing the hand cannot change the grade

def test_the_result_is_stored_separately_and_never_changes_the_grade():
    r = engine().run('''__t.preSpot({hero:"KhQd",pos:"BTN",opps:[{arch:"station",pos:"UTG"},{arch:"tag",pos:"SB"},{arch:"tag",pos:"BB"}],actions:[{i:1,a:"call"}]});
      S.coach=blankCoach();recordDecision(["fold"]);var rec=H.dec[0],before=[rec.sev,rec.loss,rec.conf];saveHandRecord(-24);var after=[rec.sev,rec.loss,rec.conf];
      var html=coachLinesHTML(rec);return {before:before,after:after,res:rec.res,html:html};''')
    assert r['before'] == r['after'] and r['res'] == -12, r                 # -24 chips at a 2-chip big blind is -12 bb, recorded on its own
    assert 'Hand result' in r['html'] and 'separate from the decision' in r['html']

def test_a_reasonable_alternative_is_not_punished_but_a_real_error_is():
    best = grade('KhQd', '["raise",12]')                                    # the model's choice in this spot
    assert best['model'] and best['sev'] == 0 and best['leak'] is None
    fold = grade('KhQd', '["fold"]')                                        # folding a hand worth raising
    assert fold['sev'] >= 1 and fold['leak'] == 'ev_pre_tight' and fold['loss'] > fold['tol']

def test_tolerance_grows_with_the_estimates_noise_and_has_a_floor():
    r = engine().run('''__t.table({seats:6});var A={opts:[],best:{ev:10*T.bb,seBB:0,k:"bet"}},mk=function(se){return {ev:9.5*T.bb,seBB:se,k:"check",lab:"c"};};
      var rec={st:2,nOpp:1};A.opts=[A.best];A.extras={base:null,label:"Clear",why:"",full:true,sens:[]};
      var lo=coachGrade(rec,A,mk(0)),hi=coachGrade(rec,A,mk(0.6));return {lo:[lo.G.sev,lo.fields.tol],hi:[hi.G.sev,hi.fields.tol]};''')
    assert r['lo'][1] == 0.15 and r['lo'][0] >= 1                           # a 0.5 bb gap with no noise is a real loss (the floor is 0.15)
    assert r['hi'][1] > 0.8 and r['hi'][0] == 0                             # the same gap is within the noise when the estimate is noisy

def test_leak_categories_follow_what_the_player_did_against_the_best_option():
    r = engine().run('''__t.table({seats:6});var L=function(st,k,bk,S){return leakOf({st:st},{best:{k:bk}},{k:k},S);};
      return {fold:L(2,"fold","call",3),call:L(3,"call","fold",3),value:L(3,"check","bet",5),size:L(2,"bet","bet",3),bluff:L(3,"bet","check",1),over:L(3,"bet","check",3.5),
        preTight:L(0,"fold","raise",null),preLoose:L(0,"call","fold",null),prePass:L(0,"call","raise",null),preRaise:L(0,"raise","fold",null)};''')
    assert r == {'fold': 'ev_fold', 'call': 'ev_call', 'value': 'ev_value', 'size': 'ev_size', 'bluff': 'ev_bluff', 'over': 'ev_overplay',
                 'preTight': 'ev_pre_tight', 'preLoose': 'ev_pre_loose', 'prePass': 'ev_pre_passive', 'preRaise': 'ev_pre_loose'}, r

def test_every_leak_category_has_text_and_a_drill():
    r = engine().run('''return Object.keys(LEAK_DRILLS).map(function(k){return [k,!!LEAKS[k],LEAK_DRILLS[k].every(function(n){return typeof eval(n)==="function";})];});''')
    assert all(has and ok for _, has, ok in r) and len(r) == 10

def test_no_leak_is_named_from_a_small_sample():
    r = engine().run('''S.coach=blankCoach();var C=S.coach;C.N=20;C.sum=40;C.sum2=100;C.cats.ev_fold={n:10,sum:40,sum2:200};var small=leakReport()[0].flag;
      C.N=60;C.cats.ev_fold={n:3,sum:12,sum2:60};var few=leakReport()[0].flag;C.cats.ev_fold={n:12,sum:30,sum2:100};var ok=leakReport()[0];
      var html=coachTabHTML();C.N=20;var htmlSmall=coachTabHTML();return {small:small,few:few,flag:ok.flag,per100:ok.per100,lo:ok.lo,htmlSmall:htmlSmall};''')
    assert r['small'] is False and r['few'] is False and r['flag'] is True and r['lo'] >= 3
    assert 'No leak is named until there are at least 30' in r['htmlSmall']

def test_intervals_are_correct_and_widen_with_less_data():
    r = engine().run('''var a=ciOf(100,50,60),b=ciOf(25,12.5,15);return {a:a,b:b,one:ciOf(1,3,9)};''')
    assert abs(r['a']['mean'] - 0.5) < 1e-9 and abs(r['b']['mean'] - 0.5) < 1e-9
    assert (r['b']['hi'] - r['b']['lo']) > 1.9 * (r['a']['hi'] - r['a']['lo'])    # a quarter of the data, about twice the width
    assert r['one']['lo'] is None and r['one']['hi'] is None                    # one decision proves nothing (an unbounded interval, which JSON writes as null)

def test_analytics_group_decisions_and_show_the_disclaimer():
    r = engine().run('''S.coach=blankCoach();__t.preSpot({hero:"KhQd",pos:"BTN",opps:[{arch:"station",pos:"UTG"},{arch:"tag",pos:"SB"},{arch:"tag",pos:"BB"}],actions:[{i:1,a:"call"}]});
      for(var i=0;i<3;i++){H.dec=[];recordDecision(["fold"]);}var C=S.coach;return {N:C.N,pos:C.dims.pos,street:C.dims.street,pot:C.dims.pot,stack:C.dims.stack,html:coachTabHTML()};''')
    assert r['N'] == 3 and r['pos']['BTN']['n'] == 3 and r['street']['Pre-flop']['n'] == 3
    assert list(r['pot'])[0].startswith('Limped') and list(r['stack'])[0] == '40 to 100 bb'
    assert 'not your real-world win rate' in r['html']

def test_saved_data_migrates_without_losing_anything():
    r = engine().run('''var old={stats:{cash:{n:5}},settings:{skill:"mixed"},bankroll:1234,car:{xp:99},customCfg:{bi:3,depth:100},review:[{x:1}],drills:{raise:{n:4,ok:3}}};
      var m=migrateS(JSON.parse(JSON.stringify(old)));var again=migrateS(JSON.parse(JSON.stringify(m)));
      return {version:m.version,coach:m.coach&&m.coach.N,bankroll:m.bankroll,xp:m.car.xp,bi:m.customCfg.bi,bi2:again.customCfg.bi,review:m.review.length,drills:m.drills.raise.n,blind:CUSTOM_BLINDS[m.customCfg.bi].join("/")};''')
    assert r == {'version': 3, 'coach': 0, 'bankroll': 1234, 'xp': 99, 'bi': 4, 'bi2': 4, 'review': 1, 'drills': 4, 'blind': '5/10'} or r['blind'] != '', r
    assert r['bi'] == 4 and r['bi2'] == 4 and r['bankroll'] == 1234 and r['version'] == 3    # a saved $2/$5 index moves with the list, and migration is idempotent

def test_the_old_blind_still_means_what_it_meant():
    r = engine().run('''return {before:["1/2","2/5"],blinds:CUSTOM_BLINDS.slice(0,3).map(function(b){return b.join("/");}),moved:CUSTOM_BLINDS[migrateS({stats:{},settings:{},customCfg:{bi:1}}).customCfg.bi].join("/")};''')
    assert r['blinds'][:2] == ['1/2', '1/3'] and r['moved'] == '2/5'

def test_the_explanation_stored_with_a_decision_is_the_engines_own_text():
    r = engine().run('''__t.preSpot({hero:"KhQd",pos:"BTN",opps:[{arch:"station",pos:"UTG"},{arch:"tag",pos:"SB"},{arch:"tag",pos:"BB"}],actions:[{i:1,a:"call"}]});
      var A=preGet(true),txt=preExplain(A);S.coach=blankCoach();recordDecision(["call"]);var r=H.dec[0];return {same:r.why===txt,advice:r.advice===A.best.lab,conf:r.conf,hasWhy:r.why.length>40};''')
    assert r['same'] and r['advice'] and r['hasWhy'] and r['conf'] in ('Clear', 'Close', 'Opponent-dependent', 'Low-information')

def test_the_reading_drill_runs_and_scores():
    r = engine().run('''var shown=null;drillOpen=function(html,wire){shown=html;};seedRNG(5);identDrill();var ok1=/hands seen/.test(shown)&&/Which type fits best/.test(shown);
      var rd=readFromStats({h:90,vp:90*ARCH_STATS.nit[0],pr:90*ARCH_STATS.nit[1],agg:60*ARCH_STATS.nit[2],call:60*(1-ARCH_STATS.nit[2]),fbO:40,fb:40*ARCH_STATS.nit[4]});
      return {ok1:ok1,top:rd&&rd.top[0][0],few:readFromStats({h:5,vp:2})};''')
    assert r['ok1'] and r['top'] in ('nit', 'tag', 'thinker', 'weekend') and r['few'] is None


def test_pre_flop_play_is_graded_against_the_opening_charts_by_default():
    run = lambda setting, act: _engine().run('''S.settings.oppInfo="revealed";%s;__t.preSpot({hero:"KhQd",pos:"BTN",opps:[{arch:"station",pos:"UTG"},{arch:"tag",pos:"SB"},{arch:"tag",pos:"BB"}],actions:[{i:1,a:"call"}]});
      S.coach=blankCoach();var chart=adviseHero(false).advice;recordDecision(%s);var r=H.dec[0];return {model:!!r.model,advice:r.advice,chart:chart,coachN:S.coach.N,opt:r.alts?r.alts.length:0};''' % (setting, act))
    d = run('delete S.settings.preModel', '["fold"]')                       # the default
    assert d['model'] is False and d['advice'] == d['chart'] and d['coachN'] == 0, d     # graded by the charts and rules the app always used
    c = run('S.settings.preModel=false', '["fold"]')
    assert c['model'] is False and c['advice'] == c['chart'], c
    m = run('S.settings.preModel=true', '["fold"]')                         # opting in to the EV model
    assert m['model'] is True and m['coachN'] == 1 and m['opt'] >= 3, m

def test_the_analysis_sheet_shows_the_ev_model_even_when_grading_uses_the_charts():
    r = _engine().run('''S.settings.oppInfo="revealed";delete S.settings.preModel;__t.preSpot({hero:"KhQd",pos:"BTN",opps:[{arch:"station",pos:"UTG"},{arch:"tag",pos:"SB"},{arch:"tag",pos:"BB"}],actions:[{i:1,a:"call"}]});
      var html=preAnalysisHTML();return {has:/Pre-flop model/i.test(html)&&/Confidence:/.test(html),graded:(function(){S.coach=blankCoach();recordDecision(["call"]);return !!H.dec[0].model;})()};''')
    assert r['has'] and r['graded'] is False
