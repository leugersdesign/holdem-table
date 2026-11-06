(function(N,style,specStr){var q=[];window.setTimeout=function(f){q.push(f);return q.length;};window.clearTimeout=function(){};
  render=function(){};renderControls=function(){};sfx=function(){};buzz=function(){};toast=function(){};flyChips=function(){};sayText=function(){};chatterStart=function(){};chatterEnd=function(){};greetRivals=function(){};
  S.settings.speed="fast";S.settings.rit="never";S.settings.difficulty="realistic";
  S.customCfg={bi:1,depth:100,seats:9,style:style,spec:specStr.split(","),table:"classic",atm:"vegas"};
  T=makeCash(customStake());S.cash=T;T.noLeave=true;
  T.players[0].hero=false;T.players[0].arch="tag";T.players[0].skill="regular";T.players[0].st=Object.assign({},ARCH.tag.st);T.players[0].name="HeroBot";
  var rec=[],errs=0,_bp=botPre;
  botPre=function(i){var p=T.players[i],k=liveKey(p),lim=H.seats.filter(function(j){return j!==i&&j!==H.bbI&&j!==H.sbI&&j!==H.straddle&&H.s[j].tot>0&&!H.s[j].folded;}).length;
    var sit=H.raises>=2?"3b":H.raises===1?"r":lim>0?"l":"o",pos=H.pos[i],pg=i===H.bbI?"BB":i===H.sbI?"SB":["CO","BTN"].indexOf(pos)>=0?"LP":["MP","HJ"].indexOf(pos)>=0?"MP":"EP";
    var d=_bp(i),a=d[0]==="raise"?"r":(d[0]==="call"||d[0]==="check")?"c":"f";var cd=codeOf(H.s[i].cards);rec.push([k,sit,pg,cd,a,inChart(pos,cd)?1:0,T.live?1:0]);return d;};
  for(var n=0;n<N;n++){T.players.forEach(function(p){if(p.stack<T.buy*0.5)p.stack=T.buy;});H=null;try{startHand();}catch(e){errs++;continue;}
    var g=0;while(q.length&&g<5000){var f=q.shift();try{f();}catch(e){errs++;break;}g++;if(H&&H.done)break;}q.length=0;if(!H||!H.done)errs++;}
  return JSON.stringify({errs:errs,rec:rec});})
