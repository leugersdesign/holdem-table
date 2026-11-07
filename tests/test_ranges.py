"""Opponent range model: prior, likelihood, posterior.

posterior(hand) is proportional to prior(hand) * product over the player's actions of P(action | hand, context).
These tests check the structure (normalization, card removal, identity, underflow, collapse) and the direction of
the evidence (bigger bets and raises shift weight toward strong hands, more for players who size by strength).
"""
from harness import engine, known_failure

SPOT = '{hero:"AhQd",board:"Ks7d2c",opps:[{arch:"%s"}],pot:20,history:%s}'
def bet(f): return '[{i:1,st:1,a:"bet",f:%s,toCall:0,pot:20}]' % f

def _post(arch, hist, extra=''):
    e = engine()
    return e.run('''__t.spot({hero:"AhQd",board:"Ks7d2c",opps:[{arch:"%s"}],pot:20,history:%s%s});var r=rangePosterior(1);var m=rangeMix(r);return {strong:m.strong,pair:m.pair,air:m.air,beats:m.beats,tot:r.tot,n:r.combos.length,collapsed:r.collapsed};''' % (arch, hist, extra))

def test_posterior_is_normalized_finite_and_card_removed():
    e = engine()
    r = e.run('''__t.spot({hero:"AhQd",board:"Ks7d2c",opps:[{arch:"station"}],pot:20,history:[{i:1,st:1,a:"bet",f:0.66,toCall:0,pot:20}]});
      var R=rangePosterior(1),dead={};H.s[0].cards.concat(H.board).forEach(function(c){dead[c]=1;});
      var s=0,bad=0,neg=0,dup=0;R.w.forEach(function(w,k){if(!isFinite(w))bad++;if(w<0)neg++;s+=w;if(dead[R.combos[k][0]]||dead[R.combos[k][1]])dup++;});
      return {sum:s,tot:R.tot,bad:bad,neg:neg,dead:dup,n:R.combos.length};''')
    assert r['bad'] == 0 and r['neg'] == 0 and r['dead'] == 0 and r['n'] > 100
    assert abs(r['sum'] - r['tot']) < 1e-9 * max(1, r['tot'])

def test_posterior_equals_prior_times_likelihood():
    """Prior, likelihood, and posterior stay separate: post[k] / (prior[k] * exp(loglik[k])) is one constant."""
    e = engine()
    r = e.run('''__t.spot({hero:"AhQd",board:"Ks7d2c",opps:[{arch:"weekend"}],pot:20,history:[{i:1,st:1,a:"bet",f:0.5,toCall:0,pot:20},{i:1,st:1,a:"bet",f:0.5,toCall:0,pot:20}]});
      var R=rangePosterior(1),ratios=[];for(var k=0;k<R.w.length;k+=7){if(R.prior[k]>0&&R.ll[k]>-50)ratios.push(R.w[k]/(R.prior[k]*Math.exp(R.ll[k])));}
      var mn=Math.min.apply(null,ratios),mx=Math.max.apply(null,ratios);return {rel:(mx-mn)/mx,n:ratios.length};''')
    assert r['n'] > 20 and r['rel'] < 1e-9, r

def test_evidence_changes_the_range():
    e = engine()
    r = e.run('''__t.spot({hero:"AhQd",board:"Ks7d2c",opps:[{arch:"tag"}],pot:20,history:[{i:1,st:1,a:"bet",f:0.66,toCall:0,pot:20}]});
      var R=rangePosterior(1),dist=0,tp=0,tw=0;R.w.forEach(function(w,k){tw+=w;tp+=R.prior[k];});R.w.forEach(function(w,k){dist+=Math.abs(w/tw-R.prior[k]/tp);});return {dist:dist};''')
    assert r['dist'] > 0.10, r   # total-variation scale: a flop bet must move the range

def test_long_action_sequences_do_not_underflow():
    e = engine()
    hist = '[' + ','.join('{i:1,st:3,a:"raise",toCall:%d,pot:%d,raises:1}' % (10 + 5 * k, 40 + 10 * k) for k in range(14)) + ']'
    r = e.run('''__t.spot({hero:"AhQd",board:"Ks7d2c9h4s",opps:[{arch:"nit"}],pot:40,history:%s});
      var R=rangePosterior(1),bad=0;R.w.forEach(function(w){if(!isFinite(w)||w<0)bad++;});return {tot:R.tot,bad:bad,collapsed:R.collapsed};''' % hist)
    assert r['bad'] == 0 and r['tot'] > 0 and not r['collapsed'], r

def test_collapsed_posterior_falls_back_to_the_prior():
    e = engine()
    r = e.run('''__t.spot({hero:"AhQd",board:"Ks7d2c",opps:[{arch:"tag"}],pot:20,history:[{i:1,st:1,a:"bet",f:0.5,toCall:0,pot:20}]});
      var keep=rangeLogLik;rangeLogLik=function(i,c){var ll=new Float64Array(c.length);for(var k=0;k<ll.length;k++)ll[k]=-Infinity;return {ll:ll,hist:[]};};H._ar={};
      var R=rangePosterior(1);rangeLogLik=keep;var same=R.w.every(function(w,k){return w===R.prior[k];});return {collapsed:R.collapsed,same:same,tot:R.tot};''')
    assert r['collapsed'] and r['same'] and r['tot'] > 0

def test_preflop_action_sets_the_prior():
    """A pre-flop 3-bettor holds a clearly stronger prior range than an opener or a limper.
    (Open vs limp is not asserted: it depends on how rarely each simulated type limps, and sparse cells are shrunk toward the pooled fit.)"""
    e = engine()
    def strength(pre):
        vpos = 'BTN' if pre == '3bet' else 'CO'
        return e.run('''__t.spot({hero:"AhQd",board:"Ks7d2c",opps:[{arch:"weekend"}],pot:20,pre:"%s",vpos:"%s",history:[]});
          var R=priorRange(1),s=0,t=0;R.combos.forEach(function(c,k){s+=R.w[k]*EQ[codeOf(c)];t+=R.w[k];});return s/t;''' % (pre, vpos))
    lim, opn, three = strength('limp'), strength('open'), strength('3bet')
    assert three > opn + 5.0 and three > lim + 5.0, (lim, opn, three)   # a 3-bet range is clearly the strongest

def test_raise_shifts_weight_toward_strong_hands_more_than_a_check():
    """Population level: averaged over 40 individuals of a type, a raise leaves a much stronger range than a bet, and a bet a
    stronger one than a check. Individuals differ (a heavy slow-player checks strong hands, a heavy c-bettor bets many weak
    ones), so a single seeded individual can invert bet vs check; the average over individuals must not."""
    e = engine()
    hist = {'check': '[{i:1,st:1,a:"check",toCall:0,pot:20}]', 'bet': '[{i:1,st:1,a:"bet",f:0.66,toCall:0,pot:20}]',
            'raise': '[{i:1,st:1,a:"raise",toCall:10,pot:30,raises:1}]'}
    for arch in ('weekend', 'tag', 'station', 'nit'):
        m = {}
        for name, h in hist.items():
            xs = e.run('''var o=[];for(var k=1;k<=40;k++){__t.spot({hero:"AhQd",board:"Ks7d2c",opps:[{arch:"%s"}],pot:20,seed:k,history:%s});o.push(rangeMix(rangePosterior(1)).strong);}return o;''' % (arch, h))
            m[name] = sum(xs) / len(xs)
        assert m['raise'] > m['bet'] + 0.3 and m['bet'] > m['check'] + 0.015, (arch, m)

def test_bigger_bets_mean_stronger_hands_for_every_player_type():
    """Direction check across all profiles: a pot-size bet leaves a stronger range than a 30% bet."""
    for arch in ('station', 'limper', 'nit', 'tag', 'weekend', 'maniac', 'lag', 'shark', 'whale'):
        big = _post(arch, bet(1.0))['strong']; small = _post(arch, bet(0.3))['strong']
        assert big > small + 0.05, (arch, big, small)

def test_size_carries_no_information_when_size_ignores_hand_strength():
    """A player whose sizing is pure habit (honesty 0) gives the same size odds for every hand strength.
    A player who sizes by strength (honesty 1) does not."""
    e = engine()
    r = e.run('''var P={k:"tag",honest:0,sizing:"std",tilted:false},Q={k:"tag",honest:1,sizing:"std",tilted:false},w={habit:0,honest:0};
      ["value","cbet","bluff","draw","probe"].forEach(function(kind){[2,4.5,7].forEach(function(S){var a=sizeProbs(P,S,kind),b=sizeProbs(P,0,"probe"),c=sizeProbs(Q,S,kind),d=sizeProbs(Q,0,"probe");
        for(var q=0;q<4;q++){w.habit=Math.max(w.habit,Math.abs(a[q]-b[q]));w.honest=Math.max(w.honest,Math.abs(c[q]-d[q]));}});});return w;''')
    assert r['habit'] < 1e-9, r
    assert r['honest'] > 0.5, r

def test_size_probabilities_are_proper_distributions():
    e = engine()
    r = e.run('''var worst=0;[ "station","lag","maniac","nit","shark","whale" ].forEach(function(k){var P=liveProf({arch:k,skill:ARCH[k].skill,st:ARCH[k].st,name:"x"});
      [0,2,4.5,6,8].forEach(function(S){["value","cbet","bluff","draw","probe"].forEach(function(kind){var p=sizeProbs(P,S,kind),s=p[0]+p[1]+p[2]+p[3];worst=Math.max(worst,Math.abs(s-1));});});});return {worst:worst};''')
    assert r['worst'] < 1e-9, r

def test_likelihood_of_a_bet_accounts_for_the_size_actually_bet():
    e = engine()
    r = e.run('''__t.spot({hero:"AhQd",board:"Ks7d2c",opps:[{arch:"station"}],pot:20,history:[]});
      var P=liveProfAt(1),hi={S:7,outs:0},ev=function(f){return liveLikeHi(P,{a:"bet",st:1,toCall:0,pot:20,nOpp:1,raises:0,f:f},hi,true,0);};
      return {big:ev(1.0),small:ev(0.3),none:liveLikeHi(P,{a:"bet",st:1,toCall:0,pot:20,nOpp:1,raises:0},hi,true,0)};''')
    assert r['big'] > 3 * r['small'], r      # a strong hand from this player almost always bets big
