/* Hold'em Table service worker: works offline after the first visit. Bump VERSION when you update index.html. */
var VERSION="holdem-v56";
var SHELL=["./","./index.html","./range/index.html","./manifest.webmanifest","./icon-192.png","./icon-512.png","./icon-maskable-512.png","./apple-touch-icon.png"];
self.addEventListener("install",function(e){e.waitUntil(caches.open(VERSION).then(function(c){return c.addAll(SHELL);}).then(function(){return self.skipWaiting();}));});
self.addEventListener("activate",function(e){e.waitUntil(caches.keys().then(function(ks){return Promise.all(ks.filter(function(k){return k!==VERSION;}).map(function(k){return caches.delete(k);}));}).then(function(){return self.clients.claim();}));});
self.addEventListener("fetch",function(e){
  var req=e.request;if(req.method!=="GET")return;
  var url=new URL(req.url);
  if(req.mode==="navigate"){
    /* the game and the Range Trainer (range/) are separate pages: cache each under its own key so one never overwrites the other */
    var key=/\/range\/(index\.html)?$/.test(new URL(req.url).pathname)?"./range/index.html":"./index.html";
    e.respondWith(fetch(req).then(function(r){if(r&&r.ok){var cp=r.clone();caches.open(VERSION).then(function(c){c.put(key,cp);});}return r;}).catch(function(){return caches.match(key);}));return;
  }
  if(url.origin===location.origin||url.hostname.indexOf("fonts.g")===0){
    e.respondWith(caches.match(req).then(function(hit){
      var net=fetch(req).then(function(r){if(r&&(r.ok||r.type==="opaque")){var cp=r.clone();caches.open(VERSION).then(function(c){c.put(req,cp);});}return r;}).catch(function(){return hit;});
      return hit||net;
    }));
  }
});
