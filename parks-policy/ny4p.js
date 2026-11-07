/* New Yorkers for Parks 2021 Open Space Profiles: a map layer and a profile section for the parks policy pages.
   NY4P.init({map, mapkit, home:'BK06'|null, scope:'cb6'|'brooklyn'|'nyc', base:'/parks-policy/', legend, info, section})  */
(function(){
const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const ord=n=>{const s=['th','st','nd','rd'],v=n%100;return n+(s[(v-20)%10]||s[v]||s[0])};
const BORO={BK:'Brooklyn',BX:'Bronx',MN:'Manhattan',QN:'Queens',SI:'Staten Island'};
const RAMP=['#eef1fb','#c9d1ee','#9fadde','#7286c9','#4a5fae','#2b3f8f','#0d1b4b'];
const TOT=['land','parkland','cityParks','pop'];
let P=null,G=null,O=[],A=[],cfg=null,metric='walk',onMap=false;
const name=c=>`${BORO[c.slice(0,2)]} ${+c.slice(2)}`;
const fullName=c=>`${BORO[c.slice(0,2)]} Community District ${+c.slice(2)}`;
const M=k=>P.metrics.find(m=>m.k===k);
function val(m,v,s){if(v==null)return '—';if(s!=null)return s;const u=m.u;return u==='%'?v+'%':u==='$'?'$'+Math.round(v/1000)+'K':u==='years'?v.toFixed(1):(v>=1000?Math.round(v).toLocaleString('en-US'):String(v))}
const shown=(c,k)=>P.s[c][k];
function cmp(m,v,n){if(TOT.includes(m.k)||!m.b||v==null||n==null||v===n)return '';const better=m.b==='hi'?v>n:v<n;return `<span style="color:${better?'#2e7d32':'#c62828'};font-weight:700">${better?'better':'worse'} than the city</span>`}
function rankTxt(c,m){const r=P.d[c].rk&&P.d[c].rk[m.k];return r?`${ord(r)} of 59`:''}
function inScope(c){return cfg.scope==='nyc'?true:cfg.scope==='brooklyn'?c.startsWith('BK'):c===cfg.home}
async function load(){if(P)return;[P,G]=await Promise.all([fetch(cfg.base+'ny4p.json').then(r=>r.json()),fetch(cfg.base+'nyc/districts.geojson').then(r=>r.json())])}
function breaks(k){const v=Object.values(P.d).map(d=>d[k]).sort((a,b)=>a-b);return [1,2,3,4,5,6].map(i=>v[Math.floor(i*v.length/7)])}
function color(k,v){const b=breaks(k);let i=0;while(i<b.length&&v>=b[i])i++;return RAMP[i]}
function rings(g){const Cd=c=>new mapkit.Coordinate(c[1],c[0]),o=[];(g.type==='Polygon'?[g.coordinates]:g.coordinates).forEach(p=>p.forEach(r=>o.push(r.map(Cd))));return o}
function styleFor(c,hi){const v=P.d[c][metric];return new mapkit.Style({fillColor:color(metric,v),fillOpacity:hi?.9:.72,strokeColor:hi?'#f47920':c===cfg.home?'#f47920':'#ffffff',lineWidth:hi?4:c===cfg.home?3:1,strokeOpacity:1})}
let hiC=null;
function paint(){O.forEach(o=>o.style=styleFor(o.data.ny4p,o.data.ny4p===hiC))}
function legendHTML(){const m=M(metric),b=breaks(metric);
  const opts=P.metrics.filter(x=>x.g!=='Demographics'||['income','poverty','under18','over65','pop'].includes(x.k)).map(x=>`<option value="${x.k}"${x.k===metric?' selected':''}>${esc(x.g)}: ${esc(x.l)}</option>`).join('');
  return `<span style="flex-basis:100%"><b>New Yorkers for Parks 2021 Open Space Profiles</b>, every community district. Pick what to color by:</span><select id="ny4pSel" style="font:inherit;font-size:.9rem;padding:7px 9px;border:1px solid #c9cde0;border-radius:8px;max-width:100%">${opts}</select>`+
  `<span style="flex-basis:100%;display:flex;align-items:center;gap:6px;flex-wrap:wrap"><span>Less</span>${RAMP.map((c,i)=>`<span class="sw sq" style="background:${c};border:1px solid #d7dbe8" title="${i?'from '+val(m,b[i-1]):'under '+val(m,b[0])}"></span>`).join('')}<span>More</span><span style="color:var(--muted)">&middot; ${m.b==='hi'?'more is better':m.b==='lo'?'less is better':'shown as published'} &middot; ${TOT.includes(metric)?'Citywide total':'City'}: ${val(m,P.nyc[metric],P.nycS[metric])}</span></span><span style="color:var(--muted)">Tap any district for its profile.</span>`}
function card(c){const d=P.d[c],groups=['Parkland','Access','Amenities','Stewardship','Health and environment'];
  const m=M(metric);
  return `<div class="bh"><span class="gb" style="background:${color(metric,d[metric])};color:${RAMP.indexOf(color(metric,d[metric]))>2?'#fff':'#0d1b4b'};font-size:.75rem">${esc(shown(c,metric))}</span><div><div class="bl">New Yorkers for Parks, 2021</div><div class="bn">${esc(fullName(c))}</div><div class="ba">${esc(m.l)}: <b>${esc(shown(c,metric))}</b> (city ${esc(P.nycS[metric])})${rankTxt(c,m)?' &middot; '+rankTxt(c,m):''} ${cmp(m,d[metric],P.nyc[metric])}</div></div></div>`+
  `<div class="chips" style="margin-top:8px">${['walk','per1k','pctParkland','playgrounds','condition','canopy','asthma','life'].map(k=>`<span class="chip">${esc(M(k).l)}: ${esc(shown(c,k))}</span>`).join('')}</div>`+
  `<div class="bq"><a href="${P.pdf.replace('{CODE}',c.slice(0,2)+(+c.slice(2)))}" target="_blank" rel="noopener">Full profile from New Yorkers for Parks (PDF) ↗</a></div>`}
function on(){if(!G)return;onMap=true;
  if(!O.length){G.features.forEach(f=>{const c=f.properties.b;if(!P.d[c])return;const o=new mapkit.PolygonOverlay(rings(f.geometry),{style:styleFor(c,false)});o.data={ny4p:c};O.push(o)})}
  if(!A.length){G.features.forEach(f=>{const c=f.properties.b;if(!P.d[c]||(cfg.scope!=='nyc'&&!c.startsWith('BK')))return;const pc=f.properties.c;A.push(new mapkit.Annotation(new mapkit.Coordinate(pc[0],pc[1]),()=>{const e=document.createElement('div');e.style.cssText='background:rgba(255,255,255,.92);border:1px solid #c9cde0;border-radius:6px;padding:1px 5px;font:700 10.5px DM Sans,sans-serif;color:#0d1b4b;white-space:nowrap;pointer-events:none';e.textContent=name(c);return e},{calloutEnabled:false,enabled:false,displayPriority:c===cfg.home?1000:400,collisionMode:mapkit.Annotation.CollisionMode.Rectangle}))})}
  cfg.map.addOverlays(O);cfg.map.addAnnotations(A);paint();cfg.legend.innerHTML=legendHTML();bindSel();
  const fit=O.filter(o=>inScope(o.data.ny4p));cfg.map.showItems(cfg.scope==='cb6'?O.filter(o=>o.data.ny4p.startsWith('BK')):fit,{animate:true,padding:new mapkit.Padding(20,20,20,20)});
  cfg.info.innerHTML=cfg.home?card(cfg.home):'<b>Tap any district</b> to see its New Yorkers for Parks profile.';cfg.info.style.display='block'}
function off(){if(!onMap)return;onMap=false;hiC=null;cfg.map.removeOverlays(O);cfg.map.removeAnnotations(A)}
function bindSel(){const s=document.getElementById('ny4pSel');if(s)s.onchange=()=>{setMetric(s.value)}}
function setMetric(k){metric=k;if(onMap){paint();cfg.legend.innerHTML=legendHTML();bindSel();if(hiC||cfg.home)cfg.info.innerHTML=card(hiC||cfg.home)}renderSection()}
function select(c){hiC=c;paint();cfg.info.innerHTML=card(c);cfg.info.style.display='block'}
// ---- section ----
function renderSection(){const el=cfg.section;if(!el||!P)return;const m=M(metric);
  const sel=`<div class="ctl"><select id="ny4pSel2">${P.metrics.map(x=>`<option value="${x.k}"${x.k===metric?' selected':''}>${esc(x.g)}: ${esc(x.l)}</option>`).join('')}</select></div>`;
  let profile='';
  if(cfg.home){const c=cfg.home,d=P.d[c];
    profile=`<h3>${esc(fullName(c))} against the city <span>tap a row to rank every district by it</span></h3><table>`+['Parkland','Access','Amenities','Stewardship','Health and environment','Demographics'].map(g=>`<tr><td colspan="4" style="font:700 .7rem 'DM Mono',monospace;text-transform:uppercase;letter-spacing:.06em;color:#1565c0;padding-top:12px">${g}</td></tr>`+P.metrics.filter(x=>x.g===g).map(x=>`<tr data-ny4p="${x.k}" style="cursor:pointer"${x.k===metric?' class="me"':''}><td>${esc(x.l)}<small>${cmp(x,d[x.k],P.nyc[x.k])}</small></td><td class="v">${esc(P.s[c][x.k])}</td><td class="v" style="color:var(--muted);font-weight:400">${esc(P.nycS[x.k])}</td><td class="v" style="font-weight:400">${rankTxt(c,x)}</td></tr>`).join('')).join('')+`<tr><td></td><td class="v"><small>${esc(name(c))}</small></td><td class="v"><small>City</small></td><td class="v"><small>Rank</small></td></tr></table>`}
  const list=Object.keys(P.d).filter(c=>cfg.scope==='brooklyn'?c.startsWith('BK'):true).sort((a,b)=>m.b==='lo'?P.d[a][m.k]-P.d[b][m.k]:P.d[b][m.k]-P.d[a][m.k]);
  const mx=Math.max(...list.map(c=>P.d[c][m.k]),TOT.includes(m.k)?0:P.nyc[m.k]);
  const bars=`<h3>${esc(m.l)}, ${cfg.scope==='brooklyn'?'every Brooklyn district':'all 59 districts'} <span>${m.b==='lo'?'lowest first (less is better)':m.b==='hi'?'highest first (more is better)':'highest first'} ${TOT.includes(m.k)?'':' &middot; dashed line is the city figure'}</span></h3><div>`+list.map((c,i)=>{const v=P.d[c][m.k],w=mx?100*v/mx:0;return `<div style="display:grid;grid-template-columns:120px minmax(0,1fr) 70px;gap:8px;align-items:center;padding:2px 0;${c===cfg.home?'background:#fff3c4;border-radius:6px;font-weight:700':''}"><span style="font-size:.8rem">${i+1}. ${esc(name(c))}</span><span style="position:relative;height:14px;background:#f1f2f7;border-radius:4px"><i style="position:absolute;left:0;top:0;bottom:0;width:${w}%;background:${c===cfg.home?'#f47920':color(m.k,v)};border-radius:4px"></i>${TOT.includes(m.k)?'':`<u style="position:absolute;top:-3px;bottom:-3px;left:${mx?100*P.nyc[m.k]/mx:0}%;border-left:2px dashed #1f2937"></u>`}</span><span style="font:600 .8rem 'DM Mono',monospace;text-align:right">${esc(shown(c,m.k))}</span></div>`}).join('')+'</div>';
  el.innerHTML=`<p class="note">New Yorkers for Parks' 2021 profile of every community district: parkland, how close residents live to a park, amenities, park condition, stewardship, and the health and environment of the people who live there. Values are as NY4P published them (rounded). Their ranks are used for percent parkland, 5-minute walk and tree canopy; other ranks are counted here from the published numbers, ties sharing a rank.</p>${sel}${profile}${bars}<p class="qs">Source: <a href="${P.url}" target="_blank" rel="noopener">${esc(P.src)}</a>. The city figure is the one printed on every profile: a citywide total for land, parkland and residents, and otherwise the citywide rate or the figure for a typical district. <a href="#" data-l="ny4p">See it on the map</a>.</p>`;
  const s2=document.getElementById('ny4pSel2');s2.onchange=()=>setMetric(s2.value);
  el.querySelectorAll('tr[data-ny4p]').forEach(r=>r.onclick=()=>setMetric(r.dataset.ny4p))}
window.NY4P={async init(o){cfg=o;await load();renderSection();
  o.map.addEventListener('select',e=>{const ov=e.overlay;if(onMap&&ov&&ov.data&&ov.data.ny4p){select(ov.data.ny4p);setTimeout(()=>{o.map.selectedOverlay=null},0)}})},
 on,off,get active(){return onMap}};
})();
