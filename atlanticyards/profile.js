(function(){
var NAVY='#0d1b4b',OR='#f47920',TEAL='#0e7490';
var el=document.getElementById('map'),KIND=el.getAttribute('data-kind'),TGT=el.getAttribute('data-target');
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
var app=/[?&]app=1\b/.test(location.search)||(function(){try{return sessionStorage.getItem('bkapp')==='1'}catch(e){return false}})();
function href(slug){return '/atlanticyards/'+slug+'/'+(app?'?app=1':'')}
var map=L.map('map',{zoomControl:false,scrollWheelZoom:false}).setView([40.6825,-73.973],17);
L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png?key=cb1_2hyw_1_9cda1572a3817275ed412c0e',{subdomains:'abcd',maxZoom:20,attribution:'&copy; OpenStreetMap &copy; CARTO'}).addTo(map);
L.control.zoom({position:'topright'}).addTo(map);
map.on('click',function(){map.scrollWheelZoom.enable()});
var RC={'2':'#EE352E','3':'#EE352E','4':'#00933C','5':'#00933C','B':'#FF6319','D':'#FF6319','N':'#FCCC0A','Q':'#FCCC0A','R':'#FCCC0A','A':'#0039A6','C':'#0039A6','G':'#6CBE45'};
var LY={},ON={lirr:true,subway:true,bus:false},TR=null,IDX=[];
function slugOf(id){for(var i=0;i<IDX.length;i++)if(IDX[i].id===id)return IDX[i].slug;return null}
function go(id){var s=slugOf(id);if(s)location.href=href(s)}
Promise.all([fetch('/atlanticyards/data.json').then(function(r){return r.json()}),fetch('/atlanticyards/transit.json').then(function(r){return r.json()}),fetch('/data/cb6_boundary.geojson').then(function(r){return r.json()}).catch(function(){return null}),fetch('/atlanticyards/profiles.json').then(function(r){return r.json()})]).then(function(a){
  var D=a[0];TR=a[1];IDX=a[3];
  /* transit underneath */
  LY.bus=L.layerGroup();TR.bus.forEach(function(r){L.geoJSON(r.g,{style:{color:r.c,weight:2.5,opacity:.7,dashArray:'2 5'}}).bindTooltip('<b>'+esc(r.r)+'</b> bus<br>'+esc(r.n),{sticky:true,className:'tip'}).addTo(LY.bus)});
  LY.subway=L.layerGroup();TR.subway.features.forEach(function(f){L.geoJSON(f,{style:{color:f.properties.c,weight:4,opacity:.75},interactive:false}).addTo(LY.subway)});
  TR.stations.forEach(function(s){var bl=s.r.map(function(r){return '<b style="background:'+RC[r]+(/[NQR]/.test(r)?';color:#000':'')+'">'+r+'</b>'}).join('');
    L.marker(s.ll,{icon:L.divIcon({className:'',html:'<div class="stn'+(/Atlantic Av/.test(s.n)?' lf':'')+'"><div class="bl">'+bl+'</div><span class="sn">'+esc(s.n)+'</span></div>',iconSize:[0,0]})}).addTo(LY.subway)});
  LY.lirr=L.layerGroup();L.geoJSON(TR.lirr,{style:{color:'#111',weight:4,dashArray:'10 6'},interactive:false}).addTo(LY.lirr);
  L.geoJSON(TR.atl.geom,{style:{color:'#111',weight:1.5,fillColor:'#111',fillOpacity:.25},interactive:false}).addTo(LY.lirr);
  L.marker(TR.atl.ll,{icon:L.divIcon({className:'',html:'<div class="atl"><img src="/assets/map-icons/lirr.png" alt="Long Island Rail Road">Atlantic Terminal</div>',iconSize:[0,0]})}).addTo(LY.lirr);
  Object.keys(ON).forEach(function(k){if(ON[k])LY[k].addTo(map)});
  if(a[2])L.geoJSON(a[2],{style:{color:OR,weight:5,fill:false},interactive:false}).addTo(map);
  L.geoJSON(D.outline,{style:{color:NAVY,weight:3,fill:false},interactive:false}).addTo(map);
  /* the project, this one highlighted */
  var tb=null;
  var lots=L.geoJSON(D.lots,{style:function(f){var p=f.properties,me=(KIND==='built'&&p.id===TGT)||(KIND==='arena'&&p.kind==='arena')||(KIND==='p2'&&p.kind==='p2'&&((TGT==='Site 5'&&p.name==='Site 5')||(/^B(5|6|7)$/.test(TGT)&&/^Block 1120/.test(p.name))||(/^B(8|9|10)$/.test(TGT)&&/^Block 1121/.test(p.name))));
      if(me)return {color:OR,weight:4,fillColor:OR,fillOpacity:.45};
      if(p.kind==='built')return {color:'#fff',weight:1,fillColor:NAVY,fillOpacity:.55};
      if(p.kind==='arena')return {color:'#fff',weight:1,fillColor:'#6b7280',fillOpacity:.55};
      if(p.kind==='park')return {color:'#15803d',weight:1,fillColor:'#16a34a',fillOpacity:.4};
      return {color:TEAL,weight:2,dashArray:'6 4',fillColor:TEAL,fillOpacity:.12}},
    onEachFeature:function(f,l){var p=f.properties,id=p.kind==='built'?p.id:p.kind==='arena'?'Arena':p.name==='Site 5'?'Site 5':null;
      if(id){l.bindTooltip(esc(p.addr||p.name||'Barclays Center'),{sticky:true,className:'tip'});l.on('click',function(){go(id)})}
      var me=(KIND==='built'&&p.id===TGT)||(KIND==='arena'&&p.kind==='arena')||(KIND==='p2'&&TGT==='Site 5'&&p.name==='Site 5');if(me)tb=l.getBounds()}}).addTo(map);
  /* Barclays logo and Phase II tags */
  D.lots.features.forEach(function(f){if(f.properties.kind!=='arena')return;var c=L.geoJSON(f).getBounds().getCenter();
    L.marker([c.lat-.00005,c.lng+.0002],{icon:L.divIcon({className:'',html:'<div class="bclogo" title="Barclays Center"></div>',iconSize:[0,0]})}).on('click',function(){go('Arena')}).addTo(map)});
  D.phase2.forEach(function(t){var me=KIND==='p2'&&t.id===TGT,cls=(t.id==='B8'?'tag2 os':t.id==='B1'?'tag2 b1':'tag2'),sub=t.id==='B8'?'open space':t.id==='B1'?'plaza':t.h+' ft';
    var m=L.marker(t.ll,{zIndexOffset:me?1000:0,icon:L.divIcon({className:'',html:'<div class="tw"><div class="'+cls+'"'+(me?' style="background:'+OR+';transform:scale(1.25)"':'')+'>'+esc(t.id)+'<small>'+esc(sub)+'</small></div></div>',iconSize:[0,0]})});
    m.on('click',function(){go(t.id)});m.addTo(map);if(me&&!tb)tb=L.latLngBounds([t.ll,t.ll]).pad(0)});
  if(tb){if(tb.getNorthEast().equals(tb.getSouthWest()))map.setView(tb.getCenter(),17);else map.fitBounds(tb,{maxZoom:17,padding:[60,60]})}
  /* key */
  var k='<span><i style="background:rgba(244,121,32,.45);border:3px solid '+OR+'"></i>This '+(KIND==='p2'?'site':'building')+'</span><span><i style="background:transparent;border:3px solid '+NAVY+'"></i>Atlantic Yards</span><span><i style="background:'+NAVY+';opacity:.6"></i>Built</span><span><i style="background:rgba(14,116,144,.2);border:2px dashed '+TEAL+'"></i>Unbuilt</span><span><i style="background:transparent;border:3px solid '+OR+';border-radius:3px;opacity:.6"></i>BKCB6</span>';
  document.getElementById('key').innerHTML=k;
  /* every profile */
  var o=document.getElementById('others'),self=o.getAttribute('data-self');
  o.innerHTML='<a class="self" href="'+href('directory')+'">Directory &rarr;</a>'+IDX.map(function(x){return '<a class="'+(x.slug===self?'self':x.k==='p2'?'p':'b')+'" href="'+href(x.slug)+'">'+esc(x.t)+'</a>'}).join('');
});
document.addEventListener('click',function(e){var t=e.target.closest('.pill[data-l]');if(!t||!LY[t.getAttribute('data-l')])return;var k=t.getAttribute('data-l');ON[k]=!ON[k];t.classList.toggle('on',ON[k]);if(ON[k])LY[k].addTo(map);else map.removeLayer(LY[k])});
})();
