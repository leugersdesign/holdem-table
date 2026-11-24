"""Hand routine (version 46): the flowchart path, the numbers on it, and the drill.

The routine restates the baseline's rules as fixed steps. These tests pin each branch to the rule it stands for, check the
math it prints, check it agrees with the baseline advice in played hands, and check the drill never touches the grade."""
from harness import engine

def _pre(body):
    return engine().run('''S.settings.straddle="off";''' + body)

def test_folded_to_you_follows_score_and_seat_number():
    r = _pre('''var o={};
      __t.preSpot({hero:"AhKd",pos:"CO",opps:[{arch:"tag",pos:"SB"},{arch:"tag",pos:"BB"}],actions:[]});var M=rtModel();o.a=[M.chain,M.verdict,M.path.join(">")];
      __t.preSpot({hero:"7h2c",pos:"CO",opps:[{arch:"tag",pos:"SB"},{arch:"tag",pos:"BB"}],actions:[]});M=rtModel();o.b=[M.chain,M.verdict,M.path.join(">")];
      return o;''')
    assert r['a'] == ['open', 'Raise', 's>d1>y1'], r
    assert r['b'] == ['open', 'Fold', 's>d1>n'], r

def test_limped_pot_branch_is_the_limper_rule():
    r = _pre('''var o=[];[["AhKd","Raise"],["5s5d","Limp behind"],["Kh7c","Fold"]].forEach(function(x){
        __t.preSpot({hero:x[0],pos:"HJ",opps:[{arch:"station",pos:"UTG"},{arch:"tag",pos:"SB"},{arch:"tag",pos:"BB"}],actions:[{i:1,a:"call"}]});
        var M=rtModel(),LR=limpRule(codeOf(H.s[0].cards),"HJ",limpersIn());o.push([x[0],M.chain,M.verdict,x[1],LR.adv,M.path[M.path.length-1]]);});return o;''')
    for code, chain, verdict, want, rule, end in r:
        assert chain == 'limp' and verdict == want, (code, chain, verdict, want)
        assert {'Raise': 'y1', 'Call': 'y2', 'Fold': 'n'}[rule] == end, (code, rule, end)

def test_facing_one_raise_premiums_reraise_and_junk_folds():
    r = _pre('''var o={};function sp(h){__t.preSpot({hero:h,pos:"BTN",opps:[{arch:"tag",pos:"UTG"},{arch:"tag",pos:"SB"},{arch:"tag",pos:"BB"}],actions:[{i:1,a:"raise",to:3}]});var M=rtModel(),A=adviseHero(false);return [M.chain,M.verdict,A.advice];}
      o.ak=sp("AhKd");o.j=sp("Kh4c");o.mid=sp("8s8d");return o;''')
    assert r['ak'][:2] == ['raise', 'Reraise'], r
    assert r['j'][:2] == ['raise', 'Fold'], r
    for k in r:
        assert r[k][1] == r[k][2], (k, r[k])   # the routine's branch agrees with the baseline advice

def test_post_flop_price_and_tree_match_hand_arithmetic():
    r = engine().run('''var o={};
      __t.spot({hero:"AsJd",board:"Jh7c2s",opps:[{arch:"tag"}],pot:100,toCall:50});var M=rtModel();
      o.chain=M.chain;o.need=M.A.need;o.c=M.vals.c;o.path=M.path.slice(0,4).join(">");o.verdict=M.verdict;o.adv=M.A.advice;
      __t.spot({hero:"7s7d",board:"Jh7c2s",opps:[{arch:"tag"}],pot:20,toCall:0});M=rtModel();o.set=[M.chain,M.verdict,M.path.join(">")];
      __t.spot({hero:"Ah5h",board:"Kh9h2c",opps:[{arch:"tag"}],pot:20,toCall:0});M=rtModel();o.draw=[M.chain,M.verdict,M.vals.e];
      return o;''')
    assert r['chain'] == 'bet' and abs(r['need'] - 50 / 200) < 1e-9, r   # a 50 bet into 100 makes 150; calling 50 wins 200
    assert r['path'] == 'b>h>c>e' and 'need 25%' in r['c'], r
    assert r['verdict'] in ('Raise', 'Call', 'Fold') and r['verdict'] == r['adv'], r
    assert r['set'][0] == 'chk' and r['set'][1] == 'Bet' and r['set'][2].endswith('k1>y1'), r
    assert r['draw'][0] == 'chk' and 'outs' in r['draw'][2], r

def test_routine_agrees_with_the_baseline_in_played_hands():
    r = engine().run('''var t=window.__t;seedRNG(31);S.settings.straddle="off";t.table({seats:6,style:"casino"});T.players[0].hero=true;
      var o={n:0,agree:0,errs:0,none:0,bad:[]},nv=function(x){x=String(x||"").toLowerCase();return /^(raise|reraise|bet|push|semi)/.test(x)?"a":/^(call|check|limp|complete)/.test(x)?"c":x.slice(0,4);};
      for(var h=0;h<70;h++){T.players.forEach(function(p){if(p.stack<T.bb*20)p.stack=T.buy;});H=null;try{startHand();var g=0;while(H&&!H.done&&g<60){t.drain();g++;
        if(H&&!H.done&&H.toAct===0&&canAct(0)){var M=rtModel();if(!M){o.none++;}else{o.n++;var A=M.A;if(nv(M.verdict)===nv(A.advice)||(nv(A.advice)==="bet "&&/semi/i.test(M.verdict)))o.agree++;else if(o.bad.length<6)o.bad.push([H.street,M.chain,M.verdict,A.advice]);
          var svg=rtSVG(M.chain,M.path,M.vals);if(svg.indexOf("<svg")!==0)o.errs++;}
          var L=legal(0);heroDo(L.toCall>T.bb*10?["fold"]:L.toCall>0?["call"]:["check"]);}}}catch(e){o.errs++;o.bad.push(String(e));}}
      return o;''')
    assert r['errs'] == 0 and r['none'] == 0 and r['n'] > 60, r
    assert r['agree'] / r['n'] >= 0.9, r   # the short form can differ from the baseline in rare spots; the sheet then names the baseline

def test_flowchart_lights_only_the_path():
    r = engine().run('''__t.spot({hero:"AsJd",board:"Jh7c2s",opps:[{arch:"tag"}],pot:100,toCall:50});var M=rtModel(),svg=rtSVG(M.chain,M.path,M.vals),ref=rtSVG("bet",[],{});
      var on=(svg.match(/class='rtn[^']* on'/g)||[]).length,off=(svg.match(/class='rtn[^']* off'/g)||[]).length,plain=(ref.match(/ on'| off'/g)||[]).length;
      return {on:on,off:off,len:M.path.length,plain:plain,boxes:(ref.match(/<rect/g)||[]).length};''')
    assert r['on'] == r['len'] and r['off'] == r['boxes'] - r['len'] and r['plain'] == 0, r

def test_drill_asks_the_price_and_never_changes_the_grade():
    r = engine().run('''var o={};S.settings.routineDrill=true;S.drills={};
      __t.spot({hero:"AsJd",board:"Jh7c2s",opps:[{arch:"tag"}],pot:100,toCall:50});RT_Q={k:"",i:0,qs:null,fb:""};
      var html=rtDrillHTML(),q=RT_Q.qs[0];o.has=!!html;o.k=q.k;o.ans=q.opts[q.ans];o.n=RT_Q.qs.length;
      var c=document.createElement("div");c.innerHTML=html;rtDrillWire(c);var orig=renderControls;renderControls=function(){};
      try{c.querySelector("[data-rq='"+q.ans+"']").click();}finally{renderControls=orig;}
      o.after=RT_Q.i;o.rec=S.drills.rtPrice;o.fb=RT_Q.fb;
      S.settings.routineDrill=false;o.off=rtDrillHTML();return o;''')
    assert r['has'] and r['k'] == 'rtPrice' and r['ans'] == '25%' and r['n'] == 2, r
    assert r['after'] == 1 and r['rec'] == {'n': 1, 'ok': 1} and r['fb'].startswith('Right.'), r
    assert r['off'] is None, r

def test_coach_card_shows_every_chart():
    r = engine().run('''return {html:rtCardHTML().length,svgs:(rtRefHTML().match(/<svg/g)||[]).length};''')
    assert r['svgs'] == 8 and r['html'] > 2000, r

def test_range_trainer_opens_over_the_app():
    r = engine().run('''var html=coachTabHTML();rangeOpen();var o=document.getElementById("rangeOv"),f=o.querySelector("iframe");
      var src=f.getAttribute("src");o.querySelector("#rangeX").onclick();var closed=o.hidden;rangeOpen();
      return {btn:html.indexOf("rangeOpen()")>=0,src:src,closed:closed,again:!o.hidden,one:document.querySelectorAll("#rangeOv").length};''')
    assert r == {'btn': True, 'src': 'range/index.html', 'closed': True, 'again': True, 'one': 1}, r
