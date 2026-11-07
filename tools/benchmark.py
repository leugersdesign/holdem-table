"""Performance profile: python3 tools/benchmark.py [out.json]
Measures hand evaluation throughput, equity and EV-analysis latency, the cost of grading a decision, and heap growth over a long session,
at normal CPU and with the CPU throttled 4x (a rough stand-in for a mid-range phone). Medians of repeated runs, seeded, headless Chromium."""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'tests'))
import harness
from playwright.sync_api import sync_playwright

def make(throttle):
    e = harness.Engine.__new__(harness.Engine)
    e._pw = sync_playwright().start(); e._browser = e._pw.chromium.launch(args=['--enable-precise-memory-info', '--js-flags=--expose-gc'])
    e.page = e._browser.new_page(); e.errors = []; e.page.on('pageerror', lambda x: e.errors.append(str(x))); e.reset()
    cdp = e.page.context.new_cdp_session(e.page)
    if throttle > 1: cdp.send('Emulation.setCPUThrottlingRate', {'rate': throttle})
    return e, cdp

MED = 'function med(f,n){var t=[];for(var i=0;i<n;i++){var a=performance.now();f();t.push(performance.now()-a);}t.sort(function(x,y){return x-y;});return Math.round(t[t.length>>1]*10)/10;}'

def measure(throttle):
    e, cdp = make(throttle); out = {'cpu_throttle': throttle}
    e.run('seedRNG(3);1')
    out['evals_per_sec'] = e.run('''var deck=[];for(var i=0;i<52;i++)deck.push(i);var hands=[];for(var k=0;k<2000;k++){for(var i=51;i>0;i--){var j=Math.floor(RNG()*(i+1)),t=deck[i];deck[i]=deck[j];deck[j]=t;}hands.push(deck.slice(0,7));}
      var t0=performance.now(),n=0;while(performance.now()-t0<1000){for(var k=0;k<2000;k++){evaluate(hands[k]);n++;}}return Math.round(n/((performance.now()-t0)/1000));''')
    spots = {
      'flop heads-up': '__t.spot({hero:"AhKd",board:"Ks7d2c",opps:[{arch:"weekend"}],pot:20,seed:5})',
      'flop three-way': '__t.spot({hero:"Jc8c",board:"Ks7d2c",opps:[{arch:"weekend"},{arch:"tag"}],pot:30,seed:5})',
      'river heads-up': '__t.spot({hero:"KhJd",board:"Ks7d2c9h4s",opps:[{arch:"nit"}],pot:40,seed:5})'}
    for k, s in spots.items():
        out['evAnalyze ms, ' + k] = e.run(MED + 'seedRNG(5);' + s + ';return med(function(){H._ar={};RESP_MEMO={};H.evA=null;evAnalyze();},7);')
        out['grade a decision ms, ' + k] = e.run(MED + 'seedRNG(5);' + s + ';S.coach=blankCoach();return med(function(){H._ar={};H.evA=null;H.dec=[];recordDecision(["check"]);},5);')
        out['grade at the tap ms after the idle precompute, ' + k] = e.run('var t=[];seedRNG(5);' + s + ';S.coach=blankCoach();for(var i=0;i<5;i++){H._ar={};H.evA=null;H.dec=[];prewarmNow();var a=performance.now();recordDecision(["check"]);t.push(performance.now()-a);}t.sort(function(x,y){return x-y;});return Math.round(t[2]*10)/10;')
    pre = '__t.preSpot({hero:"KhQd",pos:"BTN",opps:[{arch:"station",pos:"UTG"},{arch:"tag",pos:"SB"},{arch:"tag",pos:"BB"}],actions:[{i:1,a:"call"}]})'
    out['preAnalyze ms, limped pot'] = e.run(MED + 'seedRNG(5);' + pre + ';return med(function(){H.preA=null;preAnalyze();},7);')
    out['grade at the tap ms after the idle precompute, pre-flop'] = e.run('var t=[];seedRNG(5);' + pre + ';S.coach=blankCoach();for(var i=0;i<5;i++){H.preA=null;H.dec=[];prewarmNow();var a=performance.now();recordDecision(["call"]);t.push(performance.now()-a);}t.sort(function(x,y){return x-y;});return Math.round(t[2]*10)/10;')
    out['grade a decision ms, pre-flop'] = e.run(MED + 'seedRNG(5);' + pre + ';S.coach=blankCoach();return med(function(){H.preA=null;H.dec=[];recordDecision(["call"]);},5);')
    out['open the analysis sheet ms (adds three what-if runs), pre-flop'] = e.run(MED + 'seedRNG(5);' + pre + ';return med(function(){H.preA=null;preAnalysisHTML();},5);')
    out['open the analysis sheet ms (adds three what-if runs), flop'] = e.run(MED + 'seedRNG(5);' + spots['flop heads-up'] + ';return med(function(){H._ar={};H.evA=null;analysisHTML();},5);')
    e.run('seedRNG(9);__t.table({seats:6,spec:["station","limper","weekend","tag","nit"]});1')
    def heap():
        e.page.evaluate('()=>{if(window.gc){gc();gc();}}'); cdp.send('HeapProfiler.collectGarbage')
        return e.page.evaluate('()=>performance.memory.usedJSHeapSize')
    h0 = heap(); t0 = time.time()
    r = e.run('return __t.play(3000);'); secs = time.time() - t0; h1 = heap()
    out['long session, 3000 hands'] = {'hands': r['hands'], 'errors': r['errors'], 'chip_drift': r['drift'], 'duplicate_cards': r['dupCards'], 'seconds': round(secs, 1),
                                       'heap_before_MB': round(h0 / 1e6, 2), 'heap_after_MB': round(h1 / 1e6, 2), 'saved_state_KB': round(e.run('return JSON.stringify(S).length;') / 1000, 1)}
    out['page_errors'] = e.errors[:3]; e.close(); return out

if __name__ == '__main__':
    res = [measure(1), measure(4)]
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'docs', 'performance.json')
    json.dump(res, open(path, 'w'), indent=1); print(json.dumps(res, indent=1))
