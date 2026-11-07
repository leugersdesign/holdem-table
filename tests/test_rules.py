"""Memorable rules: the hand score, seat numbers, the limped-pot rule, typical-opponent post-flop grading, and the price math."""
from harness import engine as _engine

def run(js, pre_model=False, post='typical'):
    return _engine().run('S.settings.oppInfo="revealed";S.settings.preModel=%s;S.settings.postGrade="%s";' % ('true' if pre_model else 'false', post) + js)

def test_hand_scores_match_the_chen_formula():
    r = run('return ["AA","AKs","AKo","KQs","JTs","76s","A5s","22","T9o","72o","54s","QJo"].map(chenScore);')
    assert r == [20, 12, 10, 10, 9, 7, 7, 5, 6, -1, 6, 7]

def test_one_score_and_a_seat_number_reproduce_the_opening_charts():
    r = run('''var out={},w=function(c){return c.length===2?6:c[2]==="s"?4:12;};
      [["9",SETS9,SEAT9,["UTG","UTG1","UTG2","MP","HJ","CO","BTN","SB"]],["6",SETS,SEAT6,Object.keys(SETS)]].forEach(function(g){g[3].forEach(function(pos){var S=g[1][pos];if(!S)return;var a=0,t=0;
        Object.keys(EQ).forEach(function(c){t+=w(c);if(!!S[c]===(chenScore(c)>=g[2][pos]))a+=w(c);});out[g[0]+" "+pos]=a/t;});});return out;''')
    assert len(r) >= 12 and min(r.values()) >= 0.90, r                      # at least 90% of hand combos at every seat, for both table sizes

def test_the_limped_pot_rule():
    r = run('''T=T||{};var live=T.live;T.live=true;var L=function(c,p,k){return limpRule(c,p,k).adv;};var out={
      btnAJo:L("AJo","BTN",1),btn22:L("22","BTN",1),btn72o:L("72o","BTN",1),mpKQo:L("KQo","MP",1),mp22one:L("22","MP",1),mp22two:L("22","MP",2),
      coKQo3:L("KQo","CO",3),coQ9o3:L("Q9o","CO",3),sb76s:L("76s","SB",1),sbT4s:L("T4s","SB",1),btnA4s:L("A4s","BTN",3),hjK9o:L("K9o","HJ",1)};T.live=live;return out;''')
    assert r == {'btnAJo': 'Raise', 'btn22': 'Raise', 'btn72o': 'Fold', 'mpKQo': 'Raise', 'mp22one': 'Call', 'mp22two': 'Call',
                 'coKQo3': 'Raise', 'coQ9o3': 'Fold', 'sb76s': 'Raise', 'sbT4s': 'Fold', 'btnA4s': 'Raise', 'hjK9o': 'Fold'}, r      # computed from the rule as stated

def test_the_course_lessons_and_the_limp_drill_use_the_same_rule():
    r = run('''__t.table({seats:9});T.live=true;var bad=[];["UTG","MP","HJ","CO","BTN","SB"].forEach(function(p){[1,2,3].forEach(function(n){Object.keys(EQ).forEach(function(c){
        var a=isoDecide(c,p,n),r=limpRule(c,p,n,SEAT9[p]).adv,m=r==="Raise"?"Raise":r==="Call"?(p==="SB"?"Complete":"Limp behind"):"Fold";if(a!==m)bad.push([c,p,n,a,m]);});});});
      return {bad:bad.slice(0,5),n:bad.length,k9s:isoDecide("K9s","UTG",1)};''')
    assert r['n'] == 0 and r['k9s'] == 'Limp behind', r

def spot_limped(hero, pos, k):
    order = ['UTG', 'UTG1', 'MP', 'HJ', 'CO', 'BTN']
    i = order.index(pos) if pos in order else 6
    limpers = order[max(0, i - k):i] if pos in order else order[-k:]
    opps = ','.join('{arch:"limper",pos:"%s"}' % p for p in limpers) + ',{arch:"tag",pos:"BB"}' + (',{arch:"tag",pos:"SB"}' if pos != 'SB' else '')
    acts = ','.join('{i:%d,a:"call"}' % (j + 1) for j in range(len(limpers)))
    return '__t.preSpot({hero:"%s",pos:"%s",opps:[%s],actions:[%s]});T.live=true;' % (hero, pos, opps, acts)

def test_limped_pot_advice_and_grading_use_the_rule_and_opens_still_use_the_charts():
    r = run(spot_limped('2h2d', 'MP', 1) + '''var a=adviseHero(false).advice,rule=limpRule("22","MP",limpersIn()).adv;S.coach=blankCoach();recordDecision(["call"]);var g=H.dec[0];
      return {advice:a,rule:rule,graded:g.advice,sev:g.sev,model:!!g.model,limpers:limpersIn()};''')
    assert r['limpers'] == 1 and r['rule'] == 'Call' and r['advice'] == 'Call' and r['graded'] == 'Call' and r['sev'] == 0 and r['model'] is False, r
    r2 = run(spot_limped('Ah9d', 'BTN', 1) + 'S.coach=blankCoach();recordDecision(["fold"]);var g=H.dec[0];return {advice:g.advice,best:g.best};')
    assert r2['advice'] == 'Raise' and r2['best'] is False, r2
    r3 = run('__t.preSpot({hero:"AhKd",pos:"CO",opps:[{arch:"tag",pos:"BTN"},{arch:"tag",pos:"SB"},{arch:"tag",pos:"BB"}],actions:[]});return {limpers:limpersIn(),advice:adviseHero(false).advice,why:adviseHero(false).why};')
    assert r3['limpers'] == 0 and r3['advice'] == 'Raise' and 'opening chart' in r3['why'], r3

def test_post_flop_is_graded_against_a_typical_opponent_by_default_and_against_the_read_when_chosen():
    js = '__t.spot({hero:"KhJd",board:"Ks7d2c9h4s",opps:[{arch:"station"}],pot:40,seed:5});S.coach=blankCoach();H.dec=[];recordDecision(["check"]);var g=H.dec[0],A=evGet(true),X=stratExtras(A,true);return {advice:g.advice,typical:X.base.best,read:A.best.lab,vs:g.gradedVs,math:g.math||""};'
    t = run(js)
    assert t['vs'] == 'typical' and t['advice'] == t['typical'] and t['math'].startswith('The math:'), t
    rd = run(js, post='read')
    assert rd['vs'] == 'read' and rd['advice'] == rd['read'], rd

def test_the_price_math_is_exact():
    r = run('return {call:priceLine(117,29,0.4,0),bet:priceLine(40,0,0.6,20),none:priceLine(40,0,0.6,0)};')
    assert 'needs you to win 20% of the time' in r['call'] and 'keep about 75% of their range' in r['call'] and 'about 40%' in r['call'] and 'above the price' in r['call']
    assert 'fold more than 33% of the time' in r['bet'] and 'about 60%' in r['bet']
    assert r['none'] == 'The math: your equity against their likely range is about 60%.'

def test_the_rules_card_teaches_all_of_it():
    h = run('return rulesCardHTML();')
    for s in ('Chen formula', 'Seat numbers', '9-handed', 'With limpers in front of you', 'Limp behind', 'not a solver result', 'The price after the flop', '29%'):
        assert s in h, s

def test_non_live_tables_use_the_rule_too_with_six_handed_seat_numbers():
    r = run('''__t.preSpot({hero:"KhJd",pos:"CO",opps:[{arch:"limper",pos:"MP"},{arch:"tag",pos:"SB"},{arch:"tag",pos:"BB"}],actions:[{i:1,a:"call"}]});T.live=false;
      return {advice:adviseHero(false).advice,rule:limpRule("KJo","CO",1).adv,seat:seatNum("CO"),score:chenScore("KJo"),
        trash:(function(){H.s[0].cards=__t.cards("9h4d");return adviseHero(false).advice;})(),pair:(function(){H.s[0].cards=__t.cards("3h3d");return adviseHero(false).advice;})()};''')
    assert r['seat'] == 6 and r['score'] == 7 and r['rule'] == 'Raise' and r['advice'] == 'Raise', r
    assert r['trash'] == 'Fold' and r['pair'] == 'Call', r

def test_the_analysis_sheet_states_the_limped_pot_rule():
    r = run(spot_limped('Kh9h', 'UTG1', 1) + 'return {html:preAnalysisHTML(),rule:limpRule("K9s","UTG1",1).adv};')
    assert 'Your limped-pot rule says: limp behind' in r['html'] and r['rule'] == 'Call', r['rule']
