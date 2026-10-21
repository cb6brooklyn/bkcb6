/* BKCB6 voting map: early voting and Election Day sites, every election district, tap for the ballot.
   Everything it reads lives under /data/cb6vote/ and /data/cbhistory/ and /data/pollsites-history/, so it works offline in the apps. */
(function(){
  var root=document.getElementById('cb6vote');if(!root||!window.L)return;
  var B='/data/cb6vote/',EID='2026-11-03-general';
  var LOGO={'Park Slope Armory YMCA':[['YMCA','ymca']],'Prospect Park YMCA':[['YMCA','ymca']],'Dodge YMCA':[['YMCA','ymca']],'JHS 51':[['M.S. 51 William Alexander','ms51']],
    'John Jay HS':[['John Jay School for Law','johnjaylaw'],['Park Slope Collegiate','psc'],['Millennium Brooklyn HS','millennium'],['Cyberarts Studio Academy','cyberarts']],
    'Park Slope Public Library':[['Brooklyn Public Library','bpl']],'PS 142 JHS':[['The Brooklyn New School, P.S. 146','bns146'],['Brooklyn Collaborative Studies','bcs']],
    'PS 29':[['P.S. 29 John M. Harrigan','ps29']],'Joseph A Miccio Community Ctr':[['NYCHA','nycha']],'PS 15 New':[['P.S. 15 Patrick F. Daly','ps15']],
    'PS 27':[['Red Hook Neighborhood School','rhns'],['Summit Academy Charter School','summit']],
    'IS 293':[['Success Academy Cobble Hill','success'],['The Boerum Hill School for International Studies','bhs'],['Digital Arts and Cinema Technology High School','dact']],
    'PS 58':[['P.S. 58 The Carroll','ps58']],'Wyckoff Gardens Comm Ctr':[['NYCHA','nycha']],'PS 133':[['P.S. 133 William A. Butler','ps133']],'PS 282':[['P.S. 282 Park Slope','ps282']],
    'PS 321':[['P.S. 321 William Penn','ps321']],'Red Hook Recreation Center':[['NYC Parks','parks']],'Brooklyn Borough Hall':[['Brooklyn Borough President','bp']]};
  function lg(k){return B+'logos/'+k+'.png';}
  function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(m){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m];});}
  function j(u){return fetch(u).then(function(r){if(!r.ok)throw new Error(u);return r.json();});}
  var css=document.createElement('style');css.textContent=
   "#cb6vote{background:#fff;border-top:2px solid #f47920;border-bottom:2px solid #f47920;padding:14px 16px 16px}"+
   "#cb6vote .k{font:700 .62rem 'DM Mono',monospace;text-transform:uppercase;letter-spacing:.08em;color:#f47920}"+
   "#cb6vote h2{font:800 1.08rem 'DM Sans',sans-serif;color:#0d1b4b;margin:2px 0 3px;line-height:1.25}"+
   "#cb6vote .s{font:400 .8rem/1.5 'DM Sans',sans-serif;color:#6b6760}"+
   ".cvt{display:flex;gap:6px;overflow-x:auto;scrollbar-width:none;margin-top:9px;padding-bottom:2px}.cvt::-webkit-scrollbar{display:none}"+
   ".cvt button{flex:none;display:inline-flex;align-items:center;gap:6px;font:700 .76rem 'DM Sans',sans-serif;padding:7px 12px;border-radius:999px;border:1.5px solid #0d1b4b;background:#fff;color:#0d1b4b;cursor:pointer}"+
   ".cvt button.on{background:#0d1b4b;color:#fff}"+
   "#cb6voteMap{height:440px;border-radius:12px;border:1.5px solid #e5e2db;margin-top:8px;background:#b5d0e6}"+
   ".cv-lg{position:relative;display:flex;background:#fff;border-radius:999px;padding:2px;box-shadow:0 0 0 2px #0d1b4b,0 2px 6px rgba(13,27,75,.45)}.cv-lg.ev{box-shadow:0 0 0 3.5px #f47920,0 2px 7px rgba(13,27,75,.5)}"+
   ".cv-lg img{width:32px;height:32px;border-radius:50%;object-fit:contain;background:#fff;display:block}"+
   ".cv-n{position:absolute;right:-7px;top:-7px;background:#0d1b4b;color:#fff;font:800 9px 'DM Sans',sans-serif;border-radius:999px;padding:2px 4px;border:1.5px solid #fff}"+
   ".cv-tt img{width:18px;height:18px;object-fit:contain;vertical-align:middle;margin-right:4px}"+
   ".cv-hl{font:500 10px 'DM Mono',monospace;letter-spacing:.08em;text-transform:uppercase;color:#0d1b4b;white-space:nowrap;text-shadow:0 0 3px #f6f4ef,0 0 3px #f6f4ef,0 0 3px #f6f4ef;transform:translate(-50%,-50%)}"+
   ".cv-edl{font:800 10px 'DM Sans',sans-serif;color:#0d1b4b;transform:translate(-50%,-50%);text-shadow:0 0 3px #fff,0 0 3px #fff,0 0 3px #fff;pointer-events:none}"+
   "#cb6voteMap path:focus,#cb6voteMap .leaflet-interactive:focus{outline:none}"+
   ".cv-pw{position:absolute;left:0;top:0;width:0;height:0}"+
   ".cv-pin{position:absolute;left:-11px;top:-28px;width:22px;height:22px;border-radius:50% 50% 50% 0;background:#0d1b4b;border:3px solid #f47920;transform:rotate(-45deg);box-shadow:0 2px 6px rgba(13,27,75,.4)}"+
   ".cv-bal{position:absolute;bottom:34px;left:0;transform:translateX(-50%);display:flex;align-items:center;gap:8px;white-space:nowrap;background:#fff;border:2px solid #0d1b4b;border-radius:10px;padding:6px 10px 6px 7px;box-shadow:0 4px 12px rgba(13,27,75,.3);cursor:pointer;font-family:'DM Sans',sans-serif;text-align:left;animation:cvpop .35s cubic-bezier(.2,1.4,.4,1)}"+
   ".cv-bal:after{content:'';position:absolute;left:50%;bottom:-8px;margin-left:-7px;border:7px solid transparent;border-top-color:#0d1b4b;border-bottom:0}"+
   ".cv-bal{width:280px;justify-content:flex-start}.cv-bal>span{white-space:normal;flex:1;min-width:0}.cv-bal b{display:block;font-size:.82rem;color:#0d1b4b;font-weight:800}.cv-bal small{display:block;font-size:.68rem;color:#f47920;font-weight:700}"+
   ".cv-st{width:30px;height:30px;border-radius:50%;background:#fff url(/data/cb6vote/logos/voted.png) center/cover;box-shadow:0 0 0 2px #fff,0 0 0 3.5px #0d1b4b,0 2px 6px rgba(13,27,75,.45)}.cv-st.ev{width:34px;height:34px;box-shadow:0 0 0 3.5px #f47920,0 2px 7px rgba(13,27,75,.5)}"+
   ".cv-row{display:flex;align-items:center;gap:6px;flex:none}.cv-row .cv-st{width:30px;height:30px;box-shadow:none}.cv-at{font:900 1rem 'DM Sans',sans-serif;color:#f47920}"+
   ".cv-row img{width:30px;height:30px;border-radius:50%;object-fit:contain;background:#fff;border:1.5px solid #e5e2db}"+
   ".cv-site{position:absolute;bottom:26px;left:0;transform:translateX(-50%);width:max-content;max-width:270px;background:#fff;border:2px solid #0d1b4b;border-radius:10px;padding:8px 10px;box-shadow:0 4px 12px rgba(13,27,75,.3);font-family:'DM Sans',sans-serif;animation:cvpop .35s cubic-bezier(.2,1.4,.4,1);cursor:default}"+
   ".cv-site:after{content:'';position:absolute;left:50%;bottom:-8px;margin-left:-7px;border:7px solid transparent;border-top-color:#0d1b4b;border-bottom:0}"+
   ".cv-site .nm{font-weight:800;font-size:.86rem;color:#0d1b4b;margin-top:5px;white-space:normal}.cv-site .ad{font-size:.7rem;color:#6b6760;white-space:normal}.cv-site .rl{font-size:.68rem;color:#f47920;font-weight:800;margin-top:2px;white-space:normal}"+
   ".cv-site .tp{font-size:.72rem;color:#0d1b4b;font-weight:700;margin-top:6px}.cv-chips{display:flex;flex-wrap:wrap;gap:4px;margin-top:4px;max-height:96px;overflow:auto}"+
   ".cv-chips button{font:800 .68rem 'DM Sans',sans-serif;border:1.5px solid #0d1b4b;background:#fff;color:#0d1b4b;border-radius:999px;padding:3px 7px;cursor:pointer}.cv-x{position:absolute;right:4px;top:2px;border:0;background:none;font:800 1rem 'DM Sans',sans-serif;color:#6b6760;cursor:pointer}"+
   "@keyframes cvpop{from{transform:translateX(-50%) scale(.3);opacity:0}to{transform:translateX(-50%) scale(1);opacity:1}}";
  document.head.appendChild(css);
  root.innerHTML='<div class="k">Brooklyn Community Board 6</div><h2>Where BKCB6 votes</h2>'+
    '<div class="s">Every early voting site and Election Day poll site in BKCB6, and every election district. Tap a district, or anywhere on the map, to drop a pin, then tap the ballot for its poll sites, the early voting days and the full ballot.</div>'+
    '<div class="cvt" id="cvTg"><button type="button" class="on" data-l="ev"><span class="cv-st ev" style="width:18px;height:18px"></span>Early voting</button><button type="button" class="on" data-l="ed"><span class="cv-st" style="width:16px;height:16px"></span>Election Day poll sites</button><button type="button" class="on" data-l="eds">Election districts</button><button type="button" class="on" data-l="hood">Neighborhoods</button></div>'+
    '<div id="cb6voteMap"></div>';
  var G={ev:L.layerGroup(),ed:L.layerGroup(),hood:L.layerGroup(),eds:L.layerGroup()},lbl=L.layerGroup(),PS,FC,HD,CB,XW={},pinM=null,hiL=null;
  var map=L.map('cb6voteMap',{scrollWheelZoom:false,zoomSnap:.25,minZoom:13,maxZoom:18,maxBounds:[[40.63,-74.05],[40.715,-73.94]],maxBoundsViscosity:.8}).setView([40.676,-73.993],13.75);
  L.tileLayer(B+'tiles/{z}/{x}/{y}.png',{minZoom:13,maxZoom:18,maxNativeZoom:17,bounds:[[40.640,-74.035],[40.706,-73.952]],attribution:'&copy; OpenStreetMap contributors'}).addTo(map);
  ['hood','eds','ed','ev'].forEach(function(k){G[k].addTo(map);});
  map.on('zoomend',function(){var on=map.getZoom()>=14.5&&map.hasLayer(G.eds);if(on&&!map.hasLayer(lbl))lbl.addTo(map);if(!on&&map.hasLayer(lbl))map.removeLayer(lbl);});
  document.getElementById('cvTg').addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;var k=b.getAttribute('data-l'),on=!b.classList.contains('on');b.classList.toggle('on',on);if(on)G[k].addTo(map);else map.removeLayer(G[k]);map.fire('zoomend');});
  function ringIn(pt,r){var x=pt[0],y=pt[1],c=false;for(var i=0,k=r.length-1;i<r.length;k=i++){var xi=r[i][0],yi=r[i][1],xj=r[k][0],yj=r[k][1];if(((yi>y)!==(yj>y))&&(x<(xj-xi)*(y-yi)/(yj-yi)+xi))c=!c;}return c;}
  function polyIn(pt,g){var P=g.type==='Polygon'?[g.coordinates]:g.coordinates;return P.some(function(pp){return ringIn(pt,pp[0])&&!pp.slice(1).some(function(h){return ringIn(pt,h);});});}
  function edAt(ll){if(!FC)return null;var pt=[ll.lng,ll.lat];for(var i=0;i<FC.features.length;i++)if(polyIn(pt,FC.features[i].geometry))return FC.features[i].properties.e;return null;}
  function pole(f){var g=f.geometry,P=g.type==='Polygon'?[g.coordinates]:g.coordinates,best=null,ba=-1;P.forEach(function(pp){var r=pp[0],a=0,cx=0,cy=0;for(var i=0,k=r.length-1;i<r.length;k=i++){var t=r[k][0]*r[i][1]-r[i][0]*r[k][1];a+=t;cx+=(r[k][0]+r[i][0])*t;cy+=(r[k][1]+r[i][1])*t;}if(Math.abs(a)>ba){ba=Math.abs(a);best=[cy/(3*a),cx/(3*a)];}});
    if(best&&polyIn([best[1],best[0]],g))return best;return L.geoJSON(f).getBounds().getCenter();}
  var SVG='<svg width="26" height="32" viewBox="0 0 26 32" aria-hidden="true"><rect x="1" y="1" width="24" height="30" rx="2.5" fill="#fff" stroke="#0d1b4b" stroke-width="2"/><rect x="1" y="1" width="24" height="7" rx="2.5" fill="#0d1b4b"/><ellipse cx="6.5" cy="13.5" rx="2.6" ry="1.8" fill="#f47920"/><rect x="11" y="12.5" width="10" height="2" rx="1" fill="#0d1b4b"/><ellipse cx="6.5" cy="19.5" rx="2.6" ry="1.8" fill="none" stroke="#0d1b4b" stroke-width="1.3"/><rect x="11" y="18.5" width="10" height="2" rx="1" fill="#94a3b8"/><ellipse cx="6.5" cy="25.5" rx="2.6" ry="1.8" fill="none" stroke="#0d1b4b" stroke-width="1.3"/><rect x="11" y="24.5" width="8" height="2" rx="1" fill="#94a3b8"/></svg>';
  function open(key,ll){var x=XW[key]||[];if(!window.nov26Render)return;
    window.nov26Render({assemblyDistrict:key.slice(0,2),electionDistrict:key.slice(2),congressionalDistrict:x[1]||'',stateSenatorialDistrict:x[0]||'',cityCouncilDistrict:x[2]||'',communityDistrict:'',firstBoroughName:(x[4]||'Brooklyn').toUpperCase(),latitude:String(ll.lat),longitude:String(ll.lng)});
    var o=document.getElementById('out');if(o)o.scrollIntoView({behavior:'smooth',block:'start'});}
  var EDS={},EVS={};
  function logos(i){var st=PS.sites[+i];return LOGO[st.n]||[];}
  function row(i,max){var lo=logos(i).slice(0,max||1);return '<span class="cv-row"><span class="cv-st'+''+'"></span>'+(lo.length?'<span class="cv-at">@</span>'+lo.map(function(x){return '<img src="'+lg(x[1])+'" alt="'+esc(x[0])+'">';}).join(''):'')+'</span>';}
  function clear(){if(pinM){map.removeLayer(pinM);pinM=null;}if(hiL){map.removeLayer(hiL);hiL=null;}}
  function drop(ll,key){key=key||edAt(ll);clear();
    var si=key?EDS[key]:null,st=si!=null?PS.sites[+si]:null;
    var lab=key?'ED '+(+key.slice(2))+' · AD '+(+key.slice(0,2))+(st?'</small><small style="color:#6b6760">Election Day at '+esc(st.n):''):'Outside the BKCB6 election districts';
    var head=si!=null?row(si,1):'<span class="cv-row"><span class="cv-st"></span></span>';
    pinM=L.marker(ll,{icon:L.divIcon({className:'',html:'<div class="cv-pw"><button type="button" class="cv-bal">'+head+'<span><b>'+(key?'Tap to see your ballot':'No ballot here')+'</b><small>'+lab+'</small></span></button><div class="cv-pin"></div></div>',iconSize:[0,0],iconAnchor:[0,0]}),zIndexOffset:2000}).addTo(map);
    try{map.panInside(ll,{paddingTopLeft:[150,110],paddingBottomRight:[150,20]});}catch(e){}
    if(key){var f=FC.features.filter(function(x){return x.properties.e===key;})[0];if(f)hiL=L.geoJSON(f,{interactive:false,style:{color:'#0d1b4b',weight:3,fillColor:'#f47920',fillOpacity:.35}}).addTo(map);pinM.on('click',function(){open(key,ll);});}}
  function siteTap(i,r){clear();var st=PS.sites[+i],ll=L.latLng(st.ll[0],st.ll[1]),lo=logos(i);
    var keys=(r.ed||r.ev).slice().sort(),multiAD={};keys.forEach(function(k){multiAD[k.slice(0,2)]=1;});var showAD=Object.keys(multiAD).length>1;
    var role=(r.ev?'Early voting site, October 24 to November 1':'')+(r.ev&&r.ed?' · ':'')+(r.ed?'Election Day poll site, November 3, 6 AM to 9 PM':'');
    var html='<div class="cv-pw"><div class="cv-site"><button type="button" class="cv-x" data-x="1" aria-label="Close">&times;</button>'+row(i,4)+'<div class="nm">'+esc(st.n)+(lo.length>1?' <span style="font-weight:600;color:#6b6760">('+esc(lo.map(function(x){return x[0];}).join(', '))+')</span>':'')+'</div><div class="ad">'+esc(st.a)+'</div><div class="rl">'+esc(role)+'</div>'+
      '<div class="tp">Tap your election district to see your ballot'+(r.ed?'':' (these vote early here)')+'</div><div class="cv-chips">'+keys.map(function(k){return '<button type="button" data-k="'+k+'">ED '+(+k.slice(2))+(showAD?' <span style="font-weight:600">AD '+(+k.slice(0,2))+'</span>':'')+'</button>';}).join('')+'</div></div></div>';
    pinM=L.marker(ll,{icon:L.divIcon({className:'',html:html,iconSize:[0,0],iconAnchor:[0,0]}),zIndexOffset:2000}).addTo(map);
    try{map.panInside(ll,{paddingTopLeft:[150,230],paddingBottomRight:[150,20]});}catch(e){}
    pinM.on('click',function(e){var t=e.originalEvent&&e.originalEvent.target,b=t&&t.closest?t.closest('button'):null;if(!b)return;if(b.getAttribute('data-x')){clear();return;}var k=b.getAttribute('data-k');if(!k)return;
      var f=FC.features.filter(function(x){return x.properties.e===k;})[0],p=f?L.latLng(pole(f)):ll;drop(p,k);open(k,p);});}
  map.on('click',function(e){drop(e.latlng,null);});
  function edList(ks){var by={};ks.forEach(function(k){(by[k.slice(0,2)]=by[k.slice(0,2)]||[]).push(+k.slice(2));});return Object.keys(by).map(function(a){return 'AD '+a+': ED '+by[a].sort(function(x,y){return x-y;}).join(', ');}).join('; ');}
  function draw(){
    if(HD)Object.keys(HD).forEach(function(n){var pg=L.polygon(HD[n].map(function(r){return r.map(function(c){return [c[1],c[0]];});}),{interactive:false,color:'#0d1b4b',weight:1.5,opacity:.55,dashArray:'4 4',fill:false}).addTo(G.hood);
      L.marker(pg.getBounds().getCenter(),{interactive:false,icon:L.divIcon({className:'',html:'<div class="cv-hl">'+esc(n.replace(' Waterfront District',''))+'</div>',iconSize:[0,0]})}).addTo(G.hood);});
    if(FC){var ST={color:'#0d1b4b',weight:1,opacity:.6,fillColor:'#f47920',fillOpacity:0};
      L.geoJSON(FC,{style:ST,onEachFeature:function(f,l){var k=f.properties.e;
        l.bindTooltip('<b>Election District '+(+k.slice(2))+'</b><br>Assembly District '+(+k.slice(0,2)),{sticky:true,direction:'top',offset:[0,-8]});
        l.on('mouseover',function(){l.setStyle({weight:3,opacity:1,fillOpacity:.22});l.bringToFront();});l.on('mouseout',function(){l.setStyle(ST);});
        l.on('click',function(e){L.DomEvent.stopPropagation(e);l.closeTooltip();l.setStyle(ST);drop(e.latlng,k);});}}).addTo(G.eds);
      FC.features.forEach(function(f){lbl.addLayer(L.marker(pole(f),{interactive:false,icon:L.divIcon({className:'',html:'<div class="cv-edl">'+(+f.properties.e.slice(2))+'</div>',iconSize:[0,0]})}));});}
    if(CB){var o=L.geoJSON(CB,{interactive:false,style:{color:'#f47920',weight:3.5,opacity:1,fill:false}}).addTo(map);map.fitBounds(o.getBounds(),{padding:[8,8]});}
    if(PS){var all={};PS.elections.forEach(function(e){if(e.id!==EID)return;Object.keys(e.sites).forEach(function(i){var r=(all[i]=all[i]||{}),k=e.kind==='ev'?'ev':'ed';r[k]=(r[k]||[]).concat(e.sites[i]);e.sites[i].forEach(function(q){(k==='ev'?EVS:EDS)[q]=i;});});});
      Object.keys(all).forEach(function(i){var st=PS.sites[+i],r=all[i];if(!st.ll)return;var lo=LOGO[st.n]||[['','voted']],isEv=!!r.ev;
        var html='<div class="cv-st'+(isEv?' ev':'')+'"></div>';
        var tt='<div class="cv-tt"><b>'+esc(st.n)+'</b><br>'+esc(st.a)+(lo[0][0]?'<br>'+lo.map(function(x){return '<img src="'+lg(x[1])+'" alt="">'+esc(x[0]);}).join('<br>'):'')+(r.ev?'<br><b>Early voting site</b> for '+esc(edList(r.ev)):'')+(r.ed?'<br><b>Election Day poll site</b> for '+esc(edList(r.ed)):'')+'</div>';
        var sz=isEv?34:30;L.marker(st.ll,{icon:L.divIcon({className:'',html:html,iconSize:[sz,sz],iconAnchor:[sz/2,sz/2]}),zIndexOffset:isEv?900:800}).on('click',function(e){L.DomEvent.stopPropagation(e);siteTap(i,r);}).addTo(G[isEv?'ev':'ed']);});}
    map.fire('zoomend');}
  Promise.all([j('/data/pollsites-history/cb6.json').catch(function(){return null;}),j(B+'eds.json').catch(function(){return null;}),j(B+'hoods.json').catch(function(){return null;}),j(B+'boundary.geojson').catch(function(){return null;}),j(B+'xw.json').catch(function(){return {};})])
    .then(function(a){PS=a[0];FC=a[1];HD=a[2];CB=a[3];XW=a[4]||{};draw();});
})();
