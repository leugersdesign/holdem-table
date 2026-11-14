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
    assert 0.18 <= r['shark'] <= 0.5, r
    assert r['station'] <= 0.3, r

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

MEASURE = SEAT + '''function spot(a,k){seat(a,100,true,null,2,k+1);if(H.raises!==0)return false;act(0,"raise",4);var g=0;while(__t.q.length&&g<60&&!H.done&&!(H.street===1&&H.toAct===0)){__t.q.shift()();g++;}
  return !H.done&&H.street===1&&H.toAct===0&&H.cur===0;}
function respond(f){var L=legal(0),to=f>50?L.maxTo:Math.max(L.minTo,Math.round(potTotal()*f)),hl=H.hist.length;act(0,"raise",Math.min(to,L.maxTo));var g=0;
  while(__t.q.length&&g<60&&!H.done){__t.q.shift()();g++;if(H.hist.slice(hl).some(function(x){return x.i===1;}))break;}return H.hist.slice(hl).filter(function(x){return x.i===1;})[0];}'''

def test_bots_fold_more_to_bigger_bets_and_call_shoves_only_with_real_hands():
    r = engine().run(MEASURE + '''var out={};["shark","station"].forEach(function(a){var sz=[0.33,0.75,1.5,99],fo=[0,0,0,0],n=[0,0,0,0],air=0,calls=0;
      for(var k=0;k<500;k++){if(!spot(a,k))continue;var sH=JSON.stringify(H),sT=JSON.stringify(T),sd=(RNG()*1e9)|0;
        sz.forEach(function(f,j){H=JSON.parse(sH);T=JSON.parse(sT);S.cash=T;__t.q.length=0;seedRNG(sd);var e=respond(f);if(!e)return;n[j]++;if(e.a==="fold")fo[j]++;
          else if(f>50){calls++;var I=hcInfo(H.s[1].cards,H.board);if(I.S<2&&(I.outs||0)<8)air++;}});}
      out[a]={fold:fo.map(function(x,j){return x/n[j];}),airCalls:calls?air/calls:0};});return out;''')
    for a in ('shark', 'station'):
        f = r[a]['fold']
        assert f[0] < f[1] < f[2] < f[3], (a, r)
        assert r[a]['airCalls'] <= 0.05, (a, r)
    assert 0.42 <= r['shark']['fold'][2] <= 0.7 and r['shark']['fold'][3] >= 0.8, r

def test_bots_check_most_strong_hands_out_of_position():
    r = engine().run(MEASURE + '''var o={n:0,lead:0,sn:0,sl:0};for(var k=0;k<700;k++){seat("shark",100,true,null,2,k+1);if(H.raises!==0)continue;act(0,"raise",4);
      var g=0;while(__t.q.length&&g<60&&!H.done){__t.q.shift()();g++;if(H.hist.some(function(x){return x.i===1&&x.st===1;}))break;}
      var e=H.hist.filter(function(x){return x.i===1&&x.st===1;})[0];if(!e)continue;o.n++;var led=e.a==="raise"||e.a==="bet";if(led)o.lead++;
      if(hcInfo(H.s[1].cards,H.board).S>=4){o.sn++;if(led)o.sl++;}}return {lead:o.lead/o.n,strongLead:o.sn?o.sl/o.sn:0,n:o.n};''')
    assert r['lead'] <= 0.2 and r['strongLead'] <= 0.45, r
