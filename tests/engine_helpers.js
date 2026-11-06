/* Evaluated once inside the app (index.html?test=1). Everything the tests need hangs off window.__t.
   Timers are replaced by a queue so a hand runs synchronously and deterministically. */
window.__t=(function(){
  var q=[];
  window.setTimeout=function(f){q.push(f);return q.length;};
  window.clearTimeout=function(){};
  render=function(){};renderControls=function(){};sfx=function(){};buzz=function(){};toast=function(){};flyChips=function(){};sayText=function(){};
  chatterStart=function(){};chatterEnd=function(){};greetRivals=function(){};showModal=function(){};unlock=function(){};confetti=function(){};
  S.settings.speed="fast";S.settings.rit="never";S.settings.difficulty="realistic";
  var T0={};
  function card(s){return "23456789TJQKA".indexOf(s[0])*4+"shdc".indexOf(s[1]);}
  function cards(s){var o=[];for(var i=0;i<s.length;i+=2)o.push(card(s.substr(i,2)));return o;}
  function drain(max){var g=0;while(q.length&&g<(max||8000)){var f=q.shift();f();g++;if(H&&H.done)break;}q.length=0;}
  /* a cash table where the hero is played by a bot, so whole hands run unattended */
  function table(o){o=o||{};var n=o.seats||6;
    S.customCfg={bi:o.bi===undefined?1:o.bi,depth:o.depth||100,seats:n,style:o.style||"casino",spec:o.spec||["station","limper","weekend","tag","nit","lag","random","random"],table:"classic",atm:"vegas"};
    T=makeCash(customStake());S.cash=T;T.noLeave=true;T.players[0].hero=false;T.players[0].arch="tag";T.players[0].skill="regular";T.players[0].st=Object.assign({},ARCH.tag.st);T.players[0].name="HeroBot";
    if(o.rake)T.room={rake:o.rake};else T.room=undefined;return T;}
  function chipsTotal(){return T.players.reduce(function(a,p){return a+p.stack;},0);}
  function hand(){T.players.forEach(function(p){if(p.stack<T.bb*20)p.stack=T.buy;});H=null;startHand();drain();return H;}
  function play(n,o){o=o||{};var out={hands:0,errors:0,drift:0,dupCards:0,start:chipsTotal(),sig:[],max:0,rake0:T.rakePaid||0};
    for(var i=0;i<n;i++){var before=chipsTotal(),r0=T.rakePaid||0;
      T.players.forEach(function(p){if(p.stack<T.bb*20){before+=T.buy-p.stack;p.stack=T.buy;}});
      H=null;try{startHand();drain();}catch(e){out.errors++;continue;}
      if(!H||!H.done){out.errors++;continue;}
      out.hands++;var after=chipsTotal(),rk=(T.rakePaid||0)-r0;
      if(after+rk!==before){out.drift++;if(out.drift<4)out.firstDrift={before:before,after:after,rake:rk,hand:i};}
      /* card uniqueness: every hole card plus the board must be distinct */
      var seen={},dup=0;H.seats.forEach(function(j){(H.s[j].cards||[]).forEach(function(c){if(seen[c])dup++;seen[c]=1;});});H.board.forEach(function(c){if(seen[c])dup++;seen[c]=1;});if(dup)out.dupCards++;
      out.sig.push(T.players.map(function(p){return p.stack;}).join(","));}
    out.end=chipsTotal();out.rake=(T.rakePaid||0)-out.rake0;out.sig=out.sig.join("|");return out;}
  /* a hand-built spot for analysis tests. cfg: hero, board, opps:[{arch,stack}], pot, heroStack, toCall, ip, hist */
  function spot(cfg){var opps=cfg.opps,n=opps.length+1;
    S.customCfg={bi:1,depth:100,seats:n,style:"online",spec:opps.map(function(o){return o.arch;}),table:"classic",atm:"vegas"};
    seedRNG(cfg.seed||11);T=makeCash(customStake());S.cash=T;T.noLeave=true;if(cfg.rake)T.room={rake:cfg.rake};
    H=null;startHand();q.length=0;
    var bd=cards(cfg.board||""),pot=cfg.pot,toCall=cfg.toCall||0,bb=T.bb;
    H.board=bd;H.street=bd.length===0?0:bd.length-2;H.done=false;H.showdown=false;
    H.button=cfg.ip===false?1:0;
    H.seats.forEach(function(i){var s=H.s[i];s.folded=false;s.allin=false;s.acted=false;s.sb=0;s.tot=pot/n;s.label="";});
    T.players[0].stack=cfg.heroStack===undefined?100*bb:cfg.heroStack;H.s[0].cards=cards(cfg.hero);
    opps.forEach(function(o,k){var i=k+1;T.players[i].stack=o.stack===undefined?100*bb:o.stack;if(o.cards)H.s[i].cards=cards(o.cards);});
    if(toCall>0){H.s[1].sb=toCall;H.s[1].tot+=toCall;H.cur=toCall;H.raises=1;H.lastAgg=1;H.lastBetF=toCall/pot;}else{H.cur=0;H.raises=0;H.lastAgg=-1;H.lastBetF=0;}
    H.minR=bb;H.toAct=0;H.preAgg=cfg.preAgg===undefined?1:cfg.preAgg;
    H.pos=H.pos||{};H.pos[0]=cfg.ip===false?"BB":"BTN";opps.forEach(function(o,k){H.pos[k+1]=cfg.vpos||(cfg.ip===false?"BTN":"BB");});
    H.bbI=cfg.vpos==="BB"?1:-1;H.sbI=cfg.vpos==="SB"?1:-1;
    var h=[];/* pre-flop story: each opponent opened, hero called */
    var pre=cfg.pre||"open";
    opps.forEach(function(o,k){h.push({i:k+1,st:0,a:pre==="limp"?"call":"raise",toCall:bb,pot:bb*1.5,nOpp:n-1,raises:pre==="3bet"?1:0,la:pre==="3bet"?0:-1,lf:0});});
    h.push({i:0,st:0,a:"call",toCall:bb*2,pot:bb*3.5,nOpp:n-1,raises:1,la:1,lf:0});
    (cfg.history||[]).forEach(function(e){h.push(Object.assign({st:H.street,toCall:0,pot:pot,nOpp:n-1,raises:0,la:-1,lf:0},e));});
    H.hist=h;H._ar={};H.evA=null;RESP_MEMO={};return H;}
  return {card:card,cards:cards,table:table,hand:hand,play:play,spot:spot,drain:drain,chipsTotal:chipsTotal,q:q};
})()
