(function(){
var NAVY='#0d1b4b',OR='#f47920',TEAL='#0e7490',COL={open:NAVY,building:OR,filed:TEAL},LAB={open:'Open',building:'Permitted, not yet open',filed:'Filed, not yet permitted'};
var el=document.getElementById('map'),SELF=el.getAttribute('data-slug'),INDEX=!!el.getAttribute('data-index');
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function fmt(n){return Number(n||0).toLocaleString('en-US')}
var app=/[?&]app=1\b/.test(location.search)||(function(){try{return sessionStorage.getItem('bkapp')==='1'}catch(e){return false}})();
function href(s){return '/gowanusbuildings/'+s+'/'+(app?'?app=1':'')}
var map=L.map('map',{zoomControl:false,scrollWheelZoom:false}).setView([40.676,-73.988],15);
L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png?key=cb1_2hyw_1_9cda1572a3817275ed412c0e',{subdomains:'abcd',maxZoom:20,attribution:'&copy; OpenStreetMap &copy; CARTO'}).addTo(map);
L.control.zoom({position:'topright'}).addTo(map);
map.on('click',function(){map.scrollWheelZoom.enable()});
var LY={},ON={open:true,building:true,filed:true},F=null,LBL=L.layerGroup().addTo(map);
function card(p){return '<div class="rc"><div class="rct">'+esc(p.t)+'</div><div class="rcs">'+esc(p.st)+' &middot; '+fmt(p.u)+' apartments'+(p.a?' &middot; '+fmt(p.a)+' affordable':'')+'</div><div class="rcd">'+p.d+'</div><table class="rcz">'+p.z.map(function(r){return '<tr><td>'+r[0]+'</td><td>'+r[1]+'</td></tr>'}).join('')+'</table><a class="plink" href="'+href(p.slug)+'">Open the full profile &rarr;</a></div>'}
function show(p){var r=document.getElementById('res');if(r){r.className='result on';r.innerHTML=card(p)}else location.href=href(p.slug)}
function labels(){LBL.clearLayers();if(map.getZoom()<17||!F)return;F.features.forEach(function(f){var p=f.properties;if(!ON[p.k])return;L.marker(p.pt,{icon:L.divIcon({className:'',html:'<div class="gl">'+esc(p.t)+'</div>',iconSize:[0,0]}),interactive:false}).addTo(LBL)})}
map.on('zoomend',labels);
Promise.all([fetch('/gowanusbuildings/buildings.json').then(function(r){return r.json()}),fetch('/gowanusbuildings/boundary.json').then(function(r){return r.json()}),fetch('/data/cb6_boundary.geojson').then(function(r){return r.json()}).catch(function(){return null})]).then(function(a){
  F=a[0];
  L.geoJSON(a[1],{style:{color:'#7c3aed',weight:3,dashArray:'7 5',fillColor:'#7c3aed',fillOpacity:.05},interactive:false}).addTo(map);
  if(a[2])L.geoJSON(a[2],{style:{color:OR,weight:5,fill:false,opacity:.7},interactive:false}).addTo(map);
  ['filed','building','open'].forEach(function(k){
    LY[k]=L.geoJSON({type:'FeatureCollection',features:F.features.filter(function(f){return f.properties.k===k})},{
      style:function(f){var me=f.properties.slug===SELF;return {color:me?'#c2410c':'#fff',weight:me?4:1.5,fillColor:me?OR:COL[k],fillOpacity:SELF?(me?.7:.35):.8}},
      pointToLayer:function(f,ll){return L.circleMarker(ll,{radius:7,color:'#fff',weight:2,fillColor:COL[k],fillOpacity:.9})},
      onEachFeature:function(f,l){var p=f.properties;l.bindTooltip('<b>'+esc(p.t)+'</b><br>'+esc(p.st)+', '+fmt(p.u)+' apartments'+(p.a?', '+fmt(p.a)+' affordable':''),{sticky:true,className:'tip'});l.on('click',function(){if(INDEX)show(p);else location.href=href(p.slug)})}
    }).addTo(map)});
  if(SELF){var me=F.features.filter(function(f){return f.properties.slug===SELF})[0];if(me){var b=L.geoJSON(me).getBounds();map.fitBounds(b,{maxZoom:17,padding:[60,60]})}}
  else map.fitBounds(L.geoJSON(a[1]).getBounds(),{padding:[10,10]});
  labels();
  var k='';if(SELF)k+='<span><i style="background:rgba(244,121,32,.7);border:3px solid #c2410c"></i>This building</span>';
  ['open','building','filed'].forEach(function(x){k+='<span><i style="background:'+COL[x]+'"></i>'+LAB[x]+'</span>'});
  k+='<span><i style="background:rgba(124,58,237,.08);border:2px dashed #7c3aed"></i>Gowanus rezoning</span><span><i style="background:transparent;border:3px solid '+OR+';opacity:.7"></i>BKCB6</span>';
  document.getElementById('key').innerHTML=k;
  var o=document.getElementById('others');
  if(o)o.innerHTML='<a class="self" href="'+href('').replace(/\/\/?(\?app=1)?$/,'/$1')+'">All new buildings &rarr;</a>'+F.features.map(function(f){var p=f.properties;return '<a class="'+(p.slug===SELF?'self':p.k)+'" href="'+href(p.slug)+'">'+esc(p.t)+'</a>'}).join('');
});
document.addEventListener('click',function(e){var t=e.target.closest('.pill[data-l]');if(!t||!LY[t.getAttribute('data-l')])return;var k=t.getAttribute('data-l');ON[k]=!ON[k];t.classList.toggle('on',ON[k]);if(ON[k])LY[k].addTo(map);else map.removeLayer(LY[k]);labels()});
})();
