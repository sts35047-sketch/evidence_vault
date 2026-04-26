/* EvidenceVault — script.js */

// ── Custom Cursor ─────────────────────────────────────────────
const outer = document.getElementById('cursor-outer');
const inner = document.getElementById('cursor-inner');
let mx=0,my=0,ox=0,oy=0;
document.addEventListener('mousemove', e => {
  mx=e.clientX; my=e.clientY;
  if(inner){ inner.style.left=mx+'px'; inner.style.top=my+'px'; }
});
(function lerpCursor(){
  ox+=(mx-ox)*.12; oy+=(my-oy)*.12;
  if(outer){ outer.style.left=ox+'px'; outer.style.top=oy+'px'; }
  requestAnimationFrame(lerpCursor);
})();
document.querySelectorAll('a,button').forEach(el=>{
  el.addEventListener('mouseenter',()=>outer&&(outer.style.transform='translate(-50%,-50%) scale(1.6)'));
  el.addEventListener('mouseleave',()=>outer&&(outer.style.transform='translate(-50%,-50%) scale(1)'));
});

// ── Scroll Reveal ─────────────────────────────────────────────
const ro = new IntersectionObserver(entries=>{
  entries.forEach(e=>{ if(e.isIntersecting){ e.target.classList.add('visible'); ro.unobserve(e.target); } });
},{threshold:.12});
document.querySelectorAll('.reveal').forEach(el=>ro.observe(el));

// ── Stat counter animation ────────────────────────────────────
function animateNum(el){
  const target=parseInt(el.textContent,10);
  if(isNaN(target)||target===0) return;
  let cur=0; const step=Math.max(1,Math.ceil(target/40));
  const t=setInterval(()=>{ cur=Math.min(cur+step,target); el.textContent=cur; if(cur>=target)clearInterval(t); },35);
}
const so=new IntersectionObserver(entries=>{
  entries.forEach(e=>{ if(e.isIntersecting){ e.target.querySelectorAll('.stat-num').forEach(animateNum); so.unobserve(e.target); } });
},{threshold:.5});
document.querySelectorAll('.stats-bar').forEach(el=>so.observe(el));

// ── Score bars animate on scroll ─────────────────────────────
const bo=new IntersectionObserver(entries=>{
  entries.forEach(e=>{ if(e.isIntersecting){
    e.target.querySelectorAll('.score-bar-fill').forEach(b=>{ const w=b.style.width; b.style.width='0%'; setTimeout(()=>b.style.width=w,60); });
    bo.unobserve(e.target);
  }});
},{threshold:.2});
document.querySelectorAll('.scores-grid').forEach(el=>bo.observe(el));

// ── Flash auto-dismiss ────────────────────────────────────────
document.querySelectorAll('.flash-msg').forEach(el=>{
  setTimeout(()=>{ el.style.transition='opacity .5s'; el.style.opacity='0'; setTimeout(()=>el.remove(),500); },5000);
});
