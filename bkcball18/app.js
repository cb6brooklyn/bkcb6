
function fold(btn){btn.parentElement.classList.toggle('open')}
function tabTo(id){document.querySelectorAll('section.tab').forEach(s=>s.classList.toggle('on',s.id==='tab-'+id));document.querySelectorAll('nav.tabs a').forEach(a=>a.classList.toggle('on',a.dataset.tab===id));
  var s=document.getElementById('tab-'+id); if(s){s.querySelectorAll('iframe[data-src]').forEach(f=>{f.src=f.dataset.src;f.removeAttribute('data-src')}); if(s.dataset.map&&!s.dataset.mapped){s.dataset.mapped=1; window['init_'+s.dataset.map]&&window['init_'+s.dataset.map]()}}
  if(location.hash!=='#'+id) history.replaceState(null,'','#'+id); window.scrollTo(0,0)}
function startTabs(def){var h=(location.hash||'').slice(1); tabTo(document.getElementById('tab-'+h)?h:def); document.querySelectorAll('nav.tabs a').forEach(a=>a.onclick=function(e){e.preventDefault();tabTo(a.dataset.tab)})}
function ll(r){return r.map(p=>[p[1],p[0]])}
function polyLayer(rings,opt){return L.polygon(rings.map(ll),opt)}
function iconMarker(latlng,img,label,href){var m=L.marker(latlng,{icon:L.divIcon({className:'',html:'<div class="mkwrap"><img src="'+img+'" onerror="this.style.display=\'none\'"><div class="lbl">'+label+'</div></div>',iconAnchor:[0,15]})}); if(href) m.on('click',()=>location.href=href); return m}
var dataCache={};function getJSON(u){return dataCache[u]||(dataCache[u]=fetch(u).then(r=>r.json()))}
// A district map with toggles: own outline, boards, the four legislatures, subway, Citi Bike, NYC Ferry.
function districtMap(el, cfg){
  var map=L.map(el,{scrollWheelZoom:false,attributionControl:true}); L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png?key=cb1_2hyw_1_9cda1572a3817275ed412c0e',{attribution:'© CARTO © OpenStreetMap',subdomains:'abcd',maxZoom:19}).addTo(map); map.setView([40.65,-73.95],11);
  var groups={}, on={boards:true}, fit=null, own=null;
  Promise.all([getJSON(cfg.base+'data/district-shapes.json'),getJSON(cfg.base+'data/board-shapes.json')]).then(function(r){cfg.shapes=r[0];cfg.boardShapes=r[1];
    if(cfg.ownKey&&cfg.shapes[cfg.ownKey]){own=polyLayer(cfg.shapes[cfg.ownKey],{color:cfg.color||'#f47920',weight:3.5,fill:false}).addTo(map); fit=own.getBounds()}
    else if(cfg.ownCD&&cfg.boardShapes[cfg.ownCD]){own=polyLayer(cfg.boardShapes[cfg.ownCD],{color:cfg.color||'#f47920',weight:3.5,fill:false}).addTo(map); fit=own.getBounds()}
    if(fit) map.fitBounds(fit.pad(.08)); draw();
    var tg=el.parentElement.querySelector('.toggles'); if(tg) tg.querySelectorAll('.tg').forEach(b=>{b.classList.toggle('on',!!on[b.dataset.k]); b.onclick=()=>{on[b.dataset.k]=!on[b.dataset.k]; b.classList.toggle('on',!!on[b.dataset.k]); draw()}});
  });
  function draw(){Object.keys(groups).forEach(k=>{map.removeLayer(groups[k])}); groups={};
    var cds=cfg.cds||[];
    if(on.boards){var g=L.layerGroup(); cds.forEach(cd=>{var r=cfg.boardShapes[cd]; if(!r) return; var p=polyLayer(r,{color:'#0d1b4b',weight:1.5,fill:false,opacity:.6}).addTo(g); var c=p.getBounds().getCenter(); iconMarker(c, cd==='306'?cfg.base+'img/CB6_540.png':cfg.base+'img/cb'+cd+'.png', cfg.boardShort(cd), cfg.base+'board/'+cd+'.html').addTo(g)}); groups.boards=g.addTo(map); if(!fit&&g.getLayers().length){fit=L.featureGroup(g.getLayers().filter(x=>x.getBounds)).getBounds()}}
    ['council','assembly','senate','congress'].forEach(k=>{if(!on[k]) return; var g=L.layerGroup(); (cfg.districts[k]||[]).forEach(d=>{var r=cfg.shapes[k+'-'+d.n]; if(!r) return; polyLayer(r,{color:cfg.levelColor[k],weight:2.5,fill:true,fillOpacity:.05,dashArray:'8 5'}).addTo(g); var c=L.polygon(r.map(ll)).getBounds().getCenter(); iconMarker(c,cfg.base+'img/o/'+d.slug+'.png',d.label,cfg.base+'official/'+d.slug+'.html').addTo(g)}); groups[k]=g.addTo(map)});
    if(on.subway){var g=L.layerGroup(); getJSON(cfg.base+'data/subway-routes.json').then(rs=>{rs.forEach(r=>{(r.l||[]).forEach(seg=>{var pl=L.polyline(ll(seg),{color:r.p.color||'#333',weight:4,opacity:.9}); if(fit&&pl.getBounds().intersects(fit.pad(.15))) pl.addTo(g)})})}); groups.subway=g.addTo(map)}
    if(on.citibike){var g=L.layerGroup(); getJSON(cfg.base+'data/citibike.json').then(ds=>{var b=fit?fit.pad(.1):null; ds.forEach(d=>{var p=L.latLng(d[0],d[1]); if(b&&!b.contains(p)) return; L.marker(p,{icon:L.divIcon({className:'',html:'<img class="mk" style="width:18px;height:18px" src="'+cfg.base+'img/citibike.png">',iconAnchor:[9,9]})}).bindPopup('<b>'+d[3]+'</b><br>Citi Bike · '+d[2]+' docks').addTo(g)})}); groups.citibike=g.addTo(map)}
    if(on.ferry){var g=L.layerGroup(); getJSON(cfg.base+'data/ferry.json').then(f=>{f.routes.filter(r=>r.kind==='ferry').forEach(r=>r.lines.forEach(seg=>L.polyline(seg,{color:r.color,weight:3,opacity:.9}).addTo(g))); f.stops.forEach(s=>L.marker([s.lat,s.lng],{icon:L.divIcon({className:'',html:'<img class="mk" style="width:26px;height:26px;border-radius:50%" src="'+cfg.base+'img/ferry.png">',iconAnchor:[13,13]})}).bindPopup('<b>'+s.name+'</b><br>NYC Ferry · '+s.routes.join(', ')).addTo(g))}); groups.ferry=g.addTo(map)}
    if(own) setTimeout(function(){try{own.bringToFront()}catch(e){}},50);
  }
  return map;
}
