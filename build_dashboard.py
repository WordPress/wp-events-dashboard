#!/usr/bin/env python3
"""
Build events-dashboard.html from dashboard_data.json.

dashboard_data.json is assembled by the pull scripts + the browser pulls:
  - meetups: from data.js (Meetup API)
  - events:  verified WordCamp Central public counts
  - pipeline.funnel/records/scheduled/cancelled: pull_pipeline.py + browser funnel detail
  - pipeline.momentum: WordCamp Central wordcamp-status report (browser session)

Run:  python3 build_dashboard.py    ->  writes events-dashboard.html
"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = json.dumps(json.load(open(os.path.join(HERE, "dashboard_data.json"))), ensure_ascii=False)

TEMPLATE = r'''<!doctype html>
<html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>WordPress Community Events — Dashboard</title>
<style>
:root{--bg:#F6F7F7;--card:#fff;--ink:#1E1E1E;--muted:#50575E;--line:#DCDCDE;--usrow:#FBECEC;
--blue:#3858E9;--green:#2F7D5B;--amber:#B07A22;--red:#C0492B;--grey:#A7AAAD;--chip:#F0F0F1;
--blue-tint:#EAEEFD;--green-tint:#E9F3ED;--amber-tint:#F7EFDE;--red-tint:#FBECEC;
--serif:'Source Serif 4',Georgia,'Times New Roman',serif;
--sans:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
--shadow:0 1px 2px rgba(30,30,30,.05),0 2px 6px rgba(30,30,30,.06);--radius:14px;}
:root[data-theme="dark"]{--bg:#17150F;--card:#211E17;--ink:#ECE6DA;--muted:#A79E8C;--line:#332E24;--usrow:#3A241E;--chip:#2A251C;--blue-tint:#1B2340;--green-tint:#16281E;--amber-tint:#2C2617;--red-tint:#301C16;--shadow:0 1px 2px rgba(0,0,0,.3),0 2px 8px rgba(0,0,0,.25);}
:root[data-theme="light"]{--bg:#F6F7F7;--card:#fff;--ink:#1E1E1E;--muted:#50575E;--line:#DCDCDE;--usrow:#FBECEC;--chip:#F0F0F1;--blue-tint:#EAEEFD;--green-tint:#E9F3ED;--amber-tint:#F7EFDE;--red-tint:#FBECEC;--shadow:0 1px 2px rgba(30,30,30,.05),0 2px 6px rgba(30,30,30,.06);}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 var(--sans)}
.wrap{max-width:1120px;margin:0 auto;padding:24px 20px 70px}
h1{font-family:var(--serif);font-size:32px;font-weight:600;letter-spacing:-.01em;margin:0 0 5px;text-wrap:balance}
.sub{color:var(--muted);margin:0 0 20px;font-size:13.5px;max-width:64ch}
.tabs{display:flex;gap:6px;border-bottom:1px solid var(--line);margin-bottom:22px;flex-wrap:wrap}
.tab{padding:9px 16px;font-size:14px;font-weight:600;color:var(--muted);cursor:pointer;border:1px solid transparent;border-bottom:none;border-radius:9px 9px 0 0}
.tab.on{color:var(--ink);background:var(--card);border-color:var(--line)}
.view{display:none} .view.on{display:block}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(148px,1fr));gap:12px;margin-bottom:22px}
.tile{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:15px 17px;box-shadow:var(--shadow)}
.tile .n{font-family:var(--serif);font-size:29px;font-weight:600;line-height:1.05} .tile .l{font-size:12px;color:var(--muted);margin-top:3px}
.tile.hot{background:var(--blue-tint)} .tile.hot .n{color:var(--blue)}
.tile.good{background:var(--green-tint)} .tile.good .n{color:var(--green)}
.tile.us{background:var(--red-tint)} .tile.us .n{color:var(--red)}
.card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:20px;margin-bottom:20px;box-shadow:var(--shadow)}
.card h2{font-size:12px;margin:0 0 14px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);font-weight:600}
.card p b{color:var(--ink)}
.defs{display:grid;gap:15px;margin-top:2px}
.def{display:grid;grid-template-columns:170px 1fr;gap:16px;align-items:baseline}
.term{font-family:var(--serif);font-weight:600;font-size:17px}
.desc{color:var(--muted);font-size:14px;line-height:1.55}.desc b{color:var(--ink);font-weight:600}
@media(max-width:560px){.def{grid-template-columns:1fr;gap:3px}}
.frow{display:grid;grid-template-columns:200px 1fr 52px;align-items:center;gap:10px;margin:5px 0}
.frow .lbl{font-size:13px;text-align:right}
.frow .barwrap{background:var(--chip);border-radius:6px;height:20px;overflow:hidden;display:flex}
.frow .bar{height:100%}
.frow .cnt{font-size:13px;font-weight:600;color:var(--muted)}
.b-blue{background:var(--blue);opacity:.85}.b-green{background:var(--green)}.b-red{background:var(--red)}
.b-amber{background:var(--amber)}.b-grey{background:var(--grey)}
.legend{font-size:12px;color:var(--muted);margin-top:8px}.legend span{margin-right:14px}
.dot{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:4px;vertical-align:middle}
.wmap{width:100%;height:auto;display:block;margin:0 0 4px}
.wmap .land{fill:var(--chip);stroke:var(--line);stroke-width:.6}
.wmap .pt{opacity:.85}.wmap .pt.a{fill:var(--green)}.wmap .pt.d{fill:var(--red)}.wmap .pt.n{fill:var(--grey)}
.wmap .pt.ef{fill:var(--blue)}.wmap .pt.el{fill:var(--red)}.wmap .pt.ec{fill:var(--amber)}.wmap .pt.en{fill:var(--green)}
.mapwrap{position:relative}
#wmap,#wmap2{cursor:grab;touch-action:none}
#wmap.grabbing,#wmap2.grabbing{cursor:grabbing}
#wmap .pt,#wmap2 .pt{cursor:pointer}
#wmap .pt:hover,#wmap2 .pt:hover{r:3.6}
.mapzoom{position:absolute;top:8px;right:8px;display:flex;flex-direction:column;gap:4px;z-index:4}
.mapzoom button{width:30px;height:30px;border:1px solid var(--line);background:var(--card);border-radius:6px;cursor:pointer;font-size:17px;line-height:1;color:var(--ink);box-shadow:var(--shadow);padding:0}
.mapzoom button:hover{border-color:var(--blue)}
.maptip{position:absolute;display:none;z-index:6;max-width:210px;background:var(--card);border:1px solid var(--line);border-radius:8px;box-shadow:var(--shadow);padding:9px 11px;font-size:12px;line-height:1.45;color:var(--ink)}
.maptip .cl{position:absolute;top:3px;right:7px;cursor:pointer;color:var(--muted);font-size:14px;line-height:1}
/* "met this month" roll-up: country chips always, city names only while the list is short */
.mocc{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
.mocc span{display:inline-flex;align-items:baseline;gap:6px;font-size:12px;padding:3px 10px;border-radius:999px;background:var(--chip);border:1px solid var(--line);color:var(--ink);white-space:nowrap}
.mocc span b{color:var(--muted);font-weight:600;font-variant-numeric:tabular-nums}
.mocc span.more{background:none;border-color:transparent;color:var(--muted);padding-left:2px}
.mocity{color:var(--muted);font-size:12px;margin:10px 0 0;line-height:1.7}
.mocity b{color:var(--ink);font-weight:600}
.mrow{display:grid;grid-template-columns:64px 1fr;align-items:center;gap:10px;margin:6px 0}
.mrow .mo{font-size:12px;color:var(--muted);text-align:right}
.mbars{display:flex;flex-direction:column;gap:3px}
.mbar{display:flex;align-items:center;gap:8px}
.mbar .t{height:12px;border-radius:3px}.mbar .v{font-size:11px;color:var(--muted)}
.controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:14px}
.controls input,.controls select{font:13px inherit;padding:7px 10px;border:1px solid var(--line);border-radius:8px;background:#fff;color:var(--ink)}
.controls input{flex:1;min-width:170px}
.btn{font:13px inherit;padding:7px 12px;border:1px solid var(--line);border-radius:8px;background:#fff;cursor:pointer;color:var(--ink)}
.btn.on{background:var(--red);color:#fff;border-color:var(--red)}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:11px;text-transform:uppercase;letter-spacing:.03em;color:var(--muted);cursor:pointer;white-space:nowrap;user-select:none}
tr.us td{background:var(--usrow)} td.num{text-align:right;font-variant-numeric:tabular-nums}
.stage,.fmt{display:inline-block;font-size:11px;padding:2px 7px;border-radius:20px;white-space:nowrap}
.stage{background:var(--chip)} .fmt{border:1px solid var(--line);color:var(--muted)}
.funnel-row{cursor:pointer;border-radius:6px;padding:1px 6px;margin:0 -6px;transition:background .12s}
.funnel-row:hover{background:var(--chip)}
.usdot{color:var(--red);font-weight:700} a{color:var(--blue);text-decoration:none} a:hover{text-decoration:underline}
.foot{color:var(--muted);font-size:12px;margin-top:10px}
.src{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 18px;font-size:12px;color:var(--muted)}
.src b{color:var(--ink)}
.mgtabs{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px}
.mgtab{font:13px inherit;padding:6px 13px;border:1px solid var(--line);border-radius:999px;background:var(--card);color:var(--muted);cursor:pointer}
.mgtab:hover{border-color:var(--blue)}
.mgtab.on{color:#fff}
.mgtab.on[data-c="all"]{background:var(--blue);border-color:var(--blue)}
.mgtab.on[data-c="Active"]{background:var(--green);border-color:var(--green)}
.mgtab.on[data-c="Fading"]{background:var(--amber);border-color:var(--amber)}
.mgtab.on[data-c="Inactive"]{background:var(--red);border-color:var(--red)}
.mgtab.on[data-c="Never"]{background:var(--grey);border-color:var(--grey)}
.mgtab .mgn{font-size:12px;opacity:.7;margin-left:3px}
.mgtab.on .mgn{opacity:.95}
.dot-after{margin-left:6px;margin-right:0}
.mgpager{display:flex;align-items:center;gap:12px;margin-top:14px;flex-wrap:wrap}
.mgpg{font:13px inherit;padding:6px 13px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--ink);cursor:pointer}
.mgpg:hover:not(:disabled){border-color:var(--blue)}
.mgpg:disabled{opacity:.4;cursor:default}
.mgpginfo{font-size:13px;color:var(--muted)}
@media(max-width:640px){.frow{grid-template-columns:120px 1fr 40px}.hidem{display:none}}
</style></head><body><div class="wrap">
<h1>WordPress Community Events</h1>
<p class="sub" id="sub"></p>
<div class="tabs">
  <div class="tab on" data-v="overview">Overview</div>
  <div class="tab" data-v="meetups">Meetups</div>
  <div class="tab" data-v="events">Events &amp; WordCamps</div>
  <div class="tab" data-v="pipeline">Pipeline</div>
</div>
<div class="view on" id="overview"></div>
<div class="view" id="meetups"></div>
<div class="view" id="events"></div>
<div class="view" id="pipeline"></div>
<div class="src" id="src"></div>
</div>
<script>
const D=__DATA__;
const $=id=>document.getElementById(id);
const MONTHS=['January','February','March','April','May','June','July','August','September','October','November','December'];
const fmtD=s=>{if(!s)return '';const m=/^(\d{4})-(\d{2})-(\d{2})/.exec(String(s));return m?`${m[1]}-${MONTHS[+m[2]-1]}-${m[3]}`:String(s);};
$('sub').textContent='Meetups, WordCamps, and the events application pipeline.';
function tiles(a){return `<div class="tiles">`+a.map(t=>`<div class="tile ${t[0]}"><div class="n">${t[1]}</div><div class="l">${t[2]}</div></div>`).join('')+`</div>`;}
function barRow(lbl,segs,total,max){const w=v=>Math.round(v/max*100);const inner=segs.map(s=>`<div class="bar ${s[0]}"${s[2]?` data-t="${s[2]}: ${s[1]}"`:''} style="width:${w(s[1])}%"></div>`).join('');return `<div class="frow"><div class="lbl">${lbl}</div><div class="barwrap">${inner}</div><div class="cnt">${total}</div></div>`;}
/* Attach a hover tooltip to any bar-chart wrapper: shows a segment's data-t ("<label>: <count>") near the cursor. */
function attachBarTip(wrap,tip){if(!wrap||!tip)return;wrap.addEventListener('mousemove',e=>{const b=e.target.closest?e.target.closest('.bar[data-t]'):null;if(!b){tip.style.display='none';return;}tip.textContent=b.getAttribute('data-t');const r=wrap.getBoundingClientRect();tip.style.display='block';let lx=Math.min(e.clientX-r.left+12,r.width-tip.offsetWidth-6);tip.style.left=Math.max(4,lx)+'px';tip.style.top=Math.max(4,e.clientY-r.top+12)+'px';});wrap.addEventListener('mouseleave',()=>tip.style.display='none');}

/* OVERVIEW — cross-cutting summary, two tiles per domain */
(function(){
 const usPipe=D.pipeline.records.filter(r=>r.us).length;
 $('overview').innerHTML=
  tiles([['hot',D.meetups.groups,'meetup groups'],['',D.meetups.members.toLocaleString(),'members'],
  ['good',D.events.ytd,'events YTD (+'+Math.round((D.events.ytd-D.events.ytdPrev)/D.events.ytdPrev*100)+'%)'],['',D.events.calendar,'on the 2026 calendar'],
  ['hot',D.pipeline.records.length,'WordCamps in pipeline'],['us',usPipe,'US events in flight']])
 +`<div class="card"><h2>What counts as a community event</h2>
   <p style="margin:0 0 16px;color:var(--muted)">The community runs several kinds of events.</p>
   <div class="defs">
     <div class="def"><div class="term">Meetups</div><div class="desc">Locally organized groups that hold meetings regularly, usually monthly, listed through the official WordPress chapter on Meetup.com.</div></div>
     <div class="def"><div class="term">WordCamps</div><div class="desc">Larger conferences. Three are flagships, <b>WordCamp US</b>, <b>WordCamp Europe</b>, and <b>WordCamp Asia</b>, with <b>WordCamp India</b> joining as the fourth in 2027. The rest are local WordCamps, run by a city or region.</div></div>
     <div class="def"><div class="term">Lighter-lift events</div><div class="desc">WordPress Campus Connect (held on a university campus), Women WordPress Day, WordPress Developer Day, WordPress Student Clubs, WordPress Day for AI, and do_action (a charity hackathon). Usually a single day, and far less to pull off.</div></div>
   </div></div>`;
})();

/* MEETUPS */
(function(){
 const m=D.meetups, mx=Math.max(...m.recency.map(r=>r[1]));
 const esc=x=>String(x==null?'':x).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
 /* One shared group-details card, used by both maps and the table click-popup.
    Shows location, size, activity, the local organizer(s) with a one-click link to
    their Meetup profile, and a link to the group page. */
 const CATLBL={Active:'active',Fading:'fading',Inactive:'inactive',Never:'never met'};
 function groupCard(g){
   const loc=[g.city,g.country].filter(Boolean).map(esc).join(', ');
   const stat=CATLBL[g.cat]?` · ${CATLBL[g.cat]}`:'';
   const L=g.leaders||[];
   const lead=L.length
     ? `<br>Organizer${L.length>1?'s':''}: `+L.map(p=>p.u?`<a href="${esc(p.u)}" target="_blank" rel="noopener noreferrer">${esc(p.n)}</a>`:esc(p.n)).join(', ')
     : '';
   return `<b>${esc(g.group)}</b><br>${loc}<br>${(g.members||0).toLocaleString()} members · last met ${g.last?fmtD(g.last):'never'}${stat}`
     +`${lead}<br><a href="${esc(g.url)}" target="_blank" rel="noopener noreferrer">Open group ↗</a>`;
 }
 const cf=l=>l.includes('30 days')||l.includes('1 to 3')?'b-green':l.includes('3 to 6')||l.includes('6 to 12')?'b-amber':l.includes('Never')?'b-grey':'b-red';
 let rec=m.recency.map(r=>barRow(r[0],[[cf(r[0]),r[1]]],r[1]+' ('+Math.round(r[1]/m.groups*100)+'%)',mx)).join('');
 const M=m.map, ord={a:0,d:1,n:2};
 let dots='';
 M.points.slice().sort((p,q)=>ord[p[2]]-ord[q[2]]).forEach(p=>dots+=`<circle class="pt ${p[2]}" cx="${p[0]}" cy="${p[1]}" r="2" data-i="${p[3]}"/>`);
 const mapCard=`<div class="card"><h2>Global footprint — ${m.groups} groups in ${m.countries} countries</h2>
   <div class="mapwrap" id="mapwrap">
    <svg class="wmap" id="wmap" viewBox="0 0 ${M.w} ${M.h}" preserveAspectRatio="xMidYMid meet" role="img" aria-label="World map of WordPress meetup groups colored by activity"><path class="land" d="${M.land}"/>${dots}</svg>
    <div class="mapzoom"><button type="button" id="mzin" aria-label="Zoom in">+</button><button type="button" id="mzout" aria-label="Zoom out">&minus;</button><button type="button" id="mzr" aria-label="Reset view" style="font-size:13px">&#8635;</button></div>
    <div class="maptip" id="maptip"></div>
   </div>
   <div class="legend"><span><i class="dot" style="background:var(--green)"></i>active ${M.counts.a}</span><span><i class="dot" style="background:var(--red)"></i>inactive 12mo+ ${M.counts.d}</span><span><i class="dot" style="background:var(--grey)"></i>never met ${M.counts.n}</span></div>
   <p class="foot">Every group in the official chapter, placed by city. Red mark is where a group has gone quiet. <span style="color:var(--muted)">Zoom, pan, and tap a dot for details.</span></p></div>`;
 const MO=m.monthMap||{points:[],count:0,month:''};
 const moLbl=(()=>{const p=(MO.month||'').split('-');return p.length===2?MONTHS[+p[1]-1]+' '+p[0]:'this month';})();
 let modots='';
 MO.points.forEach(p=>modots+=`<circle class="pt en" cx="${p[0]}" cy="${p[1]}" r="2.6" data-i="${p[2]}"/>`);
 /* Country roll-up + short-list of cities. Derived from allGroups, not MO.points, so groups
    without map coordinates still get counted here even though no dot exists for them. */
 const MOCC=10, MOCITY=12;
 const moCohort=(m.allGroups||[]).filter(g=>(g.last||'').slice(0,7)===MO.month);
 const moByC=Object.entries(moCohort.reduce((a,g)=>{const k=g.country||'Unknown';a[k]=(a[k]||0)+1;return a;},{}))
   .sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0]));
 const moExtra=moByC.length-MOCC;
 const moChips=moByC.length?`<div class="mocc">`
   +moByC.slice(0,MOCC).map(c=>`<span>${esc(c[0])}<b>${c[1]}</b></span>`).join('')
   +(moExtra>0?`<span class="more">+${moExtra} more ${moExtra===1?'country':'countries'}</span>`:'')
   +`</div>`:'';
 const moCities=(moCohort.length&&moCohort.length<=MOCITY)
   ? `<p class="mocity">`+moCohort.slice()
       .sort((a,b)=>(a.country||'').localeCompare(b.country||'')||(a.city||'').localeCompare(b.city||''))
       .map(g=>`<b>${esc(g.city||'Unknown')}</b>, ${esc(g.country||'Unknown')}`).join(' &middot; ')+`</p>`
   : '';
 const monthCard=`<div class="card"><h2>Where the community met this month &mdash; ${moLbl}</h2>
   <div class="mapwrap" id="mapwrap3">
    <svg class="wmap" id="wmap3" viewBox="0 0 ${M.w} ${M.h}" preserveAspectRatio="xMidYMid meet" role="img" aria-label="World map of WordPress meetup groups that met in ${moLbl}"><path class="land" d="${M.land}"/>${modots}</svg>
    <div class="mapzoom"><button type="button" id="mzin3" aria-label="Zoom in">+</button><button type="button" id="mzout3" aria-label="Zoom out">&minus;</button><button type="button" id="mzr3" aria-label="Reset view" style="font-size:13px">&#8635;</button></div>
    <div class="maptip" id="maptip3"></div>
   </div>
   <div class="legend"><span><i class="dot" style="background:var(--green)"></i>met in ${moLbl}</span></div>
   ${moChips}${moCities}
   <p class="foot"><b>${MO.count} ${MO.count===1?'group':'groups'} met this month</b> (${moLbl}).${MO.count>MO.points.length?` ${MO.count-MO.points.length} without map coordinates not shown.`:''} <span style="color:var(--muted)">Zoom, pan, and tap a dot for details.</span></p></div>`;
 /* Reactivation scoreboard (renders only if reactivation data is present) */
 const RX=m.reactivation; let reactCard='';
 if(RX){
   const netN=RX.reactivated.length-RX.newlyQuiet.length;
   reactCard=`<div class="card"><h2>Reactivation scoreboard</h2>
     <p class="foot" style="margin:-4px 0 14px">Groups that went quiet for 3+ months and are meeting again, versus active groups that just went quiet. Window ${fmtD(RX.from)} &ndash; ${fmtD(RX.to)}, widening as tracking accumulates.</p>
     ${tiles([['good',RX.reactivated.length,'reactivated'],['us',RX.newlyQuiet.length,'newly quiet'],['hot',(netN>=0?'+':'')+netN,'net revival'],['',RX.membersBack.toLocaleString(),'members brought back']])}
     <h3 style="font-family:var(--serif);font-size:15px;margin:18px 0 6px">Reactivated <span style="color:var(--muted);font-weight:400;font-size:13px">&mdash; started meeting again after a 3+ month break</span></h3>
     <table><thead><tr><th>Group</th><th class="hidem">Country</th><th class="num">Members</th><th>Gap</th><th>Met again</th></tr></thead><tbody id="rxbody"></tbody></table>
     <div class="mgpager" id="rxpager"></div>
     <h3 style="font-family:var(--serif);font-size:15px;margin:22px 0 6px">Newly gone quiet <span style="color:var(--muted);font-weight:400;font-size:13px">&mdash; active &rarr; fading, catch them early</span></h3>
     <table><thead><tr><th>Group</th><th class="hidem">Country</th><th class="num">Members</th><th>Last met</th><th>Quiet for</th><th>Status</th></tr></thead><tbody id="rqbody"></tbody></table>
     <div class="mgpager" id="rqpager"></div>
     <div class="legend"><span><i class="dot b-green"></i>reactivated</span><span><i class="dot b-amber"></i>fading</span><span><i class="dot b-red"></i>inactive</span></div>
     </div>`;
 }
 $('meetups').innerHTML=
  tiles([['hot',m.groups,'groups'],['',m.members.toLocaleString(),'members'],['',m.countries,'countries'],
   ['good',m.met90,'met in 90 days'],['us',m.dormant,'inactive 12mo+'],['',m.organizers.toLocaleString(),'organizers']])
  +mapCard
  +`<div class="card"><h2>When each group last met</h2>${rec}
    <div class="legend"><span><i class="dot b-green"></i>active</span><span><i class="dot b-amber"></i>fading (3&ndash;12mo)</span><span><i class="dot b-red"></i>inactive 1yr+</span><span><i class="dot b-grey"></i>never</span></div>
    <p class="foot">${m.toWatch} groups last met 3&ndash;12 months ago &mdash; the ones most likely to go quiet next.</p></div>`
  +monthCard
  +reactCard
  +`<div class="card"><h2>All groups by activity</h2>
    <div class="controls" style="margin-bottom:12px"><label style="font-size:13px;color:var(--muted)">Country</label><select id="mgcountry"></select></div>
    <div class="mgtabs" id="mgtabs"></div>
    <table><thead><tr><th>Group</th><th class="hidem">City</th><th>Country</th><th class="num">Members</th><th>Last met</th></tr></thead><tbody id="mgbody"></tbody></table>
    <div class="mgpager" id="mgpager"></div>
    <p class="foot" id="mgfoot"></p></div>`
  +`<div class="card"><h2>United States</h2><p style="margin:0">${m.us.groups} US groups, ${m.us.met90} of them (${Math.round(m.us.met90/m.us.groups*100)}%) met in the last 90 days. A strong meetup base, with fewer larger events built on top.</p></div>`;

 /* Shared group-details popup for table clicks — same card the maps show */
 const GBYID={}, GBYURL={};
 (m.allGroups||[]).forEach(g=>{GBYID[g.id]=g; if(g.url)GBYURL[g.url]=g;});
 (function(){
   let pop=document.getElementById('gpop');
   if(!pop){
     pop=document.createElement('div'); pop.id='gpop';
     pop.style.cssText='display:none;position:fixed;inset:0;z-index:9999;background:rgba(30,30,30,.28)';
     pop.innerHTML='<div id="gpopcard" style="position:absolute;background:var(--card);color:var(--ink);border:1px solid var(--line);border-radius:12px;box-shadow:0 10px 34px rgba(0,0,0,.2);padding:15px 18px;max-width:300px;font-size:13px;line-height:1.55"></div>';
     document.body.appendChild(pop);
   }
   const card=pop.querySelector('#gpopcard'), close=()=>{pop.style.display='none';};
   function openG(g,x,y){
     if(!g)return;
     card.innerHTML='<span id="gpx" style="position:absolute;top:5px;right:10px;cursor:pointer;color:var(--muted);font-size:17px;line-height:1">×</span>'+groupCard(g);
     pop.style.display='block';
     const cw=card.offsetWidth||280, ch=card.offsetHeight||150;
     card.style.left=Math.max(10,Math.min(x+12, window.innerWidth-cw-10))+'px';
     card.style.top=Math.max(10,Math.min(y+12, window.innerHeight-ch-10))+'px';
     document.getElementById('gpx').onclick=close;
   }
   pop.addEventListener('click',e=>{if(e.target===pop)close();});
   document.addEventListener('keydown',e=>{if(e.key==='Escape')close();});
   $('meetups').addEventListener('click',e=>{
     const a=e.target.closest('.gname'); if(!a)return;
     e.preventDefault();
     const g=(a.dataset.gid!=null&&a.dataset.gid!=='')?GBYID[a.dataset.gid]:GBYURL[a.dataset.gurl];
     openG(g, e.clientX, e.clientY);
   });
 })();

 /* Reactivation scoreboard: paginate each section (10 rows per page) */
 if(RX){
   const RP=10;
   const mo=(a,b)=>Math.max(0,Math.round((new Date(b)-new Date(a))/2592e6));
   const rxRow=g=>`<tr><td><span class="dot b-green"></span><a href="${esc(g.url)}" class="gname" data-gurl="${esc(g.url)}" rel="noopener noreferrer">${esc(g.group)}</a></td><td class="hidem">${esc(g.country)}</td><td class="num">${(g.members||0).toLocaleString()}</td><td>${Math.round(g.gapDays/30)} mo</td><td>${fmtD(g.met)}</td></tr>`;
   const rqRow=g=>`<tr><td><span class="dot ${g.cat==='Inactive'?'b-red':'b-amber'}"></span><a href="${esc(g.url)}" class="gname" data-gurl="${esc(g.url)}" rel="noopener noreferrer">${esc(g.group)}</a></td><td class="hidem">${esc(g.country)}</td><td class="num">${(g.members||0).toLocaleString()}</td><td>${fmtD(g.last)}</td><td>${mo(g.last,RX.to)} mo</td><td>${g.cat}</td></tr>`;
   const drawSec=(list,rowFn,bodyId,pagerId,page,onp)=>{
     const pages=Math.max(1,Math.ceil(list.length/RP)); if(page>pages)page=pages;
     $(bodyId).innerHTML=list.slice((page-1)*RP,page*RP).map(rowFn).join('')||`<tr><td colspan="6" style="color:var(--muted)">None in this window.</td></tr>`;
     $(pagerId).innerHTML=list.length>RP?`<button class="mgpg" data-p="prev"${page<=1?' disabled':''}>← Prev</button><span class="mgpginfo">${(page-1)*RP+1}–${Math.min(page*RP,list.length)} of ${list.length}</span><button class="mgpg" data-p="next"${page>=pages?' disabled':''}>Next →</button>`:'';
     $(pagerId).querySelectorAll('.mgpg').forEach(b=>b.onclick=()=>onp(b.dataset.p==='next'?1:-1,pages));
   };
   let rxp=1,rqp=1;
   const drawRx=()=>drawSec(RX.reactivated,rxRow,'rxbody','rxpager',rxp,(d,pg)=>{rxp=Math.max(1,Math.min(pg,rxp+d));drawRx();});
   const drawRq=()=>drawSec(RX.newlyQuiet,rqRow,'rqbody','rqpager',rqp,(d,pg)=>{rqp=Math.max(1,Math.min(pg,rqp+d));drawRq();});
   drawRx();drawRq();
 }

 /* All-groups table: tabs (All/Active/Fading/Inactive/Never) + 25-per-page pagination */
 const AG=(m.allGroups||[]).slice();  // pre-sorted members desc
 const PAGE=25, CATS=[['all','All'],['Active','Active'],['Fading','Fading'],['Inactive','Inactive'],['Never','Never']];
 let curCat='all', curCountry='all', curPage=1;
 const base=()=>curCountry==='all'?AG:AG.filter(g=>(g.country||'')===curCountry);
 const rowsFor=c=>{const b=base();return c==='all'?b:b.filter(g=>g.cat===c);};
 const CATDOT={Active:'b-green',Fading:'b-amber',Inactive:'b-red',Never:'b-grey'};
 const dotFor=c=>`<i class="dot dot-after ${CATDOT[c]||'b-grey'}" title="${c}" aria-label="${c}"></i>`;
 const _cc={}; AG.forEach(g=>{const k=g.country||'Unknown';_cc[k]=(_cc[k]||0)+1;});
 $('mgcountry').innerHTML=`<option value="all">All countries (${AG.length})</option>`+Object.keys(_cc).sort((a,b)=>_cc[b]-_cc[a]||a.localeCompare(b)).map(k=>`<option value="${esc(k)}">${esc(k)} (${_cc[k]})</option>`).join('');
 $('mgcountry').onchange=e=>{curCountry=e.target.value;curPage=1;drawTabs();drawTable();};
 function drawTabs(){
   $('mgtabs').innerHTML=CATS.map(c=>`<button class="mgtab${c[0]===curCat?' on':''}" data-c="${c[0]}">${c[1]}<span class="mgn">${rowsFor(c[0]).length}</span></button>`).join('');
   $('mgtabs').querySelectorAll('.mgtab').forEach(b=>b.onclick=()=>{curCat=b.dataset.c;curPage=1;drawTabs();drawTable();});
 }
 function drawTable(){
   const rows=rowsFor(curCat), pages=Math.max(1,Math.ceil(rows.length/PAGE));
   if(curPage>pages)curPage=pages;
   const slice=rows.slice((curPage-1)*PAGE,curPage*PAGE);
   $('mgbody').innerHTML=slice.length?slice.map(g=>`<tr><td><a href="${esc(g.url)}" class="gname" data-gid="${g.id}" rel="noopener">${esc(g.group)}</a>${dotFor(g.cat)}</td><td class="hidem">${esc(g.city)}</td><td>${esc(g.country)}</td><td class="num">${(g.members||0).toLocaleString()}</td><td>${g.last?fmtD(g.last):'never'}</td></tr>`).join(''):`<tr><td colspan="5" style="color:var(--muted)">No groups in this category.</td></tr>`;
   const from=rows.length?(curPage-1)*PAGE+1:0, to=Math.min(curPage*PAGE,rows.length);
   $('mgfoot').textContent=`Showing ${from}–${to} of ${rows.length} groups.`;
   $('mgpager').innerHTML=`<button class="mgpg" data-p="prev"${curPage<=1?' disabled':''}>← Prev</button><span class="mgpginfo">Page ${curPage} / ${pages}</span><button class="mgpg" data-p="next"${curPage>=pages?' disabled':''}>Next →</button>`;
   $('mgpager').querySelectorAll('.mgpg').forEach(b=>b.onclick=()=>{if(b.dataset.p==='prev'&&curPage>1)curPage--;else if(b.dataset.p==='next'&&curPage<pages)curPage++;drawTable();});
 }
 drawTabs();drawTable();

 /* Interactive map: wheel/button zoom, drag pan, dot popups (dependency-free) */
 (function(){
   const svg=$('wmap'), wrap=$('mapwrap'), tip=$('maptip');
   if(!svg||!wrap||!tip) return;
   const byId={}; (m.allGroups||[]).forEach(g=>byId[g.id]=g);
   const W=M.w, H=M.h, ASPECT=H/W, MINW=110;
   let vb={x:0,y:0,w:W,h:H}, pinned=false;
   const clamp=()=>{vb.w=Math.min(W,vb.w);vb.h=vb.w*ASPECT;vb.x=Math.max(0,Math.min(W-vb.w,vb.x));vb.y=Math.max(0,Math.min(H-vb.h,vb.y));};
   const apply=()=>svg.setAttribute('viewBox',`${vb.x} ${vb.y} ${vb.w} ${vb.h}`);
   function zoomAt(cx,cy,f){const r=svg.getBoundingClientRect();const ux=vb.x+(cx-r.left)/r.width*vb.w,uy=vb.y+(cy-r.top)/r.height*vb.h;const nw=Math.min(W,Math.max(MINW,vb.w*f)),s=nw/vb.w;vb.x=ux-(ux-vb.x)*s;vb.y=uy-(uy-vb.y)*s;vb.w=nw;vb.h=nw*ASPECT;clamp();apply();}
   const ctr=()=>{const r=svg.getBoundingClientRect();return[r.left+r.width/2,r.top+r.height/2];};
   svg.addEventListener('wheel',e=>{e.preventDefault();zoomAt(e.clientX,e.clientY,e.deltaY<0?0.82:1.22);},{passive:false});
   $('mzin').onclick=()=>{const c=ctr();zoomAt(c[0],c[1],0.7);};
   $('mzout').onclick=()=>{const c=ctr();zoomAt(c[0],c[1],1.42);};
   $('mzr').onclick=()=>{vb={x:0,y:0,w:W,h:H};apply();hide();};
   let drag=null;
   svg.addEventListener('pointerdown',e=>{if(e.target.classList.contains('pt'))return;hide();drag={sx:e.clientX,sy:e.clientY,ox:vb.x,oy:vb.y};svg.classList.add('grabbing');try{svg.setPointerCapture(e.pointerId);}catch(_){}});
   svg.addEventListener('pointermove',e=>{if(!drag)return;const r=svg.getBoundingClientRect();vb.x=drag.ox-(e.clientX-drag.sx)/r.width*vb.w;vb.y=drag.oy-(e.clientY-drag.sy)/r.height*vb.h;clamp();apply();});
   ['pointerup','pointercancel','pointerleave'].forEach(ev=>svg.addEventListener(ev,()=>{drag=null;svg.classList.remove('grabbing');}));
   let hideT=null;
   const cancelHide=()=>{if(hideT){clearTimeout(hideT);hideT=null;}};
   const scheduleHide=()=>{if(pinned)return;cancelHide();hideT=setTimeout(()=>{tip.style.display='none';},260);};
   function hide(){cancelHide();tip.style.display='none';pinned=false;}
   function show(el,cx,cy){
     const g=byId[el.getAttribute('data-i')]; if(!g)return;
     tip.innerHTML=(pinned?`<span class="cl" id="mtcl">×</span>`:'')+groupCard(g);
     const r=wrap.getBoundingClientRect(); tip.style.display='block';
     let lx=Math.min(cx-r.left+12, r.width-tip.offsetWidth-6), ly=Math.min(cy-r.top+12, r.height-tip.offsetHeight-6);
     tip.style.left=Math.max(4,lx)+'px'; tip.style.top=Math.max(4,ly)+'px';
     if(pinned){const c=$('mtcl'); if(c)c.onclick=hide;}
   }
   svg.addEventListener('mouseover',e=>{if(pinned||drag)return;if(e.target.classList.contains('pt')){cancelHide();show(e.target,e.clientX,e.clientY);}});
   svg.addEventListener('mouseout',e=>{if(e.target.classList.contains('pt'))scheduleHide();});
   svg.addEventListener('mouseleave',scheduleHide);
   svg.addEventListener('click',e=>{if(e.target.classList.contains('pt')){pinned=true;cancelHide();show(e.target,e.clientX,e.clientY);}else hide();});
   tip.addEventListener('mouseenter',cancelHide);
   tip.addEventListener('mouseleave',()=>{if(!pinned)tip.style.display='none';});
 })();

 /* Interactive "met this month" map: same zoom/pan/tooltip, its own points */
 (function(){
   const svg=$('wmap3'), wrap=$('mapwrap3'), tip=$('maptip3');
   if(!svg||!wrap||!tip) return;
   const byId={}; (m.allGroups||[]).forEach(g=>byId[g.id]=g);
   const W=M.w, H=M.h, ASPECT=H/W, MINW=110;
   let vb={x:0,y:0,w:W,h:H}, pinned=false;
   const clamp=()=>{vb.w=Math.min(W,vb.w);vb.h=vb.w*ASPECT;vb.x=Math.max(0,Math.min(W-vb.w,vb.x));vb.y=Math.max(0,Math.min(H-vb.h,vb.y));};
   const apply=()=>svg.setAttribute('viewBox',`${vb.x} ${vb.y} ${vb.w} ${vb.h}`);
   function zoomAt(cx,cy,f){const r=svg.getBoundingClientRect();const ux=vb.x+(cx-r.left)/r.width*vb.w,uy=vb.y+(cy-r.top)/r.height*vb.h;const nw=Math.min(W,Math.max(MINW,vb.w*f)),s=nw/vb.w;vb.x=ux-(ux-vb.x)*s;vb.y=uy-(uy-vb.y)*s;vb.w=nw;vb.h=nw*ASPECT;clamp();apply();}
   const ctr=()=>{const r=svg.getBoundingClientRect();return[r.left+r.width/2,r.top+r.height/2];};
   svg.addEventListener('wheel',e=>{e.preventDefault();zoomAt(e.clientX,e.clientY,e.deltaY<0?0.82:1.22);},{passive:false});
   $('mzin3').onclick=()=>{const c=ctr();zoomAt(c[0],c[1],0.7);};
   $('mzout3').onclick=()=>{const c=ctr();zoomAt(c[0],c[1],1.42);};
   $('mzr3').onclick=()=>{vb={x:0,y:0,w:W,h:H};apply();hide();};
   let drag=null;
   svg.addEventListener('pointerdown',e=>{if(e.target.classList.contains('pt'))return;hide();drag={sx:e.clientX,sy:e.clientY,ox:vb.x,oy:vb.y};svg.classList.add('grabbing');try{svg.setPointerCapture(e.pointerId);}catch(_){}});
   svg.addEventListener('pointermove',e=>{if(!drag)return;const r=svg.getBoundingClientRect();vb.x=drag.ox-(e.clientX-drag.sx)/r.width*vb.w;vb.y=drag.oy-(e.clientY-drag.sy)/r.height*vb.h;clamp();apply();});
   ['pointerup','pointercancel','pointerleave'].forEach(ev=>svg.addEventListener(ev,()=>{drag=null;svg.classList.remove('grabbing');}));
   let hideT=null;
   const cancelHide=()=>{if(hideT){clearTimeout(hideT);hideT=null;}};
   const scheduleHide=()=>{if(pinned)return;cancelHide();hideT=setTimeout(()=>{tip.style.display='none';},260);};
   function hide(){cancelHide();tip.style.display='none';pinned=false;}
   function show(el,cx,cy){
     const g=byId[el.getAttribute('data-i')]; if(!g)return;
     tip.innerHTML=(pinned?`<span class="cl" id="mtcl3">×</span>`:'')+groupCard(g);
     const r=wrap.getBoundingClientRect(); tip.style.display='block';
     let lx=Math.min(cx-r.left+12, r.width-tip.offsetWidth-6), ly=Math.min(cy-r.top+12, r.height-tip.offsetHeight-6);
     tip.style.left=Math.max(4,lx)+'px'; tip.style.top=Math.max(4,ly)+'px';
     if(pinned){const c=$('mtcl3'); if(c)c.onclick=hide;}
   }
   svg.addEventListener('mouseover',e=>{if(pinned||drag)return;if(e.target.classList.contains('pt')){cancelHide();show(e.target,e.clientX,e.clientY);}});
   svg.addEventListener('mouseout',e=>{if(e.target.classList.contains('pt'))scheduleHide();});
   svg.addEventListener('mouseleave',scheduleHide);
   svg.addEventListener('click',e=>{if(e.target.classList.contains('pt')){pinned=true;cancelHide();show(e.target,e.clientX,e.clientY);}else hide();});
   tip.addEventListener('mouseenter',cancelHide);
   tip.addEventListener('mouseleave',()=>{if(!pinned)tip.style.display='none';});
 })();
})();

/* EVENTS */
(function(){
 const e=D.events, yrs=Object.keys(e.byYear).sort();
 const ymax=Math.max(...yrs.map(y=>e.byYear[y].reduce((a,b)=>a+b,0)));
 let yl=yrs.map(y=>{const v=e.byYear[y];return barRow(y,[['b-blue',v[0],'Flagship'],['b-red',v[1],'Local WordCamp'],['b-amber',v[2],'Campus Connect'],['b-green',v[3],'New Format']],v[0]+v[1]+v[2]+v[3],ymax);}).join('');
 const cmax=Math.max(...e.byCountry.map(c=>c[1]+c[2]+c[3]),1);
 let cl=e.byCountry.map(c=>barRow(c[0],[['b-red',c[1],'Local WordCamp'],['b-amber',c[2],'Campus Connect'],['b-green',c[3],'New Format']],c[1]+c[2]+c[3],cmax)).join('');
 const fmax=Math.max(...e.formats.map(f=>f[1]));
 let fl=e.formats.map(f=>barRow(f[0],[['b-blue',f[1]]],f[1],fmax)).join('');
 const EM=e.map, eord={n:0,l:1,c:2,f:3};
 let edots='';
 EM.points.slice().sort((p,q)=>eord[p[2]]-eord[q[2]]).forEach(p=>edots+=`<circle class="pt e${p[2]}" cx="${p[0]}" cy="${p[1]}" r="2.4" data-i="${p[3]}"/>`);
 const emap=`<div class="card"><h2>Where the events are, and where they are not</h2>
   <div class="mapwrap" id="mapwrap2">
    <svg class="wmap" id="wmap2" viewBox="0 0 ${EM.w} ${EM.h}" preserveAspectRatio="xMidYMid meet" role="img" aria-label="World map of 2026 WordPress events by type"><path class="land" d="${D.meetups.map.land}"/>${edots}</svg>
    <div class="mapzoom"><button type="button" id="mzin2" aria-label="Zoom in">+</button><button type="button" id="mzout2" aria-label="Zoom out">&minus;</button><button type="button" id="mzr2" aria-label="Reset view" style="font-size:13px">&#8635;</button></div>
    <div class="maptip" id="maptip2"></div>
   </div>
   <div class="legend"><span><i class="dot" style="background:var(--blue)"></i>Flagship ${e.byYear['2026'][0]}</span><span><i class="dot" style="background:var(--red)"></i>Local WordCamp ${e.byYear['2026'][1]}</span><span><i class="dot" style="background:var(--amber)"></i>Campus Connect ${e.byYear['2026'][2]}</span><span><i class="dot" style="background:var(--green)"></i>New Format ${e.byYear['2026'][3]}</span></div>
   <p class="foot">2026 events cluster in South Asia, Latin America, and Europe. <span style="color:var(--muted)">Zoom, pan, and tap a dot for details.</span></p></div>`;
 const B=e.bench, bt=B?B.orgFirst+B.orgReturn:0, at=B?B.attFirst+B.attReturn:0;
 const bench=B?`<div class="card"><h2>Bench renewal — are we growing new organizers?</h2>
   ${barRow('Organizers',[['b-green',B.orgFirst],['b-grey',B.orgReturn]],Math.round(B.orgFirst/bt*100)+'% new',bt)}
   ${barRow('Attendees',[['b-green',B.attFirst],['b-grey',B.attReturn]],Math.round(B.attFirst/at*100)+'% new',at)}
   <div class="legend"><span><i class="dot b-green"></i>first-time</span><span><i class="dot b-grey"></i>returning</span></div>
   <p class="foot"><b>${B.orgFirst}</b> first-time organizers stepped up this year, ${Math.round(B.orgFirst/bt*100)}% of the total. First-timers are the bench a WordCamp needs.</p></div>`:'';
 $('events').innerHTML=
  tiles([['',e.ytd,'events YTD'],['good','+'+Math.round((e.ytd-e.ytdPrev)/e.ytdPrev*100)+'%','vs '+e.ytdPrev+' last year'],
   ['us',0,'US local/newer events'],['hot',30,'countries ran an event']])
  +`<p class="foot" style="margin:-6px 0 16px">For the live, public list of upcoming events, see <a href="https://events.wordpress.org" target="_blank" rel="noopener">events.wordpress.org</a>. This dashboard focuses on what a public listing cannot show.</p>`
  +bench
  +emap
  +`<div class="card"><h2>Community events by year</h2><div id="byyear" style="position:relative">${yl}<div class="maptip" id="bytip" style="pointer-events:none"></div></div>
    <div class="legend"><span><i class="dot b-blue"></i>Flagship</span><span><i class="dot b-red"></i>Local WordCamp</span><span><i class="dot b-amber"></i>Campus Connect</span><span><i class="dot b-green"></i>New Format</span></div>
    <p class="foot">Local WordCamps fell from ${e.byYear['2019'][1]} in 2019 to ${e.byYear['2026'][1]} now, while Campus Connect (${e.byYear['2026'][2]}) and other new formats (${e.byYear['2026'][3]}) filled the gap this year. <span style="color:var(--muted)">Hover a bar segment for its count.</span></p></div>`
  +`<div class="card"><h2>2026 events by country</h2><div id="bycountry" style="position:relative">${cl}<div class="maptip" id="bctip" style="pointer-events:none"></div></div>
    <div class="legend"><span><i class="dot b-red"></i>Local WordCamp</span><span><i class="dot b-amber"></i>Campus Connect</span><span><i class="dot b-green"></i>New Format</span></div>
    <p class="foot">Flagships and meetups counted separately. <span style="color:var(--muted)">Hover a segment for its count.</span></p></div>`
  +`<div class="card"><h2>2026 by format</h2>${fl}</div>`;

 /* hover tooltips (category + count) on the by-year and by-country bar charts */
 attachBarTip($('byyear'),$('bytip'));
 attachBarTip($('bycountry'),$('bctip'));

 /* Interactive events map: zoom/pan + per-event popups (dependency-free) */
 (function(){
   const svg=$('wmap2'), wrap=$('mapwrap2'), tip=$('maptip2');
   if(!svg||!wrap||!tip) return;
   const EL=EM.eventList||[];
   const esc=x=>String(x==null?'':x).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
   const W=EM.w, H=EM.h, ASPECT=H/W, MINW=110;
   let vb={x:0,y:0,w:W,h:H}, pinned=false;
   const clamp=()=>{vb.w=Math.min(W,vb.w);vb.h=vb.w*ASPECT;vb.x=Math.max(0,Math.min(W-vb.w,vb.x));vb.y=Math.max(0,Math.min(H-vb.h,vb.y));};
   const apply=()=>svg.setAttribute('viewBox',`${vb.x} ${vb.y} ${vb.w} ${vb.h}`);
   function zoomAt(cx,cy,f){const r=svg.getBoundingClientRect();const ux=vb.x+(cx-r.left)/r.width*vb.w,uy=vb.y+(cy-r.top)/r.height*vb.h;const nw=Math.min(W,Math.max(MINW,vb.w*f)),s=nw/vb.w;vb.x=ux-(ux-vb.x)*s;vb.y=uy-(uy-vb.y)*s;vb.w=nw;vb.h=nw*ASPECT;clamp();apply();}
   const ctr=()=>{const r=svg.getBoundingClientRect();return[r.left+r.width/2,r.top+r.height/2];};
   svg.addEventListener('wheel',e=>{e.preventDefault();zoomAt(e.clientX,e.clientY,e.deltaY<0?0.82:1.22);},{passive:false});
   $('mzin2').onclick=()=>{const c=ctr();zoomAt(c[0],c[1],0.7);};
   $('mzout2').onclick=()=>{const c=ctr();zoomAt(c[0],c[1],1.42);};
   $('mzr2').onclick=()=>{vb={x:0,y:0,w:W,h:H};apply();hide();};
   let drag=null;
   svg.addEventListener('pointerdown',e=>{if(e.target.classList.contains('pt'))return;hide();drag={sx:e.clientX,sy:e.clientY,ox:vb.x,oy:vb.y};svg.classList.add('grabbing');try{svg.setPointerCapture(e.pointerId);}catch(_){}});
   svg.addEventListener('pointermove',e=>{if(!drag)return;const r=svg.getBoundingClientRect();vb.x=drag.ox-(e.clientX-drag.sx)/r.width*vb.w;vb.y=drag.oy-(e.clientY-drag.sy)/r.height*vb.h;clamp();apply();});
   ['pointerup','pointercancel','pointerleave'].forEach(ev=>svg.addEventListener(ev,()=>{drag=null;svg.classList.remove('grabbing');}));
   let hideT=null;
   const cancelHide=()=>{if(hideT){clearTimeout(hideT);hideT=null;}};
   const scheduleHide=()=>{if(pinned)return;cancelHide();hideT=setTimeout(()=>{tip.style.display='none';},260);};
   function hide(){cancelHide();tip.style.display='none';pinned=false;}
   function show(el,cx,cy){
     const g=EL[el.getAttribute('data-i')]; if(!g)return;
     const line=[g.ty?esc(g.ty):'', g.d?esc(fmtD(g.d)):''].filter(Boolean).join(' · ');
     tip.innerHTML=(pinned?`<span class="cl" id="mtcl2">×</span>`:'')+`<b>${esc(g.n)}</b><br>${esc(g.loc)}<br>${line}${g.u?`<br><a href="${esc(g.u)}" target="_blank" rel="noopener noreferrer">Event page ↗</a>`:''}`;
     const r=wrap.getBoundingClientRect(); tip.style.display='block';
     let lx=Math.min(cx-r.left+12, r.width-tip.offsetWidth-6), ly=Math.min(cy-r.top+12, r.height-tip.offsetHeight-6);
     tip.style.left=Math.max(4,lx)+'px'; tip.style.top=Math.max(4,ly)+'px';
     if(pinned){const c=$('mtcl2'); if(c)c.onclick=hide;}
   }
   svg.addEventListener('mouseover',e=>{if(pinned||drag)return;if(e.target.classList.contains('pt')){cancelHide();show(e.target,e.clientX,e.clientY);}});
   svg.addEventListener('mouseout',e=>{if(e.target.classList.contains('pt'))scheduleHide();});
   svg.addEventListener('mouseleave',scheduleHide);
   svg.addEventListener('click',e=>{if(e.target.classList.contains('pt')){pinned=true;cancelHide();show(e.target,e.clientX,e.clientY);}else hide();});
   tip.addEventListener('mouseenter',cancelHide);
   tip.addEventListener('mouseleave',()=>{if(!pinned)tip.style.display='none';});
 })();
})();

/* PIPELINE */
(function(){
 const P=D.pipeline, order=P.funnelOrder;
 const counts=P.funnelCounts||(function(){const c={};order.forEach(s=>c[s]=0);P.records.forEach(r=>{if(c[r.stage]!==undefined)c[r.stage]++});return c;})();
 const mx=Math.max(...Object.values(counts),1);
 let fh=order.map(s=>`<div class="funnel-row" data-stage="${s}" title="See these events in the outreach list below ↓">${barRow(s,[['b-blue',counts[s]]],counts[s],mx)}</div>`).join('');
 fh+=barRow('→ Scheduled',[['b-green',P.scheduledCount]],P.scheduledCount,mx);
 const usN=P.records.filter(r=>r.us).length, wcN=P.records.filter(r=>r.format==='WordCamp').length;
 const esc=x=>String(x==null?'':x).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
 /* Stale applications: active-funnel apps that haven't changed stage in STALE_DAYS+ */
 const STALE_DAYS=90;  // 3 months — change here to adjust the threshold
 const STALE_SKIP_FORMATS=['Student Club'];  // formats that follow a different timeline, excluded from this section
 const _sref=P.detailAsOf?new Date(P.detailAsOf):new Date();
 const stale=(P.records||[]).filter(r=>r.modified&&!STALE_SKIP_FORMATS.includes(r.format)).map(r=>Object.assign({stuck:Math.round((_sref-new Date(r.modified))/864e5)},r)).filter(r=>r.stuck>=STALE_DAYS).sort((a,b)=>b.stuck-a.stuck);
 /* event-date urgency: a stuck app whose planned date has passed (or is weeks away) is far more urgent */
 const _urg=r=>{
   if(!r.start) return {txt:'no date set',cls:'color:var(--muted)'};
   const rw=Math.round((new Date(r.start)-_sref)/864e5);
   if(rw<0) return {txt:fmtD(r.start)+' &middot; date passed',cls:'color:var(--red);font-weight:600'};
   if(rw<=60) return {txt:fmtD(r.start)+' &middot; in '+rw+'d',cls:'color:var(--amber);font-weight:600'};
   return {txt:fmtD(r.start),cls:'color:var(--muted)'};
 };
 let staleCard='';
 if(stale.length){
   const byS={}; stale.forEach(r=>byS[r.stage]=(byS[r.stage]||0)+1);
   const bd=Object.entries(byS).sort((a,b)=>b[1]-a[1]).map(x=>`${esc(x[0])} ${x[1]}`).join(' · ');
   const passedN=stale.filter(r=>r.start && new Date(r.start)<_sref).length;
   const soonN=stale.filter(r=>{if(!r.start)return false;const rw=(new Date(r.start)-_sref)/864e5;return rw>=0&&rw<=60;}).length;
   let urgLine='';
   if(passedN||soonN){
     const parts=[];
     if(passedN) parts.push(`<b style="color:var(--red)">${passedN} already past their planned date</b>`);
     if(soonN) parts.push(`<b style="color:var(--amber)">${soonN} within the next two months</b>`);
     urgLine=` ${parts.join(' and ')} &mdash; those are the most urgent.`;
   }
   const stStgs=order.filter(s=>stale.some(r=>r.stage===s));
   const stFmts=[...new Set(stale.map(r=>r.format))].sort();
   staleCard=`<div class="card"><h2>Needs attention</h2>
     <p class="foot" style="margin:-4px 0 12px"><b>${stale.length} applications haven't changed stage in ${Math.round(STALE_DAYS/30)}+ months.</b>${urgLine} <span style="color:var(--muted)">${bd}</span></p>
     <div class="controls"><select id="ststg"><option value="">All stages</option>${stStgs.map(s=>`<option>${esc(s)}</option>`).join('')}</select>
     <select id="stfmt"><option value="">All formats</option>${stFmts.map(f=>`<option>${esc(f)}</option>`).join('')}</select></div>
     <table><thead><tr><th>Stage</th><th>Format</th><th>Event</th><th class="hidem">Location</th><th>Country</th><th>Event date</th><th>Stuck for</th></tr></thead><tbody id="stbody"></tbody></table>
     <div class="mgpager" id="stpager"></div></div>`;
 }

 // momentum (wordcamp-status flow)
 let mom='';
 if(P.momentum){
   const mos=Object.keys(P.momentum).sort();
   const can=d=>d.cancelled||0, dec=d=>d.declined!=null?d.declined:(d.attrition||0);  // back-compat: old 'attrition' shown as declined
   const allv=mos.flatMap(k=>{const d=P.momentum[k];return [d.newApps||0,d.confirmed||0,can(d),dec(d)];});
   const mmax=Math.max(...allv,1);
   const wbar=(cls,v)=>`<div class="mbar"><div class="t ${cls}" style="width:${Math.max(2,Math.round(v/mmax*180))}px"></div><div class="v">${v}</div></div>`;
   const rows=mos.map(k=>{const d=P.momentum[k];const nm=k.slice(5)+'/'+k.slice(2,4);
     return `<div class="mrow"><div class="mo">${nm}</div><div class="mbars">${wbar('b-blue',d.newApps||0)}${wbar('b-green',d.confirmed||0)}${wbar('b-amber',can(d))}${wbar('b-red',dec(d))}</div></div>`;}).join('');
   const T=k=>mos.reduce((a,m)=>a+(P.momentum[m][k]||0),0);
   const Tcan=mos.reduce((a,m)=>a+can(P.momentum[m]),0), Tdec=mos.reduce((a,m)=>a+dec(P.momentum[m]),0);
   mom=`<div class="card"><h2>Pipeline momentum — 2026 monthly flow</h2>${rows}
     <div class="legend"><span><i class="dot b-blue"></i>new applications</span><span><i class="dot b-green"></i>confirmed (&rarr; scheduled)</span><span><i class="dot b-amber"></i>cancelled</span><span><i class="dot b-red"></i>declined</span></div>
     <p class="foot">YTD: <b>${T('newApps')}</b> new applications entered the funnel, <b>${T('confirmed')}</b> reached scheduled, <b>${T('closed')}</b> happened, <b>${Tcan}</b> cancelled, <b>${Tdec}</b> declined.</p></div>`;
 }

 $('pipeline').innerHTML=
  tiles([['hot',(P.activeFunnelTotal!=null?P.activeFunnelTotal:P.records.length),'in the funnel'],['good',P.scheduledCount,'confirmed'],['us',usN,'US in flight'],
   ['',wcN,'WordCamps'],['',P.cancelledCount,'cancelled all-time'],['',P.declinedCount,'declined all-time']])
  +`<div class="card"><h2>Application funnel — where events are stuck</h2>${fh}
    <p class="foot">${P.testCount} test records excluded. A confirmed event has cleared every stage above.</p></div>`
  +staleCard
  +mom
  +`<div class="card"><h2>The ${P.records.length} events in flight — outreach list</h2>${P.detailAsOf?`<p class="foot" style="margin:-4px 0 12px">Per-event detail as of ${fmtD(P.detailAsOf)}, refreshed manually. Funnel counts above are current.</p>`:''}
    <div class="controls"><input id="q" placeholder="Search title, city, country…">
    <select id="fmt"><option value="">All formats</option></select>
    <select id="stg"><option value="">All stages</option></select>
    <button class="btn" id="usbtn">US only</button></div>
    <table><thead><tr><th data-k="stage">Stage</th><th data-k="format">Format</th><th data-k="title">Event</th>
    <th data-k="location" class="hidem">Location</th><th data-k="country">Country</th></tr></thead><tbody id="tb"></tbody></table>
    <div class="mgpager" id="tbpager"></div>
    <p class="foot" id="cnt"></p></div>`;
 if(stale.length){(function(){
   const SP=15; let sp=1;
   const stg=$('ststg'), fmt=$('stfmt');
   const row=r=>{const u=_urg(r);return `<tr><td><span class="stage">${esc(r.stage)}</span></td><td><span class="fmt">${esc(r.format)}</span></td><td>${r.link?`<a href="${esc(r.link)}" target="_blank" rel="noopener noreferrer">${esc(r.title)}</a>`:esc(r.title)}</td><td class="hidem">${esc(r.location)||'—'}</td><td>${r.us?'<span class="usdot">● </span>':''}${esc(r.country)}</td><td><span style="${u.cls}">${u.txt}</span></td><td>${Math.max(1,Math.round(r.stuck/30))} mo</td></tr>`;};
   function cur(){const s=stg.value,f=fmt.value;return stale.filter(r=>(!s||r.stage===s)&&(!f||r.format===f));}
   function draw(){const list=cur();const pages=Math.max(1,Math.ceil(list.length/SP));if(sp>pages)sp=pages;$('stbody').innerHTML=list.length?list.slice((sp-1)*SP,sp*SP).map(row).join(''):'<tr><td colspan="7" style="color:var(--muted);padding:14px 10px">No applications match this filter.</td></tr>';$('stpager').innerHTML=list.length>SP?`<button class="mgpg" data-p="prev"${sp<=1?' disabled':''}>← Prev</button><span class="mgpginfo">${(sp-1)*SP+1}–${Math.min(sp*SP,list.length)} of ${list.length}</span><button class="mgpg" data-p="next"${sp>=pages?' disabled':''}>Next →</button>`:'';$('stpager').querySelectorAll('.mgpg').forEach(b=>b.onclick=()=>{sp+=b.dataset.p==='next'?1:-1;draw();});}
   stg.onchange=fmt.onchange=()=>{sp=1;draw();};
   draw();
 })();}
 const fmts=[...new Set(P.records.map(r=>r.format))].sort();
 $('fmt').innerHTML+=fmts.map(f=>`<option>${f}</option>`).join('');
 $('stg').innerHTML+=order.map(s=>`<option>${s}</option>`).join('');
 const rank={};order.forEach((s,i)=>rank[s]=i);
 let st={q:'',fmt:'',stg:'',us:false,sort:'stage',dir:1};
 const TBP=25; let tbPage=1;
 function rows(){let r=P.records.filter(x=>{if(st.us&&!x.us)return false;if(st.fmt&&x.format!==st.fmt)return false;if(st.stg&&x.stage!==st.stg)return false;if(st.q){const s=(x.title+' '+x.location+' '+x.country).toLowerCase();if(!s.includes(st.q))return false;}return true;});
   r.sort((a,b)=>{let av,bv;if(st.sort==='stage'){av=rank[a.stage];bv=rank[b.stage];}else{av=(a[st.sort]||'').toString().toLowerCase();bv=(b[st.sort]||'').toString().toLowerCase();}return av<bv?-st.dir:av>bv?st.dir:0;});return r;}
 function render(){const all=rows();const pages=Math.max(1,Math.ceil(all.length/TBP));if(tbPage>pages)tbPage=pages;
   const r=all.slice((tbPage-1)*TBP,tbPage*TBP);
   $('tb').innerHTML=r.map(x=>`<tr class="${x.us?'us':''}"><td><span class="stage">${x.stage}</span></td><td><span class="fmt">${x.format}</span></td><td>${x.link?`<a href="${x.link}" target="_blank" rel="noopener">${x.title}</a>`:x.title}</td><td class="hidem">${x.location||'—'}</td><td>${x.us?'<span class="usdot">● </span>':''}${x.country}</td></tr>`).join('');
   const from=all.length?(tbPage-1)*TBP+1:0, to=Math.min(tbPage*TBP,all.length);
   $('cnt').textContent=`${all.length?`Showing ${from}–${to} of ${all.length}`:'0 shown'}${st.us?' · US only':''}`;
   $('tbpager').innerHTML=all.length>TBP?`<button class="mgpg" data-p="prev"${tbPage<=1?' disabled':''}>← Prev</button><span class="mgpginfo">Page ${tbPage} / ${pages}</span><button class="mgpg" data-p="next"${tbPage>=pages?' disabled':''}>Next →</button>`:'';
   $('tbpager').querySelectorAll('.mgpg').forEach(b=>b.onclick=()=>{if(b.dataset.p==='prev'&&tbPage>1)tbPage--;else if(b.dataset.p==='next'&&tbPage<pages)tbPage++;render();});}
 const apply=()=>{tbPage=1;render();};
 $('q').oninput=e=>{st.q=e.target.value.toLowerCase();apply();};
 $('fmt').onchange=e=>{st.fmt=e.target.value;apply();};
 $('stg').onchange=e=>{st.stg=e.target.value;apply();};
 $('usbtn').onclick=e=>{st.us=!st.us;e.target.classList.toggle('on',st.us);apply();};
 document.querySelectorAll('#pipeline th[data-k]').forEach(th=>th.onclick=()=>{const k=th.dataset.k;st.dir=(st.sort===k)?-st.dir:1;st.sort=k;apply();});
 render();
 /* Funnel bars are shortcuts into the outreach list: pick the stage + scroll down */
 document.querySelectorAll('#pipeline .funnel-row').forEach(el=>el.onclick=()=>{
   const s=el.dataset.stage; st.stg=s; $('stg').value=s; apply();
   const card=$('tb').closest('.card'); if(card) card.scrollIntoView({behavior:'smooth',block:'start'});
 });
})();

const _dts=D.dates||{}, _U=iso=>fmtD(iso)||'—';
let _upd=(_dts.meetups===_dts.events && _dts.events===_dts.pipelineCounts)
  ? `Last updated ${_U(_dts.meetups)}`
  : `Last updated — Meetups ${_U(_dts.meetups)} · Events ${_U(_dts.events)} · Pipeline counts ${_U(_dts.pipelineCounts)}`;
if(_dts.pipelineDetail && _dts.pipelineDetail!==_dts.pipelineCounts) _upd+=` · pipeline detail ${_U(_dts.pipelineDetail)} (manual)`;
$('src').innerHTML=`<b>${_upd}.</b><br><b>Sources:</b> Meetup.com and WordCamp Central. Financial reports intentionally excluded. events.wordpress.org / GatherPress will be added as a fourth source once live.`;

document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{
  document.querySelectorAll('.tab').forEach(x=>x.classList.remove('on'));
  document.querySelectorAll('.view').forEach(x=>x.classList.remove('on'));
  t.classList.add('on');$(t.dataset.v).classList.add('on');
});
</script></body></html>'''

full = TEMPLATE.replace("__DATA__", DATA)
open(os.path.join(HERE, "events-dashboard.html"), "w").write(full)
print("wrote events-dashboard.html")

# Artifact-ready version: the publish skeleton supplies <!doctype><html><head></head><body>,
# so strip our document wrapper and keep <title> + <style> + content + <script>.
body = full
body = body[body.index("<title>"):]                       # drop <!doctype><html><head>
body = body.replace("</head><body>", "\n")                # seam between head and body
body = body.replace("</body></html>", "\n")               # drop closing wrapper
open(os.path.join(HERE, "events-dashboard.artifact.html"), "w").write(body)
print("wrote events-dashboard.artifact.html")
