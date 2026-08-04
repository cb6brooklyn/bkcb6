/* Shared engine for the 59 community district pages. Each page sets window.CD_CODE. */
(function(){
  var CODE=window.CD_CODE;
  var $=function(i){return document.getElementById(i);};
  var n=function(v){return v==null?'n/a':Number(Math.round(v)).toLocaleString('en-US');};
  var money=function(v){return v==null?'n/a':'$'+Number(Math.round(v)).toLocaleString('en-US');};
  var TIERS=['#1B5E8A','#82C341','#E8A800','#D45F00','#67000D'];
  var TIERNAME=['Least Expensive','Less Expensive','Mid Range','Expensive','Most Expensive'];
  var MON=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  var MONL=['January','February','March','April','May','June','July','August','September','October','November','December'];

  var D={};            // loaded data
  var lens='nb';       // nb | cc | lu | zn
  var lotLayer=null, LOTS=null, lotsLoading=false;
  var mode='1br';      // unit size
  var map, layer=null, labels=[], boroLabel=null;

  function bedKey(m){ return ({studio:'studio','1br':'br1','2br':'br2','3br':'br3'})[m]||'br1'; }
  function bedGeo(m){ return ({studio:'rent_studio','1br':'rent_1br','2br':'rent_2br','3br':'rent_3br'})[m]||'rent_1br'; }
  function bedLong(m){ return ({studio:'Studio','1br':'1 Bedroom','2br':'2 Bedroom','3br':'3+ Bedroom'})[m]||''; }

  function tiers(vals){
    var s=vals.slice().sort(function(a,b){return a-b;});
    return function(v){
      if(v==null) return null;
      var i=s.indexOf(v), q=Math.min(Math.floor(i/s.length*5),4);
      return {fill:TIERS[q],band:TIERNAME[q],rank:s.length-i,total:s.length};
    };
  }
  function invNb(name,bed){
    var r=D.inv&&D.inv.nb[name]&&D.inv.nb[name][bed];
    if(!r) return null;
    var k=(D.inv.months.length-1)-r[0];
    return (k>=0&&k<r[1].length)?r[1][k]:null;
  }
  function ccVal(d,bed){
    var rec=D.cc&&D.cc.cds[d]; if(!rec||!rec[bed]) return null;
    return rec[bed][rec[bed].length-1];
  }
  function ccInv(d,bed){
    var rec=D.cc&&D.cc.cds[d]; if(!rec||!rec['inv_'+bed]) return null;
    var a=rec['inv_'+bed]; return a[a.length-1];
  }


  var LU_LABEL={'01':'One and two family homes','02':'Multifamily walk-up','03':'Multifamily elevator',
    '04':'Mixed residential and commercial','05':'Commercial and office','06':'Industrial and manufacturing',
    '07':'Transportation and utility','08':'Public facilities and institutions','09':'Open space and recreation',
    '10':'Parking facilities','11':'Vacant land'};
  var LU_COLOR={'01':'#f2c94c','02':'#f2994a','03':'#eb5757','04':'#bb6bd9','05':'#2f80ed','06':'#9b51e0',
    '07':'#6b7280','08':'#56ccf2','09':'#27ae60','10':'#a0a0a0','11':'#d9d9d9'};
  var ZN_COLOR={'R':'#f2994a','C':'#2563eb','M':'#9b51e0','P':'#27ae60','B':'#56ccf2','?':'#9ca3af'};
  var ZN_LABEL={'R':'Residential','C':'Commercial','M':'Manufacturing','P':'Park','B':'Special district','?':'Other'};

  var ZSYM={Y:'\u25cf',L:'\u2666',S:'\u25cb',N:'\u2013'};
  var ZLBL={Y:'Yes',L:'Limits',S:'Permit',N:'No'};
  var ZCOL={Y:'#2e6b30',L:'#a65a00',S:'#2145a8',N:'#a82121'};
  var ZSHOW=['live','shop','eat','factory'];
  function zBase(z){
    if(!z) return null;
    var m=String(z).trim().toUpperCase().match(/^([RCM])\s*(\d{1,2})/);
    if(!m) return null;
    var lim={R:12,C:8,M:3}[m[1]], num=parseInt(m[2],10);
    return (num>=1&&num<=lim)?(m[1]+num):null;
  }
  var PARKLAND='Mapped parkland. Parks has jurisdiction, and changing it takes an act of the State Legislature, not a rezoning.';
  function zUses(zone){
    if(String(zone||'').trim().toUpperCase()==='PARK')
      return '<div style="margin-top:6px;border-top:1px solid #eee;padding-top:5px;font-size:.72rem;color:#2e6b30;line-height:1.5">'+PARKLAND+'</div>';
    var base=zBase(zone);
    if(!base||!D.zmx) return '';
    var rows=D.zmx.goals.filter(function(g){return ZSHOW.indexOf(g.id)>-1;}).map(function(g){
      var r=D.zmx.matrix[g.ug], v=r?r[base]:null;
      if(!v) return '';
      var lab=g.q.replace(/^I want to /,'').replace(/ here$/,'');
      return '<div style="display:flex;justify-content:space-between;gap:12px;padding:1px 0;font-size:.72rem">'+
        '<span style="color:#555">'+lab.charAt(0).toUpperCase()+lab.slice(1)+'</span>'+
        '<span style="font-weight:800;color:'+ZCOL[v]+'">'+ZSYM[v]+' '+ZLBL[v]+'</span></div>';
    }).join('');
    return rows ? ('<div style="margin-top:6px;border-top:1px solid #eee;padding-top:5px">'+
      '<div style="font-family:DM Mono,monospace;font-size:.55rem;text-transform:uppercase;letter-spacing:.07em;color:#9ca3af;margin-bottom:3px">Can be built here</div>'+rows+'</div>') : '';
  }
  function znFam(z){
    if(!z) return '?';
    var c=String(z).trim().toUpperCase().charAt(0);
    if(c==='R') return 'R'; if(c==='C') return 'C'; if(c==='M') return 'M';
    if(String(z).toUpperCase().indexOf('PARK')===0) return 'P';
    if(c==='B') return 'B';
    return '?';
  }
  function cdNum(){ return ({MN:'1',BX:'2',BK:'3',QN:'4',SI:'5'})[CODE.slice(0,2)]+String(D.look.num).padStart(2,'0'); }

  function loadLots(cb){
    if(LOTS) return cb();
    if(lotsLoading) return;
    lotsLoading=true;
    $('bnote').textContent='Loading every lot in the district\u2026';
    // token as a query parameter, not a header: a custom header forces a CORS preflight
    var url='https://data.cityofnewyork.us/resource/64uk-42ks.json'+
      '?$select=landuse,zonedist1,latitude,longitude'+
      '&$where=' + encodeURIComponent("cd='"+cdNum()+"' AND latitude IS NOT NULL") +
      '&$limit=50000&$$app_token=HvFoIfzodzpRML7a1104Ca2tM';
    fetch(url)
      .then(function(r){
        if(!r.ok) throw new Error('HTTP '+r.status);
        return r.json();
      })
      .then(function(rows){
        if(!rows || !rows.length) throw new Error('no rows');
        LOTS=rows.map(function(r){
          return {y:+r.latitude,x:+r.longitude,lu:(r.landuse||'').padStart(2,'0'),z:r.zonedist1||''};
        }).filter(function(p){return p.y&&p.x;});
        lotsLoading=false; cb();
      }).catch(function(e){
        lotsLoading=false;
        drawEmpty('Lot data could not load from NYC Open Data ('+(e&&e.message?e.message:'network')+').');
      });
  }
  function drawLots(kind){
    loadLots(function(){
      clearMap();
      var counts={};
      var grp=L.layerGroup();
      // dense districts get smaller dots and no per-lot tooltip, so they stay responsive
      var rad = LOTS.length>25000 ? 2 : (LOTS.length>12000 ? 2.5 : 3.5);
      var tips = LOTS.length<=25000;
      LOTS.forEach(function(p){
        var key = kind==='lu' ? p.lu : znFam(p.z);
        var col = kind==='lu' ? (LU_COLOR[p.lu]||'#9ca3af') : (ZN_COLOR[key]||'#9ca3af');
        counts[key]=(counts[key]||0)+1;
        var m=L.circleMarker([p.y,p.x],{radius:rad,stroke:false,fillColor:col,fillOpacity:.8,
          renderer:window.__lotCanvas});
        if(tips) m.bindTooltip(kind==='lu'
          ? (LU_LABEL[p.lu]||'Unclassified')
          : (p.z? ('<b>'+p.z+'</b> \u00b7 '+ZN_LABEL[znFam(p.z)]+zUses(p.z)) : 'No zoning recorded'),{sticky:true});
        m.addTo(grp);
      });
      grp.addTo(map); layer=grp;
      try{ if(D.cdLayer) map.fitBounds(D.cdLayer.getBounds(),{padding:[18,18]}); }catch(e){}
      var lab = kind==='lu' ? LU_LABEL : ZN_LABEL;
      var col = kind==='lu' ? LU_COLOR : ZN_COLOR;
      var order=Object.keys(counts).sort(function(a,b){return counts[b]-counts[a];});
      $('legend').innerHTML='<span class="l">'+(kind==='lu'?'Land use':'Zoning')+'</span>'+
        order.map(function(k){
          return '<span class="i"><span class="sw" style="background:'+(col[k]||'#9ca3af')+'"></span>'+
                 (lab[k]||'Other')+' ('+n(counts[k])+')</span>';
        }).join('');
      $('bnote').textContent=n(LOTS.length)+' lots \u00b7 every tax lot in the district'+
        (tips?'':' \u00b7 too dense for per-lot labels');
      $('capS').textContent=(kind==='lu'?'Land use':'Zoning')+' by tax lot';
    });
  }
  function clearMap(){
    if(layer){ map.removeLayer(layer); layer=null; }
    labels.forEach(function(m){ map.removeLayer(m); }); labels=[];
  }
  function label(text,latlng,px){
    return L.marker(latlng,{interactive:false,keyboard:false,pane:'nbNames',
      icon:L.divIcon({className:'nb-lab',html:'<span style="font-size:'+px+'px">'+text+'</span>',
        iconSize:[130,32],iconAnchor:[65,16]})}).addTo(map);
  }

  function drawNb(){
    var feats=D.nbgeo.features.filter(function(f){ return D.look.se.indexOf(f.properties.nb)>-1; });
    if(!feats.length) return drawEmpty('StreetEasy publishes no neighborhood rents for this district.');
    var T=tiers(feats.map(function(f){return f.properties[bedGeo(mode)];}).filter(function(v){return v!=null;}));
    clearMap();
    layer=L.geoJSON({type:'FeatureCollection',features:feats},{
      style:function(f){ var t=T(f.properties[bedGeo(mode)]);
        return {color:'#fff',weight:1.6,fillColor:t?t.fill:'#ddd',fillOpacity:t?.82:.25}; },
      onEachFeature:function(f,l){
        var p=f.properties, t=T(p[bedGeo(mode)]);
        var rows=[['studio','Studio'],['1br','1 BR'],['2br','2 BR'],['3br','3+ BR']].map(function(r){
          var v=p[bedGeo(r[0])], c=invNb(p.nb,bedKey(r[0])), on=(r[0]===mode);
          return '<div style="display:flex;justify-content:space-between;gap:16px;padding:2px 0;'+
            (on?'font-weight:800;color:#0d1b4b':'color:#555')+'"><span>'+r[1]+
            (c!=null?' <span style="font-family:DM Mono,monospace;font-size:.66rem;color:#9ca3af">('+n(c)+')</span>':'')+
            (on?' \u25C0':'')+'</span><span style="font-family:DM Mono,monospace">'+money(v)+'</span></div>';
        }).join('');
        l.bindTooltip('<div style="font-family:DM Sans,sans-serif;min-width:196px">'+
          '<div style="font-weight:700;font-size:.9rem;color:#0d1b4b;border-bottom:1px solid #eee;padding-bottom:4px;margin-bottom:6px">'+p.nb+'</div>'+
          '<div style="margin-bottom:7px"><span style="font-size:1.15rem;font-weight:800;color:#0d1b4b;font-family:DM Mono,monospace">'+money(p[bedGeo(mode)])+'</span>'+
          '<span style="font-size:.76rem;font-weight:700;color:#0d1b4b"> /month</span>'+
          '<div style="font-size:.78rem;font-weight:700;color:#f47920;margin-top:1px">'+bedLong(mode)+'</div></div>'+rows+
          '<div style="font-size:.65rem;color:#888;margin-top:6px;border-top:1px solid #eee;padding-top:5px">'+
          (t?t.band+' \u00b7 #'+t.rank+' of '+t.total+' in the district':'')+'</div></div>',{sticky:true,opacity:1});
        l.on('mouseover',function(){ l.setStyle({weight:3,color:'#333'}); if(l.bringToFront) l.bringToFront(); });
        l.on('mouseout',function(){ layer.resetStyle(l); });
        try{ labels.push(label(p.nb,l.getBounds().getCenter(),12)); }catch(e){}
      }
    }).addTo(map);
    fit();
    $('bnote').textContent=feats.length+' neighborhoods in this district';
    $('capS').textContent='Median asking rent by neighborhood \u00b7 '+bedLong(mode);
  }

  function drawCc(){
    var mine=D.look.cc.map(function(c){return c.d;});
    var feats=D.ccgeo.features.filter(function(f){ return mine.indexOf(f.properties.cc)>-1; });
    if(!feats.length) return drawEmpty('No council districts matched.');
    var withRent=feats.filter(function(f){ return ccVal(f.properties.cc,bedKey(mode))!=null; }).length;
    if(!withRent) return drawEmpty('StreetEasy publishes no rent figures for this part of the city. Housing built here is shown below.');
    var T=tiers(feats.map(function(f){return ccVal(f.properties.cc,bedKey(mode));}).filter(function(v){return v!=null;}));
    clearMap();
    layer=L.geoJSON({type:'FeatureCollection',features:feats},{
      style:function(f){ var t=T(ccVal(f.properties.cc,bedKey(mode)));
        return {color:'#fff',weight:1.6,fillColor:t?t.fill:'#ddd',fillOpacity:t?.82:.25}; },
      onEachFeature:function(f,l){
        var d=f.properties.cc, t=T(ccVal(d,bedKey(mode)));
        var share=(D.look.cc.filter(function(c){return c.d===d;})[0]||{}).share;
        var rows=[['studio','Studio'],['br1','1 BR'],['br2','2 BR'],['br3','3+ BR']].map(function(r){
          var v=ccVal(d,r[0]), c=ccInv(d,r[0]), on=(bedKey(mode)===r[0]);
          return '<div style="display:flex;justify-content:space-between;gap:16px;padding:2px 0;'+
            (on?'font-weight:800;color:#0d1b4b':'color:#555')+'"><span>'+r[1]+
            (c!=null?' <span style="font-family:DM Mono,monospace;font-size:.66rem;color:#9ca3af">('+n(c)+')</span>':'')+
            (on?' \u25C0':'')+'</span><span style="font-family:DM Mono,monospace">'+money(v)+'</span></div>';
        }).join('');
        l.bindTooltip('<div style="font-family:DM Sans,sans-serif;min-width:200px">'+
          '<div style="font-weight:700;font-size:.9rem;color:#0d1b4b;border-bottom:1px solid #eee;padding-bottom:4px;margin-bottom:6px">Council District '+d+'</div>'+
          '<div style="margin-bottom:7px"><span style="font-size:1.15rem;font-weight:800;color:#0d1b4b;font-family:DM Mono,monospace">'+money(ccVal(d,bedKey(mode)))+'</span>'+
          '<span style="font-size:.76rem;font-weight:700;color:#0d1b4b"> /month</span>'+
          '<div style="font-size:.78rem;font-weight:700;color:#f47920;margin-top:1px">'+bedLong(mode)+'</div></div>'+rows+
          '<div style="font-size:.65rem;color:#888;margin-top:6px;border-top:1px solid #eee;padding-top:5px">'+
          (share?'Covers about '+Math.round(share*100)+'% of this community district':'')+' \u00b7 from January 2023</div></div>',{sticky:true,opacity:1});
        l.on('mouseover',function(){ l.setStyle({weight:3,color:'#333'}); if(l.bringToFront) l.bringToFront(); });
        l.on('mouseout',function(){ layer.resetStyle(l); });
        try{ labels.push(label('Council District '+d,l.getBounds().getCenter(),12)); }catch(e){}
      }
    }).addTo(map);
    fit();
    $('bnote').textContent=feats.length+' council districts overlap this district \u00b7 from January 2023';
    $('capS').textContent='Median asking rent by council district \u00b7 '+bedLong(mode);
  }
  function drawEmpty(msg){
    clearMap();
    $('bnote').textContent=msg;
    $('capS').textContent=msg;
    try{ if(D.cdLayer) map.fitBounds(D.cdLayer.getBounds(),{padding:[24,24]}); }catch(e){}
  }
  function fit(){
    try{
      var b=layer.getBounds();
      if(D.cdLayer) b=b.extend(D.cdLayer.getBounds());
      map.fitBounds(b,{padding:[18,18]});
    }catch(e){}
  }
  var LENS_EXPL={"cb": "The 59 districts that review land use locally and are the boards this site is built around.", "nb": "The names people actually use. They follow neither official boundary.", "cc": "The 51 seats whose members hold the deciding vote on most rezonings. From January 2023.", "lu": "What every lot in the district is actually used for today.", "zn": "What the rules allow to be built, lot by lot. R residential, C commercial, M manufacturing."};
  var LENS_LBL={nb:'Neighborhoods',cc:'Council districts',lu:'Land use',zn:'Zoning'};
  function lensExpl(){
    var host=document.querySelector('.bar:not(.top0)');
    if(!host) return;
    var b=document.getElementById('lensexpl');
    if(!b){ b=document.createElement('div'); b.className='lensexpl'; b.id='lensexpl';
      host.parentNode.insertBefore(b,host.nextSibling); }
    b.innerHTML='<b>'+(LENS_LBL[lens]||'')+'</b> \u00b7 '+(LENS_EXPL[lens]||'');
  }
  function draw(){
    lensExpl();
    if(lens==='lu') return drawLots('lu');
    if(lens==='zn') return drawLots('zn');
    restoreLegend();
    if(lens==='nb') drawNb(); else drawCc();
  }
  function restoreLegend(){
    $('legend').innerHTML='<span class="l">Rent tier within this district</span>'+
      TIERS.slice().reverse().map(function(c,i){
        return '<span class="i"><span class="sw" style="background:'+c+'"></span>'+TIERNAME[4-i]+'</span>';
      }).join('');
  }

  function boot(){
    map=L.map('map',{scrollWheelZoom:true,preferCanvas:true}).setView([40.68,-73.97],12);
    window.__lotCanvas=L.canvas({padding:.4});
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',{maxZoom:17,attribution:'&copy; CARTO'}).addTo(map);
    map.createPane('nbNames'); map.getPane('nbNames').style.zIndex=640; map.getPane('nbNames').style.pointerEvents='none';

    $('legend').innerHTML='<span class="l">Rent tier within this district</span>'+
      TIERS.slice().reverse().map(function(c,i){
        return '<span class="i"><span class="sw" style="background:'+c+'"></span>'+TIERNAME[4-i]+'</span>';
      }).join('');

    Promise.all([
      fetch('/data/cd-lookup.json').then(function(r){return r.json();}),
      fetch('/data/neighborhood-rents.geojson').then(function(r){return r.json();}),
      fetch('/data/council-districts.geojson').then(function(r){return r.json();}),
      fetch('/data/cc-rents.json').then(function(r){return r.json();}).catch(function(){return null;}),
      fetch('/data/inventory-by-bed.json').then(function(r){return r.json();}).catch(function(){return null;}),
      fetch('/data/citywide-rents.geojson').then(function(r){return r.json();}),
      fetch('/data/housing-db-cd.json').then(function(r){return r.json();}).catch(function(){return null;}),
      fetch('/data/hpd-affordable.json').then(function(r){return r.json();}).catch(function(){return null;}),
      fetch('/data/housing-jobs.json').then(function(r){return r.json();}).catch(function(){return null;}),
      fetch('/data/cd-landuse.json').then(function(r){return r.json();}).catch(function(){return null;}),
      fetch('/data/nyc-nprc.json').then(function(r){return r.json();}).catch(function(){return null;}),
      fetch('/data/zoning-matrix.json').then(function(r){return r.json();}).catch(function(){return null;})
    ]).then(function(a){
      D.look=a[0][CODE]; D.nbgeo=a[1]; D.ccgeo=a[2]; D.cc=a[3]; D.inv=a[4];
      D.cdgeo=a[5]; D.hdb=a[6]; D.hpd=a[7]; D.jobs=a[8]; D.lu=a[9]; D.nprc=a[10]; D.zmx=a[11];
      if(!D.look){ $('bnote').textContent='District not found.'; return; }
      header(); outline(); kpis();
      if(!D.look.se.length){
        lens='cc';
        document.querySelectorAll('[data-lens]').forEach(function(x){ x.classList.toggle('on', x.getAttribute('data-lens')==='cc'); });
        var nb=document.querySelector('[data-lens="nb"]');
        if(nb){ nb.disabled=true; nb.title='StreetEasy publishes no neighborhood rents here'; }
      }
      draw(); housing(); table(); landuse(); helpers(); districtPicker(a[0]);
    }).catch(function(){ $('bnote').textContent='Data could not load.'; });
  }

  function header(){
    var l=D.look;
    document.title=l.boro+' CB'+l.num+' \u2014 rents and housing \u2014 bkcb6.app';
    $('h1').innerHTML=l.boro+' <span>CB'+l.num+'</span>';
    $('nbs').textContent=l.se.length?l.se.join(' \u00b7 '):'';
    $('capT').textContent=l.boro+' Community District '+l.num;
  }
  function outline(){
    var f=D.cdgeo.features.filter(function(x){return x.properties.cb_code===CODE;})[0];
    if(!f) return;
    D.cdLayer=L.geoJSON(f,{style:{color:'#0d1b4b',weight:3,fill:false,dashArray:'5,4'}}).addTo(map);
  }
  function kpis(){
    var p=(D.cdgeo.features.filter(function(x){return x.properties.cb_code===CODE;})[0]||{}).properties||{};
    var key=CODE.slice(0,2)+'-'+String(D.look.num).padStart(2,'0');
    var h=D.hdb&&D.hdb.cd[key], hp=D.hpd&&D.hpd.by_cd&&D.hpd.by_cd[key];
    var out='';
    if(p.rent_1br) out+='<div class="kpi"><div class="k">Median 1BR rent</div><div class="v">'+money(p.rent_1br)+'</div><div class="d">'+(p.boro_band_1br||'')+' in '+D.look.boro+'</div></div>';
    if(p.rent_2br) out+='<div class="kpi"><div class="k">Median 2BR rent</div><div class="v">'+money(p.rent_2br)+'</div><div class="d">across the district</div></div>';
    if(h) out+='<div class="kpi"><div class="k">Housing built since 2010</div><div class="v">'+n(h.total)+'</div><div class="d">net units completed</div></div>';
    if(h) out+='<div class="kpi"><div class="k">Permitted, not built</div><div class="v">'+n(h.permitted)+'</div><div class="d">units in the pipeline</div></div>';
    if(hp!=null) out+='<div class="kpi"><div class="k">Affordable financed</div><div class="v">'+n(hp)+'</div><div class="d">income regulated since 2014</div></div>';
    out+='<div class="kpi"><div class="k">Council districts</div><div class="v" style="font-size:1rem">'+(D.look.cc.map(function(c){return 'CD'+c.d;}).join(', ')||'\u2014')+'</div><div class="d">covering this district</div></div>';
    $('kpis').innerHTML=out;
  }
  function housing(){
    var key=CODE.slice(0,2)+'-'+String(D.look.num).padStart(2,'0');
    var h=D.hdb&&D.hdb.cd[key];
    if(!h||!window.Chart){ $('hsec').style.display='none'; return; }
    var yrs=D.hdb.years.map(String);
    new Chart($('cHouse'),{type:'bar',
      data:{labels:yrs,datasets:[{data:yrs.map(function(y){return h.comp[y];}),backgroundColor:'#132D65',borderRadius:3}]},
      options:{responsive:true,maintainAspectRatio:false,animation:false,
        plugins:{legend:{display:false},tooltip:{callbacks:{label:function(c){return n(c.parsed.y)+' units';}}}},
        scales:{x:{ticks:{font:{size:9,family:'DM Mono'},color:'#6b6760'},grid:{display:false}},
                y:{ticks:{font:{size:9,family:'DM Mono'},color:'#6b6760'},grid:{color:'#f0ede8'}}}}});
    var best=yrs.reduce(function(a,y){return h.comp[y]>h.comp[a]?y:a;},yrs[0]);
    $('nHouse').textContent='This district completed '+n(h.total)+' net units between 2010 and 2024, most in '+best+' with '+n(h.comp[best])+
      '. Another '+n(h.permitted)+' are permitted and '+n(h.filed)+' filed but not yet built. At the 2020 census it held '+n(h.cen2020)+' housing units.';
  }
  function table(){
    var rows=D.look.se.map(function(nb){
      var p=(D.nbgeo.features.filter(function(f){return f.properties.nb===nb;})[0]||{}).properties;
      if(!p) return null;
      return {n:nb,s:p.rent_studio,a:p.rent_1br,b:p.rent_2br,c:p.rent_3br,i:invNb(nb,'br1')};
    }).filter(Boolean).sort(function(x,y){return (y.a||0)-(x.a||0);});
    if(!rows.length){ $('tsec').style.display='none'; return; }
    $('tbl').innerHTML='<tr><th>Neighborhood</th><th>Studio</th><th>1 BR</th><th>2 BR</th><th>3+ BR</th><th>1BR listed</th></tr>'+
      rows.map(function(r){
        return '<tr><td>'+r.n+'</td><td>'+money(r.s)+'</td><td>'+money(r.a)+'</td><td>'+money(r.b)+'</td><td>'+money(r.c)+'</td><td>'+n(r.i)+'</td></tr>';
      }).join('');
  }

  function bars(rows,total,colors){
    return rows.map(function(r){
      var pct=total?(r.v/total*100):0;
      return '<div class="lub"><span class="lusw" style="background:'+(colors[r.k]||'#9ca3af')+'"></span>'+
        '<span class="lun">'+r.label+'</span>'+
        '<span class="lubar"><i style="width:'+pct.toFixed(1)+'%;background:'+(colors[r.k]||'#9ca3af')+'"></i></span>'+
        '<span class="lup">'+pct.toFixed(1)+'%</span></div>';
    }).join('');
  }
  var LETTERNOTE={
    R:'R does not mean only housing. Residence Districts also permit schools, houses of worship, libraries, museums, hospitals and community centers as of right. What they exclude is retail, storage and production.',
    C:'C does not mean no housing. Housing is permitted as of right in C1, C2, C4, C5 and C6. Only C7 and C8 exclude residences.',
    M:'M does not mean only factories. Offices, retail, storage and entertainment are widely permitted. The one thing Manufacturing Districts bar as of right is housing.'};
  function letterNote(){
    var d=D.lu&&D.lu.cd[CODE];
    if(!d) return '';
    var fams=Object.keys(d.zfam||{}).filter(function(k){return d.zfam[k].area>0;});
    var letters=[];
    if(fams.indexOf('Residential')>-1) letters.push('R');
    if(fams.indexOf('Commercial')>-1) letters.push('C');
    if(fams.indexOf('Manufacturing')>-1) letters.push('M');
    if(!letters.length) return '';
    return '<div style="margin-top:12px;padding:11px 12px;background:#0d1b4b;border-radius:9px;color:rgba(255,255,255,.85);font-size:.76rem;line-height:1.6">'+
      '<div style="color:#f47920;font-weight:800;font-size:.8rem;margin-bottom:4px">The letter is a name, not a description</div>'+
      letters.map(function(L){return LETTERNOTE[L];}).join(' ')+
      ' <a href="/zoning" style="color:#fff;border-bottom:1px solid #f47920;text-decoration:none">See what each district actually allows &rarr;</a></div>';
  }
  function landuse(){
    var L=D.lu, d=L&&L.cd[CODE];
    if(!d){ var s1=$('lusec'); if(s1) s1.style.display='none'; var s2=$('zsec'); if(s2) s2.style.display='none'; return; }

    // land use by share of lot area
    var luTot=0; Object.keys(d.lu).forEach(function(c){ luTot+=d.lu[c].area; });
    var luRows=Object.keys(d.lu).map(function(c){
      return {k:c,label:L.landuse_labels[c]||c,v:d.lu[c].area,lots:d.lu[c].lots,units:d.lu[c].units};
    }).sort(function(a,b){return b.v-a.v;});
    $('lubars').innerHTML=bars(luRows,luTot,L.landuse_colors);
    var top=luRows[0], res=luRows.filter(function(r){return ['01','02','03','04'].indexOf(r.k)>-1;})
      .reduce(function(t,r){return t+r.v;},0);
    $('lunote').textContent='The largest single use is '+top.label.toLowerCase()+' at '+(top.v/luTot*100).toFixed(1)+
      '% of built lot area, across '+n(top.lots)+' lots. Residential uses of all kinds account for '+(res/luTot*100).toFixed(1)+
      '%. Shares are by lot area, so a few large parcels can outweigh many small ones.';
    $('lutbl').innerHTML='<tr><th>Land use</th><th>Lots</th><th>Share of area</th><th>Homes</th></tr>'+
      luRows.map(function(r){
        return '<tr><td>'+r.label+'</td><td>'+n(r.lots)+'</td><td>'+(r.v/luTot*100).toFixed(1)+'%</td><td>'+n(r.units)+'</td></tr>';
      }).join('');

    // zoning by family, then the individual districts
    var zTot=0; Object.keys(d.zfam).forEach(function(k){ zTot+=d.zfam[k].area; });
    var zRows=Object.keys(d.zfam).map(function(k){return {k:k,label:k,v:d.zfam[k].area,lots:d.zfam[k].lots};})
      .sort(function(a,b){return b.v-a.v;});
    $('zbars').innerHTML=bars(zRows,zTot,L.zone_family_colors);
    var zd=Object.keys(d.zone).map(function(z){return {z:z,a:d.zone[z].area,l:d.zone[z].lots};})
      .sort(function(a,b){return b.a-a.a;});
    $('ztbl').innerHTML='<tr><th>Zoning district</th><th>Lots</th><th>Share of area</th></tr>'+
      zd.slice(0,18).map(function(r){
        return '<tr><td>'+r.z+'</td><td>'+n(r.l)+'</td><td>'+(r.a/zTot*100).toFixed(1)+'%</td></tr>';
      }).join('');
    var manu=(d.zfam['Manufacturing']||{}).area||0;
    $('znote').textContent='The most common zoning district here is '+zd[0].z+', covering '+(zd[0].a/zTot*100).toFixed(1)+
      '% of zoned lot area across '+n(zd[0].l)+' lots'+
      (manu?'. Manufacturing zoning covers '+(manu/zTot*100).toFixed(1)+'% of the district':'')+
      '. R is residential, C commercial, M manufacturing; the number that follows sets how much can be built.';
    var zl=$('znote');
    if(zl) zl.innerHTML=zl.textContent+' <a href="/zoning" style="color:#0d1b4b;border-bottom:1px solid #f47920;text-decoration:none">See what each zoning district allows &rarr;</a>'+letterNote();
  }
  function helpers(){
    var sec=$('nprcsec'); if(!sec) return;
    var list=(D.nprc&&D.nprc.orgs||[]).filter(function(o){return o.cb===CODE;});
    if(!list.length){ sec.style.display='none'; return; }
    $('nprclist').innerHTML=list.map(function(o){
      var q=encodeURIComponent([o.addr,o.city,'NY',o.zip].filter(Boolean).join(', '));
      return '<div style="padding:11px 0;border-bottom:1px solid #f0ede8">'+
        '<div style="font-size:.86rem;font-weight:800">'+o.name+'</div>'+
        '<div style="font-size:.76rem;color:#444;margin-top:2px;line-height:1.5">'+[o.addr,o.city].filter(Boolean).join(', ')+' '+(o.zip||'')+'</div>'+
        (o.area?'<div style="font-family:DM Mono,monospace;font-size:.68rem;color:#6b6760;margin-top:3px">Serves '+o.area+'</div>':'')+
        '<div style="margin-top:7px"><a style="padding:6px 11px;background:#132D65;color:#fff;border-radius:7px;font-size:.72rem;font-weight:700;text-decoration:none" href="https://www.google.com/maps/dir/?api=1&destination='+q+'" target="_blank" rel="noopener">Directions</a></div></div>';
    }).join('')+'<div style="font-family:DM Mono,monospace;font-size:.64rem;color:#9ca3af;line-height:1.6;margin-top:10px">'+
      'State contracted nonprofits offering free housing help. <a href="/preservation" style="color:#0d1b4b">See all '+D.nprc.orgs.length+' citywide</a>.</div>';
  }
  function districtPicker(all){
    var keys=Object.keys(all).sort(function(a,b){
      var A=all[a],B=all[b];
      return A.boro===B.boro ? A.num-B.num : (A.boro<B.boro?-1:1);
    });
    var cur=null, html='';
    keys.forEach(function(k){
      var v=all[k];
      if(v.boro!==cur){ if(cur) html+='</optgroup>'; html+='<optgroup label="'+v.boro+'">'; cur=v.boro; }
      html+='<option value="'+k+'"'+(k===CODE?' selected':'')+'>'+v.boro+' CB'+v.num+'</option>';
    });
    html+='</optgroup>';
    $('pick').innerHTML=html;
    $('pick').addEventListener('change',function(){ location.href='/cd/'+this.value.toLowerCase()+'/'; });
  }

  document.querySelectorAll('[data-bed]').forEach(function(b){
    b.addEventListener('click',function(){
      mode=this.getAttribute('data-bed');
      document.querySelectorAll('[data-bed]').forEach(function(x){x.classList.toggle('on',x===b);});
      if(lens==='lu'||lens==='zn') return;
      draw();
    });
  });
  document.querySelectorAll('[data-lens]').forEach(function(b){
    b.addEventListener('click',function(){
      lens=this.getAttribute('data-lens');
      document.querySelectorAll('[data-lens]').forEach(function(x){x.classList.toggle('on',x===b);});
      var rentLens=(lens==='nb'||lens==='cc');
      document.getElementById('bedbar').style.display=rentLens?'':'none';
      draw();
    });
  });
  boot();
})();
