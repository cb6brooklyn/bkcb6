/* Trees on the CB6 parks map: tree canopy 2010/2017 (tiles), canopy by block, every street tree, pruning cycle.
   TREES.init({map, legend, info, section, what}) then TREES.on('canopy'|'blocks'|'trees'|'prune'), TREES.off(). Data: /trees/. */
(function(){
const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const fmt=n=>Math.round(n).toLocaleString('en-US');
const CCOL={Excellent:'#1b5e20',Good:'#43a047',Fair:'#c0ca33',Poor:'#fb8c00',Critical:'#e53935',Dead:'#757575',Unknown:'#90a4ae'};
const GR=['#f7fcf5','#e5f5e0','#c7e9c0','#a1d99b','#74c476','#41ab5d','#238b45','#005a32'],GB=[2,5,10,15,20,30,40];
const gcol=v=>{let i=0;while(i<GB.length&&v>=GB[i])i++;return GR[i]};
const DV=[[-6,'#b2182b'],[-3,'#ef8a62'],[-1,'#fddbc7'],[1,'#f0f0f0'],[3,'#d9f0d3'],[6,'#7fbf7b'],[1e9,'#1b7837']];
const dcol=v=>DV.find(([b])=>v<b)[1];
const PY=[[2020,'#1b5e20'],[2015,'#7cb342'],[2010,'#fdd835'],[2005,'#fb8c00'],[0,'#e53935']];
const pcol=y=>y==null?'#9e9e9e':PY.find(([b])=>y>=b)[1];
const TB=[5,10,20,30,40,60];const tcol=v=>{let i=0;while(i<TB.length&&v>=TB[i])i++;return GR[Math.min(7,i+1)]};
let D,TI,cfg,T,COND,SP,CV,mode=null,bmode='c17',hiB=null,spOnly=null,tAnn=[],tShown=false,BO=[],PO=[],tiles=null,listen=false;
const bname=b=>b.names&&b.names.length?(b.names.length===1?esc(b.names[0]):'Bounded by '+b.names.map(esc).join(', ').replace(/, ([^,]*)$/,' and $1')):'Block '+b.id;
const Cd=c=>new mapkit.Coordinate(c[1],c[0]);
const rings=g=>{const o=[];(g.type==='Polygon'?[g.coordinates]:g.coordinates).forEach(p=>p.forEach(r=>o.push(r.map(Cd))));return o};
function bStyle(b,hi){if(mode!=='blocks'&&!(mode==='trees'&&!tShown))return new mapkit.Style({fillOpacity:hi?.25:0,fillColor:'#ffd400',strokeColor:hi?'#0d1b4b':'#5b6394',strokeOpacity:hi?1:.2,lineWidth:hi?3:.6});
  if(mode==='trees')return new mapkit.Style({fillColor:tcol(b.acres?b.trees/b.acres:0),fillOpacity:.85,strokeColor:hi?'#0d1b4b':'#fff',lineWidth:hi?3:.8});
  const v=bmode==='c17'?b.c17:b.c17-b.c10;return new mapkit.Style({fillColor:bmode==='c17'?gcol(v):dcol(v),fillOpacity:.85,strokeColor:hi?'#0d1b4b':'#ffffff',lineWidth:hi?3:.8})}
const restyle=()=>BO.forEach(o=>o.style=bStyle(o.data.tb,o===hiB));
function bCard(b){const ch=Math.round((b.c17-b.c10)*10)/10;return `<div class="bh"><span class="gb" style="background:${gcol(b.c17)};color:${b.c17>=20?'#fff':'#0d1b4b'};font-size:.8rem">${Math.round(b.c17)}%</span><div><div class="bl">Block, with its half of the streets around it</div><div class="bn">${bname(b)}</div><div class="ba">Tree canopy ${b.c17}% in 2017, ${b.c10}% in 2010</div></div></div><div class="chips" style="margin-top:8px"><span class="chip">${ch>=0?'+':''}${ch} points since 2010</span><span class="chip">${b.gain}% new canopy</span><span class="chip">${b.loss}% lost</span><span class="chip">${fmt(b.trees)} street trees${b.dead?`, ${b.dead} dead`:''}</span>${b.dbh?`<span class="chip">Average trunk ${b.dbh} inches</span>`:''}</div>`}
function selectBlock(o,fly){const prev=hiB;hiB=o;if(prev)prev.style=bStyle(prev.data.tb,false);o.style=bStyle(o.data.tb,true);cfg.info.innerHTML=bCard(o.data.tb);cfg.info.style.display='block';if(fly)cfg.map.showItems([o],{animate:true,padding:new mapkit.Padding(80,80,80,80)})}
const icon={};const tIcon=(c,s)=>{const k=c+s;if(icon[k])return icon[k];const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${s}" height="${s}" viewBox="0 0 24 24"><circle cx="12" cy="10" r="9" fill="${c}" stroke="#fff" stroke-width="1.6"/><path d="M12 5l3.5 5h-2l3 4h-9l3-4h-2z" fill="#fff" opacity=".9"/><rect x="11" y="14" width="2" height="4" fill="#fff" opacity=".9"/></svg>`;const u='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svg);return icon[k]={1:u,2:u}};
const size=d=>d<6?16:d<12?20:d<18?24:d<24?28:32;
function treeAnns(){const map=cfg.map;map.removeAnnotations(tAnn);tAnn=[];
 if(mode!=='trees')return;
 if(map.cameraDistance>2200){tShown=false;restyle();if(!hiB)cfg.info.innerHTML='<b>Zoom in</b> to a few blocks to see every street tree. Until then each block is shaded by its street trees per acre.';return}
 tShown=true;restyle();if(!hiB)cfg.info.innerHTML='<b>Tap a tree</b> for its kind, condition, trunk size and when it was planted.';
 const r=map.region,la0=r.center.latitude-r.span.latitudeDelta/2,la1=r.center.latitude+r.span.latitudeDelta/2,lo0=r.center.longitude-r.span.longitudeDelta/2,lo1=r.center.longitude+r.span.longitudeDelta/2;
 T.forEach(t=>{if(t[0]<la0||t[0]>la1||t[1]<lo0||t[1]>lo1)return;if(spOnly!=null&&t[4]!==spOnly)return;const c=COND[t[3]],s=size(t[2]);
  tAnn.push(new mapkit.ImageAnnotation(new mapkit.Coordinate(t[0],t[1]),{url:tIcon(CCOL[c],s),size:{width:s,height:s},anchorOffset:new DOMPoint(0,0),title:SP[t[4]],subtitle:`${c} · trunk ${t[2]} in${t[5]?' · planted '+t[5]:''}`,data:{tree:1},displayPriority:t[2]>12?750:500,collisionMode:mapkit.Annotation.CollisionMode.Circle}))});
 map.addAnnotations(tAnn)}
const WHAT={canopy:()=>`<b>Tree canopy</b>: the ground covered by trees seen from above, from the City's 2017 laser survey, against 2010. <span class="sw sq" style="background:#2e7d32"></span>Dark green was canopy in 2010 and 2017. <span class="sw sq" style="background:#7cb342"></span>Light green is new since 2010. <span class="sw sq" style="background:#e53935"></span>Red was lost by 2017. Zoom in to see single trees; tap a block for its numbers.`,
 blocks:()=>`<b>Canopy by block</b>: each block, with its half of the streets around it, colored by how much of it is under trees. Darker green is more shade. Switch to change since 2010 to see which blocks gained or lost canopy.`,
 trees:()=>`<b>Street trees</b>: every tree the Parks Department cares for along CB6's sidewalks. Color is the tree's condition; bigger icons are bigger trunks. Zoom in to see them; zoomed out, blocks are shaded by street trees per acre.`,
 prune:()=>`<b>Pruning</b>: each street colored by the last year the Parks Department pruned all of its trees. Green is recent, red is long ago, gray has none on record since 1995.`};
const LEG={canopy:()=>`<span><span class="sw sq" style="background:#2e7d32"></span>Canopy in 2010 and 2017</span><span><span class="sw sq" style="background:#7cb342"></span>New since 2010</span><span><span class="sw sq" style="background:#e53935"></span>Lost since 2010</span><span style="color:var(--muted)">CB6: ${CV.c17}% in 2017, ${CV.c10}% in 2010</span>`,
 blocks:()=>`<select id="trBm" style="font:inherit;padding:6px 8px;border:1px solid #c9cde0;border-radius:8px"><option value="c17"${bmode==='c17'?' selected':''}>Share under canopy, 2017</option><option value="ch"${bmode==='ch'?' selected':''}>Change since 2010</option></select>`+(bmode==='c17'?['under 2%','2 to 5','5 to 10','10 to 15','15 to 20','20 to 30','30 to 40','40% or more'].map((t,i)=>`<span><span class="sw sq" style="background:${GR[i]};border:1px solid #ddd"></span>${t}</span>`).join(''):['lost 6+ points','lost 3 to 6','lost 1 to 3','about the same','gained 1 to 3','gained 3 to 6','gained 6+'].map((t,i)=>`<span><span class="sw sq" style="background:${DV[i][1]};border:1px solid #ddd"></span>${t}</span>`).join('')),
 trees:()=>COND.map(c=>`<span><span class="sw" style="background:${CCOL[c]};border-radius:50%"></span>${c} (${fmt(T.filter(t=>COND[t[3]]===c).length)})</span>`).join('')+`<span style="color:var(--muted)">Icon size: trunk width</span>`+(spOnly!=null?`<span><b>Only ${esc(SP[spOnly])}</b> <a href="#" id="trSpAll">show all</a></span>`:''),
 prune:()=>[['2020 or later',2020],['2015 to 2019',2015],['2010 to 2014',2010],['2005 to 2009',2005],['before 2005',0]].map(([t,y])=>`<span><span class="sw sq" style="background:${pcol(y)}"></span>${t}</span>`).join('')+`<span><span class="sw sq" style="background:#9e9e9e"></span>none since 1995</span><a href="/treepruning/">Every pruning, tree by tree</a>`};
function ensure(){const map=cfg.map;if(BO.length)return;
 BO=D.blocks.map(b=>{const o=new mapkit.PolygonOverlay(rings(b.g),{style:bStyle(b,false)});o.data={tb:b};return o});
 PO=D.segs.flatMap(s=>s.ln.map(l=>{const p=new mapkit.PolylineOverlay(l.map(c=>new mapkit.Coordinate(c[0],c[1])),{style:new mapkit.Style({strokeColor:pcol(s.last),lineWidth:5,lineCap:'round'})});p.data={seg:s};return p}));
 tiles=new mapkit.TileOverlay((x,y,z)=>TI.has(z+'/'+x+'/'+y)?`/trees/canopy/${z}/${x}/${y}.png`:'/trees/blank.png',{minimumZ:13,maximumZ:18,opacity:.9});
 if(!listen){listen=true;
  map.addEventListener('region-change-end',()=>{if(mode==='trees')treeAnns()});
  map.addEventListener('select',e=>{if(!mode)return;const o=e.overlay;
   if(o&&o.data&&o.data.tb){selectBlock(o);setTimeout(()=>{map.selectedOverlay=null},0);return}
   if(o&&o.data&&o.data.seg){const s=o.data.seg;cfg.info.innerHTML=`<div class="bh"><span class="gb" style="background:${pcol(s.last)};font-size:.75rem">${s.last||'–'}</span><div><div class="bl">Street segment</div><div class="bn">${esc(s.n)}, ${esc(s.hn.filter(x=>x&&x!=='0').join(' to '))}</div><div class="ba">${s.last?'Last pruned block-wide in '+s.last:'No block pruning on record since 1995'}</div></div></div><div class="bq"><a href="/treepruning/">Every pruning on this street ↗</a></div>`;setTimeout(()=>{map.selectedOverlay=null},0);return}
   const a=e.annotation;if(a&&a.data&&a.data.tree){cfg.info.innerHTML=`<div class="bh"><span class="gb" style="background:${CCOL[a.subtitle.split(' · ')[0]]||'#43a047'}">&#127795;</span><div><div class="bl">Street tree</div><div class="bn">${esc(a.title)}</div><div class="ba">${esc(a.subtitle)}</div></div></div>`;cfg.info.style.display='block'}})}}
function on(l){const map=cfg.map;ensure();off(true);mode=l;
 if(l==='canopy')map.addTileOverlay(tiles);
 if(l==='prune')map.addOverlays(PO);
 if(l!=='prune')map.addOverlays(BO);
 restyle();
 if(cfg.what){cfg.what.innerHTML=WHAT[l]();cfg.what.style.display='block'}
 cfg.legend.innerHTML=LEG[l]();
 const bm=document.getElementById('trBm');if(bm)bm.onchange=()=>{bmode=bm.value;on('blocks')};
 const sa=document.getElementById('trSpAll');if(sa)sa.onclick=e=>{e.preventDefault();spOnly=null;on('trees')};
 cfg.info.innerHTML=l==='prune'?'<b>Tap a street</b> to see when it was last pruned.':'<b>Tap a block</b> for its tree canopy and street trees.';cfg.info.style.display='block';
 if(l==='trees')treeAnns()}
function off(keep){const map=cfg.map;if(!mode)return;
 if(tiles&&map.tileOverlays.includes(tiles))map.removeTileOverlay(tiles);
 map.removeOverlays(PO.filter(o=>map.overlays.includes(o)));map.removeOverlays(BO.filter(o=>map.overlays.includes(o)));map.removeAnnotations(tAnn);tAnn=[];
 hiB=null;mode=null;if(cfg.what&&!keep)cfg.what.style.display='none'}
function section(){const el=cfg.section;if(!el)return;const dead=T.filter(t=>COND[t[3]]==='Dead').length;
 const bars=(rows,color)=>{const mx=Math.max(...rows.map(r=>r[1]));return rows.map(([l,v,c,a])=>`<div class="tbar"${a||''}><span>${esc(l)}</span><span class="tt"><i style="width:${100*v/mx}%;background:${c||color}"></i></span><span class="tn">${fmt(v)}</span></div>`).join('')};
 const DB=[[0,6,'Under 6 inches'],[6,12,'6 to 11 inches'],[12,18,'12 to 17 inches'],[18,24,'18 to 23 inches'],[24,36,'24 to 35 inches'],[36,1e9,'36 inches or more']];
 const low=D.blocks.filter(b=>b.acres>=.5).slice().sort((a,b)=>a.c17-b.c17).slice(0,20);
 el.innerHTML=`<div class="kpis"><div class="kpi"><div class="l">Tree canopy, 2017</div><div class="v">${CV.c17}%</div><div class="c">${fmt(CV.acres17)} of ${fmt(CV.acres)} acres. New Yorkers for Parks' 2021 profile: 17%</div></div><div class="kpi"><div class="l">Change since 2010</div><div class="v">${CV.c17-CV.c10>=0?'+':''}${Math.round((CV.c17-CV.c10)*10)/10} pts</div><div class="c">from ${CV.c10}%: ${CV.gain}% of CB6 gained canopy, ${CV.loss}% lost it</div></div><div class="kpi"><div class="l">Street trees</div><div class="v">${fmt(T.length-dead)}</div><div class="c">plus ${fmt(dead)} listed as dead</div></div><div class="kpi"><div class="l">Streets pruned since 2020</div><div class="v">${fmt(D.segs.filter(s=>s.last>=2020).length)}</div><div class="c">of ${fmt(D.segs.length)} street segments; ${fmt(D.segs.filter(s=>s.last==null).length)} have none on record since 1995</div></div></div>
 <p class="note" style="margin:10px 0">See them on the map: <a href="#" data-l="tcanopy">tree canopy</a> &middot; <a href="#" data-l="tblocks">canopy by block</a> &middot; <a href="#" data-l="tstreet">every street tree</a> &middot; <a href="#" data-l="tprune">pruning</a></p>
 <div class="two"><div><h3 class="th">How the street trees are doing</h3>${bars(COND.map(c=>[c,T.filter(t=>COND[t[3]]===c).length,CCOL[c]]))}</div><div><h3 class="th">How big they are (trunk width)</h3>${bars(DB.map(([a,b,l])=>[l,T.filter(t=>COND[t[3]]!=='Dead'&&t[2]>=a&&t[2]<b).length]),'#43a047')}</div></div>
 <h3 class="th">The most common street trees <span>tap one to see only that kind on the map</span></h3>${bars(SP.slice(0,12).map((s,i)=>[s,T.filter(t=>t[4]===i).length,'#2e7d32',` data-sp="${i}" style="cursor:pointer"`]))}
 <h3 class="th">Blocks with the least shade <span>canopy in 2017, each block with its half of the streets around it; tap a row to find it</span></h3><div style="overflow-x:auto"><table class="tt2"><tr><th>Block</th><th>2017</th><th>2010</th><th>Street trees</th></tr>${low.map(b=>`<tr data-tb="${b.id}" style="cursor:pointer"><td>${bname(b)}</td><td>${b.c17}%</td><td>${b.c10}%</td><td>${fmt(b.trees)}</td></tr>`).join('')}</table></div>`;
 el.addEventListener('click',e=>{const s=e.target.closest('[data-sp]');if(s){spOnly=+s.dataset.sp;cfg.show('tstreet');document.getElementById('map').scrollIntoView({behavior:'smooth',block:'start'});if(cfg.map.cameraDistance>2200){cfg.map.setCenterAnimated(new mapkit.Coordinate(40.6745,-73.9815),false);cfg.map.cameraDistance=1500}return}
  const r=e.target.closest('tr[data-tb]');if(r){cfg.show('tblocks');const o=BO.find(x=>String(x.data.tb.id)===r.dataset.tb);document.getElementById('map').scrollIntoView({behavior:'smooth',block:'start'});if(o)selectBlock(o,true)}})}
window.TREES={async init(o){cfg=o;[D,TI]=await Promise.all([fetch('/trees/data.json').then(r=>r.json()),fetch('/trees/tiles.json').then(r=>r.json()).then(a=>new Set(a))]);T=D.trees;COND=D.cond;SP=D.sp;CV=D.canopy;section()},on,off,get active(){return mode}};
})();
