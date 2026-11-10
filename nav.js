/* Mobile nav: hamburger opens the same header links (plus Login and the trial CTA) below 900px. */
(function(){
"use strict";
const header=document.querySelector("header");
const btn=document.querySelector(".nav-toggle");
const panel=document.getElementById("site-nav");
if(!header||!btn||!panel)return;
function isOpen(){return header.classList.contains("nav-open")}
function close(){
  const was=isOpen();
  header.classList.remove("nav-open");
  btn.setAttribute("aria-expanded","false");
  if(was&&panel.contains(document.activeElement))btn.focus();
}
function open(){header.classList.add("nav-open");btn.setAttribute("aria-expanded","true")}
function toggle(){isOpen()?close():open()}
btn.addEventListener("click",function(e){e.stopPropagation();toggle()});
document.addEventListener("click",function(e){
  if(!isOpen())return;
  if(!panel.contains(e.target)&&!btn.contains(e.target))close();
});
document.addEventListener("keydown",function(e){if(e.key==="Escape")close()});
panel.querySelectorAll("a").forEach(function(a){a.addEventListener("click",close)});
document.querySelectorAll(".lang button").forEach(function(b){b.addEventListener("click",close)});
window.addEventListener("resize",function(){if(window.matchMedia("(min-width:901px)").matches)close()});
})();
