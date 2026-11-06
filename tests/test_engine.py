"""Hand engine: chip conservation, split pots, side pots, rake, card uniqueness, reproducibility."""
from harness import engine, known_failure

def test_chips_are_conserved_over_many_hands_six_handed():
    e = engine(); seedr = e.run('seedRNG(101);__t.table({seats:6});return __t.play(1500);')
    assert seedr['errors'] == 0 and seedr['drift'] == 0 and seedr['dupCards'] == 0, seedr

def test_chips_are_conserved_nine_handed_with_short_stacks_and_many_all_ins():
    e = engine(); r = e.run('seedRNG(202);__t.table({seats:9,depth:25,spec:["maniac","station","lag","limper","whale","nit","tag","weekend"]});return __t.play(1200);')
    assert r['errors'] == 0 and r['drift'] == 0 and r['dupCards'] == 0, r

def test_rake_is_taken_only_from_pots_that_saw_a_flop_and_chips_still_balance():
    e = engine()
    r = e.run('''seedRNG(303);__t.table({seats:6,rake:{pct:0.05,cap:6,drop:0}});var preRake=0,over=0,flopRake=0,hands=0,orig=endHand;
      endHand=function(a){hands++;if(H.board.length<3&&H.rake>0)preRake++;if(H.rake>6)over++;if(H.rake>0)flopRake++;return orig.apply(this,arguments);};
      var out=__t.play(1500);endHand=orig;out.preRake=preRake;out.over=over;out.flopRake=flopRake;return out;''')
    assert r['drift'] == 0 and r['errors'] == 0, r           # stacks + rake paid == chips at the start of each hand
    assert r['rake'] > 0 and r['flopRake'] > 0
    assert r['preRake'] == 0 and r['over'] == 0

def test_same_seed_replays_the_same_session():
    e = engine()
    r = e.run('''seedRNG(5);__t.table({seats:6});var a=__t.play(200).sig;seedRNG(5);__t.table({seats:6});var b=__t.play(200).sig;seedRNG(6);__t.table({seats:6});var c=__t.play(200).sig;return {same:a===b,differs:a!==c};''')
    assert r['same'] and r['differs']

def _showdown(e, tots, hands, stacks=None):
    return e.run('''seedRNG(1);__t.table({seats:%d});H=null;startHand();__t.q.length=0;
      var n=%d,tots=%s,hands=%s;H.board=__t.cards("2c7d9hJs3c");H.street=3;H.done=false;
      H.seats.forEach(function(i){H.s[i].folded=i>=n;H.s[i].allin=false;H.s[i].sb=0;H.s[i].tot=i<n?tots[i]:0;if(i<n)H.s[i].cards=__t.cards(hands[i]);});
      for(var i=0;i<n;i++)T.players[i].stack=0;for(i=0;i<n;i++)if(tots[i]<Math.max.apply(null,tots))H.s[i].allin=true;
      H.cur=0;H.ritState="no";showdown();return {won:T.players.slice(0,n).map(function(p){return p.stack;}),winners:H.winners};''' % (len(tots), len(tots), tots, hands))

def test_split_pot_three_ways_when_the_board_plays():
    e = engine()
    # Broadway on board: everybody plays the board and splits equally
    r = e.run('''seedRNG(1);__t.table({seats:3});H=null;startHand();__t.q.length=0;H.board=__t.cards("AsKdQhJcTs");H.street=3;H.done=false;
      H.seats.forEach(function(i){H.s[i].folded=false;H.s[i].allin=false;H.s[i].sb=0;H.s[i].tot=100;});H.s[0].cards=__t.cards("2h3h");H.s[1].cards=__t.cards("4c5c");H.s[2].cards=__t.cards("6c7c");
      T.players.forEach(function(p){p.stack=0;});H.cur=0;H.ritState="no";showdown();return T.players.map(function(p){return p.stack;});''')
    assert r == [100, 100, 100]

def test_odd_chip_goes_to_one_winner_and_no_chip_is_lost():
    e = engine()
    r = e.run('''seedRNG(1);__t.table({seats:3});H=null;startHand();__t.q.length=0;H.board=__t.cards("AsKdQhJcTs");H.street=3;H.done=false;
      H.seats.forEach(function(i){H.s[i].folded=false;H.s[i].allin=false;H.s[i].sb=0;H.s[i].tot=i===2?0:101;});H.s[2].folded=true;H.s[0].cards=__t.cards("2h3h");H.s[1].cards=__t.cards("4c5c");H.s[2].cards=__t.cards("6c7c");
      T.players.forEach(function(p){p.stack=0;});H.cur=0;H.ritState="no";showdown();return T.players.map(function(p){return p.stack;});''')
    assert sum(r) == 202 and sorted(r[:2]) == [101, 101]

def test_side_pots_pay_the_short_stack_only_the_main_pot():
    e = engine()
    r = _showdown(e, [50, 100, 100], ['AhAd', 'KhKd', 'QhQd'])
    assert r['won'] == [150, 100, 0], r                       # A (50 in) wins the 150 main pot, B beats C for the 100 side pot

def test_short_stack_with_the_worst_hand_cannot_win_the_side_pot():
    e = engine()
    r = _showdown(e, [50, 100, 100], ['QhQd', 'AhAd', 'KhKd'])
    assert r['won'] == [0, 250, 0], r

def test_rake_comes_out_of_the_main_pot_first():
    e = engine()
    r = e.run('''seedRNG(1);__t.table({seats:3,rake:{pct:0.10,cap:0,drop:0}});H=null;startHand();__t.q.length=0;H.board=__t.cards("2c7d9hJs3c");H.street=3;H.done=false;
      var tots=[50,100,100],hands=["AhAd","KhKd","QhQd"];H.seats.forEach(function(i){H.s[i].folded=false;H.s[i].allin=tots[i]<100;H.s[i].sb=0;H.s[i].tot=tots[i];H.s[i].cards=__t.cards(hands[i]);});
      T.players.forEach(function(p){p.stack=0;});H.cur=0;H.ritState="no";T.rakePaid=0;showdown();return {won:T.players.map(function(p){return p.stack;}),rake:H.rake};''')
    assert r['rake'] == 25 and sum(r['won']) == 250 - 25
    assert r['won'] == [150 - 25, 100, 0], r                  # 10% of the 250 pot, taken from the 150 main pot

@known_failure('act() does not validate actions. The interface only offers legal buttons, but a programmatic illegal action is accepted. Planned for the reliability work (prompt 06).')
def test_illegal_actions_are_rejected():
    e = engine()
    r = e.run('''seedRNG(1);__t.table({seats:4});H=null;startHand();__t.q.length=0;
      var who=H.toAct;var before={hist:(H.hist||[]).length,cur:H.cur,stack:T.players[who].stack};
      var L=legal(who);var facing=L.toCall>0;
      /* checking while facing a bet is illegal */
      if(facing){try{act(who,"check");}catch(e){}}
      var after=(H.hist||[]).length;return {facing:facing,accepted:after>before.hist};''')
    assert r['facing'] and not r['accepted'], r
