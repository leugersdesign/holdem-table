"""Calling ranges stay realistic: the advice must flat a single open and a 3-bet with a solver-sized range, and just
call a raise of your own bet with one strong pair instead of reraising."""
from harness import engine

CODES = '''var R="AKQJT98765432",codes=[];for(var a=0;a<13;a++)for(var b=0;b<13;b++){if(a===b)codes.push(R[a]+R[a]);else if(a<b)codes.push(R[a]+R[b]+"s");else codes.push(R[b]+R[a]+"o");}
function hand(c){return c.length===2?c[0]+"s"+c[1]+"h":c[0]+"s"+c[1]+(c[2]==="s"?"s":"h");}'''

def test_button_flats_a_cutoff_open_with_pairs_and_suited_hands():
    calls = engine().run(CODES + '''var out=[];codes.forEach(function(c){__t.preSpot({hero:hand(c),pos:"BTN",opps:[{arch:"tag",pos:"CO"},{arch:"tag",pos:"SB"},{arch:"tag",pos:"BB"}],actions:[{i:1,a:"raise",to:2.5}]});
      if(adviseHero(false).advice==="Call")out.push(c);});return out;''')
    assert len(calls) >= 15, calls
    for c in ('77', '55', 'KQs', 'A5s', 'KJs'):
        assert c in calls, (c, calls)

def test_opener_calls_a_3bet_with_mid_pairs_and_good_broadways():
    calls = engine().run(CODES + '''var out=[];codes.forEach(function(c){__t.preSpot({hero:hand(c),pos:"BTN",opps:[{arch:"tag",pos:"BB"},{arch:"tag",pos:"SB"}],actions:[{i:0,a:"raise",to:2.5},{i:1,a:"raise",to:10}]});
      H.s[2].folded=true;H.button=0;if(adviseHero(false).advice==="Call")out.push(c);});return out;''')
    assert len(calls) >= 10, calls
    for c in ('JJ', 'TT', '88', 'AQs', 'KQs'):
        assert c in calls, (c, calls)
    assert '72o' not in calls and 'K5o' not in calls, calls

def test_top_pair_top_kicker_calls_a_raise_of_its_own_bet():
    a = engine().run('''__t.spot({hero:"AsKd",board:"Kh8c3s",opps:[{arch:"tag"}],pot:44,toCall:16,history:[{i:0,a:"bet"},{i:1,a:"raise",la:0}]});return adviseHero(false).advice;''')
    assert a == 'Call', a
