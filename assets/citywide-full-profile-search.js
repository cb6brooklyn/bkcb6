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
  function render(input,a,foundCd,lat,lng,pluto,landmarks,n,context){context=context||{}; pluto=pluto||{}; var ed=parseInt(a.electionDistrict,10), ad=parseInt(a.assemblyDistrict,10), council=districtNumber(a.cityCouncilDistrict), senate=districtNumber(a.stateSenatorialDistrict), cong=districtNumber(a.congressionalDistrict), school=districtNumber(addressValue(a,['communitySchoolDistrict','schoolDistrict','schoolDistrictNumber'])||pluto.schooldist), police=districtNumber(addressValue(a,['policePrecinct','policePrecinctCode','nycPolicePrecinct'])||pluto.policeprct); var bbl=normalizeBbl(a.bbl)||normalizeBbl(pluto.bbl), b=bbl.slice(0,1)||String(foundCd||'').charAt(0), block=bbl.slice(1,6), lot=bbl.slice(6,10); var cb=validCommunityBoardCode(foundCd)?String(foundCd):String(a.communityDistrict||pluto.cd||''); var cbLabel=validCommunityBoardCode(cb)?boardLabel(cb):'Community Board not identified'; var zones=collectZones(a,pluto), zDisp=zones.length?zones.join(' / '):'Not available from PLUTO'; var spDists=collectSpecialDistricts(pluto), spDisp=spDists.length?spDists.join(' / '):''; var lUse=landUseLabel(pluto.landuse); var hd=(landmarks&&landmarks.historicDistricts)||[]; var historic=hd.length?hd.join(' / '):'Not in an LPC historic district'; var dob=b&&block&&lot?'https://a810-bisweb.nyc.gov/bisweb/PropertyBrowseByBBLServlet?allborough='+encodeURIComponent(b)+'&allblock='+parseInt(block,10)+'&alllot='+parseInt(lot,10)+'&filetype=html&requestid=0':'#'; var zola=b&&block&&lot?'https://zola.planning.nyc.gov/l/lot/'+encodeURIComponent(b)+'/'+parseInt(block,10)+'/'+parseInt(lot,10):'#'; var acris=b&&block&&lot?'https://a836-acris.nyc.gov/DS/DocumentSearch/BBL?REQUEST_BBL='+encodeURIComponent(b)+block+lot:'#'; var zap=block&&lot?'https://zap.planning.nyc.gov/projects?block='+parseInt(block,10)+'&lot='+parseInt(lot,10):'#'; var enc=encodeURIComponent(input); var cards=mini(zones.length>1?'Zoning Districts':'Zoning District',zDisp)+(spDists.length?mini(spDists.length>1?'Special Districts':'Special District',spDisp):'')+mini('Land Use',lUse)+mini('Landmark Status',historic)+mini('Election District',Number.isFinite(ed)?ed:'—')+mini('Assembly',repLabel('state_assembly',ad,'Assembly District'))+mini('City Council',repLabel('city_council',council,'Council District'))+mini('State Senate',repLabel('state_senate',senate,'State Senate District'))+mini('Congress',repLabel('congress',cong,'Congressional District'))+mini('School District',school?'CSD '+school:'—')+mini('Police Precinct',police?police+' Precinct':'—')+mini('Zoning Code Explanation',zones.length?zones.map(function(z){return z+': '+zoningPlain(z);}).join(' / '):'Check ZoLa for exact district controls.')+mini('Use Group Explanation',landUsePlain(pluto.landuse,lUse))+propertyMini('Owner',pluto.ownername||pluto.owner||a.ownerName||a.ownername)+mini('Community Board',cbLabel)+mini('Borough',pluto.borough||a.firstBoroughName||BOROUGH_NAMES[b]||'—')+propertyMini('Year Built',fmtNum(pluto.yearbuilt,''))+propertyMini('Building Class',pluto.bldgclass)+propertyMini('Lot Area',fmtNum(pluto.lotarea,' sq ft'))+propertyMini('Building Area',fmtNum(pluto.bldgarea,' sq ft'))+propertyMini('Residential Units',fmtNum(pluto.unitsres,''))+propertyMini('Total Units',fmtNum(pluto.unitstotal,'')); return '<div style="background:#f0f8f4;border:1.5px solid #a7f3d0;border-radius:8px;padding:12px 14px;margin-top:4px"><div style="font-size:.85rem;font-weight:700;color:var(--navy,#0d1b4b);margin-bottom:2px">&#10003; '+esc(input)+'</div><div style="font-size:.75rem;color:var(--muted,#6b6760);margin-bottom:8px">'+esc(cbLabel)+' &middot; ED '+(Number.isFinite(ed)?ed:'—')+' &middot; AD '+(Number.isFinite(ad)?ad:'—')+(council?' &middot; Council District '+esc(council):'')+(senate?' &middot; State Senate District '+esc(senate):'')+(cong?' &middot; Congressional District '+esc(cong):'')+(school?' &middot; School District '+esc(school):'')+(police?' &middot; Police Precinct '+esc(police):'')+'</div><div class="citywide-result-map" data-lat="'+lat+'" data-lng="'+lng+'" data-label="'+esc(input)+'" style="height:240px;border-radius:8px;border:1px solid #a7f3d0;margin-bottom:10px;background:#eef2f7"></div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:8px;margin-bottom:10px">'+cards+'</div><div style="background:#fff;border:1px solid #d1fae5;border-radius:6px;padding:9px 10px;margin-bottom:10px;font-size:.73rem;line-height:1.45;color:var(--navy,#0d1b4b)"><div><strong>Zoning:</strong> '+(zones.length?zones.map(function(z){return '<strong>'+esc(z)+'</strong>: '+esc(zoningPlain(z));}).join('<br>'):'Zoning was not available from PLUTO for this address.')+'</div><div style="margin-top:5px"><strong>Land use:</strong> '+esc(landUsePlain(pluto.landuse,lUse))+'</div>'+(spDists.length?'<div style="margin-top:5px"><strong>Special district:</strong> This lot is in the '+esc(spDisp)+' special purpose district, which adds its own zoning rules on top of the base district.</div>':'')+(hd.length?'<div style="margin-top:5px"><strong>Historic district:</strong> This is in a historic district, so exterior changes usually need LPC review.</div>':'')+'</div>'+nearbyHtml(n)+'<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px"><a href="'+dob+'" target="_blank" style="font-size:.73rem;font-weight:600;color:var(--navy,#0d1b4b);text-decoration:none;padding:5px 10px;border:1px solid var(--border,#e5e2db);border-radius:5px;background:#fff">DOB BIS</a><a href="'+zap+'" target="_blank" style="font-size:.73rem;font-weight:600;color:var(--navy,#0d1b4b);text-decoration:none;padding:5px 10px;border:1px solid var(--border,#e5e2db);border-radius:5px;background:#fff">ZAP Projects</a><a href="'+acris+'" target="_blank" style="font-size:.73rem;font-weight:600;color:var(--navy,#0d1b4b);text-decoration:none;padding:5px 10px;border:1px solid var(--border,#e5e2db);border-radius:5px;background:#fff">ACRIS Deeds</a><a href="'+zola+'" target="_blank" style="font-size:.73rem;font-weight:600;color:#2e7d32;text-decoration:none;padding:5px 10px;border:1px solid #a5d6a7;border-radius:5px;background:#f1f8f1">ZoLa Zoning</a><a href="https://maps.google.com/?q='+lat+','+lng+'" target="_blank" style="font-size:.73rem;font-weight:600;color:var(--navy,#0d1b4b);text-decoration:none;padding:5px 10px;border:1px solid var(--border,#e5e2db);border-radius:5px;background:#fff">Map</a><button type="button" class="citywide-share-btn" data-share-address="'+esc(input)+'" style="font-size:.73rem;font-weight:700;color:#fff;cursor:pointer;padding:5px 12px;border:1px solid var(--orange,#FD890E);border-radius:5px;background:var(--orange,#FD890E)">Share card</button></div><div style="border-top:1px solid #d1fae5;padding-top:8px;display:flex;flex-wrap:wrap;gap:12px"><a href="'+(boardSlug(cb)?boardSlug(cb)+'?addr='+enc+'#sec-map':'mydistricts.html?address='+enc)+'" style="font-size:.75rem;color:var(--navy,#0d1b4b);font-weight:700;text-decoration:none;border-bottom:1px solid var(--navy,#0d1b4b)">Open '+esc(cbLabel)+' district profile &rarr;</a></div></div>';}
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
  async function build(q, context){context=context||{}; var a=await geoclient(q,context.boroughName); var lat=parseFloat(a.latitude), lng=parseFloat(a.longitude); if(!Number.isFinite(lat)||!Number.isFinite(lng)) throw new Error('Address coordinates not found'); var foundCd=String(a.communityDistrict||''); if(!validCommunityBoardCode(foundCd)) foundCd=''; var bbl=normalizeBbl(a.bbl); var r=await Promise.allSettled([fetchPluto(bbl,lat,lng),fetchLandmarks(bbl),nearby(lat,lng,foundCd,a),fetchSpecialDistrictByPoint(lat,lng)]); var pluto=r[0].status==='fulfilled'?r[0].value:{}, lm=r[1].status==='fulfilled'?r[1].value:{historicDistricts:[]}, near=r[2].status==='fulfilled'?r[2].value:{}; var spPoint=r[3].status==='fulfilled'?r[3].value:null; if(spPoint&&pluto){var hasSp=collectSpecialDistricts(pluto).length>0; if(!hasSp&&(spPoint.spdist1||spPoint.spdist2||spPoint.spdist3)){pluto.spdist1=pluto.spdist1||spPoint.spdist1; pluto.spdist2=pluto.spdist2||spPoint.spdist2; pluto.spdist3=pluto.spdist3||spPoint.spdist3;}} var html=render(q,a,foundCd,lat,lng,pluto,lm,near,context); return {input:q,address:a,lat:lat,lng:lng,foundCd:foundCd,pluto:pluto,landmarkStatus:lm,nearby:near,html:html,status:foundCd?'Search complete: address is in '+boardLabel(foundCd)+'.':'Search complete: address found.'};}
  window.__bkcbBuildFullAddressProfile = build;
  function zoneFam(z){z=String(z||'').toUpperCase().trim(); if(!z) return 'Other'; if(/^MX/.test(z)) return 'Mixed Use'; if(z.indexOf('/')>-1 && /M\d/.test(z) && /R\d/.test(z)) return 'Mixed Use'; if(/^R/.test(z)) return 'Residential'; if(/^C/.test(z)) return 'Commercial'; if(/^M/.test(z)) return 'Manufacturing'; if(/PARK|PLAYGROUND/.test(z)) return 'Park/Open Space'; if(/^BPC/.test(z)) return 'Mixed Use'; return 'Other';}
  var ZONE_FAM_GRAY={'Residential':'#e0e0e0','Commercial':'#9e9e9e','Manufacturing':'#4a4a4a','Park/Open Space':'#c4c4c4','Mixed Use':'#757575','Other':'#b3b3b3'};
  var ZONE_FAM_LABEL={'Residential':'#f7c948','Commercial':'#2f6fed','Manufacturing':'#c2410c','Park/Open Space':'#15803d','Mixed Use':'#9333ea','Other':'#475569'};
  function zoneGray(z){var fam=zoneFam(z); return [fam, ZONE_FAM_GRAY[fam]||ZONE_FAM_GRAY.Other];}
  function loadResultZoning(map,lat,lng){
    var dy=0.0035, dx=0.0045;
    var env={xmin:lng-dx,ymin:lat-dy,xmax:lng+dx,ymax:lat+dy,spatialReference:{wkid:4326}};
    var url='https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services/nyzd/FeatureServer/0/query?where=1%3D1&outFields=ZONEDIST&returnGeometry=true&outSR=4326&geometry='+encodeURIComponent(JSON.stringify(env))+'&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&f=geojson&resultRecordCount=400';
    fetch(url).then(function(r){return r.json();}).then(function(d){
      if(!d||!d.features||!d.features.length) return;
      var fams={};
      var layer=L.geoJSON(d,{
        style:function(f){var z=(f.properties||{}).ZONEDIST||'';var g=zoneGray(z);fams[g[0]]=g[1];return{color:'#333',weight:1,opacity:.9,fillColor:g[1],fillOpacity:.55};},
        onEachFeature:function(f,l){var z=(f.properties||{}).ZONEDIST||'Zoning';var g=zoneGray(z);l.bindPopup('<strong>'+esc(z)+'</strong><br>'+g[0]); if(z){var c=l.getBounds&&l.getBounds().isValid&&l.getBounds().isValid()?l.getBounds().getCenter():null; if(c){var col=ZONE_FAM_LABEL[g[0]]||ZONE_FAM_LABEL.Other; L.tooltip({permanent:true,direction:'center',className:'zone-label',opacity:1}).setLatLng(c).setContent('<span style="color:'+col+'">'+esc(z)+'</span>').addTo(map);}}}
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
  function initResultMap(root){
    if(typeof L==='undefined'||!root) return;
    var el=root.querySelector('.citywide-result-map');
    if(!el||el.dataset.mapReady==='true') return;
    var lat=parseFloat(el.getAttribute('data-lat')), lng=parseFloat(el.getAttribute('data-lng'));
    if(!Number.isFinite(lat)||!Number.isFinite(lng)) return;
    el.dataset.mapReady='true';
    try{
      var map=L.map(el,{scrollWheelZoom:false}).setView([lat,lng],16);
      L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',{maxZoom:19,attribution:'&copy; OpenStreetMap &copy; CARTO'}).addTo(map);
      loadResultZoning(map,lat,lng);
      L.marker([lat,lng]).addTo(map).bindPopup(el.getAttribute('data-label')||'Searched address');
      setTimeout(function(){map.invalidateSize();},120);
    }catch(e){console.error(e);}
  }
  window.__bkcbInitResultMap = initResultMap;

  function cardModeRequested(){
    try{return new URLSearchParams(location.search).get('card')==='1';}catch(e){return false;}
  }
  function shareUrlFor(address,cardOnly){
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
    st.textContent='body.card-only header,body.card-only .hero,body.card-only .search-card>h3,body.card-only .search-card>p,body.card-only .search-card .search-row,body.card-only .search-card .status,body.card-only .search-card .examples,body.card-only .note-grid,body.card-only footer{display:none!important}body.card-only main{padding:14px 12px 40px!important;max-width:760px!important}body.card-only .search-card{border:0!important;box-shadow:none!important;background:transparent!important;padding:0!important;margin:0!important}body.card-only .result-wrap{margin-top:0!important}.card-only-bar{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:10px;padding-bottom:10px;border-bottom:1px solid var(--border,#e5e2db)}.card-only-bar a.cb-brand{text-decoration:none;color:var(--navy,#132D65);font-weight:800;font-size:.95rem;display:flex;flex-direction:column;line-height:1.1}.card-only-bar a.cb-brand span{font-family:\'DM Mono\',monospace;font-size:.6rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted,#6b6760);font-weight:500}.card-only-bar a.cb-search{font-size:.74rem;font-weight:700;text-decoration:none;color:#fff;background:var(--orange,#FD890E);border-radius:999px;padding:7px 13px;white-space:nowrap}';
    document.head.appendChild(st);
  }
  function injectCardBar(result){
    if(!cardModeRequested()||!result||result.querySelector('.card-only-bar')) return;
    var base=location.origin+location.pathname;
    var bar=document.createElement('div');
    bar.className='card-only-bar';
    bar.innerHTML='<a class="cb-brand" href="index.html">CB6 &amp; Beyond<span>NYC civic lookup</span></a><a class="cb-search" href="'+base+'">New search &rarr;</a>';
    result.insertBefore(bar,result.firstChild);
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
        try{var profile=await build(q,{boroughName:boroughName,shortLabel:boroughName}); result.innerHTML=profile.html; result.hidden=false; initResultMap(result); bindShare(result); injectCardBar(result); stampUrl(q); if(status) status.textContent=profile.status || 'Search complete.';}catch(err){console.error(err); if(status) status.textContent=err&&err.message?err.message:'Address lookup failed. Please try a full NYC street address.'; result.hidden=true; result.innerHTML='';}
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
