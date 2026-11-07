(function(NIND,NHAND){var TYPES=["station","limper","whale","maniac","nit","weekend","tag","lag","shark","wild","thinker","shorty"];
  seedRNG(2024);__t.table({seats:6});
  /* a fixed bank of random hands on random boards, labelled the way a player labels them */
  var bank={1:[],2:[],3:[]};[1,2,3].forEach(function(st){for(var k=0;k<NHAND;k++){var d=shuffle(Array.from({length:52},function(_,i){return i;})),hi=hcCached(d.slice(0,2),d.slice(2,2+st+2));bank[st].push(hi);}});
  var out={};
  TYPES.forEach(function(k){var f={n:0,callWeak:[0,0],foldBet:{1:[0,0],2:[0,0],3:[0,0]},bet:[0,0],bluffRiver:[0,0],raise:[0,0],xrRaise:[0,0],noXrRaise:[0,0],barrelAir:[0,0],noBarrelAir:[0,0],callBig:{5:[0,0],20:[0,0],50:[0,0]},foldBySize:{0.33:[0,0],0.66:[0,0],1:[0,0],2:[0,0]}};
    for(var ind=1;ind<=NIND;ind++){seedRNG(ind*977+k.length);var b=archBot(k,1000,[]),P=liveProf(b);
      [1,2,3].forEach(function(st){bank[st].forEach(function(hi){
        var base={st:st,nOpp:1,isPreAgg:false,facingRaise:false,raises:1,canRaise:true,memAdj:0,pot:100};
        /* facing a bet */
        [0.33,0.66,1,2].forEach(function(fr){var c=Object.assign({},base,{toCall:100*fr}),d=liveDecide(P,hi,c,RNG);f.n++;var fold=d[0]==="fold"?1:0;f.foldBySize[fr][0]+=fold;f.foldBySize[fr][1]++;
          if(fr===0.66){f.foldBet[st][0]+=fold;f.foldBet[st][1]++;if(hi.S>=1.5&&hi.S<=3.2){f.callWeak[0]+=d[0]!=="fold"?1:0;f.callWeak[1]++;}f.raise[0]+=d[0]==="raise"?1:0;f.raise[1]++;}});
        if(st===3)[5,20,50].forEach(function(m){var d=liveDecide(P,hi,Object.assign({},base,{toCall:100*m}),RNG);f.callBig[m][0]+=d[0]!=="fold"?1:0;f.callBig[m][1]++;f.n++;});
        /* checked to */
        var dc=liveDecide(P,hi,Object.assign({},base,{toCall:0,raises:0}),RNG);f.n++;f.bet[0]+=dc[0]==="bet"?1:0;f.bet[1]++;
        if(st===3&&hi.S<2){f.bluffRiver[0]+=dc[0]==="bet"?1:0;f.bluffRiver[1]++;}
        if(st>=2&&hi.S<2){var d1=liveDecide(P,hi,Object.assign({},base,{toCall:0,raises:0,prevAgg:true}),RNG),d0=liveDecide(P,hi,Object.assign({},base,{toCall:0,raises:0,prevAgg:false}),RNG);f.barrelAir[0]+=d1[0]==="bet"?1:0;f.barrelAir[1]++;f.noBarrelAir[0]+=d0[0]==="bet"?1:0;f.noBarrelAir[1]++;f.n+=2;}
        if(hi.S>=4.5){var x1=liveDecide(P,hi,Object.assign({},base,{toCall:66,xr:true}),RNG),x0=liveDecide(P,hi,Object.assign({},base,{toCall:66,xr:false}),RNG);f.xrRaise[0]+=x1[0]==="raise"?1:0;f.xrRaise[1]++;f.noXrRaise[0]+=x0[0]==="raise"?1:0;f.noXrRaise[1]++;f.n+=2;}
      });});}
    out[k]=f;});
  return out;})
