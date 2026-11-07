(function(seedBase,tables,hands,seats){var rows=[];
  for(var t=0;t<tables;t++){seedRNG(seedBase+t*7);__t.table({seats:9,spec:seats,style:"casino"});T.hud={};
    for(var i=0;i<hands;i++)__t.hand();
    T.players.forEach(function(p){if(p.hero||p.human||!p.arch)return;var r=T.hud&&T.hud[p.name];if(r&&r.h>=30)rows.push({k:p.arch,h:r.h,vp:r.vp,pr:r.pr,agg:r.agg,call:r.call,cbO:r.cbO,cb:r.cb,fbO:r.fbO,fb:r.fb});});}
  return {rows:rows};})
