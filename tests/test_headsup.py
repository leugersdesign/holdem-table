"""Heads-up play: bots use heads-up frequencies, the hero's advice uses the heads-up charts and the push/fold
equilibrium, and none of it touches a table with three or more players."""
from harness import engine

SEAT = '''function seat(arch,depth,heroBtn,hand,seats,sd){seats=seats||2;S.customCfg={bi:0,depth:depth,seats:seats,style:"online",spec:seats===2?[arch]:[arch,arch,arch,arch,arch],table:"classic",atm:"vegas"};
  T=makeCash(customStake());S.cash=T;T.noLeave=true;T.room=undefined;T.sb=1;T.bb=2;T.players.forEach(function(p){p.stack=depth*2;});T.players[0].hero=true;
  for(var k=0;k<40;k++){H=null;__t.q.length=0;seedRNG((sd||0)*97+77+k);T.button=heroBtn?(T.players.length-1):0;startHand();if((H.pos[0]==="BTN")===heroBtn)break;}
  if(hand)H.s[0].cards=__t.cards(hand);var g=0;while(__t.q.length&&g<40&&H.toAct!==0){__t.q.shift()();g++;}return H;}
function adv(arch,depth,btn,hand,seats){seat(arch,depth,btn,hand,seats);return adviseHero(false).advice;}'''

def test_bots_open_and_defend_like_heads_up_players():
    r = engine().run(SEAT + '''var out={};["shark","station","nit"].forEach(function(a){var o=0,l=0,n=0,f3=0,op=0;
      for(var k=0;k<600;k++){seat(a,100,false,null,2,k+1);var e=H.hist.filter(function(x){return x.i===1&&x.st===0;}).pop();if(!e)continue;n++;
        if(e.a==="raise"){o++;var s=JSON.stringify(H),t=JSON.stringify(T);act(0,"raise",H.cur*3);var g=0;while(__t.q.length&&g<40&&!H.done){__t.q.shift()();g++;}
          var r=H.hist.filter(function(x){return x.i===1&&x.st===0;}).pop();op++;if(r.a==="fold")f3++;H=JSON.parse(s);T=JSON.parse(t);S.cash=T;__t.q.length=0;}else if(e.a==="call")l++;}
      out[a]={open:o/n,limp:l/n,fold3:op?f3/op:null};});return out;''')
    assert 0.7 <= r['shark']['open'] <= 0.9 and 0.28 <= r['shark']['fold3'] <= 0.52, r
    assert r['station']['limp'] >= 0.55 and r['station']['open'] <= 0.25, r
    assert 0.3 <= r['nit']['open'] <= 0.55 and r['nit']['fold3'] >= 0.5, r

def test_bots_defend_against_a_heads_up_cbet():
    r = engine().run(SEAT + '''var out={};["shark","station"].forEach(function(a){var n=0,f=0;
      for(var k=0;k<900;k++){seat(a,100,true,null,2,k+1);if(H.raises!==0)continue;act(0,"raise",4);var g=0;while(__t.q.length&&g<60&&!H.done&&!(H.street===1&&H.toAct===0)){__t.q.shift()();g++;}
        if(H.done||H.street!==1||H.toAct!==0||H.cur!==0)continue;var hl=H.hist.length;act(0,"raise",Math.round(potTotal()*0.5));g=0;while(__t.q.length&&g<60&&!H.done){__t.q.shift()();g++;if(H.hist.slice(hl).some(function(x){return x.i===1;}))break;}
        var e=H.hist.slice(hl).filter(function(x){return x.i===1;})[0];if(!e)continue;n++;if(e.a==="fold")f++;}
      out[a]=f/n;});return out;''')
    assert 0.28 <= r['shark'] <= 0.55, r
    assert r['station'] <= 0.35, r

def test_hero_advice_uses_heads_up_charts_and_push_fold():
    r = engine().run(SEAT + '''return {btn100:adv("shark",100,true,"7h2c"),k2_10:adv("shark",10,true,"Kh2c"),e3_10:adv("shark",10,true,"8h3c"),
      bb72:adv("maniac",100,false,"7h2c"),bbAK:adv("maniac",100,false,"AhKd"),bbJ8:adv("maniac",100,false,"Jh8d")};''')
    assert r == {'btn100': 'Raise', 'k2_10': 'Push all in', 'e3_10': 'Fold', 'bb72': 'Fold', 'bbAK': 'Reraise', 'bbJ8': 'Call'}, r

def test_push_fold_sets_match_the_equilibrium():
    r = engine().run('''var s10=HU_SETS.sets[10],s15=HU_SETS.sets[15];return {p10:s10.pp,c10:s10.cp,p15:s15.pp,c15:s15.cp,k2:huIn(s10.p,"K2o"),q5call:huIn(s10.c,"Q5o"),a2call:huIn(s15.c,"A2o"),t2:huIn(s10.p,"T2o")};''')
    assert 55 <= r['p10'] <= 61 and 34 <= r['c10'] <= 40 and 43 <= r['p15'] <= 48 and 26 <= r['c15'] <= 31, r
    assert r['k2'] and r['a2call'] and not r['t2'], r

def test_ring_tables_are_unchanged():
    r = engine().run(SEAT + '''var a=adv("tag",100,true,"7h2c",6);return {adv:a,hu:huLive()};''')
    assert r == {'adv': 'Fold', 'hu': False}, r
