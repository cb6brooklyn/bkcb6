// ---- BQE kit: layers, find bar, block cards, time window, record. Needs KSCOPE, KDIST, a Leaflet `map`.
(function(){
function E(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
if(typeof window.escH!=='function')window.escH=E;
var F=function(n){return (n||0).toLocaleString();};
var MN=['January','February','March','April','May','June','July','August','September','October','November','December'];
function mlab(m){return MN[+m.slice(5,7)-1].slice(0,3)+' '+m.slice(0,4);}
var KL,KB,KT,KD,KIN=[],INSET={},STAT=[],WIN={p:'12'},PICK=[],PINM=null,MODE='block';
map.createPane('kbnd');map.getPane('kbnd').style.zIndex=390;map.createPane('ktrp');map.getPane('ktrp').style.zIndex=420;map.createPane('kblk');map.getPane('kblk').style.zIndex=430;map.createPane('khi');map.getPane('khi').style.zIndex=640;map.createPane('kptp');map.getPane('kptp').style.zIndex=650;
var HI=L.layerGroup().addTo(map);
function status2(t){var s=document.getElementById('status');if(s){s.textContent=t;s.style.display=t?'block':'none';}}
// ================================================================= layers
var DK=[['cd','Community boards','#0d1b4b'],['council','City Council','#b91c1c'],['assembly','State Assembly','#1d4ed8'],['senate','State Senate','#15803d'],['congress','Congress','#7c3aed'],['precinct','NYPD precincts','#334155']];
var KLY={},KORD=[];var DOFF={cd:[0,-40],council:[46,-76],precinct:[-46,-112],assembly:[-56,40],senate:[56,76],congress:[0,112]};
function reg(k,o){o.g=L.layerGroup();KLY[k]=o;KORD.push(k);}
var BKC={'I':'#15803d','II':'#22c55e','III':'#86efac'};
var SLC={10:'#7c3aed',15:'#db2777',20:'#f59e0b',25:'#94a3b8',45:'#111827'};
var TRAIN='<svg viewBox="0 0 24 24" width="13" height="13" fill="#111"><path d="M12 2c-4 0-8 .5-8 4v9.5A3.5 3.5 0 0 0 7.5 19L6 20.5v.5h12v-.5L16.5 19A3.5 3.5 0 0 0 20 15.5V6c0-3.5-4-4-8-4zM7.5 17a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3zm3.5-6H6V6h5v5zm2 0V6h5v5h-5zm3.5 6a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3z"/></svg>';
function bikePill(cl,ty){return '<span class="bkpill c'+E(cl)+'">Class '+E(cl)+(ty?' &middot; '+E(ty):'')+'</span>';}
function busCol(r){var f=KL.bus_routes.features.filter(function(x){return x.properties.r===r;})[0];return f&&f.properties.c&&f.properties.c!=='#0d1b4b'?f.properties.c:'#0039a6';}
function dLogo(k,id){var d=KDIST[k]&&KDIST[k][id];return d?d[1]:'';}
function dName(k,id){var d=KDIST[k]&&KDIST[k][id];return d?d[0]:(k+' '+id);}
function swatch(o){if(o.logo)return '<img class="blg1" src="'+E(o.logo)+'" alt="">';if(o.sym==='dot')return '<i class="sw dot" style="background:'+o.color+';box-shadow:0 0 0 1px '+o.color+'"></i>';return '<i class="sw" style="background:'+o.color+'"></i>';}
function ringArea(r){var a=0;for(var i=0,j=r.length-1;i<r.length;j=i++)a+=(r[j][0]+r[i][0])*(r[j][1]-r[i][1]);return Math.abs(a/2);}
function inPoly(ll,poly){var x=ll[1],y=ll[0],inside=false;for(var r=0;r<poly.length;r++){var ring=poly[r],hit=false;for(var i=0,j=ring.length-1;i<ring.length;j=i++){var xi=ring[i][0],yi=ring[i][1],xj=ring[j][0],yj=ring[j][1];if(((yi>y)!==(yj>y))&&(x<(xj-xi)*(y-yi)/(yj-yi)+xi))hit=!hit;}if(r===0){if(!hit)return false;inside=true;}else if(hit)return false;}return inside;}
function polys(g){return g.type==='Polygon'?[g.coordinates]:g.coordinates;}
function labelPt(f){// a point inside the largest piece: the grid point farthest inside, on a coarse grid
  var P=polys(f.geometry).slice().sort(function(a,b){return ringArea(b[0])-ringArea(a[0]);})[0],r=P[0],x0=1e9,x1=-1e9,y0=1e9,y1=-1e9;r.forEach(function(c){x0=Math.min(x0,c[0]);x1=Math.max(x1,c[0]);y0=Math.min(y0,c[1]);y1=Math.max(y1,c[1]);});
  var best=null,bd=-1;for(var i=1;i<12;i++)for(var j=1;j<12;j++){var x=x0+(x1-x0)*i/12,y=y0+(y1-y0)*j/12;if(!inPoly([y,x],P))continue;var d=1e9;for(var k=0;k<r.length;k+=Math.max(1,Math.floor(r.length/200))){var dx=r[k][0]-x,dy=(r[k][1]-y)*1.3;d=Math.min(d,dx*dx+dy*dy);}if(d>bd){bd=d;best=[y,x];}}
  return best||[(y0+y1)/2,(x0+x1)/2];}
function mkLayers(){
  DK.forEach(function(dk){KL.districts.features.filter(function(f){return f.properties.k===dk[0];}).sort(function(a,b){return (+a.properties.id)-(+b.properties.id);}).forEach(function(f){var id=f.properties.id;
    reg('d-'+dk[0]+'-'+id,{group:dk[1],dk:dk[0],label:dName(dk[0],id),logo:dLogo(dk[0],id),color:dk[2],on:dk[0]==='cd'&&KSCOPE.cds[0]===id&&KSCOPE.cdOn,load:function(o){
      L.geoJSON(f,{pane:'kbnd',style:{color:dk[2],weight:dk[0]==='cd'?3:2.4,opacity:.9,dashArray:dk[0]==='cd'?null:'8 5',fill:true,fillColor:dk[2],fillOpacity:.03}}).bindTooltip('<span class="dtip">'+(o.logo?'<img src="'+E(o.logo)+'" alt="">':'')+E(o.label)+'</span>',{sticky:true,className:'tr-tip'}).addTo(o.g);
      var off=DOFF[dk[0]]||[0,0];L.marker(labelPt(f),{pane:'kptp',interactive:false,keyboard:false,zIndexOffset:500,icon:L.divIcon({className:'',iconSize:null,html:'<div class="dmk" style="border-color:'+dk[2]+';margin-left:'+off[0]+'px;margin-top:'+off[1]+'px">'+(o.logo?'<img src="'+E(o.logo)+'" alt="">':'')+E(o.label)+'</div>'})}).addTo(o.g);}});});});
  reg('nbhd',{group:'Neighborhoods',label:'Neighborhood outlines',color:'#9a3412',load:function(o){KL.neighborhoods.features.forEach(function(f){L.geoJSON(f,{pane:'kbnd',style:{color:'#9a3412',weight:1.6,dashArray:'2 4',fill:false}}).bindTooltip('<strong>'+E(f.properties.nb)+'</strong><br><span class="k">Neighborhood outline used across bkcb6.app (not an official boundary)</span>',{sticky:true,className:'tr-tip'}).addTo(o.g);L.marker(labelPt(f),{pane:'kptp',interactive:false,keyboard:false,icon:L.divIcon({className:'',iconSize:null,html:'<div class="rlab"><span class="rlt">'+E(f.properties.nb)+'</span></div>'})}).addTo(o.g);});}});
  reg('busr',{group:'Transit',label:'Bus routes',color:'#0039a6',load:function(o){L.geoJSON(KL.bus_routes,{pane:'ktrp',style:function(f){return{color:busCol(f.properties.r),weight:3,opacity:.85};},onEachFeature:function(f,l){l.bindTooltip(busPill(f.properties.r,busCol(f.properties.r))+'<br><span class="k">MTA bus route, both directions</span>',{sticky:true,className:'tr-tip'});}}).addTo(o.g);
    KL.bus_routes.features.forEach(function(f){var cs=f.geometry.type==='MultiLineString'?f.geometry.coordinates.slice().sort(function(a,b){return b.length-a.length;})[0]:f.geometry.coordinates;var c=cs[Math.floor(cs.length/2)];L.marker([c[1],c[0]],{pane:'kptp',interactive:false,keyboard:false,icon:L.divIcon({className:'',iconSize:null,html:'<div class="rlab">'+busPill(f.properties.r,busCol(f.properties.r))+'</div>'})}).addTo(o.g);});}});
  reg('buss',{group:'Transit',label:'Bus stops',color:'#0039a6',sym:'dot',load:function(o){KL.bus_stops.forEach(function(p){L.marker([p[0],p[1]],{pane:'kptp',icon:L.divIcon({className:'bus-stop-icon-wrap',iconSize:null,iconAnchor:[0,0],html:'<div class="bus-stop-sign" title="'+E(p[3].join(', ')+' · '+p[2])+'"><span class="bus-stop-bus-symbol" aria-hidden="true"></span></div>'})}).bindPopup('<strong>'+E(p[2])+'</strong><br><span class="k">MTA bus stop</span><br>'+p[3].map(function(r){return busPill(r,busCol(r));}).join(' ')).addTo(o.g);});}});
  reg('subl',{group:'Transit',label:'Subway lines',color:'#FF6319',load:function(o){L.geoJSON(KL.subway_lines,{pane:'ktrp',style:function(f){return{color:f.properties.c||'#0f766e',weight:4,opacity:.85};},onEachFeature:function(f,l){l.bindTooltip('<strong>'+E(f.properties.n)+'</strong><br><span class="k">Subway line, MTA color</span>',{sticky:true,className:'tr-tip'});}}).addTo(o.g);}});
  reg('subs',{group:'Transit',label:'Subway stations',color:'#111',sym:'dot',load:function(o){KL.subway_stops.forEach(function(p){L.marker([p[0],p[1]],{pane:'kptp',icon:L.divIcon({className:'',iconSize:null,html:'<div class="subway-icon-stack" title="'+E(p[2])+'"><span class="subway-train-glyph">'+TRAIN+'</span>'+subBullets(p[3])+'</div>'})}).bindPopup('<strong>'+E(p[2])+'</strong><br>'+subBullets(p[3])+'<br><span class="k">Subway station'+(p[4]==='1'?' &middot; accessible':'')+'</span>').addTo(o.g);});}});
  reg('bike',{group:'Streets',label:'Bike lanes, by class and type',color:'#16a34a',load:function(o){var seen={};L.geoJSON(KL.bike,{pane:'ktrp',style:function(f){var c=f.properties.cl;return{color:BKC[c]||'#16a34a',weight:c==='I'?4:3,opacity:.95,dashArray:c==='III'?'4 5':null};},onEachFeature:function(f,l){var p=f.properties;l.bindTooltip('<strong>'+E(p.s)+'</strong>'+(p.f?' <span class="k">'+E(p.f)+' to '+E(p.t)+'</span>':'')+'<br>'+bikePill(p.cl,p.ty)+(p.d?'<br><span class="k">Installed '+E(p.d)+'</span>':''),{sticky:true,className:'tr-tip'});
      var k=p.s+'|'+p.cl+'|'+p.ty;if(seen[k])return;seen[k]=1;var cs=f.geometry.type==='MultiLineString'?f.geometry.coordinates[0]:f.geometry.coordinates;if(!cs||cs.length<2)return;var c=cs[Math.floor(cs.length/2)];L.marker([c[1],c[0]],{pane:'kptp',interactive:false,keyboard:false,icon:L.divIcon({className:'',iconSize:null,html:'<div class="rlab bkl">'+bikePill(p.cl,p.ty)+'<span class="rlt">'+E(p.s)+'</span></div>'})}).addTo(o.g);}}).addTo(o.g);}});
  reg('speed',{group:'Streets',label:'Speed limits',color:'#f59e0b',load:function(o){L.geoJSON(KL.speed,{pane:'ktrp',style:function(f){var v=f.properties.sl;return{color:SLC[v]||'#cbd5e1',weight:v&&v!==25?4:2,opacity:.9};},onEachFeature:function(f,l){var p=f.properties;l.bindTooltip('<strong>'+E(p.s)+'</strong><br><span class="k">'+(p.sl?p.sl+' mph':'No value')+(p.sz?' &middot; school speed zone':'')+'</span>',{sticky:true,className:'tr-tip'});}}).addTo(o.g);}});
  reg('citi',{group:'Streets',label:'Citi Bike stations',color:'#0369a1',sym:'dot',load:function(o){KL.citibike.forEach(function(p){L.marker([p[0],p[1]],{pane:'kptp',icon:kIcon('citi',20),keyboard:false}).bindPopup('<strong>'+E(p[2])+'</strong><br><span class="k">Citi Bike station &middot; '+E(String(p[3]||''))+' docks</span>').addTo(o.g);});}});
  reg('hc',{group:'Blocks (in the time window)',label:'Blocks by crashes',color:'#dc2626',dyn:1});
  reg('ht',{group:'Blocks (in the time window)',label:'Blocks by truck complaints and tickets',color:'#92400e',dyn:1});
}
function kBuild(){var h='',grp=null;KORD.forEach(function(k){var o=KLY[k];if(o.group!==grp){if(grp!==null)h+='</div>';grp=o.group;var cnt=KORD.filter(function(x){return KLY[x].group===grp;}).length;h+='<div class="lgrp"><span class="lb">'+E(grp)+(o.dk?' ('+cnt+')':'')+'</span>';}
  h+='<button class="tbtn lt'+(o.on?' active':'')+'" id="klt-'+k+'" style="--tc:'+o.color+'" onclick="kTog(\''+k+'\')">'+swatch(o)+E(o.label)+'</button>';});
  h+='</div><div class="lgrp"><button class="tbtn" style="--tc:#0d1b4b" onclick="kAll(true)">All on</button><button class="tbtn" style="--tc:#0d1b4b" onclick="kAll(false)">All off</button></div><div id="kheatleg"></div>';
  document.getElementById('kitlayers').innerHTML=h;}
function kApply(k){var o=KLY[k];if(o.on){if(o.load&&!o.loaded){o.loaded=true;o.load(o);}if(o.dyn)drawHeat(k);map.addLayer(o.g);}else map.removeLayer(o.g);var b=document.getElementById('klt-'+k);if(b)b.classList.toggle('active',!!o.on);heatLegend();}
window.kTog=function(k){KLY[k].on=!KLY[k].on;if(KLY[k].on&&KLY[k].dyn){var other=k==='hc'?'ht':'hc';if(KLY[other].on){KLY[other].on=false;kApply(other);}}kApply(k);};
window.kAll=function(v){KORD.forEach(function(k){if(KLY[k].dyn&&v&&k==='ht')return;KLY[k].on=v;kApply(k);});};
function lowZ(){document.getElementById('map').classList.toggle('lowz',map.getZoom()<14);}
// block heat
var HB=[0,1,3,6,12],HCOL=['#e5e7eb','#fde68a','#fb923c','#ef4444','#991b1b'];
function heatVal(k,b){var s=STAT[b];return k==='hc'?s.cr[0]:(s.s3t+s.t4+s.t3);}
function heatBins(k){var v=KIN.map(function(b){return heatVal(k,b);}).filter(function(x){return x>0;}).sort(function(a,b){return a-b;});if(!v.length)return [1,2,3,4];var q=function(p){return v[Math.min(v.length-1,Math.floor(v.length*p))];};var b=[q(.25),q(.5),q(.75),q(.9)];for(var i=1;i<4;i++)if(b[i]<=b[i-1])b[i]=b[i-1]+1;return b;}
function hcol(v,b){if(!v)return HCOL[0];return v<=b[0]?HCOL[1]:v<=b[1]?HCOL[2]:v<=b[2]?HCOL[3]:HCOL[4];}
function drawHeat(k){var o=KLY[k];o.g.clearLayers();o.bins=heatBins(k);KIN.forEach(function(b){var f=KB.geo.features[b],v=heatVal(k,b);L.geoJSON(f,{pane:'kblk',style:{color:hcol(v,o.bins),weight:v?5:3,opacity:.95}}).bindTooltip('<strong>'+E(bname(KB.blocks[b]))+'</strong><br><span class="k">'+(k==='hc'?F(v)+' crashes':F(v)+' truck complaints and tickets')+' in the window</span>',{sticky:true,className:'tr-tip'}).on('click',function(){kPick(String(b));}).addTo(o.g);});}
function heatLegend(){var el=document.getElementById('kheatleg');if(!el)return;var k=KLY.hc&&KLY.hc.on?'hc':KLY.ht&&KLY.ht.on?'ht':null;if(!k){el.innerHTML='';return;}var b=KLY[k].bins||heatBins(k);
  el.innerHTML='<div class="kheatleg"><b>'+E(KLY[k].label)+', '+E(winText(k==='hc'?'c':'s'))+':</b> '+[['0',HCOL[0]],['1 to '+b[0],HCOL[1]],[(b[0]+1)+' to '+b[1],HCOL[2]],[(b[1]+1)+' to '+b[2],HCOL[3]],['over '+b[2],HCOL[4]]].map(function(x){return '<span><i style="background:'+x[1]+'"></i>'+x[0]+'</span>';}).join('')+' <span class="k">Bands are quartiles of the blocks with any, plus the top 10%. Tap a block for its record.</span></div>';}
// ================================================================= blocks and window
function bname(b){return b.street+', '+(b.from.join(' / ')||'dead end')+' to '+(b.to.join(' / ')||'dead end');}
function sumD(d,i0,i1){var t=0;for(var k in d){var m=+k;if(m>=i0&&m<=i1)t+=d[k];}return t;}
function sumCr(d,i0,i1){var t=[0,0,0,0,0,0];for(var k in d){var m=+k;if(m>=i0&&m<=i1)for(var j=0;j<6;j++)t[j]+=d[k][j];}return t;}
function lastFull(last,months){var d=new Date(last+'T00:00:00Z'),n=new Date(Date.UTC(d.getUTCFullYear(),d.getUTCMonth()+1,0)).getUTCDate();var i=months.indexOf(last.slice(0,7));return d.getUTCDate()===n?i:i-1;}
var CF,SF;
function setWin(p){WIN.p=p;var CM=KT.crash_months,SM=KT.s311_months;
  if(p==='all'){WIN.c0=0;WIN.c1=CF;WIN.s0=0;WIN.s1=SF;}
  else if(p==='custom'){var a=+document.getElementById('tw-from').value,b=+document.getElementById('tw-to').value;if(b<a){var t=a;a=b;b=t;}WIN.s0=a;WIN.s1=Math.min(b,SM.length-1);var ca=CM.indexOf(SM[a]),cb=CM.indexOf(SM[b]);WIN.c0=ca<0?CM.length-1:ca;WIN.c1=cb<0?CM.length-1:cb;}
  else{var n=+p;WIN.c1=CF;WIN.c0=Math.max(0,CF-n+1);WIN.s1=SF;WIN.s0=Math.max(0,SF-n+1);}
  STAT=KB.blocks.map(function(b,i){return {cr:sumCr(KT.cr[i],WIN.c0,WIN.c1),s3:sumD(KT.s3[i],WIN.s0,WIN.s1),s3t:sumD(KT.s3t[i],WIN.s0,WIN.s1),t4:sumD(KT.tk413[i],WIN.s0,WIN.s1),t3:sumD(KT.tk385[i],WIN.s0,WIN.s1)};});}
function winText(w){var M=w==='c'?KT.crash_months:KT.s311_months,a=w==='c'?WIN.c0:WIN.s0,b=w==='c'?WIN.c1:WIN.s1;return a===b?mlab(M[a]):mlab(M[a])+' to '+mlab(M[b]);}
function tkText(sh){var ti=KT.s311_months.indexOf((KT.tk_last||'').slice(0,7));if(ti<0||WIN.s1<=ti)return winText('s');if(WIN.s0>ti)return sh?'none published yet for these months':'none published yet for these months (the NYPD summons files run to '+KT.tk_last+')';return mlab(KT.s311_months[WIN.s0])+' to '+mlab(KT.s311_months[ti])+(sh?'':' (the NYPD summons files run to '+KT.tk_last+')');}
function nMonths(w){return (w==='c'?WIN.c1-WIN.c0:WIN.s1-WIN.s0)+1;}
window.kSetPreset=function(p){document.querySelectorAll('#twbar .tbtn').forEach(function(b){b.classList.toggle('active',b.getAttribute('data-p')===p);});document.getElementById('tw-custom').style.display=p==='custom'?'inline-flex':'none';
  if(p==='custom'){var f=document.getElementById('tw-from'),t=document.getElementById('tw-to');if(!f.options.length){var o=KT.s311_months.map(function(m,i){return '<option value="'+i+'">'+mlab(m)+'</option>';}).join('');f.innerHTML=o;t.innerHTML=o;}f.value=WIN.s0;t.value=WIN.s1;}
  setWin(p);renderAll();};
window.kCustom=function(){setWin('custom');renderAll();};
function renderAll(){document.querySelectorAll('.tw-lc').forEach(function(e){e.textContent=winText('c');});document.querySelectorAll('.tw-ls').forEach(function(e){e.textContent=winText('s');});document.querySelectorAll('.tw-lt').forEach(function(e){e.textContent=tkText(1);});
  ['hc','ht'].forEach(function(k){if(KLY[k].on)drawHeat(k);});heatLegend();renderRecord();if(PICK.length)showCard(PICK,CARDT);}
// ================================================================= find bar
var STREETS=[],BYST={};
function fillStreets(){KIN.forEach(function(i){var s=KB.blocks[i].street;if(!BYST[s]){BYST[s]=[];STREETS.push(s);}BYST[s].push(i);});STREETS.sort();
  var o='<option value="">Street&hellip;</option>'+STREETS.map(function(s){return '<option>'+E(s)+'</option>';}).join('');document.getElementById('k-bst').innerHTML=o;document.getElementById('k-sst').innerHTML=o;
  document.getElementById('k-blk').innerHTML='<option value="">Block&hellip;</option>';document.getElementById('k-sfr').innerHTML='<option value="">From&hellip;</option>';document.getElementById('k-sto').innerHTML='<option value="">To&hellip;</option>';}
window.kMode=function(m){MODE=m;['block','stretch','addr','pin'].forEach(function(x){document.getElementById('f-'+x).hidden=x!==m;});document.getElementById('map').classList.toggle('pinmode',m==='pin');};
window.kFillBlocks=function(){var s=document.getElementById('k-bst').value;document.getElementById('k-blk').innerHTML='<option value="">Block&hellip;</option>'+(BYST[s]||[]).map(function(i){var b=KB.blocks[i];return '<option value="'+i+'">'+E((b.from.join(' / ')||'dead end')+' to '+(b.to.join(' / ')||'dead end'))+'</option>';}).join('');};
window.kFillStretch=function(){var s=document.getElementById('k-sst').value,L2=BYST[s]||[];document.getElementById('k-sfr').innerHTML='<option value="">From&hellip;</option>'+L2.map(function(i,j){return '<option value="'+j+'">'+E(KB.blocks[i].from.join(' / ')||'dead end')+'</option>';}).join('');document.getElementById('k-sto').innerHTML='<option value="">To&hellip;</option>'+L2.map(function(i,j){return '<option value="'+j+'">'+E(KB.blocks[i].to.join(' / ')||'dead end')+'</option>';}).join('');
  if(L2.length){document.getElementById('k-sfr').value='0';document.getElementById('k-sto').value=String(L2.length-1);}};
window.kStretch=function(){var s=document.getElementById('k-sst').value,L2=BYST[s]||[],a=document.getElementById('k-sfr').value,b=document.getElementById('k-sto').value;if(!L2.length||a===''||b==='')return;a=+a;b=+b;if(b<a){var t=a;a=b;b=t;}var ids=L2.slice(a,b+1);
  var t2=s+', '+(KB.blocks[ids[0]].from.join(' / ')||'dead end')+' to '+(KB.blocks[ids[ids.length-1]].to.join(' / ')||'dead end');showCard(ids,t2,true);};
window.kPick=function(v){if(v===''||v==null){PICK=[];HI.clearLayers();document.getElementById('k-card').hidden=true;var r=document.getElementById('k-res');r.style.display='none';return;}var i=+v,b=KB.blocks[i];
  if(INSET[i]){document.getElementById('fmode').value='block';kMode('block');document.getElementById('k-bst').value=b.street;kFillBlocks();document.getElementById('k-blk').value=String(i);}
  showCard([i],bname(b),true);};
function nearestBlock(ll){var best=null,bd=1e18,cos=Math.cos(ll[0]*Math.PI/180);KIN.forEach(function(i){var cs=KB.geo.features[i].geometry.coordinates;cs=KB.geo.features[i].geometry.type==='MultiLineString'?[].concat.apply([],cs):cs;
  for(var k=0;k<cs.length-1;k++){var ax=(cs[k][0]-ll[1])*cos,ay=cs[k][1]-ll[0],bx=(cs[k+1][0]-ll[1])*cos,by=cs[k+1][1]-ll[0],dx=bx-ax,dy=by-ay,t=dx||dy?Math.max(0,Math.min(1,-(ax*dx+ay*dy)/(dx*dx+dy*dy))):0,x=ax+t*dx,y=ay+t*dy,d=x*x+y*y;if(d<bd){bd=d;best=i;}}});
  return best==null?null:{i:best,ft:Math.sqrt(bd)*364000};}
function districtsAt(ll){var out={};KL.districts.features.forEach(function(f){if(polys(f.geometry).some(function(p){return inPoly(ll,p);}))out[f.properties.k]=f.properties.id;});return out;}
var CITYF={cd:['/cd-boundaries-simple.geojson','cd'],council:['/data/council-districts.geojson','cc'],assembly:['/data/assembly-districts.geojson','ad'],senate:['/data/senate-districts.geojson','sd'],congress:['/data/congress-districts-simple.geojson','cong_dist'],precinct:['/data/precincts-simple.geojson','precinct']},CITYC={};
function cityFile(k){if(!CITYC[k])CITYC[k]=fetch(CITYF[k][0]).then(function(r){return r.json();}).catch(function(){return {features:[]};});return CITYC[k];}
function cityDistricts(ll){return Promise.all(DK.map(function(x){return cityFile(x[0]).then(function(g){var f=g.features.filter(function(f){return f.geometry&&polys(f.geometry).some(function(p){return inPoly(ll,p);});})[0];return f?[x[0],String(f.properties[CITYF[x[0]][1]])]:null;});})).then(function(a){var o={};a.forEach(function(p){if(p)o[p[0]]=p[1];});return o;});}
var CONG={'7':'velazquez','8':'jeffries','9':'clarke','10':'goldman'};
function cName(k,id){if(KDIST[k]&&KDIST[k][id])return KDIST[k][id][0];var n=parseInt(id,10);if(k==='cd'){var r=n%100;return r>=55?'Joint interest area '+id:({'1':'MNCB','2':'BXCB','3':'BKCB','4':'QNCB','5':'SICB'}[String(id)[0]]||'CB')+r;}if(k==='congress')return 'NY-'+n;if(k==='precinct')return n+'th Precinct';return {council:'Council ',assembly:'Assembly ',senate:'Senate '}[k]+n;}
function cLogo(k,id){if(KDIST[k]&&KDIST[k][id])return KDIST[k][id][1];var n=parseInt(id,10);if(k==='cd')return String(id)[0]==='3'&&n%100<55?'/elected/CB'+(n%100)+'_540.png':'';if(k==='council')return '/elected/CD'+n+'.png';if(k==='assembly')return '/elected/AD'+n+'.png';if(k==='senate')return '/elected/SD'+n+'.png';if(k==='precinct')return '/elected/precinct/'+n+'.png';if(k==='congress')return CONG[String(n)]?'/elected/'+CONG[String(n)]+'.png':'';return '';}
function chip(k,id){var lg=cLogo(k,id);return '<span class="dchip">'+(lg?'<img src="'+E(lg)+'" alt="" onerror="this.remove()">':'')+E(cName(k,id))+'</span>';}
function atPoint(ll,label){if(PINM)map.removeLayer(PINM);PINM=L.marker(ll,{pane:'kptp'}).addTo(map);var r=document.getElementById('k-res');r.innerHTML='<b>'+E(label)+'</b><p class="k">Looking up districts&hellip;</p>';r.style.display='block';
  var nb=nearestBlock(ll);if(nb&&nb.ft<600)showCard([nb.i],bname(KB.blocks[nb.i]),false);else{document.getElementById('k-card').hidden=true;HI.clearLayers();}map.setView(ll,Math.max(map.getZoom(),16));
  cityDistricts(ll).then(function(d){var h='<b>'+E(label)+'</b><div class="kdl">'+DK.filter(function(x){return d[x[0]];}).map(function(x){return chip(x[0],d[x[0]]);}).join('')+'</div>';
    if(!Object.keys(d).length)h+='<p class="k">This point is outside New York City\'s district boundaries.</p>';
    if(nb&&nb.ft<600)h+='<p class="k">Nearest block: '+E(bname(KB.blocks[nb.i]))+', about '+F(Math.round(nb.ft/10)*10)+' ft away (its record is below).</p>';
    else if(d.cd&&d.cd!=='306')h+='<p class="k">This point is outside Community District 6. The block-by-block record on this page covers '+E(KSCOPE.name)+' only.</p>';
    else h+='<p class="k">No block in '+E(KSCOPE.name)+' within 600 ft of this point, so there is no block record for it here.</p>';
    r.innerHTML=h;});}
window.kSearch=function(){var q=document.getElementById('k-addr').value.trim();if(!q)return;status2('Searching…');fetch('https://geosearch.planninglabs.nyc/v2/search?size=1&text='+encodeURIComponent(q)).then(function(r){return r.json();}).then(function(d){status2('');var f=d.features&&d.features[0];if(!f){var r=document.getElementById('k-res');r.innerHTML='No match for that address.';r.style.display='block';return;}var c=f.geometry.coordinates;atPoint([c[1],c[0]],f.properties.label);}).catch(function(){status2('The address search did not respond.');});};
window.kClearPin=function(){if(PINM){map.removeLayer(PINM);PINM=null;}kPick('');};
// ================================================================= block card
var CARDT='';
function agg(ids){var t={cr:[0,0,0,0,0,0],s3:0,s3t:0,t4:0,t3:0,ft:0};ids.forEach(function(i){var s=STAT[i];for(var j=0;j<6;j++)t.cr[j]+=s.cr[j];t.s3+=s.s3;t.s3t+=s.s3t;t.t4+=s.t4;t.t3+=s.t3;t.ft+=KB.blocks[i].ft;});return t;}
function uniq(a){var o=[],s={};a.forEach(function(x){var k=JSON.stringify(x);if(!s[k]){s[k]=1;o.push(x);}});return o;}
function monthly(key,ids,i0,i1,j){var n=i1-i0+1,a=new Array(n).fill(0);ids.forEach(function(b){var d=KT[key][b];for(var k in d){var m=+k;if(m>=i0&&m<=i1)a[m-i0]+=j==null?d[k]:d[k][j];}});return a;}
function types311(ids){var y0=+KT.s311_months[WIN.s0].slice(0,4),y1=+KT.s311_months[WIN.s1].slice(0,4),c={};ids.forEach(function(b){var st=KT.st[b];for(var t in st)for(var y in st[t])if(+y>=y0&&+y<=y1)c[t]=(c[t]||0)+st[t][y];});
  var rows=Object.keys(c).map(function(t){return [+t<KT.types.length?KT.types[+t]:'All other types',c[t],+t>=KT.types.length];}).sort(function(a,b){return (a[2]-b[2])||(b[1]-a[1]);});return {y0:y0,y1:y1,rows:rows};}
function showCard(ids,title,zoom){PICK=ids;CARDT=title;HI.clearLayers();var bb=null;ids.forEach(function(i){var l=L.geoJSON(KB.geo.features[i],{pane:'khi',style:{color:'#facc15',weight:9,opacity:.9}}).addTo(HI);L.geoJSON(KB.geo.features[i],{pane:'khi',style:{color:'#0d1b4b',weight:3}}).addTo(HI);bb=bb?bb.extend(l.getBounds()):l.getBounds();});
  if(zoom&&bb){map.fitBounds(bb.pad(ids.length>1?.15:1.2),{maxZoom:17});}
  var bs=ids.map(function(i){return KB.blocks[i];}),t=agg(ids),d={};bs.forEach(function(b){for(var k in b.d){d[k]=d[k]||{};d[k][b.d[k][0]]=1;b.d[k][1].forEach(function(x){d[k][x]=1;});}});
  var nbs=uniq(bs.map(function(b){return b.nb||'no neighborhood outline';}));
  var h='<div class="bch"><h3>'+E(title)+'</h3><span class="k">'+(ids.length>1?F(ids.length)+' blocks, ':'')+F(t.ft)+' ft'+(ids.length===1&&bs[0].hn?' &middot; house numbers '+bs[0].hn[0]+' to '+bs[0].hn[1]:'')+' &middot; '+E(nbs.join(', '))+'</span><button class="tbtn" style="--tc:#0d1b4b" onclick="kPick(\'\')">Close</button></div>';
  h+='<div class="kdl">'+DK.filter(function(x){return d[x[0]];}).map(function(x){return Object.keys(d[x[0]]).map(function(id){var lg=dLogo(x[0],id);return '<span class="dchip">'+(lg?'<img src="'+E(lg)+'" alt="">':'')+E(dName(x[0],id))+'</span>';}).join('');}).join('')+'</div>';
  var tr=uniq([].concat.apply([],bs.map(function(b){return b.truck;}))),trn=bs.filter(function(b){return b.truck.length;}).length;
  var bk=uniq([].concat.apply([],bs.map(function(b){return b.bike;}))),bus=uniq([].concat.apply([],bs.map(function(b){return b.bus;}))),stops=uniq([].concat.apply([],bs.map(function(b){return b.stops;})));
  var sp=uniq([].concat.apply([],bs.map(function(b){return b.speed.length?b.speed:b.cscl.speed;}))),sub=[].concat.apply([],bs.map(function(b){return b.subway;})).sort(function(a,b){return a[0]-b[0];}),subU=[],ss={};sub.forEach(function(s){if(!ss[s[1]+s[2]]){ss[s[1]+s[2]]=1;subU.push(s);}});
  var ci=[].concat.apply([],bs.map(function(b){return b.citi;})).sort(function(a,b){return a[0]-b[0];}),ciU=[],cs2={};ci.forEach(function(s){if(!cs2[s[1]]){cs2[s[1]]=1;ciU.push(s);}});
  var c1=bs[0].cscl;
  h+='<div class="bcg"><div class="bcs"><b>Truck route</b> '+(tr.length?tr.map(function(x){return '<span class="dchip" style="border-color:'+(x==='Through'?'#b91c1c':'#f47920')+'">'+E(x)+' truck route</span>';}).join('')+(ids.length>1?' <span class="k">on '+trn+' of '+ids.length+' blocks</span>':''):'<span class="k">Not a designated truck route. Trucks may use it only to reach a destination on it or the next block (DOT truck route rules).</span>')+'</div>';
  h+='<div class="bcs"><b>Street</b> <span class="k">'+(sp.length?'Speed limit '+E(sp.join(' / '))+' mph':'')+(ids.length===1?(c1.width.length?' &middot; '+E(c1.width.join('/'))+' ft wide':'')+(c1.lanes.length?' &middot; '+E(c1.lanes.join('/'))+' travel lane'+(c1.lanes.join('')==='1'?'':'s'):'')+(c1.park.length?' &middot; '+E(c1.park.join('/'))+' parking lane'+(c1.park.join('')==='1'?'':'s'):'')+(c1.dir.length?' &middot; '+({FT:'one way',TF:'one way',TW:'two way'}[c1.dir[0]]||E(c1.dir[0])):''):'')+'</span></div>';
  h+='<div class="bcs"><b>Bike</b> '+(bk.length?bk.map(function(x){var m=x.match(/^Class (\w+): (.*)$/);return m?bikePill(m[1],m[2]):E(x);}).join(' '):'<span class="k">No bike lane</span>')+'</div>';
  h+='<div class="bcs"><b>Transit</b> '+(bus.length?bus.map(function(r){return busPill(r,busCol(r));}).join(' '):'<span class="k">No bus route</span>')+(stops.length?'<br><span class="k">Stops: '+stops.map(function(s){return E(s[0])+' '+s[1].map(function(r){return busPill(r,busCol(r));}).join('');}).join('; ')+'</span>':'')+(subU.length?'<br><span class="k">Nearest subway: '+subU.slice(0,3).map(function(s){return E(s[1])+' '+subBullets(s[2])+' '+F(Math.round(s[0]/10)*10)+' ft';}).join('; ')+'</span>':'')+(ciU.length?'<br><span class="k">Citi Bike: '+ciU.slice(0,2).map(function(s){return E(s[1])+' '+F(Math.round(s[0]/10)*10)+' ft';}).join('; ')+'</span>':'')+'</div></div>';
  var cr=t.cr;h+='<div class="bcw"><b>In the time window</b> <span class="k">crashes '+E(winText('c'))+'; 311 '+E(winText('s'))+'; tickets '+E(tkText())+'</span></div>';
  h+='<div class="tblwrap"><table class="cmp"><tr><th>Crashes</th><th>People injured</th><th>Cyclists injured</th><th>Pedestrians injured</th><th>Killed</th><th>Crashes involving a truck</th></tr><tr>'+cr.map(function(v){return '<td class="num">'+F(v)+'</td>';}).join('')+'</tr></table></div>';
  h+='<div class="tblwrap"><table class="cmp"><tr><th>311 requests</th><th>311 truck route complaints</th><th>NYPD truck route tickets (VTL 413)</th><th>NYPD size and weight tickets (VTL 385)</th></tr><tr><td class="num">'+F(t.s3)+'</td><td class="num">'+F(t.s3t)+'</td><td class="num">'+F(t.t4)+'</td><td class="num">'+F(t.t3)+'</td></tr></table></div>';
  var ty=types311(ids);h+='<div class="bcl"><b>Most common 311 requests</b> <span class="k">calendar year'+(ty.y0===ty.y1?' '+ty.y0:'s '+ty.y0+' to '+ty.y1)+' (the years the window touches)</span><ol>'+ty.rows.filter(function(r){return !r[2];}).slice(0,8).map(function(r){return '<li>'+E(r[0])+' <span class="k">'+F(r[1])+'</span></li>';}).join('')+'</ol>'+(ty.rows.filter(function(r){return r[2];}).map(function(r){return '<span class="k">Other types outside the 40 most common in CB6: '+F(r[1])+'</span>';}).join(''))+'</div>';
  h+='<div class="chartbox" id="k-cardc"></div><div class="chartbox" id="k-cardt"></div>';
  var el=document.getElementById('k-card');el.innerHTML=h;el.hidden=false;
  var CM=KT.crash_months.slice(WIN.c0,WIN.c1+1),SM=KT.s311_months.slice(WIN.s0,WIN.s1+1);
  if(CM.length>1){var a=monthly('cr',ids,WIN.c0,WIN.c1,0),b2=monthly('s3',ids,WIN.s0,WIN.s1);lineChart('k-cardc',[{name:'311 requests',color:'#475569',pts:SM.map(function(m,i){return [m,b2[i]];})}],{label:'311 requests by month',ymin:0});
    var tt=monthly('s3t',ids,WIN.s0,WIN.s1),t4=monthly('tk413',ids,WIN.s0,WIN.s1),t3=monthly('tk385',ids,WIN.s0,WIN.s1),cm=CM.map(function(m){return SM.indexOf(m);});
    lineChart('k-cardt',[{name:'Crashes',color:'#dc2626',pts:CM.map(function(m,i){return [m,a[i]];})},{name:'Truck complaints and tickets',color:'#92400e',pts:CM.map(function(m){var j=SM.indexOf(m);return [m,j<0?0:tt[j]+t4[j]+t3[j]];})}],{label:'Crashes and truck complaints by month',ymin:0});}}
// ================================================================= record
function sumNb(kind,i0,i1,daily){var nbs=KSCOPE.nbs||Object.keys(KD.daily),out=null;nbs.forEach(function(nb){var a=KD.daily[nb]&&KD.daily[nb][kind];if(!a)return;if(!out)out=new Array(a.length).fill(0);for(var i=0;i<a.length;i++)out[i]+=a[i];});return out||[];}
function dayIdx(ym,end){var d=new Date(Date.UTC(+ym.slice(0,4),+ym.slice(5,7)-1+(end?1:0),end?0:1)),s=new Date(KD.start+'T00:00:00Z');return Math.round((d-s)/864e5);}
function renderRecord(){var CM=KT.crash_months.slice(WIN.c0,WIN.c1+1),SM=KT.s311_months.slice(WIN.s0,WIN.s1+1);
  // by neighborhood
  var groups={};KIN.forEach(function(i){var n=KB.blocks[i].nb||'No neighborhood outline';(groups[n]=groups[n]||[]).push(i);});var gk=Object.keys(groups).sort(function(a,b){return groups[b].length-groups[a].length;});
  var row=function(n,ids){var t=agg(ids);return '<tr><td>'+E(n)+'</td><td class="num">'+F(ids.length)+'</td><td class="num">'+(100*ids.length/KIN.length).toFixed(1)+'%</td><td class="num">'+F(Math.round(t.ft/5280*10)/10)+'</td><td class="num">'+F(t.cr[0])+'</td><td class="num">'+F(t.cr[1])+'</td><td class="num">'+F(t.cr[5])+'</td><td class="num">'+F(t.s3)+'</td><td class="num">'+F(t.s3t)+'</td><td class="num">'+F(t.t4)+'</td><td class="num">'+F(t.t3)+'</td></tr>';};
  var h='<div class="tblwrap"><table class="cmp"><tr><th>Neighborhood</th><th>Blocks</th><th>Share of blocks</th><th>Street miles</th><th>Crashes</th><th>Injured</th><th>Truck crashes</th><th>311</th><th>Truck complaints</th><th>413 tickets</th><th>385 tickets</th></tr>'+gk.map(function(n){return row(n,groups[n]);}).join('')+(gk.length>1?row('Total',KIN).replace('<tr>','<tr style="font-weight:800">'):'')+'</table></div>';
  // blocks by district
  h+='<div class="sub2"><h3>Blocks by district</h3><p>A block counts in the district its midpoint is in; the "also" column counts blocks a boundary runs through.</p></div><div class="tblwrap"><table class="cmp"><tr><th>District</th><th>Blocks</th><th>Share of blocks</th><th>Also touches</th></tr>';
  DK.forEach(function(x){var c={},a={};KIN.forEach(function(i){var v=KB.blocks[i].d[x[0]];if(!v)return;c[v[0]]=(c[v[0]]||0)+1;v[1].forEach(function(y){a[y]=(a[y]||0)+1;});});Object.keys(c).concat(Object.keys(a).filter(function(y){return !c[y];})).sort(function(p,q){return (c[q]||0)-(c[p]||0);}).forEach(function(id){var lg=dLogo(x[0],id);h+='<tr><td><span class="dchip">'+(lg?'<img src="'+E(lg)+'" alt="">':'')+E(dName(x[0],id))+'</span></td><td class="num">'+F(c[id]||0)+'</td><td class="num">'+(100*(c[id]||0)/KIN.length).toFixed(1)+'%</td><td class="num">'+F(a[id]||0)+'</td></tr>';});});
  document.getElementById('k-tab').innerHTML=h+'</table></div>';
  var tt=monthly('s3t',KIN,WIN.s0,WIN.s1),t4=monthly('tk413',KIN,WIN.s0,WIN.s1),t3=monthly('tk385',KIN,WIN.s0,WIN.s1),s3=monthly('s3',KIN,WIN.s0,WIN.s1),c0=monthly('cr',KIN,WIN.c0,WIN.c1,0),c5=monthly('cr',KIN,WIN.c0,WIN.c1,5);
  var P=function(M,a){return M.map(function(m,i){return [m,a[i]];});};
  if(SM.length>1){lineChart('k-tm',[{name:'311 truck route complaints',color:'#92400e',pts:P(SM,tt)},{name:'Truck route tickets (413)',color:'#b91c1c',pts:P(SM,t4)},{name:'Size and weight tickets (385)',color:'#7c3aed',pts:P(SM,t3),dash:'5 4'}],{label:'Truck complaints and tickets by month',ymin:0});
    lineChart('k-sm',[{name:'311 requests',color:'#475569',pts:P(SM,s3)}],{label:'311 requests by month',ymin:0});}
  else{barChart('k-tm',[mlab(SM[0])],[{name:'311 truck route complaints',color:'#92400e',vals:tt},{name:'413 tickets',color:'#b91c1c',vals:t4},{name:'385 tickets',color:'#7c3aed',vals:t3}],{label:'Truck complaints and tickets'});barChart('k-sm',[mlab(SM[0])],[{name:'311 requests',color:'#475569',vals:s3}],{label:'311 requests'});}
  if(CM.length>1)lineChart('k-cm',[{name:'Crashes',color:'#dc2626',pts:P(CM,c0)},{name:'Crashes involving a truck',color:'#92400e',pts:P(CM,c5)}],{label:'Crashes by month',ymin:0});else barChart('k-cm',[mlab(CM[0])],[{name:'Crashes',color:'#dc2626',vals:c0},{name:'Involving a truck',color:'#92400e',vals:c5}],{label:'Crashes'});
  // by year
  var ys={},yk=[];var addY=function(M,a,key){M.forEach(function(m,i){var y=m.slice(0,4);if(!ys[y]){ys[y]={n:0,c:0,c5:0,s:0,t:0,k:0,cm:0,sm:0};yk.push(y);}ys[y][key]+=a[i];if(key==='c')ys[y].cm++;if(key==='s')ys[y].sm++;});};
  addY(CM,c0,'c');addY(CM,c5,'c5');addY(SM,s3,'s');addY(SM,tt,'t');addY(SM,t4.map(function(v,i){return v+t3[i];}),'k');yk.sort();
  var yl=yk.map(function(y){return y+((ys[y].sm<12||ys[y].cm<12)?'*':'');});
  document.getElementById('k-yr').innerHTML='<div id="k-yr1"></div><div id="k-yr2"></div>';
  barChart('k-yr1',yl,[{name:'Crashes',color:'#dc2626',vals:yk.map(function(y){return ys[y].c;})},{name:'Crashes involving a truck',color:'#92400e',vals:yk.map(function(y){return ys[y].c5;})},{name:'311 truck complaints',color:'#b45309',vals:yk.map(function(y){return ys[y].t;})},{name:'Truck tickets (413 and 385)',color:'#7c3aed',vals:yk.map(function(y){return ys[y].k;})}],{label:'Crashes and truck records by year'});
  barChart('k-yr2',yl,[{name:'311 requests',color:'#475569',vals:yk.map(function(y){return ys[y].s;})}],{label:'311 requests by year'});
  // day of week and hour
  var dc=sumNb('crash'),ds=sumNb('s311'),dt=sumNb('s3t'),ca=dayIdx(KT.crash_months[WIN.c0],0),cb=Math.min(dc.length-1,dayIdx(KT.crash_months[WIN.c1],1)),sa=dayIdx(KT.s311_months[WIN.s0],0),sb=Math.min(ds.length-1,dayIdx(KT.s311_months[WIN.s1],1));
  var s0=new Date(KD.start+'T00:00:00Z').getUTCDay(),DW=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];var dow=function(a,i0,i1){var o=[0,0,0,0,0,0,0];for(var i=i0;i<=i1;i++)o[((s0+i)%7+6)%7]+=a[i]||0;return o;};
  barChart('k-dow',DW,[{name:'Crashes',color:'#dc2626',vals:dow(dc,ca,cb)},{name:'311 truck complaints',color:'#92400e',vals:dow(dt,sa,sb)}],{label:'By day of the week'});
  var hr=function(kind,i0,i1){var o=new Array(24).fill(0);(KSCOPE.nbs||Object.keys(KD.hour)).forEach(function(nb){var h2=KD.hour[nb]&&KD.hour[nb][kind];if(!h2)return;for(var m=i0;m<=i1;m++){var a=h2[m];if(a)for(var j=0;j<24;j++)o[j]+=a[j];}});return o;};
  var HL=[];for(var j=0;j<24;j++)HL.push(j%3===0?(j===0?'12a':j<12?j+'a':j===12?'12p':(j-12)+'p'):'');
  barChart('k-hr',HL,[{name:'Crashes',color:'#dc2626',vals:hr('crash',WIN.c0,WIN.c1)},{name:'311 truck complaints',color:'#92400e',vals:hr('s3t',WIN.s0,WIN.s1)}],{label:'By hour of the day'});
  var dw=document.getElementById('k-daywrap');if(nMonths('s')<=24){dw.style.display='';var D0=new Date(KD.start+'T00:00:00Z'),dd=function(i){return new Date(D0.getTime()+i*864e5).toISOString().slice(0,10);},pts=[],pc=[];for(var i=sa;i<=sb;i++){pts.push([dd(i),dt[i]||0]);}
    var cmap={};for(var i2=ca;i2<=cb;i2++)cmap[dd(i2)]=dc[i2]||0;pts.forEach(function(p){pc.push([p[0],cmap[p[0]]!=null?cmap[p[0]]:0]);});
    if(pts.length>1)lineChart('k-day',[{name:'Crashes',color:'#dc2626',pts:pc},{name:'311 truck complaints',color:'#92400e',pts:pts}],{label:'By day',ymin:0});}else dw.style.display='none';
  // comparison per street mile per year
  var mi=KIN.reduce(function(s,i){return s+KB.blocks[i].ft;},0)/5280,yc=nMonths('c')/12,ysn=nMonths('s')/12,T=agg(KIN);
  var ARN={'302':'BKCB2','306':'BKCB6','307':'BKCB7','308':'BKCB8','brooklyn':'Brooklyn'};
  var r2=function(n,a,b,c,m){return '<tr><td>'+n+'</td><td class="num">'+F(Math.round(m*10)/10)+'</td><td class="num">'+(a/m/yc).toFixed(1)+'</td><td class="num">'+(b/m/ysn).toFixed(0)+'</td><td class="num">'+(c/m/ysn).toFixed(2)+'</td></tr>';};
  var ch='<div class="tblwrap"><table class="cmp"><tr><th>Area</th><th>Street miles</th><th>Crashes per mile per year</th><th>311 per mile per year</th><th>Truck complaints per mile per year</th></tr>'+r2('<b>'+E(KSCOPE.name)+'</b>, within 100 ft of its blocks',T.cr[0],T.s3,T.s3t,mi);
  KSCOPE.cds.concat(['brooklyn']).forEach(function(a){var A=KT.areas[a];if(!A)return;var sc=0,ss=0,st2=0;for(var i=WIN.c0;i<=WIN.c1;i++)sc+=A.crash_m[i]||0;for(var j=WIN.s0;j<=WIN.s1;j++){ss+=A.s311_m[j]||0;st2+=(A.truck311_m||[])[j]||0;}
    var lk='<a href="'+E(A.crash_url)+'" target="_blank" rel="noopener">crashes</a>, '+A.s311_urls.map(function(u,k){return '<a href="'+E(u)+'" target="_blank" rel="noopener">311'+(A.s311_urls.length>1?' ('+(k?'2020 on':'to 2019')+')':'')+'</a>';}).join(', ');
    ch+=r2(E(ARN[a]||a)+' whole '+(a==='brooklyn'?'borough':'district')+' <span class="k">('+lk+')</span>',sc,ss,st2,A.mi);});
  document.getElementById('k-cmp').innerHTML=ch+'</table></div>';
  // rankings
  var rk=function(fn){return KIN.map(function(i){return [bname(KB.blocks[i]),fn(i),i];}).filter(function(r){return r[1]>0;}).sort(function(a,b){return b[1]-a[1];}).slice(0,15);};
  document.getElementById('k-rk-note').textContent='The 15 blocks with the most in the window. Tap a block to open its record and see it on the map.';
  var h1=rk(function(i){return STAT[i].s3t+STAT[i].t4+STAT[i].t3;}),h2=rk(function(i){return STAT[i].cr[0];});
  document.getElementById('k-rkt').innerHTML='';document.getElementById('k-rkc').innerHTML='';
  if(h1.length){kHbar('k-rkt',h1,{label:'Truck complaints and tickets',color:'#92400e'});document.getElementById('k-rkt').insertAdjacentHTML('afterbegin','<div class="lg"><span><i style="background:#92400e;height:10px"></i>311 truck complaints plus truck route and size and weight tickets</span></div>');}else document.getElementById('k-rkt').innerHTML='<p class="k">No truck complaints or tickets in this window.</p>';
  if(h2.length){kHbar('k-rkc',h2,{label:'Crashes',color:'#dc2626'});document.getElementById('k-rkc').insertAdjacentHTML('afterbegin','<div class="lg"><span><i style="background:#dc2626;height:10px"></i>Crashes</span></div>');}
  renderAllTable();}
function kHbar(id,rows,opt){var el=document.getElementById(id);if(!el)return;var W=860,rh=24,pl=330,pr=60,H=rows.length*rh+10,mx=Math.max.apply(null,rows.map(function(r){return r[1];}))||1;var s='<svg viewBox="0 0 '+W+' '+H+'" role="img" aria-label="'+E(opt.label)+'">';
  rows.forEach(function(r,i){var y=5+i*rh,w=(W-pl-pr)*r[1]/mx,lab=r[0].length>52?r[0].slice(0,50)+'…':r[0];s+='<a href="#map" onclick="kPick('+r[2]+')"><text x="'+(pl-8)+'" y="'+(y+16)+'" text-anchor="end" font-size="11.5" fill="#0d1b4b" font-weight="700">'+E(lab)+'<title>'+E(r[0])+'</title></text><rect x="'+pl+'" y="'+(y+4)+'" width="'+w+'" height="'+(rh-8)+'" rx="3" fill="'+opt.color+'"><title>'+E(r[0])+': '+r[1].toLocaleString()+'</title></rect><text x="'+(pl+w+6)+'" y="'+(y+16)+'" font-size="11" fill="#333">'+r[1].toLocaleString()+'</text></a>';});
  el.innerHTML=s+'</svg>';}
var SORT={k:'t',d:-1};
window.kSort=function(k){SORT.d=SORT.k===k?-SORT.d:-1;SORT.k=k;renderAllTable();};
function renderAllTable(){var cols=[['b','Block'],['nb','Neighborhood'],['tr','Truck route'],['bk','Bike'],['sp','Speed'],['c','Crashes'],['i','Injured'],['c5','Truck crashes'],['s','311'],['t','Truck complaints'],['k4','413 tickets'],['k3','385 tickets']];
  var rows=KIN.map(function(i){var b=KB.blocks[i],s=STAT[i];return {id:i,b:bname(b),nb:b.nb||'',tr:b.truck.join(', '),bk:b.bike.map(function(x){return x.replace(/^Class (\w+):.*$/,'$1');}).join(', '),sp:(b.speed.length?b.speed:b.cscl.speed).join('/'),c:s.cr[0],i:s.cr[1],c5:s.cr[5],s:s.s3,t:s.s3t,k4:s.t4,k3:s.t3};});
  rows.sort(function(a,b){var x=a[SORT.k],y=b[SORT.k];if(typeof x==='number')return SORT.d*(x-y)||a.id-b.id;return SORT.d*String(x).localeCompare(String(y))*-1||a.id-b.id;});
  var h='<div class="tblwrap"><table class="cmp blkt"><tr>'+cols.map(function(c){return '<th class="srt" onclick="kSort(\''+c[0]+'\')">'+c[1]+(SORT.k===c[0]?(SORT.d<0?' &#9660;':' &#9650;'):'')+'</th>';}).join('')+'</tr>';
  rows.forEach(function(r){h+='<tr><td><a href="#map" onclick="kPick('+r.id+')">'+E(r.b)+'</a></td><td>'+E(r.nb)+'</td><td>'+E(r.tr)+'</td><td>'+E(r.bk)+'</td><td>'+E(r.sp)+'</td>'+['c','i','c5','s','t','k4','k3'].map(function(k){return '<td class="num">'+F(r[k])+'</td>';}).join('')+'</tr>';});
  document.getElementById('k-all').innerHTML=h+'</table></div>';}
// ================================================================= boot
map.on('zoomend',lowZ);lowZ();
map.on('click',function(e){if(MODE==='pin')atPoint([e.latlng.lat,e.latlng.lng],'Pin at '+e.latlng.lat.toFixed(5)+', '+e.latlng.lng.toFixed(5));});
document.getElementById('k-addr').addEventListener('keydown',function(e){if(e.key==='Enter')kSearch();});
var J=function(u){return fetch(u).then(function(r){if(!r.ok)throw new Error(u);return r.json();});};
Promise.all([J('/data/bqe/kit/layers.json'),J('/data/bqe/kit/blocks.json'),J('/data/bqe/kit/ts.json'),J('/data/bqe/kit/daily.json')]).then(function(a){KL=a[0];KB=a[1];KT=a[2];KD=a[3];
  KB.blocks.forEach(function(b,i){if(!KSCOPE.nbs||KSCOPE.nbs.indexOf(b.nb)>=0){KIN.push(i);INSET[i]=1;}});
  CF=lastFull(KT.crash_last,KT.crash_months);SF=lastFull(KT.s311_last,KT.s311_months);
  mkLayers();kBuild();setWin('12');KORD.forEach(kApply);fillStreets();renderAll();if(window.kSwapSwatches)kSwapSwatches(document);
}).catch(function(e){var el=document.getElementById('k-tab');if(el)el.innerHTML='<p class="k">The block data could not be loaded.</p>';if(window.console)console.error(e);});
})();
