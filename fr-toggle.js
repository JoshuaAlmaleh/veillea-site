/* /fr/ only: in-place FR/EN toggle. The static HTML is French; English comes from /fr/index.en.json (built by build_pages.py).
   Shares the root page's saved choice (key veillea_root_lang); no other page reads it. No browser-language guess. */
(function(){
"use strict";
const LK="veillea_root_lang",APP="https://app.veillea.ca";
const main=document.querySelector("main"),meta=document.querySelector('meta[name="description"]');
const FR={main:main.innerHTML,title:document.title,desc:meta?meta.content:"",lang:document.documentElement.lang||"fr-CA"};
let EN=window.__FR_EN__||null,cur="fr";
function load(){return EN?Promise.resolve(EN):fetch("/fr/index.en.json?v=w18").then(r=>{if(!r.ok)throw 0;return r.json()}).then(j=>EN=j)}
function mapText(m){document.querySelectorAll("header, footer").forEach(root=>{const w=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);let n;
 while((n=w.nextNode())){const k=n.nodeValue;if(Object.prototype.hasOwnProperty.call(m,k))n.nodeValue=m[k]}})}
function appLang(l){document.querySelectorAll('header a[href^="'+APP+'"], footer a[href^="'+APP+'"]').forEach(a=>{try{const u=new URL(a.href);if(u.searchParams.has("lang")){u.searchParams.set("lang",l);a.href=u.toString()}}catch(e){}})}
function buttons(l){document.querySelectorAll(".lang button").forEach(b=>{const on=b.dataset.l===l;b.classList.toggle("on",on);b.setAttribute("aria-pressed",on?"true":"false")})}
function syncUrl(l){try{const u=new URL(location.href);if(l==="en")u.searchParams.set("lang","en");else u.searchParams.delete("lang");history.replaceState(history.state,"",u.pathname+u.search+u.hash)}catch(e){}}
function setLang(l){
 if(l===cur){buttons(l);return Promise.resolve()}
 if(l==="en")return load().then(d=>{main.innerHTML=d.main;document.title=d.title;if(meta)meta.content=d.desc;document.documentElement.lang=d.lang;mapText(d.map);appLang("en");cur="en";buttons("en")}).catch(()=>{buttons(cur)});
 const rev={};if(EN)Object.keys(EN.map).forEach(k=>rev[EN.map[k]]=k);
 main.innerHTML=FR.main;document.title=FR.title;if(meta)meta.content=FR.desc;document.documentElement.lang=FR.lang;mapText(rev);appLang("fr");cur="fr";buttons("fr");return Promise.resolve()}
document.querySelectorAll(".lang button").forEach(b=>b.addEventListener("click",()=>{const l=b.dataset.l==="en"?"en":"fr";setLang(l).then(()=>{if(cur===l){try{localStorage.setItem(LK,l)}catch(e){}syncUrl(l)}})}));
const q=new URLSearchParams(location.search).get("lang");let saved=null;try{saved=localStorage.getItem(LK)}catch(e){}
const L0=q==="en"||q==="fr"?q:(saved==="en"?"en":"fr");
setLang(L0).then(()=>syncUrl(cur));
})();
