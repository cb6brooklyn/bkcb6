/* Where Brooklyn votes, where New York City votes: the BKCB6 voting map's model for the borough and the city.
   Early voting and Election Day sites for every election district, the districts drawn as you zoom in, tap for the ballot.
   Reads /data/vote/sites.json, /data/eds/adNN.geojson, /data/assembly-districts.geojson, /data/boro-simple.geojson,
   /data/cd-boundaries-lite.geojson and /app/data/civic/ed-crosswalk.json. Street tiles come from OpenStreetMap. */
(function(){
  if(!window.L)return;
  var SCOPES={
    bk:{id:'bkvote',k:'Brooklyn',h:'Where Brooklyn votes',boro:'K',boroName:'Brooklyn',s:'Search an address, or tap the map to drop a pin. Every early voting site and Election Day poll site in Brooklyn; zoom in for the election districts. The pin opens where you vote, the early voting days and your ballot.',
        view:[[40.566,-74.045],[40.74,-73.83]],minZoom:11,pad:.08},
    nyc:{id:'nycvote',k:'New York City',h:'Where New York City votes',boro:null,boroName:'New York City',s:'Search an address, or tap the map to drop a pin. Every early voting site and Election Day poll site in the five boroughs; zoom in for the election districts. The pin opens where you vote, the early voting days and your ballot.',
        view:[[40.49,-74.27],[40.92,-73.68]],minZoom:10,pad:.1}};
  var roots=Object.keys(SCOPES).filter(function(s){return document.getElementById(SCOPES[s].id);});
  if(!roots.length)return;
  function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(m){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m];});}
  function j(u){return fetch(u).then(function(r){if(!r.ok)throw new Error(u);return r.json();});}
  var css=document.createElement('style');css.textContent=
   ".vm{background:#fff;border-bottom:2px solid #f47920;padding:14px 16px 16px}"+
   ".vm .k{font:700 .62rem 'DM Mono',monospace;text-transform:uppercase;letter-spacing:.08em;color:#f47920}"+
   ".vm h2{font:800 1.08rem 'DM Sans',sans-serif;color:#0d1b4b;margin:2px 0 3px;line-height:1.25}"+
   ".vm .s{font:400 .8rem/1.5 'DM Sans',sans-serif;color:#6b6760}"+
   ".vm .vm-map{height:440px;border-radius:12px;border:1.5px solid #e5e2db;margin-top:8px;background:#b5d0e6}"+
   ".vm .vm-sb{position:relative;margin:10px 0 0}.vm .vm-sb label{display:block;font:700 .62rem 'DM Mono',monospace;text-transform:uppercase;letter-spacing:.08em;color:#6b6760;margin-bottom:4px}"+
   ".vm .vm-sb input{width:100%;box-sizing:border-box;font:500 1rem 'DM Sans',sans-serif;padding:12px 14px;border:1.5px solid #0d1b4b;border-radius:10px;color:#0d1b4b;background:#fff;outline:0}.vm .vm-sb input:focus{box-shadow:0 0 0 3px rgba(244,121,32,.35)}"+
   ".vm .vm-sug{display:none;position:absolute;left:0;right:0;top:100%;z-index:1200;background:#fff;border:1.5px solid #0d1b4b;border-top:0;border-radius:0 0 10px 10px;max-height:240px;overflow:auto;box-shadow:0 10px 24px rgba(13,27,75,.25)}"+
   ".vm .vm-sug div{padding:9px 12px;font:500 .9rem 'DM Sans',sans-serif;color:#0d1b4b;cursor:pointer;border-top:1px solid #f0ede7}.vm .vm-sug div:hover{background:#fff4ea}"+
   ".vm .hint{font:400 .74rem 'DM Sans',sans-serif;color:#6b6760;margin-top:6px}"+
   ".vm .leaflet-interactive:focus,.vm path:focus{outline:none}"+
   "#bkvote .cv-st{background-image:url(/data/vote/voted-bk.png?v=2)}#nycvote .cv-st{background-image:url(/data/vote/voted-nyc.png?v=2)}"+
   ".vm-cdl{font:700 10px 'DM Mono',monospace;letter-spacing:.06em;color:#0d1b4b;white-space:nowrap;text-shadow:0 0 3px #fff,0 0 3px #fff,0 0 3px #fff;transform:translate(-50%,-50%)}";
  document.head.appendChild(css);
  // shared data, loaded once for both maps
  var D={sites:null,ads:null,boro:null,cds:null,xw:null},P={},EDC={},ADBB=null;
  function get(k,u){if(!P[k])P[k]=j(u).then(function(x){D[k]=x;return x;}).catch(function(){P[k]=null;return null;});return P[k];}
  function sites(){return get('sites','/data/vote/sites.json');}
  function ads(){return get('ads','/data/assembly-districts.geojson').then(function(a){if(a&&!ADBB){ADBB=a.features.map(function(f){var b=L.geoJSON(f).getBounds();return {ad:f.properties.ad,f:f,b:b};});}return a;});}
  function eds(ad){ad=String(+ad);if(!EDC[ad])EDC[ad]=j('/data/eds/ad'+ad+'.geojson').catch(function(){return null;});return EDC[ad];}
  function ringIn(pt,r){var x=pt[0],y=pt[1],c=false;for(var i=0,k=r.length-1;i<r.length;k=i++){var xi=r[i][0],yi=r[i][1],xj=r[k][0],yj=r[k][1];if(((yi>y)!==(yj>y))&&(x<(xj-xi)*(y-yi)/(yj-yi)+xi))c=!c;}return c;}
  function polyIn(pt,g){var P=g.type==='Polygon'?[g.coordinates]:g.coordinates;return P.some(function(pp){return ringIn(pt,pp[0])&&!pp.slice(1).some(function(h){return ringIn(pt,h);});});}
  function pole(f){var g=f.geometry,P=g.type==='Polygon'?[g.coordinates]:g.coordinates,best=null,ba=-1;P.forEach(function(pp){var r=pp[0],a=0,cx=0,cy=0;for(var i=0,k=r.length-1;i<r.length;k=i++){var t=r[k][0]*r[i][1]-r[i][0]*r[k][1];a+=t;cx+=(r[k][0]+r[i][0])*t;cy+=(r[k][1]+r[i][1])*t;}if(Math.abs(a)>ba){ba=Math.abs(a);best=[cy/(3*a),cx/(3*a)];}});
    if(best&&polyIn([best[1],best[0]],g))return best;return L.geoJSON(f).getBounds().getCenter();}
  function adAt(ll){if(!ADBB)return null;var pt=[ll.lng,ll.lat];for(var i=0;i<ADBB.length;i++)if(ADBB[i].b.contains(ll)&&polyIn(pt,ADBB[i].f.geometry))return ADBB[i].ad;return null;}
  function edIn(fc,ll){if(!fc)return null;var pt=[ll.lng,ll.lat];for(var i=0;i<fc.features.length;i++)if(polyIn(pt,fc.features[i].geometry))return fc.features[i];return null;}
  function keyAt(ll){return ads().then(function(){var ad=adAt(ll);if(!ad)return null;return eds(ad).then(function(fc){var f=edIn(fc,ll);return f?{key:f.properties.e,f:f}:{key:null,ad:ad};});});}
  function edList(ks){var by={};ks.forEach(function(k){(by[k.slice(0,2)]=by[k.slice(0,2)]||[]).push(+k.slice(2));});return Object.keys(by).sort().map(function(a){return 'AD '+(+a)+': ED '+by[a].sort(function(x,y){return x-y;}).join(', ');}).join('; ');}
  function jump(t){var el=t==='ballot'?(document.getElementById('sheet')||{}).parentNode:document.getElementById(t==='ev'?'evcard':'edcard');if(!el)el=document.getElementById('out');if(el)setTimeout(function(){el.scrollIntoView({behavior:'smooth',block:'start'});},60);}
  var BN={K:'Brooklyn',M:'Manhattan',Q:'Queens',X:'Bronx',R:'Staten Island'};
  function open(key,ll,t){if(!window.nov26Render)return;get('xw','/app/data/civic/ed-crosswalk.json').then(function(X){var x=(X||{})[key]||[];var b=x[4]||BN[(D.sites&&D.sites.ed[key]||[])[2]]||'';
    window.__cvFromMap=true;
    window.nov26Render({assemblyDistrict:key.slice(0,2),electionDistrict:key.slice(2),congressionalDistrict:x[1]||'',stateSenatorialDistrict:x[0]||'',cityCouncilDistrict:x[2]||'',communityDistrict:x[3]||'',firstBoroughName:String(b).toUpperCase(),latitude:String(ll.lat),longitude:String(ll.lng)});
    window.__cvFromMap=false;jump(t||'ed');});}

  function build(sc){
    var S=SCOPES[sc],root=document.getElementById(S.id);root.className=(root.className+' vm').trim();
    root.innerHTML='<div class="k">'+esc(S.k)+'</div><h2>'+esc(S.h)+'</h2><div class="s">'+esc(S.s)+'</div>'+
      '<div class="vm-sb"><label for="'+S.id+'Addr">Your address or place in '+esc(S.boroName)+'</label><input id="'+S.id+'Addr" type="text" placeholder="Address, building, park or housing development" autocomplete="off" autocapitalize="off" spellcheck="false"><div class="vm-sug"></div><div class="hint" id="'+S.id+'Hint"></div></div>'+
      '<div class="cvt"><button type="button" class="on" data-l="ev"><span class="cv-st ev" style="width:18px;height:18px"></span>Early voting</button><button type="button" class="on" data-l="ed"><span class="cv-st" style="width:16px;height:16px"></span>Election Day poll sites</button><button type="button" class="on" data-l="eds">Election districts</button><button type="button" class="on" data-l="cd">Community districts</button></div>'+
      '<div class="vm-map" id="'+S.id+'Map"></div>';
    var G={ev:L.layerGroup(),ed:L.layerGroup(),eds:L.layerGroup(),cd:L.layerGroup()},lbl=L.layerGroup(),on={ev:1,ed:1,eds:1,cd:1},pinM=null,hiL=null,EDS={},EVS={},ROLE={},ADL={},ADLB={};
    var bb=L.latLngBounds(S.view);
    var map=L.map(S.id+'Map',{scrollWheelZoom:false,zoomSnap:.25,minZoom:S.minZoom,maxZoom:18,maxBounds:bb.pad(S.pad),maxBoundsViscosity:.8});
    map.fitBounds(bb,{padding:[6,6]});root.__map=map;
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,attribution:'&copy; OpenStreetMap contributors'}).addTo(map);
    G.cd.addTo(map);G.ev.addTo(map);
    function sync(){var z=map.getZoom();
      function want(k,c){var w=on[k]&&c;if(w&&!map.hasLayer(G[k]))G[k].addTo(map);if(!w&&map.hasLayer(G[k]))map.removeLayer(G[k]);}
      want('ev',true);want('ed',z>=13);want('cd',true);want('eds',z>=14.5);
      var lw=on.eds&&z>=15;if(lw&&!map.hasLayer(lbl))lbl.addTo(map);if(!lw&&map.hasLayer(lbl))map.removeLayer(lbl);
      if(on.eds&&z>=14.5)loadEds();
      var h=document.getElementById(S.id+'Hint');if(h)h.textContent=z<13?'Zoom in for the Election Day poll sites and, closer, the election districts.':(z<14.5?'Zoom in further for the election districts.':'');}
    map.on('zoomend moveend',sync);
    root.querySelector('.cvt').addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;var k=b.getAttribute('data-l');on[k]=!on[k];b.classList.toggle('on',!!on[k]);sync();});
    function clear(){if(pinM){map.removeLayer(pinM);pinM=null;}if(hiL){map.removeLayer(hiL);hiL=null;}}
    function inScope(key){var r=D.sites&&D.sites.ed[key];return !!r&&(!S.boro||r[2]===S.boro);}
    function siteOf(i){return i==null?null:D.sites.sites[i];}
    function pinRow(){return '<span class="cv-row"><span class="cv-st"></span></span>';}
    function drop(ll,key,opt){opt=opt||{};clear();
      var r=key?D.sites.ed[key]:null,st=r?siteOf(r[0]):null,ev=r?siteOf(r[1]):null;
      var lab=key?(opt.label?esc(opt.label)+'</small><small>':'')+'ED '+(+key.slice(2))+' · AD '+(+key.slice(0,2))+(r&&r[2]?' · '+esc(BN[r[2]]):'')+(st?'</small><small style="color:#6b6760">Election Day at '+esc(st[0]):'')+(ev?'</small><small style="color:#6b6760">Early voting at '+esc(ev[0]):''):(opt.ad?'No election district here (Assembly District '+(+opt.ad)+')':'Outside New York City');
      var btns=key?'<span class="cv-go"><button type="button" data-t="ed">Where you vote</button><button type="button" data-t="ev">Early voting days</button><button type="button" data-t="ballot">Your ballot</button></span>':'';
      pinM=L.marker(ll,{icon:L.divIcon({className:'',html:'<div class="cv-pw"><div class="cv-bal cv-bal2"><div style="display:flex;align-items:center;gap:8px">'+pinRow()+'<span><b>'+(key?'Your ballot and where you vote':'No ballot here')+'</b><small>'+lab+'</small></span></div>'+btns+'</div><div class="cv-pin"></div></div>',iconSize:[0,0],iconAnchor:[0,0]}),zIndexOffset:2000}).addTo(map);
      try{map.panInside(ll,{paddingTopLeft:[150,150],paddingBottomRight:[150,20]});}catch(e){}
      if(key){if(opt.f)hiL=L.geoJSON(opt.f,{interactive:false,style:{color:'#0d1b4b',weight:3,fillColor:'#f47920',fillOpacity:.35}}).addTo(map);
        var done=!!opt.rendered;pinM.on('click',function(e){var t=e.originalEvent&&e.originalEvent.target,b=t&&t.closest?t.closest('button'):null,tg=b?b.getAttribute('data-t'):'ed';if(done)jump(tg);else{open(key,ll,tg);done=true;}});}}
    function dropAt(ll,hi){clear();keyAt(ll).then(function(x){if(!x){drop(ll,null);return;}if(!x.key){drop(ll,null,{ad:x.ad});return;}if(!inScope(x.key)){drop(ll,null);pinM&&pinM.setIcon(L.divIcon({className:'',html:'<div class="cv-pw"><div class="cv-bal cv-bal2"><div style="display:flex;align-items:center;gap:8px">'+pinRow()+'<span><b>Not in '+esc(S.boroName)+'</b><small>ED '+(+x.key.slice(2))+' · AD '+(+x.key.slice(0,2))+' votes in '+esc(BN[(D.sites.ed[x.key]||[])[2]]||'another borough')+'. Use the New York City map below.</small></span></div></div><div class="cv-pin"></div></div>',iconSize:[0,0],iconAnchor:[0,0]}));return;}drop(ll,x.key,{f:x.f});});}
    map.on('click',function(e){dropAt(e.latlng);});
    window[sc+'voteAddr']=function(a,lat,lng){if(!D.sites||!isFinite(lat)||!isFinite(lng))return false;var key=('0'+parseInt(a.assemblyDistrict,10)).slice(-2)+('00'+parseInt(a.electionDistrict,10)).slice(-3);
      if(!inScope(key))return false;var ll=L.latLng(lat,lng),ad=document.getElementById(S.id+'Addr');
      map.setView(ll,15.5);drop(ll,key,{label:ad&&ad.value?ad.value.split(',')[0]:'',rendered:true});
      eds(key.slice(0,2)).then(function(fc){if(!fc||!pinM)return;var f=fc.features.filter(function(x){return x.properties.e===key;})[0];if(f&&!hiL)hiL=L.geoJSON(f,{interactive:false,style:{color:'#0d1b4b',weight:3,fillColor:'#f47920',fillOpacity:.35}}).addTo(map);});
      setTimeout(function(){root.scrollIntoView({behavior:'smooth',block:'start'});},50);return true;};
    function siteTap(i){clear();var st=siteOf(i),r=ROLE[i],ll=L.latLng(st[2],st[3]);
      var keys=(r.ed||r.ev).slice().sort(),multiAD={};keys.forEach(function(k){multiAD[k.slice(0,2)]=1;});var showAD=Object.keys(multiAD).length>1;
      var role=(r.ev?'Early voting site, October 24 to November 1':'')+(r.ev&&r.ed?' · ':'')+(r.ed?'Election Day poll site, November 3, 6 AM to 9 PM':'');
      var html='<div class="cv-pw"><div class="cv-site"><button type="button" class="cv-x" data-x="1" aria-label="Close">&times;</button>'+pinRow()+'<div class="nm">'+esc(st[0])+'</div><div class="ad">'+esc(st[1])+(st[4]?' · '+esc(st[4]):'')+'</div><div class="rl">'+esc(role)+'</div>'+
        '<div class="tp">Tap your election district to see your ballot'+(r.ed?'':' (these vote early here)')+'</div><div class="cv-chips">'+keys.map(function(k){return '<button type="button" data-k="'+k+'">ED '+(+k.slice(2))+(showAD?' <span style="font-weight:600">AD '+(+k.slice(0,2))+'</span>':'')+'</button>';}).join('')+'</div></div></div>';
      pinM=L.marker(ll,{icon:L.divIcon({className:'',html:html,iconSize:[0,0],iconAnchor:[0,0]}),zIndexOffset:2000}).addTo(map);
      try{map.panInside(ll,{paddingTopLeft:[150,230],paddingBottomRight:[150,20]});}catch(e){}
      pinM.on('click',function(e){var t=e.originalEvent&&e.originalEvent.target,b=t&&t.closest?t.closest('button'):null;if(!b)return;if(b.getAttribute('data-x')){clear();return;}var k=b.getAttribute('data-k');if(!k)return;
        eds(k.slice(0,2)).then(function(fc){var f=fc?fc.features.filter(function(x){return x.properties.e===k;})[0]:null,p=f?L.latLng(pole(f)):ll;if(f&&map.getZoom()<14.5)map.setView(p,15);drop(p,k,{f:f});open(k,p,'ed');});});}
    function drawSites(){var all={};Object.keys(D.sites.ed).forEach(function(k){var r=D.sites.ed[k];if(S.boro&&r[2]!==S.boro)return;
        if(r[0]!=null){var a=all[r[0]]=all[r[0]]||{};(a.ed=a.ed||[]).push(k);EDS[k]=r[0];}
        if(r[1]!=null){var b=all[r[1]]=all[r[1]]||{};(b.ev=b.ev||[]).push(k);EVS[k]=r[1];}});
      ROLE=all;var n=0;
      Object.keys(all).forEach(function(i){var st=siteOf(i),r=all[i],isEv=!!r.ev;n++;
        var tt='<div class="cv-tt"><b>'+esc(st[0])+'</b><br>'+esc(st[1])+(r.ev?'<br><b>Early voting site</b> for '+esc(edList(r.ev)):'')+(r.ed?'<br><b>Election Day poll site</b> for '+esc(edList(r.ed)):'')+'</div>';
        var sz=isEv?34:30;L.marker([st[2],st[3]],{icon:L.divIcon({className:'',html:'<div class="cv-st'+(isEv?' ev':'')+'"></div>',iconSize:[sz,sz],iconAnchor:[sz/2,sz/2]}),zIndexOffset:isEv?900:800}).bindTooltip(tt,{direction:'top',offset:[0,-16]}).on('click',function(e){L.DomEvent.stopPropagation(e);siteTap(i);}).addTo(G[isEv?'ev':'ed']);});
      return n;}
    function loadEds(){if(!ADBB)return;var vb=map.getBounds();ADBB.forEach(function(x){if(!vb.intersects(x.b))return;if(ADL[x.ad])return;ADL[x.ad]=1;
      eds(x.ad).then(function(fc){if(!fc)return;var ST={color:'#0d1b4b',weight:1,opacity:.6,fillColor:'#f47920',fillOpacity:0};
        L.geoJSON(fc,{filter:function(f){return inScope(f.properties.e);},style:ST,onEachFeature:function(f,l){var k=f.properties.e;
          l.bindTooltip('<b>Election District '+(+k.slice(2))+'</b><br>Assembly District '+(+k.slice(0,2)),{sticky:true,direction:'top',offset:[0,-8]});
          l.on('mouseover',function(){l.setStyle({weight:3,opacity:1,fillOpacity:.22});l.bringToFront();});l.on('mouseout',function(){l.setStyle(ST);});
          l.on('click',function(e){L.DomEvent.stopPropagation(e);l.closeTooltip();l.setStyle(ST);drop(e.latlng,k,{f:f});});}}).addTo(G.eds);
        fc.features.forEach(function(f){if(!inScope(f.properties.e))return;lbl.addLayer(L.marker(pole(f),{interactive:false,icon:L.divIcon({className:'',html:'<div class="cv-edl">'+(+f.properties.e.slice(2))+'</div>',iconSize:[0,0]})}));});});});}
    function drawBounds(){
      if(D.boro){var fs=D.boro.features.filter(function(f){return !S.boro||f.properties.boroname===S.boroName;});L.geoJSON({type:'FeatureCollection',features:fs},{interactive:false,style:{color:'#f47920',weight:3,opacity:1,fill:false}}).addTo(map);}
      if(D.cds){var cf=D.cds.features.filter(function(f){var c=String(f.properties.c);return /^[1-5](0[1-9]|1[0-8])$/.test(c)&&(!S.boro||c.charAt(0)==='3');});
        L.geoJSON({type:'FeatureCollection',features:cf},{interactive:false,style:{color:'#0d1b4b',weight:1.5,opacity:.55,dashArray:'4 4',fill:false}}).addTo(G.cd);
        var BL={1:'MN',2:'BX',3:'BK',4:'QN',5:'SI'};cf.forEach(function(f){var c=String(f.properties.c);L.marker(pole(f),{interactive:false,icon:L.divIcon({className:'',html:'<div class="vm-cdl">'+BL[c.charAt(0)]+' '+(+c.slice(1))+'</div>',iconSize:[0,0]})}).addTo(G.cd);});}}
    // the search box: the page's own lookup, aimed at this map
    (function(){var inp=document.getElementById(S.id+'Addr'),sug=root.querySelector('.vm-sug'),feats=[],t;
      function pick(i){var f=feats[i];if(!f)return;sug.style.display='none';inp.value=f.properties.label||inp.value;window.__voteTarget=sc;if(window.nov26Lookup)window.nov26Lookup(f);}
      inp.addEventListener('input',function(){clearTimeout(t);var q=inp.value.trim();if(q.length<3){sug.style.display='none';return;}
        t=setTimeout(function(){var qq=q;if(S.boro&&!/brooklyn|,/i.test(qq))qq+=', Brooklyn';
          fetch('https://geosearch.planninglabs.nyc/v2/autocomplete?size=6&text='+encodeURIComponent(qq)).then(function(r){return r.json();}).then(function(d){feats=(d&&d.features)?d.features:[];
            if(S.boro){var ff=feats.filter(function(f){return /brooklyn/i.test((f.properties||{}).borough||'');});if(ff.length)feats=ff;}
            if(!feats.length){sug.style.display='none';return;}sug.innerHTML='';feats.forEach(function(f,i){var d=document.createElement('div');d.textContent=f.properties.label||'';d.addEventListener('click',function(){pick(i);});sug.appendChild(d);});sug.style.display='block';}).catch(function(){sug.style.display='none';});},220);});
      inp.addEventListener('keydown',function(e){if(e.key==='Enter'){e.preventDefault();if(feats.length)pick(0);}if(e.key==='Escape')sug.style.display='none';});
      document.addEventListener('click',function(e){if(e.target!==inp&&!sug.contains(e.target))sug.style.display='none';});})();
    Promise.all([sites(),ads(),get('boro','/data/boro-simple.geojson'),get('cds','/data/cd-boundaries-lite.geojson')]).then(function(){if(!D.sites)return;var n=drawSites();drawBounds();
      var h=document.getElementById(S.id+'Hint');var eds=Object.keys(D.sites.ed).filter(inScope).length;
      root.querySelector('.s').textContent=S.s+' '+(S.boro?eds.toLocaleString()+' of New York City’s 4,070 election districts are in Brooklyn, voting at '+n.toLocaleString()+' sites.':'4,070 election districts, voting at '+n.toLocaleString()+' sites.');
      sync();});
  }
  roots.forEach(build);
})();
