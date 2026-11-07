"""Opponent realism: individuals, distinct types, richer decisions, limited observation, hidden information.

Decision-level tests use a fixed bank of random hands on random boards and 150 freshly generated individuals per type
(more than 200,000 decisions per type). Thresholds come from the design intent of each type, not from tuning to pass.
"""
import functools, itertools, math, os, statistics as st
from harness import engine, TESTS

TYPES = ['station', 'limper', 'whale', 'maniac', 'nit', 'weekend', 'tag', 'lag', 'shark', 'wild', 'thinker', 'shorty']
REC = ['station', 'limper', 'whale', 'wild', 'shorty']
PROBE = open(os.path.join(TESTS, 'opponent_probe.js'), encoding='utf-8').read().strip().rstrip(';')
rt = lambda x: x[0] / x[1] if x[1] else float('nan')

@functools.lru_cache(maxsize=1)
def probe():
    return engine().js('(%s)(150,70)' % PROBE)

def gen(k, n, seed=1):
    return engine().run('var o=[];for(var i=0;i<%d;i++)o.push(genTraits("%s",seeded(%d+i*7919)));return o;' % (n, k, seed))

# ---------- individuals ----------
def test_decision_sample_is_large_enough():
    assert all(f['n'] >= 200000 for f in probe().values())            # the pack asks for at least 20,000 per type

def test_every_generated_trait_is_in_range_and_free_of_contradictions():
    e = engine()
    r = e.run('''var bad=0,n=0,undoc=[];var doc={};TRAIT_DOC.forEach(function(d){doc[d[0]]=1;});
      Object.keys(TRAIT_RANGE).forEach(function(k){if(!doc[k])undoc.push(k);});
      ARCH_ORDER.concat(["shark"]).forEach(function(k){for(var i=0;i<1500;i++){var t=genTraits(k,seeded(i*31+5));n++;if(traitProblems(t).length)bad++;}});return {bad:bad,n:n,undoc:undoc};''')
    assert r['n'] == 1500 * 12 and r['bad'] == 0 and not r['undoc'], r     # also: every trait is documented

def test_individuals_of_one_type_differ_and_averages_match_the_archetype():
    e = engine()
    r = e.run('''var out={};["station","nit","wild","tag","maniac"].forEach(function(k){var a=[],A=ARCH[k].st;for(var i=0;i<1500;i++)a.push(genTraits(k,seeded(i*13+1)));
      var m=function(f){return a.reduce(function(s,x){return s+f(x);},0)/a.length;},sd=function(f){var mu=m(f);return Math.sqrt(a.reduce(function(s,x){return s+(f(x)-mu)*(f(x)-mu);},0)/a.length);};
      out[k]={loose:m(function(x){return x.loose;}),sdLoose:sd(function(x){return x.loose;}),aggRatio:m(function(x){return x.agg;})/A.agg,sdBluff:sd(function(x){return x.bluff;}),sdCap:sd(function(x){return x.cap;}),want:A.loose};});return out;''')
    for k, v in r.items():
        assert abs(v['loose'] - v['want']) < 0.6, (k, v)                 # archetype mean is preserved
        assert 0.93 < v['aggRatio'] < 1.10, (k, v)
        assert v['sdLoose'] > 0.8 and v['sdBluff'] > 0.05 and v['sdCap'] > 0.15, (k, v)   # individuals genuinely differ
    assert r['wild']['sdLoose'] > 1.8 * r['nit']['sdLoose']              # the wildcard varies far more than a rock

def test_traits_move_together_the_way_the_factor_model_says():
    e = engine()
    r = e.run('''var a=[];for(var i=0;i<3000;i++)a.push(genTraits("weekend",seeded(i*17+3)));
      var corr=function(f,g){var n=a.length,mf=0,mg=0;a.forEach(function(x){mf+=f(x);mg+=g(x);});mf/=n;mg/=n;var c=0,vf=0,vg=0;a.forEach(function(x){c+=(f(x)-mf)*(g(x)-mg);vf+=Math.pow(f(x)-mf,2);vg+=Math.pow(g(x)-mg,2);});return c/Math.sqrt(vf*vg);};
      return {looseCall:corr(function(x){return x.loose;},function(x){return x.dCall;}),aggBluff:corr(function(x){return x.agg;},function(x){return x.bluff;}),adaptAttn:corr(function(x){return x.adapt;},function(x){return x.attn;}),
        stickyPair:corr(function(x){return x.sticky;},function(x){return x.pairBias;}),skillHonest:corr(function(x){return x.zK;},function(x){return x.dHonest;})};''')
    assert r['looseCall'] < -0.3 and r['aggBluff'] > 0.3 and r['adaptAttn'] > 0.3 and r['stickyPair'] > 0.15 and r['skillHonest'] < -0.3, r

# ---------- types are distinct ----------
def test_types_behave_in_the_ways_they_were_designed_to():
    P = probe()
    cw = {k: rt(f['callWeak']) for k, f in P.items()}                    # call a weak or middle pair against a two-thirds-pot bet
    for k in ('station', 'whale', 'shorty'): assert cw[k] > 0.6, (k, cw[k])
    for k in ('nit', 'tag', 'weekend', 'shark', 'lag', 'thinker'): assert cw[k] < 0.2, (k, cw[k])
    assert 0.35 < cw['maniac'] < 0.7 and 0.35 < cw['wild'] < 0.7 and 0.1 < cw['limper'] < 0.4
    bl = {k: rt(f['bluffRiver']) for k, f in P.items()}                  # bet the river with nothing when checked to
    assert bl['maniac'] > 0.18 and bl['nit'] < 0.04 and bl['station'] < 0.04 and 0.1 < bl['shark'] < 0.2 and 0.1 < bl['lag'] < 0.2
    bet = {k: rt(f['bet']) for k, f in P.items()}
    assert bet['maniac'] == max(bet.values()) and bet['maniac'] > 0.5 and bet['nit'] == min(bet.values()) and bet['nit'] < 0.25
    rs = {k: rt(f['raise']) for k, f in P.items()}
    assert rs['maniac'] > 1.8 * rs['station']
    assert rt(P['nit']['foldBet']['1']) > 0.9 and rt(P['whale']['foldBet']['1']) < 0.8

def test_every_pair_of_types_is_distinguishable_by_how_they_decide():
    P = probe()
    V = {k: [rt(f['callWeak']), rt(f['foldBet']['1']), rt(f['foldBet']['2']), rt(f['foldBet']['3']), rt(f['bet']), rt(f['bluffRiver']), rt(f['raise']), rt(f['callBig']['20'])] for k, f in P.items()}
    d = sorted((math.dist(V[a], V[b]), a, b) for a, b in itertools.combinations(V, 2))
    assert d[0][0] > 0.04, d[:3]

def test_bigger_bets_fold_out_more_for_every_type():
    for k, f in probe().items():
        fo = [rt(f['foldBySize'][s]) for s in ('0.33', '0.66', '1', '2')]
        assert all(fo[i] <= fo[i + 1] + 0.01 for i in range(3)), (k, fo)

def test_real_strength_still_calls_huge_bets_and_no_type_is_a_universal_bluff_target():
    P = probe()
    for k, f in P.items():
        c20 = rt(f['callBig']['20']); assert c20 > 0.15, (k, c20)        # nobody folds everything to a 20x pot shove
        for m, key in ((5, '5'), (20, '20'), (50, '50')):
            fold = 1 - rt(f['callBig'][key]); ev = fold - (1 - fold) * m   # EV in pots of bluffing with nothing
            assert ev < -0.1, (k, m, ev)                                 # a bluff of 5x pot or more loses against every type
    for k in REC: assert rt(P[k]['callBig']['20']) > 0.35, k             # recreational players call with any pair

def test_barrels_check_raises_and_pair_overvaluation_exist():
    P = probe()
    gain = [rt(f['barrelAir']) - rt(f['noBarrelAir']) for f in P.values()]
    assert sum(g > 0 for g in gain) >= 10 and st.mean(gain) > 0.03       # betting the previous street makes a bluff barrel more likely
    xr = lambda k: rt(P[k]['xrRaise']) - rt(P[k]['noXrRaise'])
    assert xr('maniac') > 0.1 and xr('station') < -0.1                   # check-raise tendency differs by type
    r = engine().run('''seedRNG(3);__t.table({seats:6});var hi={S:3.3,outs:0,c:"midpair"},c={st:2,nOpp:1,isPreAgg:false,facingRaise:false,raises:1,canRaise:true,memAdj:0,pot:166,toCall:66},n=[0,0];   /* a 66 bet into a pot of 100 */
      [0,0.6].forEach(function(pb,j){var P=liveProf({name:"x",arch:"weekend",skill:"regular",st:ARCH.weekend.st,tr:canonTraits("weekend")});P.pairBias=pb;for(var k=0;k<4000;k++)if(liveDecide(P,hi,c,RNG)[0]!=="fold")n[j]++;});return n;''')
    assert r[1] > r[0] + 800                                             # a regular's borderline pair is folded; over-valuing it means calling

def test_a_wildcard_sizes_far_less_consistently_than_a_regular():
    e = engine()
    def sd(arch):
        return e.run('''__t.spot({hero:"AhQd",board:"Ks7d2c",opps:[{arch:"%s"}],pot:20,seed:4});var p=T.players[1],P=liveProf(p);P.honest=1;var a=[];for(var k=0;k<3000;k++){liveBet(1,p,P,6,20,"value");a.push(Math.log(H.bsize[1].f));}
          var m=a.reduce(function(s,v){return s+v;},0)/a.length;return Math.sqrt(a.reduce(function(s,v){return s+(v-m)*(v-m);},0)/a.length);''' % arch)
    assert sd('wild') > 1.8 * sd('tag')

def test_short_stack_player_buys_in_short_and_shoves_or_folds():
    r = engine().run('''seedRNG(8);__t.table({seats:9,spec:["shorty","station","limper","weekend","tag","nit","maniac","whale"],style:"casino"});var sh=T.players.filter(function(p){return p.arch==="shorty";})[0],i=T.players.indexOf(sh),bb=T.bb,start=sh.stack/bb,
      raises=0,allin=0,orig=raiseTo;raiseTo=function(j,to){var d=orig.apply(this,arguments);if(j===i&&H.street===0){raises++;if(d[1]>=legal(i).maxTo)allin++;}return d;};
      for(var k=0;k<900;k++){if(sh.stack<bb*8)sh.stack=shortStack(T.buy);__t.hand();}raiseTo=orig;return {start:start,buy:T.buy/bb,raises:raises,allin:allin};''')
    assert 0.2 * r['buy'] <= r['start'] <= 0.45 * r['buy'], r
    assert r['raises'] >= 20 and r['allin'] / r['raises'] >= 0.9, r

# ---------- limited observation and adaptation ----------
def _bot(arch, **over):
    return 'var b=archBot("%s",1000,[]);b.tr=Object.assign(canonTraits("%s"),%s);' % (arch, arch, over or {})

def test_a_new_opponent_knows_nothing_and_one_hand_barely_moves_it():
    r = engine().run('''seedRNG(2);__t.table({seats:6});var b=archBot("thinker",1000,[]);b.tr=canonTraits("thinker");
      var fresh={call:adaptCall(b),bluff:adaptBluff(b),vp:belief(b,"vpip"),sdb:belief(b,"sdb")};obsAdd(b,"sdb",1,1);obsAdd(b,"fb",1,1);
      return {fresh:fresh,afterOne:{call:adaptCall(b),bluff:adaptBluff(b)},prior:POP};''')
    assert r['fresh']['call'] == 0 and r['fresh']['bluff'] == 1
    assert abs(r['fresh']['vp'] - r['prior']['vpip'][0]) < 1e-9 and abs(r['fresh']['sdb'] - r['prior']['sdb'][0]) < 1e-9
    assert abs(r['afterOne']['call']) < 0.06 and abs(r['afterOne']['bluff'] - 1) < 0.06   # one observation is almost nothing

def test_evidence_changes_play_gradually_and_skilled_players_adapt_more():
    r = engine().run('''seedRNG(2);__t.table({seats:6});var res={};
      [["station"],["thinker"],["shark"]].forEach(function(a){var b=archBot(a[0],1000,[]);b.tr=canonTraits(a[0]);var steps=[];[0,5,20,60,200].forEach(function(n,j){var add=n-(j?[0,5,20,60,200][j-1]:0);for(var q=0;q<add;q++){obsAdd(b,"sdb",1,1);obsAdd(b,"agg",1,1);}steps.push(adaptCall(b));});res[a[0]]=steps;});
      var c=archBot("thinker",1000,[]);c.tr=canonTraits("thinker");for(var q=0;q<80;q++)obsAdd(c,"fb",1,1);res.bluffMul=adaptBluff(c);
      var d=archBot("thinker",1000,[]);d.tr=canonTraits("thinker");for(var q=0;q<80;q++)obsAdd(d,"fb",0,1);res.bluffMulFoldsLittle=adaptBluff(d);return res;''')
    for k in ('thinker', 'shark'):
        s = r[k]; assert s[0] == 0 and all(s[i] >= s[i + 1] - 1e-9 for i in range(4)) and s[4] < -0.3, (k, s)   # monotone, bounded, builds slowly
        assert s[1] > -0.15 and s[2] > -0.35, (k, s)                     # 5 observed bluffs barely matter; 20 matter somewhat, not fully
    assert abs(r['station'][4]) < 0.15 and r['shark'][4] < r['station'][4] - 0.3                              # a station barely adapts
    assert r['bluffMul'] > 1.15 and r['bluffMulFoldsLittle'] < 0.9      # bluff more against someone who folds, less against someone who does not

def test_beliefs_regress_to_the_population_and_old_evidence_fades():
    r = engine().run('''seedRNG(2);__t.table({seats:6});var b=archBot("tag",1000,[]);for(var q=0;q<3;q++)obsAdd(b,"sdb",1,1);var few=belief(b,"sdb");
      var c=archBot("tag",1000,[]);for(var q=0;q<1000;q++)obsAdd(c,"vpip",1,1);return {few:few,prior:POP.sdb[0],trialsCapped:beliefTrials(c,"vpip"),cap:OBS_CAP,many:belief(c,"vpip")};''')
    assert r['prior'] < r['few'] < 0.6                                   # 3 straight bluffs is not "always bluffs"
    assert r['trialsCapped'] <= r['cap'] + 1 and r['many'] > 0.9         # capped memory still reaches the truth given enough evidence

def test_players_only_learn_from_events_they_noticed():
    r = engine().run('''seedRNG(12);S.settings.oppInfo="revealed";var out={};
      [0,1].forEach(function(att){__t.table({seats:3,spec:["tag","tag"],style:"online"});T.players.forEach(function(p){if(p.arch)trOf(p).attn=att;});var n=0;
        for(var k=0;k<200;k++){__t.hand();n++;}var tot=0;T.players.forEach(function(p){if(p.arch){var o=obsOf(p);tot+=o.vpip[1]+o.agg[1]+o.fb[1];}});out["a"+att]=tot;});return out;''')
    assert r['a0'] == 0 and r['a1'] > 200                                # attention 0 learns nothing; attention 1 learns from what it saw

def test_a_player_who_already_folded_notices_less():
    r = engine().run('''seedRNG(14);var seen={in:0,out:0},N=600;
      for(var k=0;k<N;k++){__t.table({seats:3,spec:["tag","tag"],style:"online"});T.players.forEach(function(p){if(p.arch)trOf(p).attn=1;});
        H=null;startHand();__t.q.length=0;var a=T.players[1],b=T.players[2];
        H.hist=[{i:0,st:1,a:"bet",toCall:0,pot:20},{i:1,st:1,a:"fold",toCall:6,pot:26},{i:0,st:2,a:"bet",toCall:0,pot:20}];
        H.seats.forEach(function(i){H.s[i].folded=false;});H.s[1].folded=true;H.board=[1,2,3,4,5];H.street=3;H.showdown=false;H.done=true;
        var oa=obsOf(a),ob=obsOf(b);observeHand();seen.out+=oa.agg[1];seen.in+=ob.agg[1];}
      return {inHand:seen.in/N/2,folded:seen.out/N/2};''')
    # the player who folded between the hero's two bets saw the first fully and the second about 30% of the time
    assert r['inHand'] > 0.95 and 0.55 < r['folded'] < 0.75, r      # expected (1 + 0.3) / 2 = 0.65 for the player who folded between the two bets

# ---------- hidden information ----------
def test_bots_never_use_the_heros_hole_cards():
    """Twin runs with the same seed: in the second the hero holds two different cards. The hero's actions do not depend on
    his cards (always check or call), so if any bot decision read his hand, the action sequences would differ."""
    e = engine()
    for mode in ('observed', 'revealed'):
        r = e.run('''S.settings.oppInfo="%s";var diff=0,total=0;
          function run(seed,swap){seedRNG(seed);__t.table({seats:6,spec:["station","limper","weekend","tag","nit","lag","maniac","shark"],style:"casino"});var ob=botPre,op=botPost;
            botPre=function(i){return i===0?(legal(0).toCall>0?["call"]:["check"]):ob(i);};botPost=function(i){return i===0?(legal(0).toCall>0?["call"]:["check"]):op(i);};
            T.players.forEach(function(p){p.stack=T.buy;});H=null;startHand();
            if(swap){var d=H.deck;H.s[0].cards=[d.shift(),d.shift()];}   /* two cards that are never dealt to anyone else */
            __t.drain();botPre=ob;botPost=op;return JSON.stringify([H.hist.filter(function(e){return e.i!==0;}).map(function(e){return [e.i,e.st,e.a,e.toCall,Math.round(e.f*1000)];}),H.board]);}
          for(var s=1;s<=240;s++){var a=run(s*101,false),b=run(s*101,true);total++;if(a!==b)diff++;}return {diff:diff,total:total};''' % mode)
        assert r['diff'] == 0 and r['total'] == 240, (mode, r)

def test_observed_mode_analysis_does_not_depend_on_the_hidden_type():
    e = engine()
    def ev(arch, mode='observed'):
        return e.run('''S.settings.oppInfo="%s";__t.spot({hero:"AhQd",board:"Ks7d2c9h4s",opps:[{arch:"%s"}],pot:40,seed:5,history:[{i:1,st:3,a:"bet",f:0.66,toCall:0,pot:40}]});H.s[0].sb=0;
          S.settings.oppInfo="%s";var A=evAnalyze();return A.opts.map(function(o){return [o.lab,Math.round(o.ev*1e6)/1e6];});''' % (mode, arch, mode))
    # no hand history seen yet: a maniac and a rock must look identical to the analysis
    assert ev('maniac') == ev('nit') == ev('station')
    # revealed mode really uses the player, so it differs
    assert ev('maniac', 'revealed') != ev('nit', 'revealed')

def test_observed_mode_sheet_shows_no_type_before_a_read_exists_and_revealed_mode_does():
    e = engine()
    html = lambda mode: e.run('''S.settings.oppInfo="%s";__t.table({seats:6,spec:["maniac","station","nit","tag","whale"],style:"casino"});T.hud={};openPlayer(1);var h=$("p-body").innerHTML;closePlayer();return h;''' % mode)
    names = ['Calling station', 'Limp-caller', 'Gambler', 'Maniac', 'Rock', 'Weekend regular', 'Solid regular', 'Loose-aggressive pro', 'Shark', 'Recreational wildcard', 'Thinking player', 'Short-stack recreational']
    obs = html('observed'); rev = html('revealed')
    assert not any(n in obs for n in names) and 'class="dot' not in obs and 'On tilt' not in obs   # the browser serializes attributes with double quotes
    assert any(n in rev for n in names) and 'class="dot' in rev

def test_the_reader_names_the_true_type_among_its_top_three_almost_always():
    e = engine(fresh=True); ok = []
    for shift, seed in ((0, 31000), (4, 31100), (8, 31200)):
        spec = [TYPES[(shift + k) % 12] for k in range(8)]
        ok += e.run('''seedRNG(%d);S.settings.oppInfo="observed";__t.table({seats:9,spec:%s,style:"casino"});T.hud={};for(var i=0;i<300;i++)__t.hand();
          return T.players.filter(function(p){return p.arch;}).map(function(p){var rd=readOpp(p);return {k:p.arch,top:rd?rd.top.slice(0,3).map(function(x){return x[0];}):null};});''' % (seed, __import__('json').dumps(spec)))
    ok = [x for x in ok if x['top']]
    top3 = sum(x['k'] in x['top'] for x in ok) / len(ok); top1 = sum(x['k'] == x['top'][0] for x in ok) / len(ok)
    assert len(ok) >= 20 and top3 >= 0.9 and top1 >= 0.5, (len(ok), top1, top3)     # measured: 97% and 65% at about 300 hands

def test_reader_declines_to_guess_from_too_few_hands():
    r = engine().run('''__t.table({seats:6});var p=T.players[1];T.hud={};T.hud[p.name]={h:11,vp:6,pr:2,agg:3,call:3,cbO:1,cb:1,fbO:2,fb:1};var few=readOpp(p);T.hud[p.name].h=12;return {few:few,enough:!!readOpp(p)};''')
    assert r['few'] is None and r['enough']

def test_default_is_observed_only_and_the_setting_switches():
    r = engine().run('''delete S.settings.oppInfo;var d=oppMode();S.settings.oppInfo="revealed";var r=oppMode();S.settings.oppInfo="observed";return [d,r,oppMode()];''')
    assert r == ['observed', 'revealed', 'observed']

# ---------- the whole table still plays like a low-stakes live game ----------
def test_a_seeded_table_of_individuals_still_plays_like_a_live_game():
    r = engine(fresh=True).run('''seedRNG(77);S.settings.oppInfo="revealed";__t.table({seats:9,spec:["station","station","limper","limper","weekend","nit","maniac","lag"],style:"casino"});
      var vp=0,pf=0,seen=0,fold=[0,0],cb=[0,0],eh=endHand;T.hud={};for(var k=0;k<1500;k++)__t.hand();
      T.players.forEach(function(p){var r=T.hud[p.name];if(r&&!p.hero&&r.h){seen+=r.h;vp+=r.vp;pf+=r.pr;fold[0]+=r.fb;fold[1]+=r.fbO;cb[0]+=r.cb;cb[1]+=r.cbO;}});
      return {vpip:vp/seen,pfr:pf/seen,foldToBet:fold[0]/fold[1],cbet:cb[0]/Math.max(1,cb[1])};''')
    assert 0.3 < r['vpip'] < 0.5 and 0.05 < r['pfr'] < 0.16 and 0.4 < r['foldToBet'] < 0.7 and 0.4 < r['cbet'] < 0.85, r

def test_a_hand_stronger_than_the_call_cap_still_calls_a_big_bet():
    """Each type has a strength at which it calls any bet. A hand just above that cap must keep calling a river bet of twice
    the pot, even though the uncapped rule (base + fear of size) would fold it for most types."""
    r = engine().run('''seedRNG(4);__t.table({seats:6});var out={};
      ["station","limper","whale","maniac","nit","weekend","tag","lag","shark","wild","thinker","shorty"].forEach(function(k){var P=canonProf(k),hi={S:P.cap+0.4,outs:0,c:"set"},
        c={st:3,nOpp:1,isPreAgg:false,facingRaise:false,raises:1,canRaise:true,memAdj:0,pot:300,toCall:200},n=0,uncapped=P.callBase[2]+P.sens*2;
        for(var q=0;q<400;q++)if(liveDecide(P,hi,c,RNG)[0]!=="fold")n++;out[k]={call:n/400,cap:P.cap,uncapped:uncapped};});return out;''')
    assert all(v['call'] > 0.97 for v in r.values()), r
    assert sum(v['uncapped'] > v['cap'] + 0.45 for v in r.values()) >= 3, r      # the cap really binds for the tighter types here (rock, weekend, solid regular)
