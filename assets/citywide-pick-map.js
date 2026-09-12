/* Citywide search: pick any point on the map.
   Community boards are drawn across the whole city with their seals (BKCB6 in
   its own colours with the CB6 logo). Council, Senate, Assembly and Congress
   overlays are off by default and toggle individually, each labelled with the
   elected official's logo from /elected/. Hover a lot to see its address, click
   it to see zoning and land use, then open the full address card. Shares
   colours and labels with the search card through window.__bkcbCardBits. */
(function(){
  'use strict';
  var TOKEN='HvFoIfzodzpRML7a1104Ca2tM';
  var NYC=[40.7128,-73.9860], MIN_HOVER_ZOOM=15;
  var CB6_NAVY='#0d1b4b', CB6_ORANGE='#f47920';
  var BORO_COLOR={1:'#0f766e',2:'#b45309',3:CB6_NAVY,4:'#7c3aed',5:'#be185d'};
  var BORO_PREFIX={1:'MN_',2:'BX_',3:'',4:'QN_',5:'SI_'};
  var BORO_ABBR={1:'MN',2:'BX',3:'BK',4:'QN',5:'SI'};

  var OVERLAYS={
    cc:{url:'data/council-districts.geojson',key:'cc',color:'#0f766e',office:'Council District',lookup:'_councilLookup',logo:function(n){return 'elected/CD'+n+'.png';}},
    sd:{url:'data/senate-districts.geojson',key:'sd',color:'#7c3aed',office:'Senate District',lookup:'_senateLookup',logo:function(n){return 'elected/SD'+n+'.png';}},
    ad:{url:'data/assembly-districts.geojson',key:'ad',color:'#65a30d',office:'Assembly District',lookup:'_assemblyLookup',logo:function(n){return 'elected/AD'+n+'.png';}},
    cg:{url:'data/congress-districts-simple.geojson',key:'cong_dist',color:'#b91c1c',office:'NY-',lookup:'_congressLookup',logo:function(n){var s=CONGRESS_SLUG[n];return s?('elected/'+s+'.png'):'';}}
  };
  var CONGRESS_SLUG={3:'suozzi',5:'meeks',6:'meng',7:'velazquez',8:'jeffries',9:'clarke',10:'goldman',11:'malliotakis',12:'nadler',13:'espaillat',14:'aoc',15:'torres',16:'latimer'};

  window._councilLookup={1:["Christopher Marte","https://council.nyc.gov/district-1/"],2:["Harvey Epstein","https://council.nyc.gov/district-2/"],3:["Carl Wilson","https://council.nyc.gov/district-3/"],4:["Virginia Maloney","https://council.nyc.gov/district-4/"],5:["Julie Menin","https://council.nyc.gov/district-5/"],6:["Gale A. Brewer","https://council.nyc.gov/district-6/"],7:["Shaun Abreu","https://council.nyc.gov/district-7/"],8:["Elsie Encarnacion","https://council.nyc.gov/district-8/"],9:["Yusef Salaam","https://council.nyc.gov/district-9/"],10:["Carmen De La Rosa","https://council.nyc.gov/district-10/"],11:["Eric Dinowitz","https://council.nyc.gov/district-11/"],12:["Kevin C. Riley","https://council.nyc.gov/district-12/"],13:["Shirley Aldebol","https://council.nyc.gov/district-13/"],14:["Pierina Ana Sanchez","https://council.nyc.gov/district-14/"],15:["Oswald Feliz","https://council.nyc.gov/district-15/"],16:["Althea Stevens","https://council.nyc.gov/district-16/"],17:["Justin Sanchez","https://council.nyc.gov/district-17/"],18:["Amanda Farías","https://council.nyc.gov/district-18/"],19:["Vickie Paladino","https://council.nyc.gov/district-19/"],20:["Sandra Ung","https://council.nyc.gov/district-20/"],21:["Shanel Thomas-Henry","https://council.nyc.gov/district-21/"],22:["Tiffany Cabán","https://council.nyc.gov/district-22/"],23:["Linda Lee","https://council.nyc.gov/district-23/"],24:["James F. Gennaro","https://council.nyc.gov/district-24/"],25:["Shekar Krishnan","https://council.nyc.gov/district-25/"],26:["Julie Won","https://council.nyc.gov/district-26/"],27:["Nantasha Williams","https://council.nyc.gov/district-27/"],28:["Tyrell Hankerson","https://council.nyc.gov/district-28/"],29:["Lynn Schulman","https://council.nyc.gov/district-29/"],30:["Phil Wong","https://council.nyc.gov/district-30/"],31:["Selvena Brooks-Powers","https://council.nyc.gov/district-31/"],32:["Joann Ariola","https://council.nyc.gov/district-32/"],33:["Lincoln Restler","https://council.nyc.gov/district-33/"],34:["Jennifer Gutiérrez","https://council.nyc.gov/district-34/"],35:["Crystal Hudson","https://council.nyc.gov/district-35/"],36:["Chi Ossé","https://council.nyc.gov/district-36/"],37:["Sandy Nurse","https://council.nyc.gov/district-37/"],38:["Alexa Avilés","https://council.nyc.gov/district-38/"],39:["Shahana Hanif","https://council.nyc.gov/district-39/"],40:["Rita Joseph","https://council.nyc.gov/district-40/"],41:["Darlene Mealy","https://council.nyc.gov/district-41/"],42:["Chris Banks","https://council.nyc.gov/district-42/"],43:["Susan Zhuang","https://council.nyc.gov/district-43/"],44:["Simcha Felder","https://council.nyc.gov/district-44/"],45:["Farah N. Louis","https://council.nyc.gov/district-45/"],46:["Mercedes Narcisse","https://council.nyc.gov/district-46/"],47:["Kayla Santosuosso","https://council.nyc.gov/district-47/"],48:["Inna Vernikov","https://council.nyc.gov/district-48/"],49:["Kamillah Hanks","https://council.nyc.gov/district-49/"],50:["David Carr","https://council.nyc.gov/district-50/"],51:["Frank Morano","https://council.nyc.gov/district-51/"]};
  window._assemblyLookup={23:["Stacey Pheffer Amato","https://nyassembly.gov/mem/Stacey-Pheffer-Amato"],24:["David I. Weprin","https://nyassembly.gov/mem/David-I-Weprin"],25:["Nily Rozic","https://nyassembly.gov/mem/Nily-Rozic"],26:["Edward C. Braunstein","https://nyassembly.gov/mem/Edward-C-Braunstein"],27:["Sam Berger","https://nyassembly.gov/mem/Sam-Berger"],28:["Andrew Hevesi","https://nyassembly.gov/mem/Andrew-Hevesi"],29:["Alicia Hyndman","https://nyassembly.gov/mem/Alicia-Hyndman"],30:["Steven Raga","https://nyassembly.gov/mem/Steven-Raga"],31:["Khaleel M. Anderson","https://nyassembly.gov/mem/Khaleel-M-Anderson"],32:["Vivian E. Cook","https://nyassembly.gov/mem/Vivian-E-Cook"],33:["Clyde Vanel","https://nyassembly.gov/mem/Clyde-Vanel"],34:["Jessica González-Rojas","https://nyassembly.gov/mem/Jessica-Gonzalez-Rojas"],35:["Larinda C. Hooks","https://nyassembly.gov/mem/Larinda-C-Hooks"],36:["Diana C. Moreno","https://nyassembly.gov/mem/Diana-C-Moreno"],37:["Claire Valdez","https://nyassembly.gov/mem/Claire-Valdez"],38:["Jenifer Rajkumar","https://nyassembly.gov/mem/Jenifer-Rajkumar"],39:["Catalina Cruz","https://nyassembly.gov/mem/Catalina-Cruz"],40:["Ron Kim","https://nyassembly.gov/mem/Ron-Kim"],41:["Kalman Yeger","https://nyassembly.gov/mem/Kalman-Yeger"],42:["Rodneyse Bichotte Hermelyn","https://nyassembly.gov/mem/Rodneyse-Bichotte-Hermelyn"],43:["Brian Cunningham","https://nyassembly.gov/mem/Brian-Cunningham"],44:["Robert C. Carroll","https://nyassembly.gov/mem/Robert-C-Carroll"],45:["Michael Novakhov","https://nyassembly.gov/mem/Michael-Novakhov"],46:["Alec Brook-Krasny","https://nyassembly.gov/mem/Alec-Brook-Krasny"],47:["William Colton","https://nyassembly.gov/mem/William-Colton"],48:["Simcha Eichenstein","https://nyassembly.gov/mem/Simcha-Eichenstein"],49:["Lester Chang","https://nyassembly.gov/mem/Lester-Chang"],50:["Emily Gallagher","https://nyassembly.gov/mem/Emily-Gallagher"],51:["Marcela Mitaynes","https://nyassembly.gov/mem/Marcela-Mitaynes"],52:["Jo Anne Simon","https://nyassembly.gov/mem/Jo-Anne-Simon"],53:["Maritza Davila","https://nyassembly.gov/mem/Maritza-Davila"],54:["Erik M. Dilan","https://nyassembly.gov/mem/Erik-M-Dilan"],55:["Latrice M. Walker","https://nyassembly.gov/mem/Latrice-M-Walker"],56:["Stefani Zinerman","https://nyassembly.gov/mem/Stefani-Zinerman"],57:["Phara Souffrant Forrest","https://nyassembly.gov/mem/Phara-Souffrant-Forrest"],58:["Monique Chandler-Waterman","https://nyassembly.gov/mem/Monique-Chandler-Waterman"],59:["Jaime R. Williams","https://nyassembly.gov/mem/Jaime-R-Williams"],60:["Nikki Lucas","https://nyassembly.gov/mem/Nikki-Lucas"],61:["Charles D. Fall","https://nyassembly.gov/mem/Charles-D-Fall"],62:["Michael Reilly","https://nyassembly.gov/mem/Michael-Reilly"],63:["Sam Pirozzolo","https://nyassembly.gov/mem/Sam-Pirozzolo"],64:["Michael Tannousis","https://nyassembly.gov/mem/Michael-Tannousis"],65:["Grace Lee","https://nyassembly.gov/mem/Grace-Lee"],66:["Deborah J. Glick","https://nyassembly.gov/mem/Deborah-J-Glick"],67:["Linda B. Rosenthal","https://nyassembly.gov/mem/Linda-B-Rosenthal"],68:["Edward Gibbs","https://nyassembly.gov/mem/Edward-Gibbs"],69:["Micah C. Lasher","https://nyassembly.gov/mem/Micah-C-Lasher"],70:["Jordan J.G. Wright","https://nyassembly.gov/mem/Jordan-J.G-Wright"],71:["Al Taylor","https://nyassembly.gov/mem/Al-Taylor"],72:["Manny De Los Santos","https://nyassembly.gov/mem/Manny-De-Los-Santos"],73:["Alex Bores","https://nyassembly.gov/mem/Alex-Bores"],74:["Keith Powers","https://nyassembly.gov/mem/Keith-Powers"],75:["Tony Simone","https://nyassembly.gov/mem/Tony-Simone"],76:["Rebecca A. Seawright","https://nyassembly.gov/mem/Rebecca-A-Seawright"],77:["Landon C. Dais","https://nyassembly.gov/mem/Landon-C-Dais"],78:["George Alvarez","https://nyassembly.gov/mem/George-Alvarez"],79:["Chantel Jackson","https://nyassembly.gov/mem/Chantel-Jackson"],80:["John Zaccaro, Jr.","https://nyassembly.gov/mem/John-Zaccaro-Jr"],81:["Jeffrey Dinowitz","https://nyassembly.gov/mem/Jeffrey-Dinowitz"],82:["Michael Benedetto","https://nyassembly.gov/mem/Michael-Benedetto"],83:["Carl E. Heastie","https://nyassembly.gov/mem/Carl-E-Heastie"],84:["Amanda Septimo","https://nyassembly.gov/mem/Amanda-Septimo"],85:["Emérita Torres","https://nyassembly.gov/mem/Emerita-Torres"],86:["Yudelka Tapia","https://nyassembly.gov/mem/Yudelka-Tapia"],87:["Karines Reyes","https://nyassembly.gov/mem/Karines-Reyes"]};
  window._senateLookup={10:["James Sanders Jr.","https://www.nysenate.gov/senators/james-sanders-jr"],11:["Toby Ann Stavisky","https://www.nysenate.gov/senators/toby-ann-stavisky"],12:["Michael Gianaris","https://www.nysenate.gov/senators/michael-gianaris"],13:["Jessica Ramos","https://www.nysenate.gov/senators/jessica-ramos"],14:["Leroy Comrie","https://www.nysenate.gov/senators/leroy-comrie"],15:["Joseph P. Addabbo Jr.","https://www.nysenate.gov/senators/joseph-p-addabbo-jr"],16:["John C. Liu","https://www.nysenate.gov/senators/john-c-liu"],17:["Stephen T. Chan","https://www.nysenate.gov/senators/stephen-t-chan"],18:["Julia Salazar","https://www.nysenate.gov/senators/julia-salazar"],19:["Roxanne J. Persaud","https://www.nysenate.gov/senators/roxanne-j-persaud"],20:["Zellnor Myrie","https://www.nysenate.gov/senators/zellnor-myrie"],21:["Kevin S. Parker","https://www.nysenate.gov/senators/kevin-s-parker"],22:["Sam Sutton","https://www.nysenate.gov/senators/sam-sutton"],23:["Jessica Scarcella-Spanton","https://www.nysenate.gov/senators/jessica-scarcella-spanton"],24:["Andrew J. Lanza","https://www.nysenate.gov/senators/andrew-j-lanza"],25:["Jabari Brisport","https://www.nysenate.gov/senators/jabari-brisport"],26:["Andrew Gounardes","https://www.nysenate.gov/senators/andrew-gounardes"],27:["Brian Kavanagh","https://www.nysenate.gov/senators/brian-kavanagh"],28:["Liz Krueger","https://www.nysenate.gov/senators/liz-krueger"],29:["Jose M. Serrano","https://www.nysenate.gov/senators/jose-m-serrano"],30:["Cordell Cleare","https://www.nysenate.gov/senators/cordell-cleare"],31:["Robert Jackson","https://www.nysenate.gov/senators/robert-jackson"],32:["Luis R. Sepúlveda","https://www.nysenate.gov/senators/luis-r-sepulveda"],33:["Gustavo Rivera","https://www.nysenate.gov/senators/gustavo-rivera"],34:["Nathalia Fernandez","https://www.nysenate.gov/senators/nathalia-fernandez"],36:["Jamaal Bailey","https://www.nysenate.gov/senators/jamaal-t-bailey"],47:["Erik Bottcher","https://www.nysenate.gov/senators/erik-bottcher"],59:["Kristen Gonzalez","https://www.nysenate.gov/senators/kristen-gonzalez"]};
  window._congressLookup={3:["Tom Suozzi","https://suozzi.house.gov"],5:["Gregory Meeks","https://meeks.house.gov"],6:["Grace Meng","https://meng.house.gov"],7:["Nydia Velázquez","https://velazquez.house.gov"],8:["Hakeem Jeffries","https://jeffries.house.gov"],9:["Yvette Clarke","https://clarke.house.gov"],10:["Dan Goldman","https://goldman.house.gov"],11:["Nicole Malliotakis","https://malliotakis.house.gov"],12:["Jerry Nadler","https://nadler.house.gov"],13:["Adriano Espaillat","https://espaillat.house.gov"],14:["Alexandria Ocasio-Cortez","https://ocasio-cortez.house.gov"],15:["Ritchie Torres","https://torres.house.gov"],16:["George Latimer","https://latimer.house.gov"]};

  function bits(){ return window.__bkcbCardBits||{}; }
  function esc(v){return String(v==null?'':v).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
  function cleanLabel(l){return String(l||'').replace(/,\s*(NY|New York),?\s*(USA)?\s*$/i,'').trim();}
  function boardCode(cd){cd=String(cd||''); var b=parseInt(cd.charAt(0),10), n=parseInt(cd.slice(1),10); return (BORO_ABBR[b]||'')+'CB'+n;}
  function boardSeal(cd){cd=String(cd||''); var b=parseInt(cd.charAt(0),10), n=parseInt(cd.slice(1),10); if(cd==='306') return 'cb6-logo-square.png'; return 'elected/'+(BORO_PREFIX[b]||'')+'CB'+n+'_540.png';}
  function isJointInterest(cd){ var n=parseInt(String(cd).slice(1),10); return n>18; }
  function boardHref(cd){cd=String(cd||''); var b=parseInt(cd.charAt(0),10), n=parseInt(cd.slice(1),10); if(!BORO_ABBR[b]||isJointInterest(cd)) return ''; return 'cb-'+BORO_ABBR[b].toLowerCase()+'-'+n+'.html';}

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
    if(!input||!btn){
      var card=document.querySelector('[data-full-profile-search]');
      if(card){
        input=input||card.querySelector('[data-full-profile-input]');
        btn=btn||card.querySelector('[data-full-profile-button]');
      }
    }
    if(!input||!btn) return;
    input.value=address;
    btn.click();
  }

  function init(){
    var host=document.getElementById('cw-pick-map');
    var panel=document.getElementById('cw-pick-panel');
    if(!host||!panel||typeof L==='undefined'||host.dataset.ready==='true') return;
    host.dataset.ready='true';

    var startCenter=NYC, startZoom=11;
    var cAttr=(host.getAttribute('data-center')||'').split(',');
    if(cAttr.length===2){
      var cLat=parseFloat(cAttr[0]), cLng=parseFloat(cAttr[1]);
      if(isFinite(cLat)&&isFinite(cLng)) startCenter=[cLat,cLng];
    }
    var zAttr=parseFloat(host.getAttribute('data-zoom'));
    if(isFinite(zAttr)) startZoom=zAttr;
    var map=L.map(host,{scrollWheelZoom:true,zoomSnap:0.25}).setView(startCenter,startZoom);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png?key=cb1_2hyw_1_9cda1572a3817275ed412c0e',{
      maxZoom:19, attribution:'&copy; OpenStreetMap &copy; CARTO'
    }).addTo(map);

    var labelPts=null;
    var labelsReady=getJson('data/citywide-search-labels.json').then(function(d){ labelPts=d||{}; }).catch(function(){ labelPts={}; });

    /* ---------- community boards (on by default) ---------- */
    var cdLayer=L.layerGroup(), cdSeals=L.layerGroup();
    var SEAL_MIN_ZOOM=12, LOGO_MIN_ZOOM=12;
    function sealSize(){ var z=map.getZoom(); return z<12.5?24:z<13.5?32:z<14.5?40:46; }
    var pinned=false;
    function cdStyle(f){
      var cd=String(f.properties.cd||''), b=parseInt(cd.charAt(0),10);
      if(cd==='306') return {color:CB6_NAVY,weight:2.4,fillColor:CB6_ORANGE,fillOpacity:.10,interactive:false};
      var c=BORO_COLOR[b]||'#475569';
      if(isJointInterest(cd)) return {color:c,weight:.8,dashArray:'4,4',fillColor:c,fillOpacity:.02,interactive:false};
      return {color:c,weight:1.2,fillColor:c,fillOpacity:.03,interactive:false};
    }
    function sealIcon(cd){
      var s=sealSize(), code=boardCode(cd), isCB6=cd==='306';
      var pt=labelPts&&labelPts.cd&&labelPts.cd[cd];
      var wide=cd.charAt(0)==='5', showLabel=map.getZoom()>=13;
      return L.divIcon({className:'cw-seal-wrap',iconSize:[s,s+18],iconAnchor:[s/2,(s+18)/2],
        html:'<div class="cw-seal'+(isCB6?' cb6':'')+(wide?' wide':'')+'" style="--w:'+s+'px"><img src="'+boardSeal(cd)+'" alt="'+esc(code)+'" loading="lazy" onerror="this.style.display=\'none\'">'
          + (showLabel?'<b>'+esc(code)+'</b>':'')+'</div>'});
    }
    function drawSeals(){
      cdSeals.clearLayers();
      if(!labelPts||!labelPts.cd||!map.hasLayer(cdLayer)||map.getZoom()<SEAL_MIN_ZOOM) return;
      Object.keys(labelPts.cd).forEach(function(cd){
        if(isJointInterest(cd)) return;
        var ll=labelPts.cd[cd];
        var m=L.marker([ll[0],ll[1]],{icon:sealIcon(cd),interactive:true,keyboard:false,zIndexOffset:cd==='306'?500:0});
        var href=boardHref(cd);
        m.bindTooltip(esc(boardCode(cd)),{direction:'top',offset:[0,-sealSize()/2-6],className:'cw-pick-tip'});
        if(href) m.on('click',function(){ window.location.href=href; });
        cdSeals.addLayer(m);
      });
    }
    getJson('cd-boundaries-simple.geojson').then(function(d){
      var gj=L.geoJSON(d,{style:cdStyle,interactive:false}).addTo(cdLayer);
      cdLayer.addTo(map); cdSeals.addTo(map);
      if(!pinned&&!host.getAttribute('data-center')){ try{ map.fitBounds(gj.getBounds(),{padding:[4,4]}); }catch(e){} }
      labelsReady.then(drawSeals);
    }).catch(function(e){ console.error('community boards',e); });

    /* ---------- legislative overlays (off by default) ---------- */
    var ov={};
    function officeLabel(t,n){ var o=OVERLAYS[t]; return t==='cg'?('NY-'+n):(o.office+' '+n); }
    function logoIcon(t,n){
      var o=OVERLAYS[t], url=o.logo(n), rep=(window[o.lookup]||{})[n], name=rep?rep[0]:'';
      return L.divIcon({className:'cw-elogo-wrap',iconSize:null,
        html:'<div class="cw-elogo" style="--elc:'+o.color+'">'
          + (url?'<img src="'+url+'" alt="'+esc(name||officeLabel(t,n))+'" loading="lazy" onerror="this.style.display=\'none\'">':'')
          + (name?'<b>'+esc(name)+'</b>':'')
          + '<em>'+esc(officeLabel(t,n))+'</em></div>'});
    }
    var ovLogos={};
    function drawOverlayLogos(t){
      var g=ovLogos[t], d=ovData[t], o=OVERLAYS[t]; if(!g||!d) return;
      g.clearLayers();
      if(!ov[t]||!map.hasLayer(ov[t])||map.getZoom()<LOGO_MIN_ZOOM) return;
      var pts=(labelPts||{})[t]||{};
      (d.features||[]).forEach(function(f){
        var n=parseInt(f.properties[o.key],10); if(!isFinite(n)) return;
        var ll=pts[String(n)]; if(!ll) return;
        var rep=(window[o.lookup]||{})[n], href=rep&&rep[1]?rep[1]:'';
        var m=L.marker([ll[0],ll[1]],{icon:logoIcon(t,n),interactive:!!href,keyboard:false});
        if(href) m.on('click',function(){ window.open(href,'_blank','noopener'); });
        g.addLayer(m);
      });
    }
    var ovData={};
    function buildOverlay(t,d){
      var o=OVERLAYS[t], g=L.layerGroup();
      ovData[t]=d;
      L.geoJSON(d,{interactive:false,style:function(){ return {color:o.color,weight:1.8,fillColor:o.color,fillOpacity:.04,dashArray:'6,4',interactive:false}; }}).addTo(g);
      ovLogos[t]=L.layerGroup().addTo(g);
      return g;
    }
    function setOverlay(t,on){
      var o=OVERLAYS[t]; if(!o) return;
      if(!on){ if(ov[t]) map.removeLayer(ov[t]); return; }
      if(ov[t]){ ov[t].addTo(map); drawOverlayLogos(t); return; }
      labelsReady.then(function(){ return getJson(o.url,15000); }).then(function(d){
        ov[t]=buildOverlay(t,d);
        var cb=document.querySelector('[data-cw-overlay="'+t+'"]');
        if(cb&&cb.checked){ ov[t].addTo(map); drawOverlayLogos(t); }
      }).catch(function(e){ console.error('overlay',t,e); });
    }
    document.querySelectorAll('[data-cw-overlay]').forEach(function(cb){
      cb.addEventListener('change',function(){
        var t=cb.getAttribute('data-cw-overlay');
        if(t==='cd'){ if(cb.checked){ cdLayer.addTo(map); cdSeals.addTo(map); drawSeals(); } else { map.removeLayer(cdLayer); map.removeLayer(cdSeals); } return; }
        setOverlay(t,cb.checked);
      });
    });
    map.on('zoomend',function(){ drawSeals(); Object.keys(ovLogos).forEach(drawOverlayLogos); });

    /* ---------- lot picking ---------- */
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
      else marker=L.marker(ev.latlng,{zIndexOffset:1000}).addTo(map);
      map.closeTooltip(tip);
      pick(lat,lng);
      try{ panel.scrollIntoView({block:'nearest',behavior:'smooth'}); }catch(e){}
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
      pinned=true;
      map.setView([lat,lng],17);
      if(marker) marker.setLatLng([lat,lng]);
      else marker=L.marker([lat,lng],{zIndexOffset:1000}).addTo(map);
      if(label) lastAddress=cleanLabel(label);
      pick(lat,lng);
    };

    setTimeout(function(){ map.invalidateSize(); },200);
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init);
  else init();
})();
