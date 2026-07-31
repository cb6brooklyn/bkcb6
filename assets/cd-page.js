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
  var lens='nb';       // nb | cc
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
  function draw(){ if(lens==='nb') drawNb(); else drawCc(); }

  function boot(){
    map=L.map('map',{scrollWheelZoom:true}).setView([40.68,-73.97],12);
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
      fetch('/data/housing-jobs.json').then(function(r){return r.json();}).catch(function(){return null;})
    ]).then(function(a){
      D.look=a[0][CODE]; D.nbgeo=a[1]; D.ccgeo=a[2]; D.cc=a[3]; D.inv=a[4];
      D.cdgeo=a[5]; D.hdb=a[6]; D.hpd=a[7]; D.jobs=a[8];
      if(!D.look){ $('bnote').textContent='District not found.'; return; }
      header(); outline(); kpis();
      if(!D.look.se.length){
        lens='cc';
        document.querySelectorAll('[data-lens]').forEach(function(x){ x.classList.toggle('on', x.getAttribute('data-lens')==='cc'); });
        var nb=document.querySelector('[data-lens="nb"]');
        if(nb){ nb.disabled=true; nb.title='StreetEasy publishes no neighborhood rents here'; }
      }
      draw(); housing(); table(); districtPicker(a[0]);
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
      draw();
    });
  });
  document.querySelectorAll('[data-lens]').forEach(function(b){
    b.addEventListener('click',function(){
      lens=this.getAttribute('data-lens');
      document.querySelectorAll('[data-lens]').forEach(function(x){x.classList.toggle('on',x===b);});
      draw();
    });
  });
  boot();
})();
