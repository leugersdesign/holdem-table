(function(SPOTS,M,stake,spec){var q=[];var mainST=function(f){q.push(f);return q.length;};window.setTimeout=mainST;window.clearTimeout=function(){};
  render=function(){};renderControls=function(){};sfx=function(){};buzz=function(){};toast=function(){};flyChips=function(){};sayText=function(){};chatterStart=function(){};chatterEnd=function(){};greetRivals=function(){};showModal=function(){};unlock=function(){};confetti=function(){};
  S.settings.speed="fast";S.settings.rit="never";S.settings.difficulty="realistic";
  if(spec){S.customCfg={bi:1,depth:100,seats:6,style:"casino",spec:spec.split(","),table:"classic",atm:"vegas"};T=makeCash(customStake());}else T=makeCash(STK(stake));
  S.cash=T;T.noLeave=true;T.players[0].hero=false;T.players[0].arch="tag";T.players[0].skill="regular";T.players[0].st=Object.assign({},ARCH.tag.st);T.players[0].name="HeroBot";
  var spots=[],inRoll=false,_bp=botPost,tms=0;
  function roll(hs,ts,o,decks){var res=[];for(var m=0;m<decks.length;m++){H=JSON.parse(hs);T=JSON.parse(ts);S.cash=T;H.deck=decks[m].slice();var before=T.players[0].stack,rq=[];window.setTimeout=function(f){rq.push(f);return rq.length;};inRoll=true;
      try{if(o.k==="fold")act(0,"fold");else if(o.k==="check")act(0,"check");else if(o.k==="call")act(0,"call");else act(0,"raise",o.amt);
        var g=0;while(rq.length&&g<3000&&!H.done){rq.shift()();g++;}}catch(e){}
      inRoll=false;window.setTimeout=mainST;res.push(H.done?(T.players[0].stack-before)/T.bb:null);}
    var v=res.filter(function(x){return x!==null;});return v.length?v.reduce(function(a,b){return a+b;},0)/v.length:null;}
  botPost=function(i){if(i!==0||inRoll||H.street<1||spots.length>=SPOTS)return _bp(i);
    delete H._ar;var t1=Date.now(),A=evAnalyze();tms+=Date.now()-t1;if(!A)return _bp(i);
    var adv=adviseHero(false).advice,hs=JSON.stringify(H,function(k,v){return (k==='evA'||k==='_ar'||k==='_ev')?undefined:v;}),ts=JSON.stringify(T),decks=[];for(var m=0;m<M;m++)decks.push(shuffle(H.deck.slice()));
    var rec={st:H.street,hu:A.hu,opts:[]};A.opts.forEach(function(o){var r=roll(hs,ts,o,decks);rec.opts.push({k:o.k,lab:o.lab,model:o.bb,real:r,extrap:!!o.extrap});});
    H=JSON.parse(hs);T=JSON.parse(ts);S.cash=T;
    var botD=_bp(i);var bk=botD[0]==="raise"?(H.cur>0?"raise":"bet"):botD[0];rec.bot=bk;rec.adv=adv;rec.best=A.best.k+"|"+A.best.amt;rec.opts.forEach(function(o,ix){o.rec=(A.opts[ix]===A.best);});spots.push(rec);return botD;};
  var n=0;while(spots.length<SPOTS&&n<6000){T.players.forEach(function(p){if(p.stack<T.buy*0.5)p.stack=T.buy;});H=null;try{startHand();}catch(e){}var g=0;while(q.length&&g<6000){var f=q.shift();try{f();}catch(e){break;}g++;if(H&&H.done)break;}q.length=0;n++;}
  return JSON.stringify({spots:spots,hands:n,avgEvMs:Math.round(tms/Math.max(1,spots.length))});})
