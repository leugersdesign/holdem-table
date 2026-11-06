"""Equity and sampling tests.

References come from tests/fixtures/reference_equities.json, produced by exhaustive enumeration with the independent
treys evaluator (tests/make_fixtures.py). Tolerance: |app - exact| <= 4 * reported standard error + 0.002.
Equity = (wins + ties as shares of the pot) / valid trials.
"""
import math
from harness import engine, fixtures, known_failure

def _single(c): return {'combos': [c], 'w': [1], 'tot': 1}

def _eq(e, hero, board, ranges, n, seed=1):
    return e.run('seedRNG(%d);var r=eqVsRangesD(%s,%s,%s,%d);return r;' % (seed, hero, board, ranges, n))

def test_hand_vs_hand_matches_exhaustive_enumeration():
    e = engine(); fx = fixtures(); bad = []
    for sp in fx['spots']:
        n = 60000 if not sp['board'] else 30000
        rs = '[' + ','.join('{combos:[%s],w:[1],tot:1}' % str(o) for o in sp['opps']) + ']'
        r = _eq(e, str(sp['hero']), str(sp['board']), rs, n)
        tol = 4 * r['se'] + 0.002
        if abs(r['eq'] - sp['eq']) > tol: bad.append((sp['name'], round(r['eq'], 4), round(sp['eq'], 4), round(tol, 4)))
        assert r['n'] == n and r['impossible'] == 0
    assert not bad, bad

def test_multiway_ranges_match_exact_river_enumeration():
    e = engine(); fx = fixtures(); bad = []
    for sp in fx['multiway_river']:
        rs = '[' + ','.join('{combos:%s,w:%s,tot:%s}' % (str([c for c, w in r]), str([w for c, w in r]), sum(w for c, w in r)) for r in sp['ranges']) + ']'
        r = _eq(e, str(sp['hero']), str(sp['board']), rs, 60000)
        tol = 4 * r['se'] + 0.001
        if abs(r['eq'] - sp['eq']) > tol: bad.append((sp['name'], round(r['eq'] * 100, 3), round(sp['eq'] * 100, 3), round(tol * 100, 3)))
    assert not bad, bad

def test_random_opponent_equity_matches_reference():
    e = engine(); fx = fixtures(); bad = []
    for sp in fx['vs_random']:
        r = e.run('seedRNG(3);return eqRandomD(%s,[],%d,150000);' % (sp['hero'], sp['nopp']))
        tol = 4 * math.sqrt(r['se'] ** 2 + sp['se'] ** 2)
        if abs(r['eq'] - sp['eq']) > tol: bad.append((sp['name'], sp['nopp'], round(r['eq'], 4), round(sp['eq'], 4), round(tol, 4)))
    assert not bad, bad

def test_no_overlapping_cards_between_opponents_hero_or_board():
    e = engine()
    r = e.run('''seedRNG(9);var board=__t.cards("2c7d9h"),hero=__t.cards("AhKd");
      function mk(codes){var c=[],w=[];codes.forEach(function(cd){combosOfCode(cd).forEach(function(x){c.push(x);w.push(1);});});return {combos:c,w:w,tot:w.length};}
      var R=[mk(["AA","KK","AKs","AKo"]),mk(["AA","KK","AKs","AKo"]),mk(["AA","KK","QQ","AKs"])];
      EQ_TRACE=[];var out=eqVsRangesD(hero,board,R,6000);var bad=0,seenTuples=EQ_TRACE.length;
      EQ_TRACE.forEach(function(t){var u={};hero.concat(board).forEach(function(c){u[c]=1;});t.hands.forEach(function(h){h.forEach(function(c){if(u[c])bad++;u[c]=1;});});});
      EQ_TRACE=null;return {bad:bad,tuples:seenTuples,n:out.n};''')
    assert r['tuples'] == r['n'] > 0
    assert r['bad'] == 0, r

def test_no_valid_assignment_reports_zero_samples_not_a_number():
    e = engine()
    r = e.run('''seedRNG(1);var a={combos:[__t.cards("AhAs")],w:[1],tot:1},b={combos:[__t.cards("AhAd")],w:[1],tot:1};
      return eqVsRangesD(__t.cards("KcQc"),__t.cards("2c7d9h"),[a,b],500);''')
    assert r['n'] == 0 and r['impossible'] == 500 and r['eq'] == 0   # callers already treat n==0 as "no estimate"

def test_same_seed_gives_identical_results():
    e = engine()
    a = _eq(e, '[48,44]', '[2,21,36]', '[{combos:[[40,41],[32,33]],w:[1,2],tot:3}]', 5000, seed=77)
    b = _eq(e, '[48,44]', '[2,21,36]', '[{combos:[[40,41],[32,33]],w:[1,2],tot:3}]', 5000, seed=77)
    c = _eq(e, '[48,44]', '[2,21,36]', '[{combos:[[40,41],[32,33]],w:[1,2],tot:3}]', 5000, seed=78)
    assert a == b and a['eq'] != c['eq']

def test_reported_standard_error_matches_observed_spread():
    """40 independent runs: the spread of the estimates should match the standard error each run reports."""
    e = engine()
    r = e.run('''var out=[],ses=[];for(var k=0;k<40;k++){seedRNG(1000+k);var x=eqVsRangesD(__t.cards("AhKd"),__t.cards("2c7d9h"),[{combos:[__t.cards("QsQc"),__t.cards("JhTh"),__t.cards("8s8d"),__t.cards("AsQd")],w:[2,1,1,3],tot:7}],1200);out.push(x.eq);ses.push(x.se);}
      var m=out.reduce(function(a,b){return a+b;},0)/out.length,sd=Math.sqrt(out.reduce(function(a,b){return a+(b-m)*(b-m);},0)/(out.length-1)),se=ses.reduce(function(a,b){return a+b;},0)/ses.length;return {sd:sd,se:se};''')
    assert 0.7 < r['sd'] / r['se'] < 1.4, r

def test_error_shrinks_with_the_square_root_of_samples():
    e = engine()
    def se(n): return e.run('seedRNG(5);return eqVsRangesD(__t.cards("AhKd"),__t.cards("2c7d9h"),[{combos:[__t.cards("QsQc"),__t.cards("JhTh"),__t.cards("8s8d")],w:[1,1,1],tot:3}],%d).se;' % n)
    assert 0.35 < se(16000) / se(4000) < 0.70   # four times the samples, about half the error

def test_effective_sample_size_is_reported_and_bounded():
    e = engine()
    r = _eq(e, '[48,44]', '[2,21,36]', '[{combos:[[40,41],[32,33]],w:[1,2],tot:3},{combos:[[38,39],[30,31]],w:[1,1],tot:2}]', 4000)
    assert 0 < r['ess'] <= r['n'] and r['method'].startswith('sequential importance sampling')

def test_split_pot_shares_are_exact_for_two_and_three_way_ties():
    e = engine()
    two = e.run('''seedRNG(1);return eqVsRangesD(__t.cards("2h3h"),__t.cards("AsKdQhJcTs"),[{combos:[__t.cards("4c5c")],w:[1],tot:1}],200);''')
    three = e.run('''seedRNG(1);return eqVsRangesD(__t.cards("2h3h"),__t.cards("AsKdQhJcTs"),[{combos:[__t.cards("4c5c")],w:[1],tot:1},{combos:[__t.cards("6c7c")],w:[1],tot:1}],200);''')
    assert abs(two['eq'] - 0.5) < 1e-9 and abs(three['eq'] - 1 / 3) < 1e-9

def test_equity_is_not_hand_strength_percentile():
    """Same hand, same board: showdown equity against a strong range differs from the hand's percentile among all hands."""
    e = engine()
    r = e.run('''seedRNG(2);var hero=__t.cards("9h9d"),board=__t.cards("2c7d4s"),rg={combos:[__t.cards("AsKs"),__t.cards("QcQd"),__t.cards("JhJd")],w:[1,1,1],tot:3};
      return {pct:comboPct(hero,board),eq:eqVsRangesD(hero,board,[rg],4000).eq};''')
    assert abs(r['pct'] - r['eq']) > 0.05, r

def test_heavily_overlapping_ranges_match_exact_enumeration():
    """Spots chosen so that card removal between opponents matters a lot: a sampler that does not correct for it is off
    by 25 to 30 equity points here (stored as `naive` in the fixture). The app must land within 4 standard errors."""
    e = engine(); fx = fixtures(); bad = []
    assert len(fx['multiway_blockers']) >= 5
    for sp in fx['multiway_blockers']:
        assert abs(sp['naive'] - sp['eq']) > 0.20          # the fixture really discriminates
        rs = '[' + ','.join('{combos:%s,w:%s,tot:%s}' % (str([c for c, w in r]), str([w for c, w in r]), sum(w for c, w in r)) for r in sp['ranges']) + ']'
        r = _eq(e, str(sp['hero']), str(sp['board']), rs, 80000)
        tol = 4 * r['se'] + 0.002
        if abs(r['eq'] - sp['eq']) > tol: bad.append((sp['name'], round(r['eq'] * 100, 2), round(sp['eq'] * 100, 2), round(tol * 100, 2)))
    assert not bad, bad
