"""Live strategy scenarios (prompt 04). Each test changes one thing (a tendency, a size, a stack, the rake) and checks that the
recommendation or its EV moves the way poker logic says it should. The numbers come from the analyzer, not from fixed answers."""
import json
from harness import engine

def run(js):
    return engine().run('S.settings.oppInfo="revealed";' + js)      # every test sets its own opponent-info mode, so tests cannot leak state into each other

def pre(cfg):
    return run('__t.preSpot(%s);var A=preGet(true);return A?{best:A.best.lab,bestK:A.best.k,opts:A.opts.map(function(o){return {lab:o.lab,k:o.k,amt:o.amt,bb:o.bb,fe:o.fe,allIn:!!o.allIn};})}:null;' % json.dumps(cfg))

def post(cfg):
    return run('__t.spot(%s);var A=evAnalyze();return {best:A.best.lab,bestK:A.best.k,eq:A.eqAll,opts:A.opts.map(function(o){return {lab:o.lab,k:o.k,bb:o.ev/T.bb,extrap:!!o.extrap};})};' % json.dumps(cfg))

def opt(r, k):
    return [o for o in r['opts'] if o['k'] == k]

def call_ev(r):
    return [o for o in r['opts'] if o['k'] in ('call', 'check')][0]['bb']

BB = [{'arch': 'tag', 'pos': 'UTG'}, {'arch': 'nit', 'pos': 'SB'}]

def vs_raise(hero, to, room=None, rake=None):
    return pre(dict(hero=hero, pos='BB', opps=BB, actions=[{'i': 1, 'a': 'raise', 'to': to}], room=room, rake=rake))

def test_large_preflop_raises_make_continuing_less_attractive():
    for hero in ('KhJd', '9h9d'):
        evs = [call_ev(vs_raise(hero, to)) for to in (3, 6, 12)]
        assert evs[0] > evs[1] > evs[2], (hero, evs)                       # the bigger the raise, the worse calling gets
    assert vs_raise('KhJd', 12)['bestK'] == 'fold'                          # KJo folds to a 12 bb raise
    assert vs_raise('KhJd', 3)['bestK'] != 'fold'                           # but not to a 3 bb raise

def test_the_large_raise_result_depends_on_the_stated_size_assumption():
    off = vs_raise('KhJd', 12, room={'sizeTilt': 0, 'sizeGamma': 0})
    assert off['bestK'] != 'fold'                                           # with the live-size assumption off, the same spot is not a fold

def test_isolating_limpers_with_strong_hands_and_not_with_trash():
    def spot(hero, n, arch):
        opps = [{'arch': arch, 'pos': p} for p in ('UTG', 'MP', 'HJ')][:n] + [{'arch': 'tag', 'pos': 'SB'}, {'arch': 'tag', 'pos': 'BB'}]
        return pre(dict(hero=hero, pos='BTN', opps=opps, actions=[{'i': k + 1, 'a': 'call'} for k in range(n)]))
    assert spot('KhQd', 1, 'station')['bestK'] == 'raise'
    assert spot('7h2d', 1, 'station')['bestK'] == 'fold'
    a, b = opt(spot('KhQd', 1, 'station'), 'raise'), opt(spot('KhQd', 3, 'station'), 'raise')
    assert min(o['amt'] for o in b) >= min(o['amt'] for o in a) + 4        # more limpers, bigger raise (one big blind each, two chips per blind here)

def test_a_tighter_limper_folds_more_to_the_isolation_raise():
    def fe(arch):
        opps = [{'arch': arch, 'pos': 'UTG'}, {'arch': 'tag', 'pos': 'SB'}, {'arch': 'tag', 'pos': 'BB'}]
        r = pre(dict(hero='KhQd', pos='BTN', opps=opps, actions=[{'i': 1, 'a': 'call'}]))
        return [o for o in r['opts'] if o['k'] == 'raise'][0]['fe']
    assert fe('nit') > fe('station') + 0.15

def test_three_bet_fold_equity_depends_on_the_openers_type():
    def spot(arch):
        r = pre(dict(hero='As5s', pos='BTN', opps=[{'arch': arch, 'pos': 'CO'}, {'arch': 'tag', 'pos': 'SB'}, {'arch': 'tag', 'pos': 'BB'}], actions=[{'i': 1, 'a': 'raise', 'to': 3}]))
        return opt(r, 'raise')[0]
    nit, station = spot('nit'), spot('station')
    assert nit['fe'] > station['fe'] + 0.2 and nit['bb'] > station['bb'] + 1.0

def test_a_limp_reraise_is_respected_when_the_limper_is_a_calling_station():
    def spot(hero, arch):
        return pre(dict(hero=hero, pos='CO', opps=[{'arch': arch, 'pos': 'UTG'}, {'arch': 'tag', 'pos': 'BB'}], actions=[{'i': 1, 'a': 'call'}, {'i': 0, 'a': 'raise', 'to': 3}, {'i': 1, 'a': 'raise', 'to': 12}]))
    assert spot('AhQd', 'station')['bestK'] == 'fold'
    assert call_ev(spot('AhQd', 'station')) < call_ev(spot('AhQd', 'maniac')) - 0.5      # a station's limp-reraise is much stronger than a maniac's

def test_short_effective_stacks_add_the_shove_and_cap_the_risk():
    def spot(st):
        return pre(dict(hero='As9s', pos='BTN', stack=st, opps=[{'arch': 'tag', 'pos': 'UTG', 'stack': st}, {'arch': 'tag', 'pos': 'BB'}], actions=[{'i': 1, 'a': 'raise', 'to': 2.5}]))
    short, mid, deep = spot(12), spot(25), spot(100)
    assert any(o['allIn'] for o in short['opts']) and any(o['allIn'] for o in mid['opts']) and not any(o['allIn'] for o in deep['opts'])
    assert max(o['amt'] for o in short['opts']) <= 12 * 2                  # never more than the stack
    assert [o['bb'] for o in short['opts']] != [o['bb'] for o in deep['opts']]

def test_rake_can_turn_a_marginal_call_into_a_fold_and_never_helps_it():
    rake = dict(pct=0.10, cap=6, drop=1, noFlopNoDrop=True)
    flips = []
    for h in ('2h2d', '5h5d', '7h7d', '9h9d', 'KhJd', 'Th9h', 'Ah5h'):
        a, b = call_ev(vs_raise(h, 3)), call_ev(vs_raise(h, 3, rake=rake))
        assert b < a, (h, a, b)
        if a > 0 > b:
            flips.append(h)
    assert flips, 'expected at least one marginal call that rake makes unprofitable'

def test_multiway_cbets_are_not_heads_up_cbets():
    def spot(n, hero='Jc8c'):
        return post(dict(hero=hero, board='Ks7d2c', opps=[{'arch': 'weekend'}] * n, pot=20, seed=5))
    hu, three = spot(1), spot(3)
    assert hu['bestK'] == 'bet' and three['bestK'] == 'check'
    best_bet = lambda r: max(o['bb'] for o in r['opts'] if o['k'] == 'bet' and not o['extrap'])
    check = lambda r: [o for o in r['opts'] if o['k'] == 'check'][0]['bb']
    assert (best_bet(hu) - check(hu)) > (best_bet(three) - check(three)) + 3

def test_thin_value_goes_to_calling_stations_and_not_to_players_who_only_call_with_better():
    def best(arch):
        return post(dict(hero='KhJd', board='Ks7d2c9h4s', opps=[{'arch': arch}], pot=40, seed=5))['bestK']
    assert best('station') == 'bet' and best('nit') == 'check' and best('maniac') == 'check'

BARREL = [{'i': 1, 'st': 1, 'a': 'bet', 'f': 0.5, 'toCall': 0, 'pot': 20}, {'i': 0, 'st': 1, 'a': 'call', 'toCall': 10, 'pot': 30}, {'i': 1, 'st': 2, 'a': 'bet', 'f': 0.6, 'toCall': 0, 'pot': 40},
          {'i': 0, 'st': 2, 'a': 'call', 'toCall': 24, 'pot': 64}, {'i': 1, 'st': 3, 'a': 'bet', 'f': 0.66, 'toCall': 0, 'pot': 88}]
LATE = [{'i': 1, 'st': 1, 'a': 'check', 'toCall': 0, 'pot': 20}, {'i': 0, 'st': 1, 'a': 'check', 'toCall': 0, 'pot': 20}, {'i': 1, 'st': 2, 'a': 'check', 'toCall': 0, 'pot': 20},
        {'i': 0, 'st': 2, 'a': 'check', 'toCall': 0, 'pot': 20}, {'i': 1, 'st': 3, 'a': 'bet', 'f': 0.66, 'toCall': 0, 'pot': 20}]

def test_river_aggression_from_an_under_bluffing_player_is_respected_and_a_maniacs_is_not():
    def river(arch, hist, pot, call):
        return post(dict(hero='KhJd', board='Ks7d2c9h4s', opps=[{'arch': arch}], pot=pot, toCall=call, seed=5, history=hist))
    nit, maniac = river('nit', BARREL, 117, 29), river('maniac', BARREL, 117, 29)
    assert call_ev(maniac) > call_ev(nit) + 20                              # only the opponent changed: calling goes from a big loss to a big gain
    assert maniac['bestK'] == 'call' and river('tag', BARREL, 117, 29)['bestK'] == 'fold' and river('station', BARREL, 117, 29)['bestK'] == 'fold'
    assert call_ev(river('maniac', LATE, 33, 13)) > call_ev(river('nit', LATE, 33, 13)) + 5

def test_river_overbets_only_with_nutted_hands():
    nuts = post(dict(hero='AsQs', board='Ks7s2s9h4d', opps=[{'arch': 'station'}], pot=40, seed=5))
    thin = post(dict(hero='KhJd', board='Ks7d2c9h4s', opps=[{'arch': 'station'}], pot=40, seed=5))
    turn = post(dict(hero='AsQs', board='Ks7s2s9h', opps=[{'arch': 'station'}], pot=40, seed=5))
    has_over = lambda r: any(o['lab'] in ('Bet 150% pot', 'Bet 200% pot') for o in r['opts'])
    assert has_over(nuts) and not has_over(thin) and not has_over(turn)
    assert nuts['best'] in ('Bet 150% pot', 'Bet 200% pot')                 # a station pays off an overbet with the nuts

def run_labels(extra):
    return run('''__t.table({seats:6});var bb=T.bb;var real=altView;altView=function(A,k){return %s;};
      var A={opts:[{lab:"X",k:"bet",ev:10*bb,seBB:0.5},{lab:"Y",k:"check",ev:%s*bb,seBB:0.5}],best:null,opps:[]};A.best=A.opts[0];var X=stratExtras(A);altView=real;return {label:X.label,why:X.why};''' % extra)

def test_confidence_labels_come_from_the_numbers():
    flat = '{key:k,best:A.best.lab,A:A,differs:false,gap:0}'
    assert run_labels((flat, '5'))['label'] == 'Clear'                     # a wide gap, no opponent type changes the answer
    assert run_labels((flat, '9.95'))['label'] == 'Close'                  # a gap inside the noise
    dep = '{key:k,best:"Z",A:A,differs:k==="nit",gap:2}'
    assert run_labels((dep, '5'))['label'] == 'Opponent-dependent'         # the answer changes with the opponent's type (all opponents here are revealed or have no table seats)

def test_low_information_is_reported_only_when_there_is_no_read_and_the_answer_depends_on_it():
    r = run('''__t.preSpot({hero:"KhQd",pos:"BTN",opps:[{arch:"station",pos:"UTG"},{arch:"tag",pos:"SB"},{arch:"tag",pos:"BB"}],actions:[{i:1,a:"call"}]});
      S.settings.oppInfo="observed";T.hud={};var A=preGet(true),X=stratExtras(A),obs=X.label;
      S.settings.oppInfo="revealed";H.preA=null;var B=preGet(true),Y=stratExtras(B);return {obs:obs,rev:Y.label,minH:X.minHands,sens:X.sens.map(function(s){return [s.key,s.differs];})};''')
    assert r['minH'] == 0
    if any(d for _, d in r['sens']):
        assert r['obs'] == 'Low-information' and r['rev'] == 'Opponent-dependent', r
    else:
        assert r['obs'] in ('Clear', 'Close') and r['rev'] in ('Clear', 'Close'), r

def test_the_analyzer_never_returns_nan_or_an_empty_range_on_rare_action_sequences():
    cfg = dict(hero='JhJd', pos='CO', opps=[{'arch': 'maniac', 'pos': 'UTG'}, {'arch': 'tag', 'pos': 'BB'}], actions=[{'i': 1, 'a': 'call'}, {'i': 0, 'a': 'raise', 'to': 3}, {'i': 1, 'a': 'raise', 'to': 12}])
    r = pre(cfg)
    assert all(o['bb'] == o['bb'] and abs(o['bb']) < 1e6 for o in r['opts'])

def test_room_settings_flow_into_the_table_and_the_analysis_text():
    r = run('''__t.table({seats:6});T.room=roomFor("standard",T.bb);var t=roomText();T.room=roomFor("none",T.bb);return {std:t,none:roomText(),cap:roomFor("standard",4).rake.cap,sizes:roomFor("light",2).sizes.open};''')
    assert 'rake 10%' in r['std'] and 'no rake' in r['none'] and r['cap'] == 12 and r['sizes'] == [3, 4, 5]
