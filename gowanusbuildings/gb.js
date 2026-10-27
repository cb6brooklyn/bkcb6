(function(){
var NAVY='#0d1b4b',OR='#f47920',TEAL='#0e7490',COL={open:NAVY,building:OR,filed:TEAL},LAB={open:'Open',building:'Permitted, not yet open',filed:'Filed, not yet permitted'};
var PL={groups:'Community group',biz:'Local business',fac:'School, park or facility',nycha:'NYCHA'};
var el=document.getElementById('map'),SELF=el.getAttribute('data-slug'),INDEX=!!el.getAttribute('data-index');
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function fmt(n){return Number(n||0).toLocaleString('en-US')}
var app=/[?&]app=1\b/.test(location.search)||(function(){try{return sessionStorage.getItem('bkapp')==='1'}catch(e){return false}})();
function href(s){return '/gowanusbuildings/'+(s?s+'/':'')+(app?'?app=1':'')}
function orgHref(p){return '/app/orgs.html?only=1&group='+encodeURIComponent(p.grp)+'&org='+encodeURIComponent(p.slug)}
var map=L.map('map',{zoomControl:false,scrollWheelZoom:false}).setView([40.676,-73.988],15);
L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png?key=cb1_2hyw_1_9cda1572a3817275ed412c0e',{subdomains:'abcd',maxZoom:20,attribution:'&copy; OpenStreetMap &copy; CARTO'}).addTo(map);
L.control.zoom({position:'topright'}).addTo(map);
map.on('click',function(){map.scrollWheelZoom.enable()});
var RC={'2':'#EE352E','3':'#EE352E','4':'#00933C','5':'#00933C','B':'#FF6319','D':'#FF6319','F':'#FF6319','M':'#FF6319','N':'#FCCC0A','Q':'#FCCC0A','R':'#FCCC0A','W':'#FCCC0A','A':'#0039A6','C':'#0039A6','E':'#0039A6','G':'#6CBE45'};
var LY={},ON={open:true,building:true,filed:true,groups:true,nycha:true,biz:false,fac:false,subway:true,bus:false};
if(SELF){ON.biz=false;ON.fac=false;ON.bus=false}
var F=null,AR=null,LBL=L.layerGroup().addTo(map);
function card(p){return '<div class="rc">'+(p.logo?'<img src="'+p.logo+'" alt="" style="width:80px;border-radius:10px">':'')+'<div class="rct">'+esc(p.nm||p.t)+'</div>'+(p.nm?'<div class="rcs">'+esc(p.t)+'</div>':'')+'<div class="rcs">'+esc(p.st)+' &middot; '+fmt(p.u)+' apartments'+(p.a?' &middot; '+fmt(p.a)+' affordable':'')+'</div><div class="rcd">'+p.d+'</div>'+(p.web?'<a class="plink" href="'+p.web+'" target="_blank" rel="noopener">'+esc(p.web.replace(/^https?:\/\/(www\.)?/,''))+' &#8599;</a>':'')+'<table class="rcz">'+p.z.map(function(r){return '<tr><td>'+r[0]+'</td><td>'+r[1]+'</td></tr>'}).join('')+'</table><a class="plink" href="'+href(p.slug)+'">Open the full profile &rarr;</a></div>'}
function show(h){var r=document.getElementById('res');if(r){r.className='result on';r.innerHTML=h}}
var POP=null;
function pop(p){if(POP)map.removeLayer(POP);
  var inner=p.logo?'<div class="pi"><img src="'+p.logo+'" alt=""></div>':'<div class="pt">'+esc(p.nm||p.t)+'<small>'+esc(p.st)+' &middot; '+fmt(p.u)+' apartments</small></div>';
  POP=L.marker(p.pt,{zIndexOffset:2000,icon:L.divIcon({className:'',html:'<div class="pop">'+inner+'</div>',iconSize:[0,0]})}).on('click',function(){location.href=href(p.slug)}).addTo(map)}
function drawLabels(){LBL.clearLayers();if(!F)return;var z=map.getZoom();
  if(z>=17)F.features.forEach(function(f){var p=f.properties;if(!ON[p.k])return;L.marker(p.pt,{icon:L.divIcon({className:'',html:'<div class="gl">'+esc(p.t)+'</div>',iconSize:[0,0]}),interactive:false}).addTo(LBL)});
  if(z>=15&&z<=17)L.marker([40.6765,-73.9905],{icon:L.divIcon({className:'',html:'<div class="canal">Gowanus Canal</div>',iconSize:[0,0]}),interactive:false}).addTo(LBL)}
function drawPlaces(){if(!AR)return;['groups','nycha','biz','fac'].forEach(function(g){var l=LY[g];if(!l)return;l.clearLayers();var z=map.getZoom();
  if(g!=='nycha'&&z<16)return;
  AR.places.forEach(function(p){if(p.g!==g)return;
    var m=L.marker(p.ll,{icon:L.divIcon({className:'',html:'<div class="lg '+g+'" style="background-image:url(\''+p.logo+'\')"></div>',iconSize:[0,0]})});
    var tip='<b>'+esc(p.n)+'</b><br>'+PL[g]+(p.addr?', '+esc(p.addr):'');m.bindTooltip(tip,{className:'tip'});
    m.on('click',function(){if(p.slug){if(INDEX)show('<div class="rc"><div class="rct">'+esc(p.n)+'</div><div class="rcs">'+PL[g]+'</div><div class="rcd">'+esc(p.addr)+'</div><a class="plink" href="'+orgHref(p)+'">Open the profile &rarr;</a></div>');else location.href=orgHref(p)}else show(tip)});
    m.addTo(l)})})}
function drawTransit(){if(!AR)return;var z=map.getZoom();
  if(LY.subway){LY.subway.clearLayers();AR.subway.features.forEach(function(f){L.geoJSON(f,{style:{color:f.properties.c,weight:4,opacity:.7},interactive:false}).addTo(LY.subway)});
    AR.stations.forEach(function(s){var bl=s.r.map(function(r){return '<b style="background:'+(RC[r]||'#666')+(/[NQRW]/.test(r)?';color:#000':'')+'">'+r+'</b>'}).join('');
      L.marker(s.ll,{icon:L.divIcon({className:'',html:'<div class="stn"><div class="bl">'+bl+'</div>'+(z>=15?'<span class="sn">'+esc(s.n)+'</span>':'')+'</div>',iconSize:[0,0]})}).bindTooltip('<b>'+esc(s.n)+'</b><br>'+s.r.join(' ')+' trains',{className:'tip'}).addTo(LY.subway)})}
  if(LY.bus){LY.bus.clearLayers();AR.bus.forEach(function(r){L.geoJSON(r.g,{style:{color:r.c,weight:2.5,opacity:.7,dashArray:'2 5'}}).bindTooltip('<b>'+esc(r.r)+'</b> bus<br>'+esc(r.n),{sticky:true,className:'tip'}).addTo(LY.bus)})}}
map.on('zoomend',function(){drawLabels();drawPlaces();drawTransit()});
function setOn(k,on){ON[k]=on;var b=document.querySelector('.pill[data-l="'+k+'"]');if(b)b.classList.toggle('on',on);if(!LY[k])return;if(on)LY[k].addTo(map);else map.removeLayer(LY[k]);drawLabels();renderKey()}
document.addEventListener('click',function(e){var t=e.target.closest('.pill[data-l]');if(!t)return;var k=t.getAttribute('data-l');setOn(k,!ON[k])});
function renderKey(){var k='';if(SELF)k+='<span><i style="background:rgba(244,121,32,.7);border:3px solid #c2410c"></i>This building</span>';
  ['open','building','filed'].forEach(function(x){if(ON[x])k+='<span><i style="background:'+COL[x]+'"></i>'+LAB[x]+'</span>'});
  k+='<span><i style="background:rgba(124,58,237,.08);border:2px dashed #7c3aed"></i>Gowanus rezoning</span><span><i style="background:transparent;border:3px solid '+OR+';opacity:.7"></i>BKCB6</span>';
  if(ON.groups)k+='<span><i style="background:#fff;border:2px solid #16a34a"></i>Community group, its logo</span>';
  if(ON.nycha)k+='<span><img src="/assets/map-icons/nycha.png" alt="" style="width:16px;height:16px">NYCHA</span>';
  if(ON.subway)k+='<span><i style="height:5px;width:20px;border-radius:2px;background:linear-gradient(90deg,#FF6319,#6CBE45,#FCCC0A,#EE352E)"></i>Subway</span>';
  if(ON.bus)k+='<span><i style="height:4px;width:20px;border-radius:2px;background:repeating-linear-gradient(90deg,#006CB7 0 3px,transparent 3px 7px)"></i>Bus</span>';
  document.getElementById('key').innerHTML=k}
Promise.all([fetch('/gowanusbuildings/buildings.json').then(function(r){return r.json()}),fetch('/gowanusbuildings/boundary.json').then(function(r){return r.json()}),fetch('/data/cb6_boundary.geojson').then(function(r){return r.json()}).catch(function(){return null}),fetch('/gowanusbuildings/around.json').then(function(r){return r.json()}).catch(function(){return null})]).then(function(a){
  F=a[0];AR=a[3];
  L.geoJSON(a[1],{style:{color:'#7c3aed',weight:3,dashArray:'7 5',fillColor:'#7c3aed',fillOpacity:.05},interactive:false}).addTo(map);
  if(a[2])L.geoJSON(a[2],{style:{color:OR,weight:5,fill:false,opacity:.7},interactive:false}).addTo(map);
  LY.bus=L.layerGroup();LY.subway=L.layerGroup();
  ['filed','building','open'].forEach(function(k){
    LY[k]=L.geoJSON({type:'FeatureCollection',features:F.features.filter(function(f){return f.properties.k===k})},{
      style:function(f){var me=f.properties.slug===SELF;return {color:me?'#c2410c':'#fff',weight:me?4:1.5,fillColor:me?OR:COL[k],fillOpacity:SELF?(me?.7:.35):.8}},
      pointToLayer:function(f,ll){return L.circleMarker(ll,{radius:7,color:'#fff',weight:2,fillColor:COL[k],fillOpacity:.9})},
      onEachFeature:function(f,l){var p=f.properties;l.bindTooltip('<b>'+esc(p.t)+'</b><br>'+esc(p.st)+', '+fmt(p.u)+' apartments'+(p.a?', '+fmt(p.a)+' affordable':''),{sticky:true,className:'tip'});l.on('click',function(){pop(p);if(INDEX)show(card(p));else if(p.slug!==SELF)setTimeout(function(){location.href=href(p.slug)},600)})}
    })});
  ['groups','nycha','biz','fac'].forEach(function(g){LY[g]=L.layerGroup()});
  drawTransit();drawPlaces();
  ['bus','subway','filed','building','open','fac','biz','nycha','groups'].forEach(function(k){if(ON[k]&&LY[k])LY[k].addTo(map)});
  if(SELF){var me=F.features.filter(function(f){return f.properties.slug===SELF})[0];if(me){map.fitBounds(L.geoJSON(me).getBounds(),{maxZoom:17,padding:[90,60]});pop(me.properties)}}
  else map.fitBounds(L.geoJSON(a[1]).getBounds(),{padding:[10,10]});
  drawLabels();renderKey();
  var chips='<a class="dir" href="'+href('directory')+'">Directory: every new building &rarr;</a>'+F.features.map(function(f){var p=f.properties;return '<a class="'+(p.slug===SELF?'dir':p.k)+'" href="'+href(p.slug)+'">'+esc(p.t)+'</a>'}).join('');
  var o=document.getElementById('profs')||document.getElementById('others');if(o){o.className='profs';o.innerHTML=chips}
});
})();
