(function(){
  'use strict';
  if (window.__bkcbCitywideFullProfileLoaded) return;
  window.__bkcbCitywideFullProfileLoaded = true;

  var BOROUGH_NAMES = {'1':'Manhattan','2':'Bronx','3':'Brooklyn','4':'Queens','5':'Staten Island'};
  var BOROUGH_SHORT = {'1':'mn','2':'bx','3':'bk','4':'qn','5':'si'};
  var BOROUGH_KEY = {'1':'manhattan','2':'bronx','3':'brooklyn','4':'queens','5':'statenisland'};
  var LAND_USE_LABELS = {
    '01':'One & Two Family Buildings','02':'Multi-Family Walk-Up Buildings','03':'Multi-Family Elevator Buildings','04':'Mixed Residential & Commercial Buildings','05':'Commercial & Office Buildings','06':'Industrial & Manufacturing','07':'Transportation & Utility','08':'Public Facilities & Institutions','09':'Open Space & Outdoor Recreation','10':'Parking Facilities','11':'Vacant Land'
  };

  var SPECIAL_DISTRICTS = {
    'G':'Gowanus','SG':'Gowanus Mixed Use','SRD':'Transit Land Use','OP':'Ocean Parkway','BR':'Bay Ridge','HS':'Hillsides Preservation','DJ':'Downtown Jamaica','LIC':'Long Island City','MiD':'Midtown','CL':'Clinton','DB':'Downtown Brooklyn','EHC':'East Harlem Corridors','LM':'Lower Manhattan','LI':'Limited Industrial','TMU':'Tribeca Mixed Use','HP':'Hunters Point Mixed Use','125th':'125th Street','HY':'Hudson Yards','ETC':'Enhanced Commercial','WCh':'West Chelsea','CI':'Coney Island','SB':'Sheepshead Bay','FH':'Forest Hills','HSQ':'Hudson Square','US':'Union Square','BPC':'Battery Park City','HRP':'Hudson River Park','TMD':'Theater','WP':'Willets Point'
  };
  function specialDistrictName(code){var c=String(code||'').trim().toUpperCase(); if(!c||/^(NA|N\/A|NONE|0)$/.test(c)) return ''; var key=Object.keys(SPECIAL_DISTRICTS).filter(function(k){return k.toUpperCase()===c;})[0]; if(key) return SPECIAL_DISTRICTS[key]+' ('+key+')'; if(/^MX/.test(c)) return 'Mixed Use ('+c+')'; return c;}
  function collectSpecialDistricts(p){var out=[]; ['spdist1','spdist2','spdist3'].forEach(function(k){var n=specialDistrictName(p&&p[k]); if(n && out.indexOf(n)===-1) out.push(n);}); return out;}
  // Plain-language explanation of what a special purpose district does. Codes verified against PLUTO; text grounded in the NYC Zoning Resolution / DCP.
  var SPECIAL_DISTRICT_EXPLAIN={
    'G':'The Special Gowanus Mixed Use District was created by the 2021 Gowanus rezoning. It pairs residential and light-manufacturing (M1) districts so housing and industry can sit side by side, and is organized into five subdistricts with their own rules. It layers in Mandatory Inclusionary Housing in mapped areas, treats blocks along the Gowanus Canal as waterfront subject to a Waterfront Access Plan, and adds environmental, ground-floor, and streetscape requirements on top of the base zoning.',
    'SG':'The Special Gowanus Mixed Use District was created by the 2021 Gowanus rezoning. It pairs residential and light-manufacturing (M1) districts so housing and industry can sit side by side, and is organized into five subdistricts with their own rules. It layers in Mandatory Inclusionary Housing in mapped areas, treats blocks along the Gowanus Canal as waterfront subject to a Waterfront Access Plan, and adds environmental, ground-floor, and streetscape requirements on top of the base zoning.'
  };
  function specialDistrictExplain(spDisp,codes){
    var keys=(codes||[]).map(function(c){return String(c||'').toUpperCase();});
    for(var i=0;i<keys.length;i++){ if(SPECIAL_DISTRICT_EXPLAIN[keys[i]]) return SPECIAL_DISTRICT_EXPLAIN[keys[i]]; }
    return 'This lot is in the '+spDisp+' special purpose district. Special purpose districts are created by the City Planning Commission to meet specific planning and urban-design goals in a defined area, and their rules modify, supplement, or override the underlying zoning, with the special-district rules controlling where they conflict.';
  }



  function esc(v){return String(v == null ? '' : v).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
  function validCommunityBoardCode(cd){cd=String(cd||''); var b=cd.charAt(0), n=parseInt(cd.slice(1),10); return !!(BOROUGH_NAMES[b] && n >= 1 && ((b==='1'&&n<=12)||(b==='2'&&n<=12)||(b==='3'&&n<=18)||(b==='4'&&n<=14)||(b==='5'&&n<=3)));}
  function boardLabel(cd){cd=String(cd||''); var b=cd.charAt(0), n=parseInt(cd.slice(1),10); return validCommunityBoardCode(cd) ? BOROUGH_NAMES[b] + ' Community Board ' + n : 'Community Board';}
  function boardSlug(cd){cd=String(cd||''); if(!validCommunityBoardCode(cd)) return ''; return 'cb-' + BOROUGH_SHORT[cd.charAt(0)] + '-' + parseInt(cd.slice(1),10) + '.html';}
  function districtNumber(value){var m=String(value||'').match(/\d+/); return m ? String(parseInt(m[0],10)) : '';}
  function normalizeBbl(value){var d=String(value||'').replace(/\D/g,''); if(d.length>10) d=d.slice(0,10); return d.length===10 ? d : '';}
  function addressValue(obj,names){obj=obj||{}; for(var i=0;i<names.length;i++){var v=obj[names[i]]; if(v!==undefined&&v!==null&&String(v).trim()!=='') return v;} return '';}
  function hasReal(value){var s=String(value==null?'':value).trim(); return !!(s && s!=='—' && !/^not available( from pluto)?$/i.test(s));}
  function mini(label,value){return '<div style="background:#fff;border:1px solid #d1fae5;border-radius:6px;padding:7px 9px"><div style="font-size:.62rem;font-family:\'DM Mono\',monospace;text-transform:uppercase;letter-spacing:.06em;color:var(--muted,#6b6760);margin-bottom:2px">'+esc(label)+'</div><div style="font-size:.8rem;font-weight:800;color:var(--navy,#0d1b4b)">'+esc(value || '—')+'</div></div>';}
  function propertyMini(label,value){return hasReal(value)?mini(label,value):'';}
  function fmtNum(value,suffix){var raw=String(value==null?'':value).replace(/,/g,'').trim(); if(!raw) return '—'; var n=Number(raw); return Number.isFinite(n) ? n.toLocaleString() + (suffix||'') : String(value) + (suffix||'');}
  function landUseLabel(code){var key=String(code||'').trim().padStart(2,'0'); return LAND_USE_LABELS[key] ? LAND_USE_LABELS[key] + ' (' + key + ')' : (key && key !== '00' ? 'Land use code ' + key : 'Not available from PLUTO');}
  function landUsePlain(code,label){var key=String(code||'').trim().padStart(2,'0'); var notes={'01':'Low-density residential lots, typically one- and two-family homes.','02':'Walk-up apartment buildings, typically smaller multifamily housing.','03':'Elevator apartment buildings, typically larger multifamily housing.','04':'Mixed-use buildings combining residential units with stores, offices, or other commercial uses.','05':'Commercial or office buildings.','06':'Industrial, warehouse, or manufacturing uses.','07':'Transportation or utility infrastructure.','08':'Public facilities and institutions such as schools, hospitals, houses of worship, or government uses.','09':'Open space or outdoor recreation, including parks and playgrounds.','10':'Parking facilities.','11':'Vacant land.'}; return notes[key] || (label ? label + '.' : 'Land-use detail was not available from PLUTO.');}
  function zoningPlain(z){z=String(z||'').trim().toUpperCase(); if(!z) return ''; if(/^R/.test(z)) return z+' is a residence district. The number generally indicates permitted density and building form; suffixes refine bulk, height, parking, or contextual rules.'; if(/^C/.test(z)) return z+' is a commercial district. It generally permits retail, office, service, or mixed commercial activity depending on district and overlays.'; if(/^M/.test(z)) return z+' is a manufacturing district. It generally permits industrial, warehouse, production, or certain commercial uses depending on performance standards.'; if(/^PARK$/i.test(z)) return 'Mapped parkland or open-space zoning context.'; return z+' is a mapped zoning district. Check ZoLa for exact controls, overlays, and special district rules.';}
  function addZone(items,v){var z=String(v||'').trim().toUpperCase(); if(z && !/^(NA|N\/A|NONE|0)$/.test(z) && items.indexOf(z)===-1) items.push(z);}
  function collectZones(a,p){var items=[]; ['zonedist1','zonedist2','zonedist3','zonedist4'].forEach(function(k){addZone(items,p&&p[k]);}); ['zoningDistrict1','zoningDistrict2','zoningDistrict3','zoningDistrict4'].forEach(function(k){addZone(items,a&&a[k]);}); return items;}
  function knownBoroughName(v){var s=String(v||'').toLowerCase().replace(/[^a-z]/g,''); var map={manhattan:'Manhattan',newyork:'Manhattan',ny:'Manhattan',brooklyn:'Brooklyn',kings:'Brooklyn',bronx:'Bronx',queens:'Queens',statenisland:'Staten Island',richmond:'Staten Island'}; return map[s]||'';}
  function parseAddress(q, fallbackBorough){q=String(q||'').trim().replace(/,\s*(NY|New York)\s*$/i,''); var parts=q.split(',').map(function(p){return p.trim();}).filter(Boolean); var street=parts[0]||q; var borough=knownBoroughName(parts[1])||knownBoroughName(fallbackBorough); if(!borough){var tail=street.match(/\s+(Manhattan|Brooklyn|Bronx|Queens|Staten\s+Island|New\s+York|NY)$/i); if(tail){borough=knownBoroughName(tail[1]); street=street.slice(0,tail.index).trim();}} var m=street.match(/^(\d[\dA-Za-z-]*)\s+(.+)$/); if(!m) throw new Error('Enter a street address with a house number, such as 250 Baltic Street.'); return {houseNumber:m[1], street:m[2], borough:borough};}
  function explicitBoroughInQuery(q){q=String(q||'').trim().replace(/,\s*(NY|New York)\s*$/i,''); var parts=q.split(',').map(function(p){return p.trim();}).filter(Boolean); var explicit=knownBoroughName(parts[1]); if(explicit) return explicit; var tail=(parts[0]||q).match(/\s+(Manhattan|Brooklyn|Bronx|Queens|Staten\s+Island|New\s+York|NY)$/i); return tail ? knownBoroughName(tail[1]) : ''; }
  async function fetchJson(url,opts,timeoutMs){opts=Object.assign({},opts||{}); var controller=null, timer=null; if(typeof AbortController!=='undefined'){controller=new AbortController(); opts.signal=controller.signal; timer=setTimeout(function(){controller.abort();}, timeoutMs||9000);} try{var r=await fetch(url,opts); if(!r.ok) throw new Error('Request failed: '+r.status); return await r.json();} finally{if(timer) clearTimeout(timer);}}
  async function fetchJsonOptional(url,timeoutMs){if(!url) return null; try{return await fetchJson(url,undefined,timeoutMs||6500);}catch(e){return null;}}
  function candidateKey(a,b){return normalizeBbl(a&&a.bbl)||[b,parseFloat(a&&a.latitude).toFixed(6),parseFloat(a&&a.longitude).toFixed(6)].join('|');}
  async function geoclient(q, borough){var p=parseAddress(q, borough); var key='b913bdfb9c47466589d0f08c99c75b21'; async function lookup(b){var url='https://api.nyc.gov/geoclient/v2/address.json?houseNumber='+encodeURIComponent(p.houseNumber)+'&street='+encodeURIComponent(p.street)+'&borough='+encodeURIComponent(b)+'&subscription-key='+encodeURIComponent(key); var d=await fetchJson(url,undefined,12000); var a=d&&d.address; if(a&&Number.isFinite(parseFloat(a.latitude))&&Number.isFinite(parseFloat(a.longitude))){a.__searchedBorough=b; return a;} return null;} if(p.borough){var one=await lookup(p.borough); if(one) return one; throw new Error('Address not found. Try checking the street number and borough.');} var boroughs=['Brooklyn','Manhattan','Queens','Bronx','Staten Island']; var settled=await Promise.allSettled(boroughs.map(lookup)); var seen={}, matches=[]; settled.forEach(function(r,i){var a=r.status==='fulfilled'?r.value:null; if(a){var k=candidateKey(a,boroughs[i]); if(!seen[k]){seen[k]=true; matches.push(a);}}}); if(matches.length===1) return matches[0]; if(matches.length>1){var names=matches.map(function(a){return a.__searchedBorough||knownBoroughName(a.firstBoroughName)||'a borough';}).join(', '); throw new Error('Multiple NYC matches found. Add the borough to search this address: '+names+'.');} throw new Error('Address not found. Try adding the borough, for example: '+q+', Brooklyn.');}
  async function fetchArcgisPluto(safeBbl,lat,lng){try{var params=new URLSearchParams({f:'json',where:safeBbl?'BBL='+safeBbl:'1=1',outFields:'BBL,Address,LandUse,ZoneDist1,ZoneDist2,ZoneDist3,ZoneDist4,Overlay1,Overlay2,SPDist1,SPDist2,SPDist3,SplitZone,LtdHeight,YearBuilt,UnitsRes,UnitsTotal,BldgClass,LotArea,BldgArea,Borough,Block,Lot,CD,SchoolDist,Council,PolicePrct,OwnerName,Owner',returnGeometry:'false',outSR:'4326'}); if(!safeBbl&&Number.isFinite(lat)&&Number.isFinite(lng)){params.set('geometry',String(lng)+','+String(lat));params.set('geometryType','esriGeometryPoint');params.set('inSR','4326');params.set('spatialRel','esriSpatialRelIntersects');} var d=await fetchJsonOptional('https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services/MAPPLUTO/FeatureServer/0/query?'+params.toString()); var a=d&&d.features&&d.features[0]&&d.features[0].attributes; if(!a) return null; return {bbl:normalizeBbl(a.BBL||a.bbl||safeBbl),borough:a.Borough||'',block:a.Block||'',lot:a.Lot||'',address:a.Address||'',landuse:a.LandUse||'',zonedist1:a.ZoneDist1||'',zonedist2:a.ZoneDist2||'',zonedist3:a.ZoneDist3||'',zonedist4:a.ZoneDist4||'',overlay1:a.Overlay1||'',overlay2:a.Overlay2||'',spdist1:a.SPDist1||'',spdist2:a.SPDist2||'',spdist3:a.SPDist3||'',splitzone:a.SplitZone||'',yearbuilt:a.YearBuilt||'',unitsres:a.UnitsRes||'',unitstotal:a.UnitsTotal||'',bldgclass:a.BldgClass||'',lotarea:a.LotArea||'',bldgarea:a.BldgArea||'',cd:a.CD||'',council:a.Council||'',policeprct:a.PolicePrct||'',schooldist:a.SchoolDist||'',ownername:a.OwnerName||a.Owner||'',owner:a.Owner||a.OwnerName||'',__lookupStatus:'ok_arcgis'};}catch(e){return null;}}
  async function fetchPluto(bbl,lat,lng){var safe=normalizeBbl(bbl); if(!safe) return await fetchArcgisPluto('',lat,lng) || {__lookupStatus:'invalid_bbl'}; try{var params=new URLSearchParams({'$where':"bbl='"+safe+"'",'$select':'bbl,borough,block,lot,address,landuse,zonedist1,zonedist2,zonedist3,zonedist4,overlay1,overlay2,spdist1,spdist2,spdist3,splitzone,ltdheight,yearbuilt,unitsres,unitstotal,bldgclass,lotarea,bldgarea,cd,council,policeprct,schooldist,ownername','$limit':'1'}); var rows=await fetchJson('https://data.cityofnewyork.us/resource/64uk-42ks.json?'+params.toString()); if(rows&&rows[0]){rows[0].__lookupStatus='ok'; return rows[0];}}catch(e){} return await fetchArcgisPluto(safe,lat,lng) || {__lookupStatus:'no_record'};}
  async function fetchLandmarks(bbl){bbl=normalizeBbl(bbl); if(!bbl) return {historicDistricts:[]}; try{var rows=await fetchJson('https://data.cityofnewyork.us/resource/gpmc-yuvp.json?'+new URLSearchParams({bbl:bbl,'$select':'hist_dist,lm_orig,lm_new,des_addres','$limit':'50'})); return {historicDistricts:Array.from(new Set((rows||[]).map(function(r){return String(r.hist_dist||'').trim();}).filter(function(n){return n&&n!=='0';})))};}catch(e){return {historicDistricts:[]};}}
  function distFt(a,b,c,d){var R=3959*5280, dLat=(c-a)*Math.PI/180, dLng=(d-b)*Math.PI/180; var x=Math.sin(dLat/2)**2+Math.cos(a*Math.PI/180)*Math.cos(c*Math.PI/180)*Math.sin(dLng/2)**2; return R*2*Math.atan2(Math.sqrt(x),Math.sqrt(1-x));}
  function distLabel(f){return !Number.isFinite(f)?'':(f<700?Math.round(f/25)*25+' ft':(f/5280).toFixed(1)+' mi');}
  function featurePoints(item){if(!item) return []; var g=item.geometry, p=item.properties||item, pts=[]; function add(c){if(Array.isArray(c)&&c.length>=2){var x=+c[0], y=+c[1]; if(Number.isFinite(x)&&Number.isFinite(y)) pts.push({lng:x,lat:y,properties:p});}} function walk(c){if(!Array.isArray(c)) return; if(typeof c[0]==='number') add(c); else c.forEach(walk);} if(g&&g.coordinates) walk(g.coordinates); var plat=parseFloat(p.lat||p.latitude||p.entrance_latitude||p.Latitude||p.LATITUDE), plng=parseFloat(p.lon||p.lng||p.longitude||p.entrance_longitude||p.Longitude||p.LONGITUDE); if(Number.isFinite(plat)&&Number.isFinite(plng)) pts.push({lat:plat,lng:plng,properties:p}); return pts;}
  function nearest(items,lat,lng,filterFn){return (items||[]).map(function(it){var pts=featurePoints(it); if(!pts.length) return null; var p=(it.properties||it||{}); if(filterFn&&!filterFn(p)) return null; var d=Math.min.apply(null,pts.map(function(pt){return distFt(lat,lng,pt.lat,pt.lng);})); return Number.isFinite(d)?{properties:p,distanceFeet:d}:null;}).filter(Boolean).sort(function(a,b){return a.distanceFeet-b.distanceFeet;})[0]||null;}
  async function nearby(lat,lng,foundCd,a){var out={}; var cd=String(foundCd||''); var b=cd.charAt(0), key=BOROUGH_KEY[b], short=BOROUGH_SHORT[b], n=parseInt(cd.slice(1),10); var transport=await fetchJsonOptional(short&&n?'transport-data/cb-'+short+'-'+n+'.json':''); var subway=transport&&transport.subway&&transport.subway.features||[], bus=transport&&transport.busstops&&transport.busstops.features||[]; out.subway=nearest(subway,lat,lng); out.bus=nearest(bus,lat,lng); var parks=await fetchJsonOptional(key?'data/topmap-parks-'+key+'.geojson':''); out.park=nearest(parks&&parks.features||[],lat,lng,function(p){return String(p.retired||'').toLowerCase()!=='true';}); var libs=await fetchJsonOptional('data/nyc_libraries.geojson'); out.library=nearest(libs&&libs.features||[],lat,lng,function(p){return String(p.status||'').toLowerCase().indexOf('closed')===-1;}) || nearest(libs&&libs.features||[],lat,lng); var schools=await fetchJsonOptional('data/nyc_school_points.json'); out.school=nearest(Array.isArray(schools)?schools:[],lat,lng,function(p){return String(p.category||'').toLowerCase()!=='childcare' && (!key || String(p.borough||'').toLowerCase().replace(/[^a-z]/g,'')===key);}); var citi=await fetchJsonOptional('https://gbfs.citibikenyc.com/gbfs/en/station_information.json',15000) || await fetchJsonOptional('data/citibike_station_information.json',8000); out.citibike=nearest(citi&&citi.data&&citi.data.stations||[],lat,lng); var mayor=await fetchJsonOptional('data/cb6-ed-results.geojson'); var ed=parseInt(a&&a.electionDistrict,10), ad=parseInt(a&&(a.assemblyDistrict||a.stateLegislativeDistrict),10); if(mayor&&mayor.features&&Number.isFinite(ed)&&Number.isFinite(ad)){var wanted=String(ad).padStart(2,'0')+String(ed).padStart(3,'0'); var f=mayor.features.find(function(x){return String((x.properties||{}).elect_dist||'')===wanted;}); if(f) out.mayor=f.properties;} return out;}
  function service(label,item,nameFn,detailFn){if(!item) return mini(label,'Not available'); var p=item.properties||{}, v=(nameFn?nameFn(p):(p.name||p.stop_name||label))||label, d=distLabel(item.distanceFeet), detail=detailFn?detailFn(p):''; if(d) v+=' · '+d; if(detail) v+=' · '+detail; return mini(label,v);}
  function nearbyHtml(n){n=n||{}; return '<div style="margin-bottom:10px"><div style="font-size:.66rem;font-family:\'DM Mono\',monospace;text-transform:uppercase;letter-spacing:.08em;color:var(--muted,#6b6760);margin:0 0 5px">Nearby civic services</div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px">'+service('Closest Park',n.park,function(p){return p.signname||p.name311||'Park/Open Space';},function(p){return p.typecategory||p.location||p.address||'';})+service('Closest Subway',n.subway,function(p){return p.display_name||p.stop_name||'Subway station';},function(p){return p.daytime_routes||p.routes||'';})+service('Closest Bus Stop',n.bus,function(p){var r=Array.isArray(p.routes)?p.routes.join(', '):(p.routes||p.route_short_name||'Bus'); return r+' · '+(p.stop_name||'Bus stop');})+service('Closest Citi Bike',n.citibike,function(p){return p.name||p.station_name||'Citi Bike station';},function(p){return p.short_name||'';})+service('Closest Library',n.library,function(p){return p.name||'Library';},function(p){var b=[]; if(p.address)b.push(p.address); if(p.system)b.push(p.system); return b.join(' · ');})+service('Closest School',n.school,function(p){return p.name||'School';},function(p){return p.program_type||p.typecategory||p.address||'';})+'</div></div>';}
  function repLabel(type,id,fallback){id=districtNumber(id); var name=(typeof window.repName==='function')?window.repName(type,id):''; return id ? (fallback||'District')+' '+id+(name?' — '+name:'') : '—';}

  // ---- what can be built here: Use Group verdicts for the lot's zoning district ----
  var USEMATRIX=null;
  (function(){try{fetch('/data/zoning-matrix.json').then(function(r){return r.json();}).then(function(j){USEMATRIX=j;
    document.querySelectorAll('[data-usegrid]').forEach(function(el){paintUseGrid(el);});}).catch(function(){});}catch(e){}})();
  function baseDistrict(z){
    if(!z) return null;
    var m=String(z).trim().toUpperCase().match(/^([RCM])\s*(\d{1,2})/);
    if(!m) return null;
    var lim={R:12,C:8,M:3}[m[1]], num=parseInt(m[2],10);
    return (num>=1&&num<=lim) ? (m[1]+num) : null;
  }
  var USE_SYM={Y:'\u25cf',L:'\u2666',S:'\u25cb',N:'\u2013'};
  var USE_LBL={Y:'Yes',L:'With limits',S:'Special permit',N:'No'};
  var USE_BG={Y:'#e3f2e4',L:'#fff1e0',S:'#e8eefb',N:'#fbe6e6'};
  var USE_FG={Y:'#2e6b30',L:'#a65a00',S:'#2145a8',N:'#a82121'};
  var USE_SHOW=['live','shop','eat','office','factory','school','hotel','warehouse'];
  var PATH_NOTE='This only applies to uses that are already permitted. Where the answer above is yes, switching to that use is a Department of Buildings filing for a new or amended Certificate of Occupancy, with no rezoning, no Board of Standards and Appeals and no community board vote. Where the answer is no, there is no administrative route at any size: it takes a variance or a rezoning.';
  var LETTER_NOTE={
    R:'R does not mean only housing. Residence Districts also permit schools, houses of worship, libraries, museums, hospitals and community centers as of right.',
    C:'C does not mean no housing. Housing is permitted as of right in C1, C2, C4, C5 and C6. Only C7 and C8 exclude residences.',
    M:'M does not mean only factories. Offices, retail, storage and entertainment are widely permitted. What M bars as of right is housing.'};
  var PARK_NOTE='This lot is mapped as public parkland. It is not an ordinary zoning district: the Parks Department has jurisdiction, and converting parkland to another use requires an act of the State Legislature, not a rezoning.';
  function paintUseGrid(el){
    if(!USEMATRIX||!el) return;
    var base=el.getAttribute('data-usegrid');
    var rawz=el.getAttribute('data-zone')||'';
    if(String(rawz).trim().toUpperCase()==='PARK'){
      el.innerHTML='<div style="font-size:.74rem;font-weight:700;color:#0d1b4b;margin-bottom:4px">Mapped parkland</div>'+
        '<div style="font-size:.75rem;line-height:1.55;color:#444">'+esc(PARK_NOTE)+'</div>';
      return;
    }
    if(!base){ el.style.display='none'; return; }
    var rows=USEMATRIX.goals.filter(function(g){return USE_SHOW.indexOf(g.id)>-1;}).map(function(g){
      var row=USEMATRIX.matrix[g.ug], v=row?row[base]:null;
      if(!v) return '';
      var note=(g.notes&&g.notes[base])||'';
      var lab=g.q.replace(/^I want to /,'');
      lab=lab.charAt(0).toUpperCase()+lab.slice(1);
      return '<div style="display:flex;align-items:flex-start;gap:8px;padding:6px 0;border-bottom:1px solid #f0ede8">'+
        '<span style="flex:none;min-width:86px;text-align:center;font-size:.63rem;font-weight:800;padding:3px 6px;border-radius:5px;background:'+USE_BG[v]+';color:'+USE_FG[v]+'">'+USE_SYM[v]+' '+USE_LBL[v]+'</span>'+
        '<span style="flex:1;min-width:0"><span style="font-size:.75rem;font-weight:700;color:#0d1b4b">'+esc(lab)+'</span>'+
        (note?'<span style="display:block;font-size:.69rem;color:#6b6760;line-height:1.45;margin-top:1px">'+esc(note)+'</span>':'')+'</span></div>';
    }).join('');
    if(!rows){ el.style.display='none'; return; }
    el.innerHTML='<div style="font-size:.74rem;font-weight:700;color:#0d1b4b;margin-bottom:5px">What can be built here &middot; '+esc(base)+' rules</div>'+rows+
      '<div style="font-size:.7rem;color:#0d1b4b;line-height:1.5;margin-top:8px;padding:8px 9px;background:#f8f7f4;border-left:3px solid #f47920;border-radius:0 5px 5px 0"><b>The letter is a name, not a description.</b> '+esc(LETTER_NOTE[base.charAt(0)]||'')+'</div>'+
      '<div style="font-size:.7rem;color:#0d1b4b;line-height:1.5;margin-top:7px;padding:8px 9px;background:#f8f7f4;border-left:3px solid #2e6b30;border-radius:0 5px 5px 0"><b>Changing the use is administrative.</b> '+esc(PATH_NOTE)+'</div>'+
      '<div style="font-size:.66rem;color:#9ca3af;line-height:1.5;margin-top:7px">Overlays, special purpose districts and Article VI can change this on a given lot. <a href="/zoning" style="color:#0d1b4b">Full chart and checker &rarr;</a></div>';
  }

  // ---- what is actually at this address: NYC Facilities Database ----
  var FAC_ICON={'LIBRARIES AND CULTURAL PROGRAMS':'\u{1F4DA}','ADMINISTRATION OF GOVERNMENT':'\u{1F3DB}',
    'HEALTH AND HUMAN SERVICES':'\u{1FA7A}','EDUCATION, CHILD WELFARE, AND YOUTH':'\u{1F393}',
    'PARKS, GARDENS, AND HISTORICAL SITES':'\u{1F333}','PUBLIC SAFETY, EMERGENCY SERVICES, AND ADMINISTRATION OF JUSTICE':'\u{1F693}',
    'CORE INFRASTRUCTURE AND TRANSPORTATION':'\u{1F6A7}'};
  function titleCase(t){
    return String(t||'').toLowerCase().replace(/\b([a-z])/g,function(m,c){return c.toUpperCase();})
      .replace(/\bNyc\b/g,'NYC').replace(/\bOf\b/g,'of').replace(/\bAnd\b/g,'and').replace(/\bThe\b/g,'the');
  }
  var FACFIX=null;
  (function(){try{fetch('/data/facility-corrections.json').then(function(r){return r.json();}).then(function(j){FACFIX=j;}).catch(function(){});}catch(e){}})();
  function applyFacCorrections(bbl,rows){
    if(!FACFIX) return rows;
    var safe=normalizeBbl(bbl);
    var closed=(FACFIX.closed||[]).filter(function(c){return normalizeBbl(c.bbl)===safe;});
    var out=rows.filter(function(r){
      return !closed.some(function(c){
        return String(r.facname||'').trim().toUpperCase()===String(c.facname||'').trim().toUpperCase();
      });
    });
    (FACFIX.add||[]).forEach(function(a){
      if(normalizeBbl(a.bbl)===safe) out.push({facname:a.facname,factype:a.factype||'',facsubgrp:a.facsubgrp||'',
        facdomain:a.facdomain||'',overagency:a.overagency||'',__local:true});
    });
    out.__removed=closed.length;
    return out;
  }
  async function fetchFacilities(bbl){
    var safe=normalizeBbl(bbl);
    if(!safe) return [];
    try{
      var url='https://data.cityofnewyork.us/resource/ji82-xba5.json?$select=facname,factype,facsubgrp,facgroup,facdomain,overagency,opname,capacity,captype'+
        '&$where='+encodeURIComponent("bbl='"+safe+"' OR bbl='"+safe+".0'")+'&$limit=25&$$app_token=HvFoIfzodzpRML7a1104Ca2tM';
      var rows=await fetchJsonOptional(url);
      return applyFacCorrections(bbl,Array.isArray(rows)?rows:[]);
    }catch(e){ return []; }
  }

  // ---- why is this facility allowed here: map the facility to its Use Group ----
  var FAC_UG=[
    [/LIBRAR/,'III','a library, which is a community facility'],
    [/MUSEUM|CULTURAL|ART GALLER/,'III','a cultural institution, which is a community facility'],
    [/SCHOOL|EDUCATION|UNIVERSIT|COLLEGE|DAY CARE|CHILD CARE|HEAD START|PRE-?K/,'III','an educational or child care use, which is a community facility'],
    [/HOSPITAL|HEALTH|MENTAL|CLINIC|MEDICAL|NURSING/,'III','a health facility, which is a community facility'],
    [/HUMAN SERVICE|SENIOR|COMMUNITY CENTER|SETTLEMENT|SHELTER|WELFARE|SOCIAL/,'III','a human services use, which is a community facility'],
    [/HOUSE OF WORSHIP|RELIGIOUS|CHURCH|SYNAGOGUE|MOSQUE/,'III','a house of worship, which is a community facility'],
    [/PARK|PLAYGROUND|GARDEN|RECREATION/,'I','an open space use'],
    [/POLICE|FIRE|EMERGENCY|COURT|JUSTICE|CORRECTION/,'IV','a public safety facility'],
    [/INFRASTRUCTURE|TRANSPORT|SANITATION|WATER|SEWER|UTILIT/,'IV','public infrastructure'],
    [/OFFICE|ADMINISTRATION OF GOVERNMENT|TRAINING|TESTING/,'VII','a government or business office']
  ];
  function facUseGroup(r){
    var hay=[r.factype,r.facsubgrp,r.facgroup,r.facdomain].join(' ').toUpperCase();
    for(var i=0;i<FAC_UG.length;i++){ if(FAC_UG[i][0].test(hay)) return {ug:FAC_UG[i][1],why:FAC_UG[i][2]}; }
    return null;
  }
  // a C1 or C2 overlay on a Residence District permits commercial use groups the R district alone would not
  function districtsInPlay(zones,overlay){
    var out=[];
    var base=baseDistrict(zones&&zones[0]);
    if(base) out.push({d:base,label:zones[0],kind:'base'});
    var ov=baseDistrict(overlay);
    if(ov) out.push({d:ov,label:overlay,kind:'overlay'});
    return out;
  }
  function whyAllowed(r,zones,overlay){
    var f=facUseGroup(r);
    if(!f||!USEMATRIX) return '';
    var opts=districtsInPlay(zones,overlay);
    if(!opts.length) return '';
    var best=null;
    var rank={Y:3,L:2,S:1,N:0};
    opts.forEach(function(o){
      var row=USEMATRIX.matrix[f.ug], v=row?row[o.d]:null;
      if(!v) return;
      if(!best||rank[v]>rank[best.v]) best={v:v,d:o.d,label:o.label,kind:o.kind};
    });
    if(!best) return '';
    var msg;
    if(best.v==='Y'){
      msg='Permitted as of right. This is '+f.why+', Use Group '+f.ug+', which '+esc(best.label)+' allows without any special approval.';
      if(best.kind==='overlay') msg+=' The '+esc(best.label)+' overlay is what permits it here; the underlying district alone would not.';
    } else if(best.v==='L'){
      msg='Permitted with limits. This is '+f.why+', Use Group '+f.ug+', allowed in '+esc(best.label)+' subject to size or location rules.';
      if(best.kind==='overlay') msg+=' The overlay is what permits it here.';
    } else if(best.v==='S'){
      msg='This is '+f.why+', Use Group '+f.ug+', which needs a special permit in '+esc(best.label)+'. That is a public review the community board weighs in on.';
    } else {
      msg='This is '+f.why+', Use Group '+f.ug+', which '+esc(best.label)+' does not permit as of right. It may predate the current zoning, sit on city owned land reviewed through a separate process, or hold a variance.';
    }
    var col={Y:'#2e6b30',L:'#a65a00',S:'#2145a8',N:'#a82121'}[best.v];
    return '<span style="display:block;font-size:.69rem;color:'+col+';line-height:1.45;margin-top:3px"><b>Why it can be here:</b> '+msg+'</span>';
  }
  function facilitiesHtml(rows,zones,overlay){
    if(!rows||!rows.length) return '';
    var seen={}, items=[];
    rows.forEach(function(r){
      var k=(r.facname||'')+'|'+(r.factype||'');
      if(seen[k]) return; seen[k]=1; items.push(r);
    });
    var list=items.map(function(r){
      var ic=FAC_ICON[r.facdomain]||'\u{1F4CD}';
      var agency=r.overagency||r.opname||'';
      var cap=(r.capacity&&Number(r.capacity)>0)?(' \u00b7 '+fmtNum(r.capacity,'')+' '+(r.captype||'capacity')):'';
      return '<div style="display:flex;gap:9px;padding:7px 0;border-bottom:1px solid #f0ede8">'+
        '<span style="font-size:1.05rem;flex:none">'+ic+'</span>'+
        '<span style="flex:1;min-width:0">'+
          '<span style="display:block;font-size:.78rem;font-weight:700;color:#0d1b4b;line-height:1.3">'+esc(titleCase(r.facname))+'</span>'+
          '<span style="display:block;font-size:.7rem;color:#6b6760;line-height:1.45;margin-top:1px">'+
            esc(titleCase(r.factype||r.facsubgrp||''))+cap+'</span>'+
          (agency?'<span style="display:block;font-size:.68rem;color:#9ca3af;line-height:1.4;margin-top:1px">'+esc(agency)+'</span>':'')+
          whyAllowed(r,zones,overlay)+
        '</span></div>';
    }).join('');
    return '<div style="background:#fff;border:1px solid #d1fae5;border-radius:6px;padding:9px 10px;margin-bottom:10px">'+
      '<div style="font-size:.74rem;font-weight:700;color:#0d1b4b;margin-bottom:4px">What is here now &middot; '+items.length+
      (items.length===1?' public facility':' public facilities')+'</div>'+list+
      '<div style="font-size:.66rem;color:#9ca3af;line-height:1.5;margin-top:7px">Public and publicly funded facilities recorded at this lot in the NYC Facilities Database. Private businesses are not included.</div></div>';
  }
  function render(input,a,foundCd,lat,lng,pluto,landmarks,n,context,facs){context=context||{}; pluto=pluto||{}; var ed=parseInt(a.electionDistrict,10), ad=parseInt(a.assemblyDistrict,10), council=districtNumber(a.cityCouncilDistrict), senate=districtNumber(a.stateSenatorialDistrict), cong=districtNumber(a.congressionalDistrict), school=districtNumber(addressValue(a,['communitySchoolDistrict','schoolDistrict','schoolDistrictNumber'])||pluto.schooldist), police=districtNumber(addressValue(a,['policePrecinct','policePrecinctCode','nycPolicePrecinct'])||pluto.policeprct); var bbl=normalizeBbl(a.bbl)||normalizeBbl(pluto.bbl), b=bbl.slice(0,1)||String(foundCd||'').charAt(0), block=bbl.slice(1,6), lot=bbl.slice(6,10); var cb=validCommunityBoardCode(foundCd)?String(foundCd):String(a.communityDistrict||pluto.cd||''); var cbLabel=validCommunityBoardCode(cb)?boardLabel(cb):'Community Board not identified'; var zones=collectZones(a,pluto), zDisp=zones.length?zones.join(' / '):'Not available from PLUTO'; var spDists=collectSpecialDistricts(pluto), spDisp=spDists.length?spDists.join(' / '):''; var lUse=landUseLabel(pluto.landuse); var hd=(landmarks&&landmarks.historicDistricts)||[]; var historic=hd.length?hd.join(' / '):'Not in an LPC historic district'; var dob=b&&block&&lot?'https://a810-bisweb.nyc.gov/bisweb/PropertyBrowseByBBLServlet?allborough='+encodeURIComponent(b)+'&allblock='+parseInt(block,10)+'&alllot='+parseInt(lot,10)+'&filetype=html&requestid=0':'#'; var zola=b&&block&&lot?'https://zola.planning.nyc.gov/l/lot/'+encodeURIComponent(b)+'/'+parseInt(block,10)+'/'+parseInt(lot,10):'#'; var acris=b&&block&&lot?'https://a836-acris.nyc.gov/DS/DocumentSearch/BBL?REQUEST_BBL='+encodeURIComponent(b)+block+lot:'#'; var zap=block&&lot?'https://zap.planning.nyc.gov/projects?block='+parseInt(block,10)+'&lot='+parseInt(lot,10):'#'; var enc=encodeURIComponent(input); var cards=mini(zones.length>1?'Zoning Districts':'Zoning District',zDisp)+(spDists.length?mini(spDists.length>1?'Special Districts':'Special District',spDisp):'')+mini('Land Use',lUse)+mini('Landmark Status',historic)+mini('Election District',Number.isFinite(ed)?ed:'—')+mini('Assembly',repLabel('state_assembly',ad,'Assembly District'))+mini('City Council',repLabel('city_council',council,'Council District'))+mini('State Senate',repLabel('state_senate',senate,'State Senate District'))+mini('Congress',repLabel('congress',cong,'Congressional District'))+mini('School District',school?'CSD '+school:'—')+mini('Police Precinct',police?police+' Precinct':'—')+mini('Zoning Code Explanation',zones.length?zones.map(function(z){return z+': '+zoningPlain(z);}).join(' / '):'Check ZoLa for exact district controls.')+mini('Use Group Explanation',landUsePlain(pluto.landuse,lUse))+propertyMini('Owner',pluto.ownername||pluto.owner||a.ownerName||a.ownername)+mini('Community Board',cbLabel)+mini('Borough',pluto.borough||a.firstBoroughName||BOROUGH_NAMES[b]||'—')+propertyMini('Year Built',fmtNum(pluto.yearbuilt,''))+propertyMini('Building Class',pluto.bldgclass)+propertyMini('Lot Area',fmtNum(pluto.lotarea,' sq ft'))+propertyMini('Building Area',fmtNum(pluto.bldgarea,' sq ft'))+propertyMini('Residential Units',fmtNum(pluto.unitsres,''))+propertyMini('Total Units',fmtNum(pluto.unitstotal,'')); return '<div style="background:#f0f8f4;border:1.5px solid #a7f3d0;border-radius:8px;padding:12px 14px;margin-top:4px"><div style="font-size:.85rem;font-weight:700;color:var(--navy,#0d1b4b);margin-bottom:2px">&#10003; '+esc(input)+'</div><div style="font-size:.75rem;color:var(--muted,#6b6760);margin-bottom:8px">'+esc(cbLabel)+' &middot; ED '+(Number.isFinite(ed)?ed:'—')+' &middot; AD '+(Number.isFinite(ad)?ad:'—')+(council?' &middot; Council District '+esc(council):'')+(senate?' &middot; State Senate District '+esc(senate):'')+(cong?' &middot; Congressional District '+esc(cong):'')+(school?' &middot; School District '+esc(school):'')+(police?' &middot; Police Precinct '+esc(police):'')+'</div><div class="citywide-result-map" data-lat="'+lat+'" data-lng="'+lng+'" data-label="'+esc(input)+'" style="height:240px;border-radius:8px;border:1px solid #a7f3d0;margin-bottom:10px;background:#eef2f7"></div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:8px;margin-bottom:10px">'+cards+'</div><div style="background:#fff;border:1px solid #d1fae5;border-radius:6px;padding:9px 10px;margin-bottom:10px;font-size:.73rem;line-height:1.45;color:var(--navy,#0d1b4b)"><div><strong>Zoning:</strong> '+(zones.length?zones.map(function(z){return '<strong>'+esc(z)+'</strong>: '+esc(zoningPlain(z));}).join('<br>'):'Zoning was not available from PLUTO for this address.')+'</div><div style="margin-top:5px"><strong>Land use:</strong> '+esc(landUsePlain(pluto.landuse,lUse))+'</div>'+(spDists.length?'<div style="margin-top:5px"><strong>Special district:</strong> '+esc(specialDistrictExplain(spDisp,[pluto.spdist1,pluto.spdist2,pluto.spdist3]))+'</div>':'')+(hd.length?'<div style="margin-top:5px"><strong>Historic district:</strong> This is in a historic district, so exterior changes usually need LPC review.</div>':'')+'</div>'+facilitiesHtml(facs,zones,pluto.overlay1||pluto.overlay2||'')+'<div data-usegrid="'+esc(baseDistrict(zones[0])||'')+'" data-zone="'+esc(zones[0]||'')+'" style="background:#fff;border:1px solid #d1fae5;border-radius:6px;padding:9px 10px;margin-bottom:10px"></div>'+nearbyHtml(n)+'<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px"><a href="'+dob+'" target="_blank" style="font-size:.73rem;font-weight:600;color:var(--navy,#0d1b4b);text-decoration:none;padding:5px 10px;border:1px solid var(--border,#e5e2db);border-radius:5px;background:#fff">DOB BIS</a><a href="'+zap+'" target="_blank" style="font-size:.73rem;font-weight:600;color:var(--navy,#0d1b4b);text-decoration:none;padding:5px 10px;border:1px solid var(--border,#e5e2db);border-radius:5px;background:#fff">ZAP Projects</a><a href="'+acris+'" target="_blank" style="font-size:.73rem;font-weight:600;color:var(--navy,#0d1b4b);text-decoration:none;padding:5px 10px;border:1px solid var(--border,#e5e2db);border-radius:5px;background:#fff">ACRIS Deeds</a><a href="'+zola+'" target="_blank" style="font-size:.73rem;font-weight:600;color:#2e7d32;text-decoration:none;padding:5px 10px;border:1px solid #a5d6a7;border-radius:5px;background:#f1f8f1">ZoLa Zoning</a><a href="https://maps.google.com/?q='+lat+','+lng+'" target="_blank" style="font-size:.73rem;font-weight:600;color:var(--navy,#0d1b4b);text-decoration:none;padding:5px 10px;border:1px solid var(--border,#e5e2db);border-radius:5px;background:#fff">Map</a><button type="button" class="citywide-share-btn" data-share-address="'+esc(input)+'" style="font-size:.73rem;font-weight:700;color:#fff;cursor:pointer;padding:5px 12px;border:1px solid var(--orange,#FD890E);border-radius:5px;background:var(--orange,#FD890E)">Share card</button></div><div style="border-top:1px solid #d1fae5;padding-top:8px;display:flex;flex-wrap:wrap;gap:12px"><a href="'+(boardSlug(cb)?boardSlug(cb)+'?addr='+enc+'#sec-map':'mydistricts.html?address='+enc)+'" style="font-size:.75rem;color:var(--navy,#0d1b4b);font-weight:700;text-decoration:none;border-bottom:1px solid var(--navy,#0d1b4b)">Open '+esc(cbLabel)+' district profile &rarr;</a></div></div>';}
  async function nyzdQuery(geomObj,geomType){
    var url='https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services/nyzd/FeatureServer/0/query?where=1%3D1&outFields=ZONEDIST&returnGeometry=false&outSR=4326&geometry='+encodeURIComponent(JSON.stringify(geomObj))+'&geometryType='+geomType+'&inSR=4326&spatialRel=esriSpatialRelIntersects&f=json&resultRecordCount=20';
    var d=await fetchJsonOptional(url);
    return (d&&d.features)||[];
  }
  async function fetchZoningByPoint(lat,lng){
    if(!Number.isFinite(lat)||!Number.isFinite(lng)) return [];
    try{
      // exact point first — this is the authoritative district for the coordinate
      var feats=await nyzdQuery({x:lng,y:lat,spatialReference:{wkid:4326}},'esriGeometryPoint');
      var out=[];
      feats.forEach(function(f){var z=String((f.attributes&&f.attributes.ZONEDIST)||'').trim().toUpperCase(); if(z && out.indexOf(z)===-1) out.push(z);});
      if(out.length) return out;
      // fallback: tiny envelope if the point landed exactly on a boundary and matched nothing
      var env={xmin:lng-0.00012,ymin:lat-0.00012,xmax:lng+0.00012,ymax:lat+0.00012,spatialReference:{wkid:4326}};
      var efeats=await nyzdQuery(env,'esriGeometryEnvelope');
      var counts={};
      efeats.forEach(function(f){var z=String((f.attributes&&f.attributes.ZONEDIST)||'').trim().toUpperCase(); if(z) counts[z]=(counts[z]||0)+1;});
      var eout=Object.keys(counts);
      eout.sort(function(a,b){var as=a.indexOf('/')!==-1?1:0, bs=b.indexOf('/')!==-1?1:0; if(as!==bs) return bs-as; return counts[b]-counts[a];});
      return eout.slice(0,1);
    }catch(e){return [];}
  }
  async function fetchSpecialDistrictByPoint(lat,lng){
    if(!Number.isFinite(lat)||!Number.isFinite(lng)) return null;
    try{
      var params=new URLSearchParams({f:'json',where:'1=1',outFields:'SPDist1,SPDist2,SPDist3',returnGeometry:'false',outSR:'4326',geometry:String(lng)+','+String(lat),geometryType:'esriGeometryPoint',inSR:'4326',spatialRel:'esriSpatialRelIntersects'});
      var d=await fetchJsonOptional('https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services/MAPPLUTO/FeatureServer/0/query?'+params.toString());
      var a=d&&d.features&&d.features[0]&&d.features[0].attributes;
      if(!a) return null;
      return {spdist1:a.SPDist1||'',spdist2:a.SPDist2||'',spdist3:a.SPDist3||''};
    }catch(e){return null;}
  }
  async function build(q, context){context=context||{}; var a=await geoclient(q,context.boroughName); var lat=parseFloat(a.latitude), lng=parseFloat(a.longitude); if(!Number.isFinite(lat)||!Number.isFinite(lng)) throw new Error('Address coordinates not found'); var foundCd=String(a.communityDistrict||''); if(!validCommunityBoardCode(foundCd)) foundCd=''; var bbl=normalizeBbl(a.bbl); var r=await Promise.allSettled([fetchPluto(bbl,lat,lng),fetchLandmarks(bbl),nearby(lat,lng,foundCd,a),fetchSpecialDistrictByPoint(lat,lng),fetchZoningByPoint(lat,lng),fetchFacilities(bbl)]); var pluto=r[0].status==='fulfilled'?r[0].value:{}, lm=r[1].status==='fulfilled'?r[1].value:{historicDistricts:[]}, near=r[2].status==='fulfilled'?r[2].value:{}; var spPoint=r[3].status==='fulfilled'?r[3].value:null; var zPoint=r[4].status==='fulfilled'?(r[4].value||[]):[]; var facs=r[5]&&r[5].status==='fulfilled'?(r[5].value||[]):[]; if(spPoint&&pluto){var hasSp=collectSpecialDistricts(pluto).length>0; if(!hasSp&&(spPoint.spdist1||spPoint.spdist2||spPoint.spdist3)){pluto.spdist1=pluto.spdist1||spPoint.spdist1; pluto.spdist2=pluto.spdist2||spPoint.spdist2; pluto.spdist3=pluto.spdist3||spPoint.spdist3;}} if(zPoint.length&&pluto){var plutoZones=collectZones(a,pluto); var pointMatches=zPoint.some(function(z){return plutoZones.indexOf(z)!==-1;}); if(!pointMatches){pluto.zonedist1=zPoint[0]||pluto.zonedist1; pluto.zonedist2=zPoint[1]||''; pluto.zonedist3=zPoint[2]||''; pluto.zonedist4=zPoint[3]||''; if(a){a.zoningDistrict1=zPoint[0]||''; a.zoningDistrict2=zPoint[1]||''; a.zoningDistrict3=zPoint[2]||''; a.zoningDistrict4=zPoint[3]||'';} pluto.__zoningSource='nyzd_point';}} if((!facs||!facs.length)&&pluto&&pluto.bbl){try{facs=await fetchFacilities(pluto.bbl);}catch(e){}}
  var html=render(q,a,foundCd,lat,lng,pluto,lm,near,context,facs); return {input:q,address:a,lat:lat,lng:lng,foundCd:foundCd,pluto:pluto,landmarkStatus:lm,nearby:near,html:html,status:foundCd?'Search complete: address is in '+boardLabel(foundCd)+'.':'Search complete: address found.'};}
  window.__bkcbBuildFullAddressProfile = build;
  function zoneFam(z){z=String(z||'').toUpperCase().trim(); if(!z) return 'Other'; if(/^MX/.test(z)) return 'Mixed Use'; if(z.indexOf('/')>-1 && /M\d/.test(z) && /R\d/.test(z)) return 'Mixed Use'; if(/^R/.test(z)) return 'Residential'; if(/^C/.test(z)) return 'Commercial'; if(/^M/.test(z)) return 'Manufacturing'; if(/PARK|PLAYGROUND/.test(z)) return 'Park/Open Space'; if(/^BPC/.test(z)) return 'Mixed Use'; return 'Other';}
  var ZONE_FAM_GRAY={'Residential':'#e0e0e0','Commercial':'#9e9e9e','Manufacturing':'#4a4a4a','Park/Open Space':'#c4c4c4','Mixed Use':'#757575','Other':'#b3b3b3'};
  var ZONE_FAM_LABEL={'Residential':'#f7c948','Commercial':'#2f6fed','Manufacturing':'#c2410c','Park/Open Space':'#15803d','Mixed Use':'#9333ea','Other':'#475569'};
  // Okabe-Ito colorblind-safe qualitative palette (Okabe & Ito 2002; Wong, Nature Methods 2011).
  // Hues distinguish nominal zoning families; fill is the hue, label uses a darkened hue for legibility on the light fill.
  var ZONE_FAM_FILL={'Residential':'#56B4E9','Commercial':'#E69F00','Manufacturing':'#D55E00','Mixed Use':'#CC79A7','Park/Open Space':'#009E73','Other':'#999999'};
  var ZONE_FAM_TEXT={'Residential':'#1b6fa3','Commercial':'#946400','Manufacturing':'#8a3d00','Mixed Use':'#8a4e6e','Park/Open Space':'#00674c','Other':'#5c5c5c'};
  function zoneColor(z){var fam=zoneFam(z); return [fam, ZONE_FAM_FILL[fam]||ZONE_FAM_FILL.Other];}
  function zoneGray(z){var fam=zoneFam(z); return [fam, ZONE_FAM_GRAY[fam]||ZONE_FAM_GRAY.Other];}
  function loadResultZoning(map,lat,lng){
    var dy=0.0035, dx=0.0045;
    var env={xmin:lng-dx,ymin:lat-dy,xmax:lng+dx,ymax:lat+dy,spatialReference:{wkid:4326}};
    var url='https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services/nyzd/FeatureServer/0/query?where=1%3D1&outFields=ZONEDIST&returnGeometry=true&outSR=4326&geometry='+encodeURIComponent(JSON.stringify(env))+'&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&f=geojson&resultRecordCount=400';
    fetch(url).then(function(r){return r.json();}).then(function(d){
      if(!d||!d.features||!d.features.length) return;
      var fams={};
      var layer=L.geoJSON(d,{
        style:function(f){var z=(f.properties||{}).ZONEDIST||'';var g=zoneColor(z);fams[g[0]]=g[1];return{color:'#374151',weight:1,opacity:.9,fillColor:g[1],fillOpacity:.5};},
        onEachFeature:function(f,l){var z=(f.properties||{}).ZONEDIST||'Zoning';var g=zoneColor(z);l.bindPopup('<strong>'+esc(z)+'</strong><br>'+g[0]); if(z){var c=l.getBounds&&l.getBounds().isValid&&l.getBounds().isValid()?l.getBounds().getCenter():null; if(c){var col=ZONE_FAM_TEXT[g[0]]||ZONE_FAM_TEXT.Other; L.tooltip({permanent:true,direction:'center',className:'zone-label',opacity:1}).setLatLng(c).setContent('<span style="color:'+col+'">'+esc(z)+'</span>').addTo(map);}}}
      });
      layer.addTo(map); layer.bringToBack();
      var keys=Object.keys(fams);
      if(keys.length){
        var Legend=L.control({position:'bottomright'});
        Legend.onAdd=function(){var div=L.DomUtil.create('div');div.style.cssText='background:rgba(255,255,255,.92);padding:6px 8px;border-radius:5px;border:1px solid #ccc;font:600 10px/1.4 DM Sans,sans-serif;color:#333';div.innerHTML='<div style="font-weight:700;margin-bottom:3px">Zoning</div>'+keys.map(function(k){return '<div style="display:flex;align-items:center;gap:5px"><span style="display:inline-block;width:11px;height:11px;background:'+fams[k]+';border:1px solid #333"></span>'+esc(k)+'</div>';}).join('');return div;};
        Legend.addTo(map);
      }
    }).catch(function(e){console.warn('result zoning load failed',e);});
  }
  function ensureZoneLabelCss(){
    if(document.getElementById('cw-zone-label-css')) return;
    var st=document.createElement('style'); st.id='cw-zone-label-css';
    st.textContent=".leaflet-tooltip.zone-label{background:none;border:0;box-shadow:none;padding:0;font-family:'DM Sans',sans-serif;font-weight:800;font-size:11px;white-space:nowrap}.leaflet-tooltip.zone-label:before{display:none}.zone-label span{text-shadow:0 0 2px #fff,0 0 2px #fff,0 0 3px #fff,0 0 3px #fff}";
    document.head.appendChild(st);
  }
  function initResultMap(root){
    if(typeof L==='undefined'||!root) return;
    var el=root.querySelector('.citywide-result-map');
    if(!el||el.dataset.mapReady==='true') return;
    var lat=parseFloat(el.getAttribute('data-lat')), lng=parseFloat(el.getAttribute('data-lng'));
    if(!Number.isFinite(lat)||!Number.isFinite(lng)) return;
    el.dataset.mapReady='true';
    ensureZoneLabelCss();
    try{
      var map=L.map(el,{scrollWheelZoom:false}).setView([lat,lng],16);
      L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',{maxZoom:19,attribution:'&copy; OpenStreetMap &copy; CARTO'}).addTo(map);
      loadResultZoning(map,lat,lng);
      try{document.querySelectorAll('[data-usegrid]').forEach(function(el){paintUseGrid(el);});}catch(e){}
      L.marker([lat,lng]).addTo(map).bindPopup(el.getAttribute('data-label')||'Searched address');
      setTimeout(function(){map.invalidateSize();},120);
    }catch(e){console.error(e);}
  }
  window.__bkcbInitResultMap = initResultMap;

  function cardModeRequested(){
    try{return new URLSearchParams(location.search).get('card')==='1';}catch(e){return false;}
  }
  var SHARE_PAGES={'250 BALTIC STREET':'/250baltic.html'};
  function shareUrlFor(address,cardOnly){
    var key=String(address||'').trim().toUpperCase().replace(/\s+/g,' ').replace(/,.*$/,'').replace(/\s+(BROOKLYN|NY|NEW YORK).*$/,'');
    if(SHARE_PAGES[key]) return location.origin+SHARE_PAGES[key];
    var base=location.origin+location.pathname;
    var url=base+'?address='+encodeURIComponent(address);
    if(cardOnly) url+='&card=1';
    return url;
  }
  function stampUrl(address){
    try{
      if(!history.replaceState) return;
      var p=new URLSearchParams(location.search);
      p.set('address',address);
      p.delete('v');
      history.replaceState(null,'',location.pathname+'?'+p.toString());
    }catch(e){}
  }
  function applyCardMode(){
    if(!cardModeRequested()||document.body.classList.contains('card-only')) return;
    document.body.classList.add('card-only');
    var st=document.createElement('style');
    st.textContent='body.card-only header,body.card-only .hero,body.card-only .search-card>h3,body.card-only .search-card>p,body.card-only .search-card .search-row,body.card-only .search-card .status,body.card-only .search-card .examples,body.card-only .note-grid,body.card-only footer{display:none!important}body.card-only main{padding:14px 12px 40px!important;max-width:760px!important}body.card-only .search-card{border:0!important;box-shadow:none!important;background:transparent!important;padding:0!important;margin:0!important;min-height:0!important}body.card-only .result-wrap{margin-top:0!important}.card-only-bar{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:10px;padding-bottom:10px;border-bottom:1px solid var(--border,#e5e2db)}.card-only-bar a.cb-brand{text-decoration:none;color:var(--navy,#132D65);font-weight:800;font-size:.95rem;display:flex;flex-direction:column;line-height:1.1}.card-only-bar a.cb-brand span{font-family:\'DM Mono\',monospace;font-size:.6rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted,#6b6760);font-weight:500}.card-only-bar a.cb-search{font-size:.74rem;font-weight:700;text-decoration:none;color:#fff;background:var(--orange,#FD890E);border-radius:999px;padding:7px 13px;white-space:nowrap}';
    document.head.appendChild(st);
  }
  function injectSiteNote(result){
    if(!result || result.querySelector('.site-note')) return;
    var txt=(result.textContent||'');
    if(txt.indexOf('250 BALTIC STREET')<0 && txt.indexOf('250 Baltic Street')<0) return;
    var box=document.createElement('div');
    box.className='site-note';
    box.setAttribute('style','margin:12px 0;padding:13px 14px;background:#0d1b4b;border:2px solid #f47920;border-radius:12px');
    box.innerHTML='<div style="font-family:\'DM Mono\',monospace;font-size:.56rem;text-transform:uppercase;letter-spacing:.1em;color:#f47920;font-weight:700;margin-bottom:6px">&#127968; Suggested for the LIFT list</div>'+
      '<div style="color:#fff;font-size:.95rem;font-weight:900;line-height:1.32">The Mayor&rsquo;s LIFT list has 120 city owned sites for housing. We&rsquo;d like to add one more.</div>'+
      '<div style="color:rgba(255,255,255,.8);font-size:.8rem;line-height:1.55;margin-top:6px">Four floors above the CB6 office have been empty for a couple of years. The city owns the building and the lot is already zoned for housing.</div>'+
      '<a href="/blockbyblock/#propose-250baltic" style="display:inline-block;margin-top:10px;background:#f47920;color:#fff;text-decoration:none;font-size:.78rem;font-weight:800;padding:8px 13px;border-radius:18px">See it on Block by Block &rarr;</a>';
    var first=result.firstElementChild;
    if(first && first.nextElementSibling) result.insertBefore(box, first.nextElementSibling);
    else result.appendChild(box);
  }
  function injectCardBar(result){
    if(!cardModeRequested()||!result||result.querySelector('.card-only-bar')) return;
    var base=location.origin+location.pathname;
    var bar=document.createElement('div');
    bar.className='card-only-bar';
    bar.innerHTML='<a class="cb-brand" href="index.html">CB6 &amp; Beyond<span>NYC civic lookup</span></a><a class="cb-search" href="'+base+'">New search &rarr;</a>';
    result.insertBefore(bar,result.firstChild);
    hoistResult(result);
  }
  function hoistResult(result){
    if(!cardModeRequested()||!result||result.dataset.cardHoisted==='true') return;
    var main=document.querySelector('main')||document.body;
    if(main && result.parentNode){ main.insertBefore(result,main.firstChild); result.dataset.cardHoisted='true'; }
  }
  function bindShare(root){
    if(!root) return;
    Array.prototype.forEach.call(root.querySelectorAll('.citywide-share-btn'),function(btn){
      if(btn.dataset.shareBound==='true') return;
      btn.dataset.shareBound='true';
      btn.addEventListener('click',function(){
        var address=btn.getAttribute('data-share-address')||'';
        var url=shareUrlFor(address,true);
        var title='Citywide Address Search — '+address;
        function flash(msg){var prev=btn.textContent; btn.textContent=msg; setTimeout(function(){btn.textContent=prev;},1800);}
        if(navigator.share){
          navigator.share({title:title,url:url}).then(function(){},function(){
            if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(url).then(function(){flash('Link copied');},function(){window.prompt('Copy this link to share:',url);});}
            else{window.prompt('Copy this link to share:',url);}
          });
          return;
        }
        if(navigator.clipboard&&navigator.clipboard.writeText){
          navigator.clipboard.writeText(url).then(function(){flash('Link copied');},function(){window.prompt('Copy this link to share:',url);});
        }else{
          window.prompt('Copy this link to share:',url);
        }
      });
    });
  }
  window.__bkcbBindShare = bindShare;

  function bindBoroughSearch(){
    applyCardMode();
    var h=document.querySelector('.bh-title h2');
    var titleGuess=(h&&h.textContent||'').replace(/by CB/i,'').trim() || (document.title||'').split('—')[0].trim();
    var pageBoroughName=knownBoroughName(titleGuess);
    function bindInstance(root, input, status, result, button){
      if(!input||!result||input.dataset.fullProfileBound==='true') return null;
      var declared=root&&root.getAttribute&&root.getAttribute('data-borough-name');
      var boroughName=(input.id === 'citywide-borough-address-input') ? '' : (knownBoroughName(declared)||pageBoroughName);
      async function runFull(){
        var q=input.value.trim();
        if(!q){if(status) status.textContent='Enter an address to search.'; result.hidden=true; result.innerHTML=''; return;}
        var explicit=explicitBoroughInQuery(q);
        if(boroughName && explicit && explicit!==boroughName){
          if(status) status.textContent='This '+boroughName+' page searches '+boroughName+' addresses only. Use Citywide Search for '+explicit+' addresses.';
          result.hidden=true; result.innerHTML=''; return;
        }
        if(status) status.textContent='Searching full '+(boroughName||'citywide')+' address profile…';
        result.hidden=true; result.innerHTML='';
        try{var profile=await build(q,{boroughName:boroughName,shortLabel:boroughName}); result.innerHTML=profile.html; result.hidden=false; initResultMap(result); bindShare(result); injectCardBar(result); injectSiteNote(result); stampUrl(q); if(status) status.textContent=profile.status || 'Search complete.';}catch(err){console.error(err); if(status) status.textContent=err&&err.message?err.message:'Address lookup failed. Please try a full NYC street address.'; result.hidden=true; result.innerHTML='';}
      }
      input.dataset.fullProfileBound='true';
      if(button && button.dataset.fullProfileBound!=='true'){button.dataset.fullProfileBound='true'; button.addEventListener('click', function(e){e.preventDefault(); e.stopImmediatePropagation(); runFull();}, true);}
      input.addEventListener('keydown', function(e){if(e.key==='Enter'){e.preventDefault(); e.stopImmediatePropagation(); runFull();}}, true);
      if(root){Array.prototype.forEach.call(root.querySelectorAll('[data-example]'),function(btn){if(btn.dataset.exampleBound==='true') return; btn.dataset.exampleBound='true'; btn.addEventListener('click',function(){input.value=btn.getAttribute('data-example')||''; runFull();});});}
      return runFull;
    }
    Array.prototype.forEach.call(document.querySelectorAll('[data-full-profile-search]'),function(root){
      var runFull=bindInstance(root,root.querySelector('[data-full-profile-input]'),root.querySelector('[data-full-profile-status]'),root.querySelector('[data-full-profile-result]'),root.querySelector('[data-full-profile-button]'));
      if(runFull){
        var inp=root.querySelector('[data-full-profile-input]');
        try{var qp=new URLSearchParams(location.search).get('address'); if(qp && inp && !inp.value){inp.value=qp; runFull();}}catch(e){}
      }
    });
    Array.prototype.forEach.call(document.querySelectorAll('[id$="-borough-address-input"]'),function(input){
      var id=input.id.replace(/-input$/,'');
      var root=input.closest ? input.closest('.zoning-search-panel') : null;
      var runFull=bindInstance(root,input,document.getElementById(id+'-search-status'),document.getElementById(id+'-search-result'),document.getElementById(id+'-search-btn'));
      var m=input.id.match(/^([a-z]{2})-/), code=m?m[1].toUpperCase():'';
      if(runFull && code){window['run'+code+'BoroughAddressSearch']=runFull;}
      if(runFull){
        try{
          var qp=new URLSearchParams(location.search).get('address');
          if(qp && !input.value){input.value=qp; runFull();}
        }catch(e){}
      }
    });
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', bindBoroughSearch); else bindBoroughSearch();
})();
