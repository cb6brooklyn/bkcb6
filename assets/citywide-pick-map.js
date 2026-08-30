/* Citywide search: pick any point on the map.
   Hover a lot to see its address, click it to see zoning and land use, then
   open the full address card. Shares colours and labels with the search card
   through window.__bkcbCardBits so the two can never disagree. */
(function(){
  'use strict';
  var TOKEN='HvFoIfzodzpRML7a1104Ca2tM';
  var NYC=[40.7128,-73.9860], MIN_HOVER_ZOOM=15;

  function bits(){ return window.__bkcbCardBits||{}; }
  function esc(v){return String(v==null?'':v).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
  function cleanLabel(l){return String(l||'').replace(/,\s*(NY|New York),?\s*(USA)?\s*$/i,'').trim();}

  var revCache={}, plutoCache={};
  function key(lat,lng){return lat.toFixed(5)+','+lng.toFixed(5);}

  async function getJson(url,ms){
    var ctrl=(typeof AbortController!=='undefined')?new AbortController():null;
    var t=ctrl?setTimeout(function(){ctrl.abort();},ms||7000):null;
    try{
      var r=await fetch(url,ctrl?{signal:ctrl.signal}:undefined);
      if(!r.ok) throw new Error('HTTP '+r.status);
      return await r.json();
    } finally { if(t) clearTimeout(t); }
  }

  async function reverse(lat,lng){
    var k=key(lat,lng);
    if(revCache[k]) return revCache[k];
    var d=await getJson('https://geosearch.planninglabs.nyc/v2/reverse?point.lat='+lat+'&point.lon='+lng+'&size=1');
    var f=(d&&d.features&&d.features[0])||null;
    if(!f) throw new Error('No address at that point');
    var p=f.properties||{};
    var out={label:cleanLabel(p.label),bbl:((p.addendum||{}).pad||{}).bbl||'',borough:p.borough||''};
    revCache[k]=out;
    return out;
  }

  async function plutoFor(bbl){
    if(!bbl) return {};
    if(plutoCache[bbl]) return plutoCache[bbl];
    var url='https://data.cityofnewyork.us/resource/64uk-42ks.json'
      + '?$where=bbl=%27'+encodeURIComponent(bbl)+'%27'
      + '&$select=address,borough,cd,landuse,zonedist1,ownername,yearbuilt,numfloors'
      + '&$$app_token='+TOKEN;
    var rows=await getJson(url);
    var row=(rows&&rows[0])||{};
    plutoCache[bbl]=row;
    return row;
  }

  function chip(label,value,bg,sub){
    var b=bits();
    var ink=(typeof b.heroInk==='function')?b.heroInk(bg||'#BAB8B6'):{fg:'#fff',sub:'rgba(255,255,255,.85)'};
    return '<div style="flex:1 1 160px;min-width:0;background:'+esc(bg||'#BAB8B6')+';border-radius:7px;padding:9px 11px">'
      + '<div style="font-family:\'DM Mono\',monospace;font-size:.58rem;text-transform:uppercase;letter-spacing:.1em;font-weight:700;color:'+ink.sub+'">'+esc(label)+'</div>'
      + '<div style="font-size:.95rem;font-weight:900;line-height:1.16;margin-top:2px;color:'+ink.fg+';word-break:normal;overflow-wrap:break-word">'+esc(value)+'</div>'
      + (sub?'<div style="font-family:\'DM Mono\',monospace;font-size:.62rem;margin-top:3px;color:'+ink.sub+'">'+esc(sub)+'</div>':'')
      + '</div>';
  }

  function panelHtml(info,row){
    var b=bits();
    var zone=String(row.zonedist1||'').trim();
    var zBg=(typeof b.zoneColor==='function'&&zone)?b.zoneColor(zone)[1]:'';
    var luName=(typeof b.landUseLabel==='function')?b.landUseLabel(row.landuse):'';
    var luBg=(typeof b.landUseColor==='function')?b.landUseColor(row.landuse):'';
    var ug=(typeof b.ugText==='function')?b.ugText(row.landuse):'';
    var ugShort=/ \u00b7 /.test(ug)?('use group '+ug.split(' \u00b7 ')[0]):'';
    var board=(typeof b.boardLabel==='function')?b.boardLabel(row.cd||''):'';
    var chips='';
    if(zone) chips+=chip('zoned',zone,zBg);
    if(luName) chips+=chip('land use',luName.replace(/\s*\(\d\d\)\s*$/,''),luBg,ugShort);
    var biz=(typeof b.bizBlock==='function')?b.bizBlock(info.label||''):'';
    return '<div style="font-size:1.05rem;font-weight:800;line-height:1.2">'+esc(info.label||'This location')+'</div>'
      + (board?'<div style="font-size:.82rem;font-weight:700;margin-top:2px">is in '+esc(board)+'</div>':'')
      + (chips?'<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:9px">'+chips+'</div>':'')
      + (biz?'<div style="margin-top:11px">'+biz+'</div>':'')
      + '<button type="button" data-cw-openfull style="margin-top:10px;border:0;border-radius:9px;background:#FD890E;color:#fff;font-family:inherit;font-weight:800;font-size:.82rem;padding:9px 14px;cursor:pointer">See the full card &rarr;</button>';
  }

  function openFull(address){
    var input=document.getElementById('citywide-borough-address-input');
    var btn=document.getElementById('citywide-borough-address-search-btn');
    if(!input||!btn) return;
    input.value=address;
    btn.click();
    var card=document.querySelector('.search-card');
    if(card){ try{ card.scrollIntoView({block:'start',behavior:'smooth'}); }catch(e){ card.scrollIntoView(); } }
  }

  function init(){
    var host=document.getElementById('cw-pick-map');
    var panel=document.getElementById('cw-pick-panel');
    if(!host||!panel||typeof L==='undefined'||host.dataset.ready==='true') return;
    host.dataset.ready='true';

    var map=L.map(host,{scrollWheelZoom:true}).setView(NYC,11);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png?key=cb1_2hyw_1_9cda1572a3817275ed412c0e',{
      maxZoom:19, attribution:'&copy; OpenStreetMap &copy; CARTO'
    }).addTo(map);

    var marker=null, hoverTimer=null, seq=0, lastAddress='';

    function bizIcon(address){
      var b=bits();
      var list=(typeof b.bizFor==='function')?b.bizFor(address||''):null;
      if(!list||!list.length) return null;
      var z=list[0];
      var iw=64, ih=Math.round(iw*(z.h/z.w));
      return L.divIcon({className:'',iconSize:[iw,ih+10],iconAnchor:[iw/2,ih+10],
        html:'<div style="text-align:center"><img src="'+z.src+'" alt="'+esc(z.name)+'" '+
          'style="width:'+iw+'px;height:'+ih+'px;display:block;background:'+(z.plate||'#fff')+';'+
          'border:2px solid #0d1b4b;border-radius:7px;box-shadow:0 2px 6px rgba(0,0,0,.28)">'+
          '<div style="width:0;height:0;margin:0 auto;border-left:6px solid transparent;'+
          'border-right:6px solid transparent;border-top:9px solid #0d1b4b"></div></div>'});
    }
    function dressMarker(address){
      if(!marker) return;
      var ic=bizIcon(address);
      if(ic) marker.setIcon(ic);
      else if(marker.setIcon) marker.setIcon(new L.Icon.Default());
    }

    var tip=L.tooltip({direction:'top',offset:[0,-6],className:'cw-pick-tip',opacity:.95});

    function setPanel(html,muted){
      panel.innerHTML=html;
      panel.style.color=muted?'#6b6760':'';
    }

    async function pick(lat,lng){
      var mine=++seq;
      setPanel('<div style="font-family:\'DM Mono\',monospace;font-size:.78rem">Reading that lot\u2026</div>',true);
      try{
        var info=await reverse(lat,lng);
        if(mine!==seq) return;
        var row=await plutoFor(info.bbl);
        if(mine!==seq) return;
        lastAddress=info.label||'';
        dressMarker(lastAddress);
        setPanel(panelHtml(info,row||{}));
      }catch(e){
        if(mine!==seq) return;
        setPanel('<div style="font-family:\'DM Mono\',monospace;font-size:.78rem">No lot found at that point. Try clicking on a building.</div>',true);
      }
    }

    map.on('click',function(ev){
      var lat=ev.latlng.lat, lng=ev.latlng.lng;
      if(marker) marker.setLatLng(ev.latlng);
      else marker=L.marker(ev.latlng).addTo(map);
      map.closeTooltip(tip);
      pick(lat,lng);
    });

    map.on('mousemove',function(ev){
      if(map.getZoom()<MIN_HOVER_ZOOM) return;
      if(hoverTimer) clearTimeout(hoverTimer);
      var ll=ev.latlng;
      hoverTimer=setTimeout(async function(){
        try{
          var info=await reverse(ll.lat,ll.lng);
          tip.setLatLng(ll).setContent(esc(info.label||'')).addTo(map);
        }catch(e){}
      },320);
    });
    map.on('mouseout',function(){ if(hoverTimer) clearTimeout(hoverTimer); map.closeTooltip(tip); });

    panel.addEventListener('click',function(ev){
      var b=ev.target&&ev.target.closest?ev.target.closest('[data-cw-openfull]'):null;
      if(!b||!lastAddress) return;
      openFull(lastAddress);
    });

    // Keep the map on whatever the address search just found.
    window.__bkcbPickMapGoTo=function(lat,lng,label){
      if(!Number.isFinite(lat)||!Number.isFinite(lng)) return;
      map.setView([lat,lng],17);
      if(marker) marker.setLatLng([lat,lng]);
      else marker=L.marker([lat,lng]).addTo(map);
      if(label) lastAddress=cleanLabel(label);
      pick(lat,lng);
    };

    setTimeout(function(){ map.invalidateSize(); },200);
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init);
  else init();
})();
