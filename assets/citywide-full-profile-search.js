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
    'MX-11':'This lot sits in Special Mixed Use District MX-11, the Gowanus pairing of an M1 manufacturing district with an R7 residence district. MX districts let residential and light industrial uses share a block, each following its own half of the pair, with performance standards on the industrial side so the two can sit next to each other.',
    'SG':'The Special Gowanus Mixed Use District was created by the 2021 Gowanus rezoning. It pairs residential and light-manufacturing (M1) districts so housing and industry can sit side by side, and is organized into five subdistricts with their own rules. It layers in Mandatory Inclusionary Housing in mapped areas, treats blocks along the Gowanus Canal as waterfront subject to a Waterfront Access Plan, and adds environmental, ground-floor, and streetscape requirements on top of the base zoning.'
  };
  var SPECIAL_DISTRICT_WHAT='A special purpose district is an extra layer of zoning mapped over the base districts. The City Planning Commission creates one to meet goals in a defined area, and its rules modify, supplement or override the zoning underneath, with the special district controlling wherever the two conflict.';
  function specialDistrictExplain(spDisp,codes){
    var keys=[];
    (codes||[]).forEach(function(c){
      var v=String(c||'').toUpperCase().trim(); if(!v) return;
      keys.push(v);
      var m=v.match(/\(([^)]+)\)/); if(m) keys.push(m[1].trim());
      keys.push(v.replace(/\s*\([^)]*\)\s*/,'').trim());
    });
    for(var i=0;i<keys.length;i++){ if(SPECIAL_DISTRICT_EXPLAIN[keys[i]]) return SPECIAL_DISTRICT_WHAT+' '+SPECIAL_DISTRICT_EXPLAIN[keys[i]]; }
    for(var j=0;j<keys.length;j++){ if(/GOWANUS/.test(keys[j])) return SPECIAL_DISTRICT_WHAT+' '+SPECIAL_DISTRICT_EXPLAIN.G; }
    return SPECIAL_DISTRICT_WHAT+' This lot is in the '+spDisp+' special purpose district.';
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
  // Every combination of zoning family and PLUTO land use, explained.
  // ok:true means the two agree and the note just says why. ok:false means they read as
  // different things and the note says how that happens.
  var USE_GAP={
    R:{
      '01':{ok:1,t:'One and two family homes are exactly what a residence district is mapped for. The district number and any suffix set how much more could be built here.'},
      '02':{ok:1,t:'Walk-up apartments are a residential use in a residence district. Whether the building uses all the floor area the district allows is a separate question.'},
      '03':{ok:1,t:'Elevator apartments are a residential use in a residence district, and usually a sign the district permits real density.'},
      '04':{ok:1,t:'A building with apartments over stores in a residence district almost always means a commercial overlay, a C1 or C2 mapped along the avenue, or a store that predates the zoning.'},
      '05':{ok:0,t:'A commercial or office building on residentially zoned land is usually one of three things: a commercial overlay mapped over the residence district, a use that predates the current zoning and is allowed to continue, or a use that holds a variance from the Board of Standards and Appeals.'},
      '06':{ok:0,t:'Industrial use on residentially zoned land is a legal nonconforming use. It predates the zoning that would bar it today, may continue, but cannot expand, and if it stops for two years the right is lost.'},
      '07':{ok:0,t:'Transportation and utility uses sit in residence districts all over the city. Many are permitted by special permit, some are public infrastructure outside ordinary zoning, and rail and highway land often keeps whatever district was mapped around it.'},
      '08':{ok:1,t:'Schools, houses of worship, libraries, hospitals and community centers are permitted as of right in residence districts. R does not mean only housing, and this is the clearest example of that.'},
      '09':{ok:0,t:'Parks and open space are frequently mapped inside residence districts rather than given their own designation. The Parks Department has jurisdiction over public parkland whatever the zoning says, and converting it takes an act of the State Legislature, not a rezoning.'},
      '10':{ok:0,t:'Parking on residentially zoned land is normally accessory parking for nearby housing, a lot that predates the zoning, or a facility approved by special permit. A standalone commercial garage is not an as of right use in a residence district.'},
      '11':{ok:0,t:'Vacant land in a residence district is land the zoning already allows housing on. Nothing is recorded as built here, so the district and its density are the whole story of what could go up.'}
    },
    C:{
      '01':{ok:1,t:'Housing is permitted as of right in C1, C2, C4, C5 and C6. A one or two family home on commercially zoned land is a legal residential use, often a holdover from before the avenue was upzoned.'},
      '02':{ok:1,t:'Walk-up apartments are permitted in most commercial districts. Only C7 and C8 exclude residences.'},
      '03':{ok:1,t:'Elevator apartments are permitted in most commercial districts, and residential floor area in a C district is usually governed by an equivalent R district.'},
      '04':{ok:1,t:'Apartments over stores is the classic commercial district building, and what most C districts along a shopping street are mapped to produce.'},
      '05':{ok:1,t:'A commercial or office building in a commercial district is exactly what the mapping anticipates.'},
      '06':{ok:0,t:'Industrial use in a commercial district is as of right only in C8, which is mapped for auto and repair uses. Anywhere else it predates the zoning or holds a variance.'},
      '07':{ok:0,t:'Transportation and utility uses in commercial districts are often permitted by special permit or are public infrastructure that the zoning map runs across rather than around.'},
      '08':{ok:1,t:'Schools, hospitals, houses of worship and government uses are widely permitted in commercial districts.'},
      '09':{ok:0,t:'Open space on commercially zoned land is usually public parkland the zoning map never redrew, or a privately owned public space built in exchange for extra floor area.'},
      '10':{ok:1,t:'Parking facilities are permitted in most commercial districts, sometimes as of right and sometimes by special permit depending on the district and the size.'},
      '11':{ok:0,t:'Vacant land in a commercial district is a site the zoning already allows retail, offices and, in most C districts, housing on.'}
    },
    M:{
      '01':{ok:0,t:'Housing is not permitted as of right in a manufacturing district. A one or two family home here predates the zoning, sits in a paired Mixed Use district, or holds a variance. It may continue but cannot expand.'},
      '02':{ok:0,t:'Apartments in a manufacturing district are a nonconforming use or a converted loft. Many are legal under the Loft Law, which brought residential conversions in industrial buildings into the legal system without changing the zoning.'},
      '03':{ok:0,t:'An elevator apartment building on manufacturing zoned land almost always means a conversion, a variance, or a rezoning that has not been reflected in this record.'},
      '04':{ok:0,t:'Apartments over stores in a manufacturing district is a nonconforming residential use with commercial space that the district would allow on its own.'},
      '05':{ok:1,t:'Offices and retail are widely permitted in manufacturing districts. M does not mean only factories. What M bars as of right is housing.'},
      '06':{ok:1,t:'Industrial and manufacturing use in a manufacturing district, which is what the district is mapped for. The number after the M sets the performance standards for noise, odor, vibration and emissions.'},
      '07':{ok:1,t:'Transportation and utility uses are permitted in manufacturing districts, and much of the city\u2019s infrastructure is deliberately mapped into them.'},
      '08':{ok:0,t:'Public facilities and institutions in a manufacturing district vary by use. Some are permitted, schools and houses of worship generally are not as of right, and those that exist usually predate the zoning or hold a special permit.'},
      '09':{ok:0,t:'Open space on manufacturing zoned land is common on the waterfront, where parkland was carved out of industrial areas without the zoning map being redrawn underneath it.'},
      '10':{ok:1,t:'Parking and storage of vehicles is a normal, permitted use in manufacturing districts.'},
      '11':{ok:0,t:'Vacant land in a manufacturing district is a site where industry, warehousing, offices and retail are allowed as of right, and housing is not without a rezoning.'}
    },
    MX:{
      '01':{ok:1,t:'A paired Mixed Use district allows housing and light industry on the same block. A one or two family home here follows the residential half of the pair.'},
      '02':{ok:1,t:'Walk-up apartments are permitted under the residential half of the pair. The manufacturing half continues to govern industrial uses on the same lot.'},
      '03':{ok:1,t:'Elevator apartments follow the residential half of the pair for density, bulk and height. This is what the pairing is designed to allow.'},
      '04':{ok:1,t:'Apartments over stores is a natural outcome in a Mixed Use district, where residential and commercial rules both apply.'},
      '05':{ok:1,t:'Commercial and office use is permitted under both halves of a Mixed Use pairing.'},
      '06':{ok:1,t:'Industrial use is permitted under the manufacturing half of the pair. That is the point of the pairing: industry stays, housing becomes possible next to it.'},
      '07':{ok:1,t:'Transportation and utility uses are permitted under the manufacturing half of the pairing.'},
      '08':{ok:1,t:'Schools, houses of worship and institutions are permitted under the residential half of the pairing.'},
      '09':{ok:0,t:'Open space in a Mixed Use district is usually public land or an esplanade required by the rezoning that created the pairing, rather than the zoning being wrong.'},
      '10':{ok:1,t:'Parking is permitted under the manufacturing half of the pairing.'},
      '11':{ok:0,t:'Vacant land in a Mixed Use district is a site where both housing and light industry are allowed as of right. This is the zoning most often mapped to get housing built on former industrial blocks.'}
    },
    PARK:{
      '01':{ok:0,t:'A home on mapped parkland is almost always a caretaker residence or a structure that predates the mapping. Parks jurisdiction, not zoning, governs what happens here.'},
      '02':{ok:0,t:'Residential buildings on mapped parkland predate the mapping or serve the park itself. Converting parkland to another use requires an act of the State Legislature.'},
      '03':{ok:0,t:'An apartment building on mapped parkland is a record that predates the mapping or a boundary that runs through the lot. Parks jurisdiction controls.'},
      '04':{ok:0,t:'Mixed residential and commercial use on mapped parkland predates the mapping. It is not something the mapping would permit today.'},
      '05':{ok:0,t:'Commercial use on mapped parkland is normally a concession operating under a Parks agreement rather than a zoning permission.'},
      '06':{ok:0,t:'Industrial use on mapped parkland predates the mapping. Parkland is not an ordinary zoning district and industry is not a park use.'},
      '07':{ok:0,t:'Transportation and utility infrastructure runs through mapped parkland all over the city, often under easements older than the park.'},
      '08':{ok:1,t:'Recreation centers, pools, museums and comfort stations on mapped parkland are park facilities. This is a normal reading.'},
      '09':{ok:1,t:'Open space on mapped parkland is what the mapping is for. The Parks Department has jurisdiction, and converting it to another use requires an act of the State Legislature, not a rezoning.'},
      '10':{ok:1,t:'Parking on mapped parkland is normally a lot serving the park itself.'},
      '11':{ok:0,t:'Vacant mapped parkland is land held for park use. It is not a development site in the way a vacant zoning lot is.'}
    }
  };
  function zoneFamilyKey(z){z=String(z||'').trim().toUpperCase();
    if(z.indexOf('/')>-1) return 'MX';
    if(z==='PARK') return 'PARK';
    if(/^R/.test(z)) return 'R'; if(/^C/.test(z)) return 'C'; if(/^M/.test(z)) return 'M';
    return '';}
  var FAMILY_WORD={R:'a residence district',C:'a commercial district',M:'a manufacturing district',
    MX:'a paired Mixed Use district',PARK:'mapped parkland'};
  function zoneUseNote(z,code){
    var fam=zoneFamilyKey(z), key=String(code||'').trim().padStart(2,'0');
    if(!fam||!USE_GAP[fam]||!USE_GAP[fam][key]) return null;
    var e=USE_GAP[fam][key];
    return {ok:!!e.ok, head:(e.ok?'Zoning and current use line up':'Zoned one way, used another'),
      text:z+' is '+FAMILY_WORD[fam]+'. '+e.t};
  }
  function zoneWords(z){
    z=String(z||'').trim().toUpperCase(); if(!z) return '';
    if(z==='PARK') return 'Mapped parkland';
    if(z.indexOf('/')>-1){
      var parts=z.split('/').map(function(x){return x.trim();}).filter(Boolean);
      var names=parts.map(function(x){return /^R/.test(x)?'residential':(/^C/.test(x)?'commercial':(/^M/.test(x)?'manufacturing':'other'));});
      var uniq=names.filter(function(v,i,a){return a.indexOf(v)===i;});
      return uniq.join(' paired with ').replace(/^./,function(c){return c.toUpperCase();})+', a Mixed Use district';
    }
    if(/^R/.test(z)) return 'Residential district';
    if(/^C/.test(z)) return 'Commercial district';
    if(/^M/.test(z)) return 'Manufacturing district';
    return 'Mapped zoning district';
  }
  function zoneBase(z){z=String(z||'').trim().toUpperCase(); if(!z) return '';
    if(/^R/.test(z)) return 'a residence district. The number sets permitted density and building form, and any letter suffix refines bulk, height, parking or contextual rules.';
    if(/^C/.test(z)) return 'a commercial district. It permits retail, office, service or mixed commercial uses depending on the district and any overlay.';
    if(/^M/.test(z)) return 'a manufacturing district. It permits industrial, warehouse, production and certain commercial uses subject to performance standards.';
    if(/^PARK$/.test(z)) return 'mapped parkland or open space, not an ordinary zoning district.';
    return 'a mapped zoning district. Check ZoLa for exact controls, overlays and special district rules.';}
  function zoningPlain(z){z=String(z||'').trim().toUpperCase(); if(!z) return '';
    if(z.indexOf('/')>-1){
      var parts=z.split('/').map(function(x){return x.trim();}).filter(Boolean);
      var each=parts.map(function(x){return x+' is '+zoneBase(x);}).join(' ');
      return 'a paired Mixed Use district, two districts mapped together on the same lot rather than one district with a slash in its name. '+each+
        ' Because both are mapped here, housing and light industry are each allowed, every use governed by its own half of the pair, and a residential building follows the '+
        (parts.filter(function(x){return /^R/.test(x);})[0]||parts[parts.length-1])+' rules for density, bulk and height. Pairings like this are how the city puts homes and industry on the same block instead of separating them.';
    }
    return zoneBase(z);}
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
  function baseDistricts(z){
    return String(z||'').split('/').map(function(part){return baseDistrict(part);})
      .filter(function(b,i,arr){return b && arr.indexOf(b)===i;});
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
    var bases=String(base).split(',').filter(Boolean), paired=bases.length>1;
    var RANK={N:0,S:1,L:2,Y:3};
    var rows=USEMATRIX.goals.filter(function(g){return USE_SHOW.indexOf(g.id)>-1;}).map(function(g){
      var row=USEMATRIX.matrix[g.ug];
      if(!row) return '';
      var vs=bases.map(function(b){return row[b]||null;});
      if(!vs.filter(Boolean).length) return '';
      var v=vs.filter(Boolean).sort(function(x,y){return RANK[y]-RANK[x];})[0];
      var best=bases[vs.indexOf(v)];
      var note=(g.notes&&g.notes[best])||'';
      if(paired){
        var parts=bases.map(function(b,i){return vs[i]?(b+': '+USE_LBL[vs[i]].toLowerCase()):null;}).filter(Boolean);
        note=parts.join(', ')+'. The lot takes the more permissive of the two.'+(note?' '+note:'');
      }
      var lab=g.q.replace(/^I want to /,'');
      lab=lab.charAt(0).toUpperCase()+lab.slice(1);
      return '<div style="display:flex;align-items:flex-start;gap:8px;padding:6px 0;border-bottom:1px solid #f0ede8">'+
        '<span style="flex:none;min-width:86px;text-align:center;font-size:.63rem;font-weight:800;padding:3px 6px;border-radius:5px;background:'+USE_BG[v]+';color:'+USE_FG[v]+'">'+USE_SYM[v]+' '+USE_LBL[v]+'</span>'+
        '<span style="flex:1;min-width:0"><span style="font-size:.75rem;font-weight:700;color:#0d1b4b">'+esc(lab)+'</span>'+
        (note?'<span style="display:block;font-size:.69rem;color:#6b6760;line-height:1.45;margin-top:1px">'+esc(note)+'</span>':'')+'</span></div>';
    }).join('');
    if(!rows){ el.style.display='none'; return; }
    var pairNote=paired?'<div style="font-size:.7rem;color:#0d1b4b;line-height:1.5;margin:0 0 7px;padding:8px 9px;background:#eef2fb;border-left:3px solid #2145a8;border-radius:0 5px 5px 0"><b>Two districts, one lot.</b> '+esc(rawz)+' is a paired Mixed Use district. Both sets of rules apply here, so a use permitted by either half is permitted on the lot. That is why housing is allowed on a lot whose name starts with M.</div>':'';
    el.innerHTML='<div style="font-size:.74rem;font-weight:700;color:#0d1b4b;margin-bottom:5px">What can be built here &middot; '+esc(paired?rawz:base)+' rules</div>'+pairNote+rows+
      bases.map(function(b){return '<div style="font-size:.7rem;color:#0d1b4b;line-height:1.5;margin-top:8px;padding:8px 9px;background:#f8f7f4;border-left:3px solid #f47920;border-radius:0 5px 5px 0"><b>'+esc(b.charAt(0))+' is a name, not a description.</b> '+esc(LETTER_NOTE[b.charAt(0)]||'')+'</div>';}).join('')+
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
  function render(input,a,foundCd,lat,lng,pluto,landmarks,n,context,facs){context=context||{}; pluto=pluto||{}; var ed=parseInt(a.electionDistrict,10), ad=parseInt(a.assemblyDistrict,10), council=districtNumber(a.cityCouncilDistrict), senate=districtNumber(a.stateSenatorialDistrict), cong=districtNumber(a.congressionalDistrict), school=districtNumber(addressValue(a,['communitySchoolDistrict','schoolDistrict','schoolDistrictNumber'])||pluto.schooldist), police=districtNumber(addressValue(a,['policePrecinct','policePrecinctCode','nycPolicePrecinct'])||pluto.policeprct); var bbl=normalizeBbl(a.bbl)||normalizeBbl(pluto.bbl), b=bbl.slice(0,1)||String(foundCd||'').charAt(0), block=bbl.slice(1,6), lot=bbl.slice(6,10); var cb=validCommunityBoardCode(foundCd)?String(foundCd):String(a.communityDistrict||pluto.cd||''); var cbLabel=validCommunityBoardCode(cb)?boardLabel(cb):'Community Board not identified'; var zones=collectZones(a,pluto), zDisp=zones.length?zones.join(' / '):'Not available from PLUTO'; var spDists=collectSpecialDistricts(pluto), spDisp=spDists.length?spDists.join(' / '):''; var lUse=landUseLabel(pluto.landuse); var hd=(landmarks&&landmarks.historicDistricts)||[]; var historic=hd.length?hd.join(' / '):'Not in an LPC historic district'; var dob=b&&block&&lot?'https://a810-bisweb.nyc.gov/bisweb/PropertyBrowseByBBLServlet?allborough='+encodeURIComponent(b)+'&allblock='+parseInt(block,10)+'&alllot='+parseInt(lot,10)+'&filetype=html&requestid=0':'#'; var zola=b&&block&&lot?'https://zola.planning.nyc.gov/l/lot/'+encodeURIComponent(b)+'/'+parseInt(block,10)+'/'+parseInt(lot,10):'#'; var acris=b&&block&&lot?'https://a836-acris.nyc.gov/DS/DocumentSearch/BBL?REQUEST_BBL='+encodeURIComponent(b)+block+lot:'#'; var zap=block&&lot?'https://zap.planning.nyc.gov/projects?block='+parseInt(block,10)+'&lot='+parseInt(lot,10):'#'; var enc=encodeURIComponent(input); var boardShort=validCommunityBoardCode(cb)?BOROUGH_SHORT[cb.charAt(0)]:'', boardNum=validCommunityBoardCode(cb)?parseInt(cb.slice(1),10):0;
    var cardLogo='';
    var siteIcon=SITE_ICON[liftNorm(input)]||null;
    var logoImg='';
    if(cb==='306'){ logoImg='<img src="/cb6-logo-card.png" alt="Brooklyn Community Board 6" width="500" height="500" loading="lazy" style="display:block;width:74px;height:74px;border-radius:6px">'; }
    else if(boardShort&&boardNum){ logoImg='<img src="/banners/banner-'+boardShort+'-'+boardNum+'.png" alt="'+esc(cbLabel)+'" width="540" height="270" loading="lazy" style="display:block;width:124px;height:62px;border-radius:5px;background:#fff">'; }
    if(logoImg||siteIcon){
      var iconImg=siteIcon?'<img src="'+siteIcon.src+'" alt="'+esc(siteIcon.alt)+'" width="'+siteIcon.w+'" height="'+siteIcon.h+'" loading="lazy" style="display:block;width:'+(cb==='306'?74:124)+'px;height:auto;border-radius:4px;background:#fff">':'';
      cardLogo='<div style="flex:none;display:flex;flex-direction:column;align-items:flex-end;gap:6px">'+logoImg+iconImg+'</div>';

    }
    var cards=mini(zones.length>1?'Zoning Districts':'Zoning District',zDisp)+(spDists.length?mini(spDists.length>1?'Special Districts':'Special District',spDisp):'')+mini('Land Use',lUse)+mini('Landmark Status',historic)+mini('Election District',Number.isFinite(ed)?ed:'—')+mini('Assembly',repLabel('state_assembly',ad,'Assembly District'))+mini('City Council',repLabel('city_council',council,'Council District'))+mini('State Senate',repLabel('state_senate',senate,'State Senate District'))+mini('Congress',repLabel('congress',cong,'Congressional District'))+mini('School District',school?'CSD '+school:'—')+mini('Police Precinct',police?police+' Precinct':'—')+mini('Zoning Code Explanation',zones.length?zones.map(function(z){return z+': '+zoningPlain(z);}).join(' / '):'Check ZoLa for exact district controls.')+mini('Use Group Explanation',landUsePlain(pluto.landuse,lUse))+propertyMini('Owner',pluto.ownername||pluto.owner||a.ownerName||a.ownername)+mini('Community Board',cbLabel)+mini('Borough',pluto.borough||a.firstBoroughName||BOROUGH_NAMES[b]||'—')+propertyMini('Year Built',fmtNum(pluto.yearbuilt,''))+propertyMini('Building Class',pluto.bldgclass)+propertyMini('Lot Area',fmtNum(pluto.lotarea,' sq ft'))+propertyMini('Building Area',fmtNum(pluto.bldgarea,' sq ft'))+propertyMini('Residential Units',fmtNum(pluto.unitsres,''))+propertyMini('Total Units',fmtNum(pluto.unitstotal,'')); return '<div data-cardtop style="scroll-margin-top:12px;position:relative;background:#f0f8f4;border:1.5px solid #a7f3d0;border-radius:8px;padding:12px 14px;margin-top:4px"><div data-cardaddr style="font-size:1.15rem;font-weight:900;line-height:1.2;color:var(--navy,#0d1b4b)">'+esc(input)+'</div><div style="font-size:.95rem;font-weight:600;line-height:1.35;color:var(--navy,#0d1b4b);margin-top:3px">is in <strong style="font-weight:900">'+esc(cbLabel)+'</strong></div><div style="display:flex;align-items:flex-start;gap:10px;margin:10px 0 9px"><div style="flex:1;min-width:0;background:#0d1b4b;border-radius:7px;padding:11px 13px;align-self:stretch"><div style="font-family:\'DM Mono\',monospace;font-size:.6rem;text-transform:uppercase;letter-spacing:.1em;color:#f47920;font-weight:700">zoned</div><div style="font-size:1.9rem;font-weight:900;line-height:1.12;color:#fff;margin-top:3px;word-break:break-word">'+esc(zones.length?zDisp:'Not available from PLUTO')+'</div>'+(zones.length?'<a href="#" data-zoomto="1" style="display:inline-block;margin-top:6px;font-size:.72rem;font-weight:700;color:#fff;opacity:.85;text-decoration:none;border-bottom:1px solid rgba(255,255,255,.5)">See what this means &rarr;</a>':'')+(spDists.length?'<div style="font-family:\'DM Mono\',monospace;font-size:.66rem;color:rgba(255,255,255,.82);margin-top:5px">in the '+esc(spDisp)+' special district</div>':'')+'</div>'+cardLogo+'</div><div style="font-size:.75rem;color:var(--muted,#6b6760);margin-bottom:8px">ED '+(Number.isFinite(ed)?ed:'—')+' &middot; AD '+(Number.isFinite(ad)?ad:'—')+(council?' &middot; Council District '+esc(council):'')+(senate?' &middot; State Senate District '+esc(senate):'')+(cong?' &middot; Congressional District '+esc(cong):'')+(school?' &middot; School District '+esc(school):'')+(police?' &middot; Police Precinct '+esc(police):'')+'</div><div class="citywide-result-map" data-lat="'+lat+'" data-lng="'+lng+'" data-label="'+esc(input)+'" style="height:240px;border-radius:8px;border:1px solid #a7f3d0;margin-bottom:10px;background:#eef2f7"></div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:8px;margin-bottom:10px">'+cards+'</div><div style="background:#fff;border:1px solid #d1fae5;border-radius:6px;padding:9px 10px;margin-bottom:10px;font-size:.73rem;line-height:1.45;color:var(--navy,#0d1b4b)"><div><strong>Zoning:</strong> '+(zones.length?zones.map(function(z){return '<strong>'+esc(z)+'</strong>: '+esc(zoningPlain(z));}).join('<br>'):'Zoning was not available from PLUTO for this address.')+'</div><div style="margin-top:5px"><strong>Land use:</strong> '+esc(landUsePlain(pluto.landuse,lUse))+'</div>'+(function(){var g=zoneUseNote(zones[0],pluto.landuse); if(!g) return '';
      return '<div style="margin-top:6px;padding:7px 9px;background:'+(g.ok?'#f4f8f4':'#fff8f2')+';border-left:3px solid '+(g.ok?'#2e6b30':'#f47920')+';border-radius:0 5px 5px 0"><strong>'+g.head+':</strong> '+esc(g.text)+'</div>';})()+''+(spDists.length?'<div style="margin-top:5px"><strong>Special district:</strong> '+esc(specialDistrictExplain(spDisp,[pluto.spdist1,pluto.spdist2,pluto.spdist3]))+'</div>':'')+(hd.length?'<div style="margin-top:5px"><strong>Historic district:</strong> This is in a historic district, so exterior changes usually need LPC review.</div>':'')+'</div>'+facilitiesHtml(facs,zones,pluto.overlay1||pluto.overlay2||'')+'<div data-usegrid="'+esc(baseDistricts(zones[0]).join(','))+'" data-zone="'+esc(zones[0]||'')+'" style="background:#fff;border:1px solid #d1fae5;border-radius:6px;padding:9px 10px;margin-bottom:10px"></div>'+nearbyHtml(n)+'<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px"><a href="'+dob+'" target="_blank" style="font-size:.73rem;font-weight:600;color:var(--navy,#0d1b4b);text-decoration:none;padding:5px 10px;border:1px solid var(--border,#e5e2db);border-radius:5px;background:#fff">DOB BIS</a><a href="'+zap+'" target="_blank" style="font-size:.73rem;font-weight:600;color:var(--navy,#0d1b4b);text-decoration:none;padding:5px 10px;border:1px solid var(--border,#e5e2db);border-radius:5px;background:#fff">ZAP Projects</a><a href="'+acris+'" target="_blank" style="font-size:.73rem;font-weight:600;color:var(--navy,#0d1b4b);text-decoration:none;padding:5px 10px;border:1px solid var(--border,#e5e2db);border-radius:5px;background:#fff">ACRIS Deeds</a><a href="'+zola+'" target="_blank" style="font-size:.73rem;font-weight:600;color:#2e7d32;text-decoration:none;padding:5px 10px;border:1px solid #a5d6a7;border-radius:5px;background:#f1f8f1">ZoLa Zoning</a><a href="https://maps.google.com/?q='+lat+','+lng+'" target="_blank" style="font-size:.73rem;font-weight:600;color:var(--navy,#0d1b4b);text-decoration:none;padding:5px 10px;border:1px solid var(--border,#e5e2db);border-radius:5px;background:#fff">Map</a><button type="button" class="citywide-share-btn" data-share-address="'+esc(input)+'" style="font-size:.73rem;font-weight:700;color:#fff;cursor:pointer;padding:5px 12px;border:1px solid var(--orange,#FD890E);border-radius:5px;background:var(--orange,#FD890E)">Share card</button><button type="button" class="citywide-pdf-btn" style="font-size:.73rem;font-weight:700;color:var(--navy,#0d1b4b);cursor:pointer;padding:5px 12px;border:1px solid var(--navy,#0d1b4b);border-radius:5px;background:#fff">Download PDF</button></div><div style="border-top:1px solid #d1fae5;padding-top:8px;display:flex;flex-wrap:wrap;gap:12px"><a href="'+(boardSlug(cb)?boardSlug(cb)+'?addr='+enc+'#sec-map':'mydistricts.html?address='+enc)+'" style="font-size:.75rem;color:var(--navy,#0d1b4b);font-weight:700;text-decoration:none;border-bottom:1px solid var(--navy,#0d1b4b)">Open '+esc(cbLabel)+' district profile &rarr;</a></div></div>';}
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
  var SHARE_PAGES={'250 BALTIC STREET':'/250baltic','1 EAST 161 STREET':'/yankeestadium'};
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
  var LIFT_P=null;
  var LIFT_PLACE={'435 HOYT ST':'Gowanus Green'};
  var LIFT_DEEP={
    '24-64 KANE ST':{
      note:'This site does not go through the city\'s ULURP. Zoning here is set by the State: Empire State Development adopts a General Project Plan, with environmental review first and Public Authorities Control Board approval at the end. A 28 member Advisory Task Force and the Brooklyn Marine Terminal Development Corporation oversee the commitments.',
      href:'/bmt.html',
      label:'The full BMT page &rarr;'
    },
    '435 HOYT ST':{
      note:'This site is a product of the Gowanus rezoning, the largest neighborhood rezoning in the city in a decade, which CB6 voted to approve and the Council adopted in 2021. It went through the city\'s ULURP, and what gets built here is governed by the rezoning and the Points of Agreement that came with it, including the affordability commitments. The canal alongside it is an active federal Superfund cleanup.',
      href:'/gowanus.html#gowanus-poa',
      label:'The full Gowanus page &rarr;'
    }
  };
  function liftSites(){
    if(LIFT_P) return LIFT_P;
    LIFT_P=fetch('/data/lift-sites.json').then(function(r){return r.json();})
      .then(function(d){return (d&&d.sites)||[];}).catch(function(){return [];});
    return LIFT_P;
  }
  function liftNorm(a){
    return String(a||'').toUpperCase()
      .replace(/,?\s*(BROOKLYN|MANHATTAN|NEW YORK|QUEENS|BRONX|THE BRONX|STATEN ISLAND)\b/g,' ')
      .replace(/,?\s*NY\b/g,' ').replace(/\b\d{5}(-\d{4})?\b/g,' ')
      .replace(/[.,]/g,' ')
      .replace(/\bSTREET\b/g,'ST').replace(/\bAVENUE\b/g,'AVE').replace(/\bBOULEVARD\b/g,'BLVD')
      .replace(/\bROAD\b/g,'RD').replace(/\bPLACE\b/g,'PL').replace(/\bDRIVE\b/g,'DR')
      .replace(/\bPARKWAY\b/g,'PKWY').replace(/\bEAST\b/g,'E').replace(/\bWEST\b/g,'W')
      .replace(/\bNORTH\b/g,'N').replace(/\bSOUTH\b/g,'S')
      .replace(/\s+/g,' ').trim();
  }
  function liftDist(a,b,c,d){
    var R=6371000, p=Math.PI/180;
    var x=(c-a)*p, y=(d-b)*p;
    var h=Math.sin(x/2)*Math.sin(x/2)+Math.cos(a*p)*Math.cos(c*p)*Math.sin(y/2)*Math.sin(y/2);
    return 2*R*Math.asin(Math.sqrt(h));
  }
  function liftMatch(sites,addr,lat,lng){
    var na=liftNorm(addr), out=[];
    (sites||[]).forEach(function(s){
      var ns=liftNorm(s.addr), hit=false;
      if(na && ns && na===ns) hit=true;
      if(!hit && na && ns){
        var pa=/^(\d+)\s+(.+)$/.exec(na), ps=/^(\d+)(?:-(\d+))?\s+(.+)$/.exec(ns);
        if(pa&&ps&&pa[2]===ps[3]){
          var n=parseInt(pa[1],10), lo=parseInt(ps[1],10), hi=ps[2]?parseInt(ps[2],10):lo;
          if(lo>hi){var t=lo; lo=hi; hi=t;}
          if(n>=lo&&n<=hi) hit=true;
        }
      }
      if(!hit && isFinite(lat) && isFinite(lng) && s.lat!=null && s.lng!=null){
        if(liftDist(lat,lng,s.lat,s.lng)<=200) hit=true;
      }
      if(hit) out.push(s);
    });
    return out;
  }
  var NICKNAMES={
    'BMT':'Brooklyn Marine Terminal',
    'THE BMT':'Brooklyn Marine Terminal',
    'BROOKLYN MARINE':'Brooklyn Marine Terminal',
    'MARINE TERMINAL':'Brooklyn Marine Terminal',
    '250 BALTIC':'250 Baltic Street',
    'CB6':'250 Baltic Street',
    'CB6 OFFICE':'250 Baltic Street',
    'GOWANUS GREEN':'435 Hoyt Street, Brooklyn',
    'BBP':'Brooklyn Bridge Park',
    'BBG':'Brooklyn Botanic Garden',
    'MSG':'Madison Square Garden',
    'BAM':'Brooklyn Academy of Music',
    'ATLANTIC YARDS':'620 Atlantic Avenue, Brooklyn',
    'THE ATLANTIC YARDS':'620 Atlantic Avenue, Brooklyn',
    'ATLANTIC YARDS/BARCLAYS CENTER':'620 Atlantic Avenue, Brooklyn',
    'PACIFIC PARK':'620 Atlantic Avenue, Brooklyn',
    'PACIFIC PARK BROOKLYN':'620 Atlantic Avenue, Brooklyn',
    'ATLANTIC TERMINAL':'139 Flatbush Avenue, Brooklyn'
  };
  var LAST_PLACE='';
  function titlePlace(t){t=String(t||''); if(/[a-z]/.test(t)) return t;
    return t.toLowerCase().replace(/(^|[^a-z'])([a-z])/g,function(m,a,b){return a+b.toUpperCase();})
      .replace(/\b(Of|The|And|At)\b/g,function(w){return w.toLowerCase();})
      .replace(/^./,function(c){return c.toUpperCase();});}
  function cleanPlace(l){return titlePlace(String(l||'').replace(/,\s*(Kings|Queens|New York|Bronx|Richmond)\s+County.*$/i,'').replace(/,\s*(Brooklyn|Manhattan|Queens|Bronx|Staten Island)?,?\s*NY,?\s*USA\s*$/i,'').replace(/,\s*(Brooklyn|Manhattan|Queens|Bronx|Staten Island)\s*$/i,'').trim());}
  function nickAlias(q){
    var k=String(q||'').trim().toUpperCase().replace(/\s+/g,' ').replace(/[.]/g,'');
    if(!NICKNAMES[k]) return q;
    LAST_PLACE=/^\d/.test(NICKNAMES[k]) ? String(q).trim() : NICKNAMES[k];
    return NICKNAMES[k];
  }
  function liftAlias(q){
    var t=String(q||'').trim();
    if(!t || /\d/.test(t.split(/\s+/)[0])) return Promise.resolve(t);
    var k=t.toUpperCase().replace(/\s+/g,' ');
    return liftSites().then(function(sites){
      var hit=null;
      (sites||[]).forEach(function(s){
        if(hit) return;
        var n=String(s.n||'').toUpperCase().replace(/\s+/g,' ');
        if(n===k) hit=s;
      });
      if(!hit) (sites||[]).forEach(function(s){
        if(hit) return;
        var n=String(s.n||'').toUpperCase().replace(/\s+/g,' ');
        if(n.indexOf(k)===0 || k.indexOf(n)===0) hit=s;
      });
      if(!hit || !hit.addr || !/^\d/.test(hit.addr)) return t;
      LAST_PLACE=hit.n||t;
      var boro=hit.boro?', '+hit.boro:'';
      return hit.addr+boro;
    }).catch(function(){return t;});
  }
  var BORO_FULL={BX:'Bronx',BK:'Brooklyn',MN:'Manhattan',QN:'Queens',SI:'Staten Island'};
  async function placeAlias(q){
    var t=String(q||'').trim();
    if(!t || /^\d/.test(t)) return null;
    try{
      var g=await fetchJson('https://geosearch.planninglabs.nyc/v2/search?size=5&text='+encodeURIComponent(t),undefined,10000);
      var f=(g&&g.features)||[];
      if(!f.length) return null;
      var best=null;
      for(var i=0;i<f.length;i++){
        var c=f[i].geometry&&f[i].geometry.coordinates;
        if(c&&c.length>=2){ best={lng:+c[0],lat:+c[1],label:(f[i].properties||{}).label||t,
          hn:(f[i].properties||{}).housenumber||'', st:(f[i].properties||{}).street||'',
          boro:(f[i].properties||{}).borough||''}; break; }
      }
      if(!best) return null;
      if(best.hn && best.st) return {q:best.hn+' '+best.st+(best.boro?', '+best.boro:''), label:best.label};
      LAST_PLACE=cleanPlace(best.label)||LAST_PLACE;
      var params=new URLSearchParams({f:'json',where:'1=1',outFields:'BBL,Address,Borough',
        returnGeometry:'false',outSR:'4326',geometry:String(best.lng)+','+String(best.lat),
        geometryType:'esriGeometryPoint',inSR:'4326',spatialRel:'esriSpatialRelIntersects'});
      var d=await fetchJsonOptional('https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services/MAPPLUTO/FeatureServer/0/query?'+params.toString());
      var a=d&&d.features&&d.features[0]&&d.features[0].attributes;
      if(!a||!a.Address) return null;
      var bn=BORO_FULL[String(a.Borough||'').toUpperCase()]||best.boro||'';
      LAST_PLACE=cleanPlace(best.label)||LAST_PLACE;
      return {q:a.Address+(bn?', '+bn:''), label:best.label};
    }catch(e){ return null; }
  }
  var SITE_ICON={
    '1 E 161 ST':{src:'/site-icons/yankee-stadium.png',alt:'Yankee Stadium',w:360,h:147}
  };
  var AKA={
    '24-64 KANE ST':'Brooklyn Marine Terminal, or the BMT',
    '435 HOYT ST':'Gowanus Green, on the site long known as Public Place',
    '250 BALTIC ST':{full:'Location of the CB6 district office'},
    '1 E 161 ST':{text:'Yankee Stadium',bg:'#142448',fg:'#FFFFFF'}
  };
  function bindZoneLink(result){
    if(!result) return;
    var link=result.querySelector('[data-zoomto]'), target=result.querySelector('[data-zoneexplain]');
    if(!link||!target) return;
    link.addEventListener('click',function(ev){
      ev.preventDefault();
      try{ target.scrollIntoView({block:'start',behavior:'smooth'}); }catch(e){ target.scrollIntoView(); }
      target.style.boxShadow='0 0 0 2px #f47920';
      setTimeout(function(){ target.style.boxShadow=''; },1600);
    });
  }
  function injectAliasLine(result,placeName,address){
    if(!result) return;
    var head=result.querySelector('[data-cardaddr]');
    if(!head||result.querySelector('[data-cardalias]')) return;
    var hit=AKA[liftNorm(address)], text=hit||placeName, full='', bg='', fg='';
    if(hit&&typeof hit==='object'){ full=hit.full||''; text=hit.text||''; bg=hit.bg||''; fg=hit.fg||''; }
    if(!text&&!full) return;
    var d=document.createElement('div');
    d.setAttribute('data-cardalias','');
    d.setAttribute('style','font-size:.9rem;font-weight:700;line-height:1.35;margin-top:4px'+(bg?'':';color:var(--orange,#f47920)'));
    if(bg){
      d.innerHTML='<span style="display:inline-block;background:'+bg+';color:'+fg+';border:1.5px solid '+bg+
        ';padding:3px 11px;border-radius:14px;font-weight:900;letter-spacing:.01em">'+esc(full||('aka '+text))+'</span>';
    } else {
      d.textContent=full||('aka '+text);
    }
    head.parentNode.insertBefore(d, head.nextSibling);
  }
  function injectLiftBadge(result,address){
    if(!result || result.querySelector('.lift-badge')) return;
    var m=result.querySelector('.citywide-result-map');
    var lat=m?parseFloat(m.getAttribute('data-lat')):NaN, lng=m?parseFloat(m.getAttribute('data-lng')):NaN;
    var addr=address||(m?m.getAttribute('data-label'):'')||'';
    liftSites().then(function(sites){
      var hits=liftMatch(sites,addr,lat,lng);
      if(!hits.length || !result.isConnected || result.querySelector('.lift-badge')) return;
      var s=hits[0], units=0;
      hits.forEach(function(h){ units+=(h.u||0); });
      var name=LIFT_PLACE[liftNorm(s.addr)] || (hits.length>1 ? s.n.replace(/\s+(Building|Bldg|Phase)\s+\S+$/i,'') : s.n);
      var bits=[];
      if(units) bits.push(units.toLocaleString()+' homes planned');
      if(hits.length>1) bits.push(hits.length+' buildings');
      if(s.ag) bits.push(s.ag);
      if(s.st) bits.push(s.st);
      var deep=LIFT_DEEP[liftNorm(s.addr)]||null;
      var box=document.createElement('div');
      box.className='lift-badge';
      box.setAttribute('style','margin:10px 0;padding:11px 13px;background:#0d1b4b;border-left:5px solid #f47920;border-radius:9px');
      box.innerHTML='<img src="/lift-badge-banner.jpg" alt="Block by Block, Land Inventory Fast Track (LIFT), Office of the Mayor" width="1173" height="342" loading="lazy" style="display:block;width:100%;height:auto;border-radius:5px;margin-bottom:9px">'+
        '<div style="font-family:\'DM Mono\',monospace;font-size:.56rem;text-transform:uppercase;letter-spacing:.1em;color:#f47920;font-weight:700;margin-bottom:5px">On the LIFT list &middot; Block by Block</div>'+
        '<div style="color:#fff;font-size:.9rem;font-weight:900;line-height:1.3">'+esc(name||'')+'</div>'+
        '<div style="color:rgba(255,255,255,.78);font-family:\'DM Mono\',monospace;font-size:.68rem;line-height:1.5;margin-top:4px">'+esc(bits.join(' \u00b7 '))+'</div>'+
        (deep?('<div style="margin-top:9px;padding-top:9px;border-top:1px solid rgba(255,255,255,.22);color:rgba(255,255,255,.86);font-size:.79rem;line-height:1.55">'+deep.note+'</div>'):'')+
        '<div style="display:flex;flex-wrap:wrap;gap:7px;margin-top:10px">'+
        (deep?('<a href="'+deep.href+'" style="background:#f47920;color:#fff;text-decoration:none;font-size:.73rem;font-weight:800;padding:6px 12px;border-radius:16px">'+deep.label+'</a>'):'')+
        '<a href="/blockbyblock/#foldAllSites" style="background:'+(deep?'transparent':'#f47920')+';color:#fff;text-decoration:none;font-size:.73rem;font-weight:800;padding:6px 12px;border-radius:16px'+(deep?';border:1.5px solid rgba(255,255,255,.35)':'')+'">See it on Block by Block &rarr;</a>'+
        '</div>';
      var first=result.firstElementChild;
      if(first && first.firstElementChild && first.firstElementChild.nextElementSibling)
        first.insertBefore(box, first.firstElementChild.nextElementSibling.nextElementSibling);
      else if(first) first.insertBefore(box, first.firstElementChild);
      else result.appendChild(box);
    }).catch(function(){});
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
      '<a href="/blockbyblock/#propose-250baltic" style="display:inline-block;margin-top:10px;background:#f47920;color:#fff;text-decoration:none;font-size:.78rem;font-weight:800;padding:8px 13px;border-radius:18px">See it on Block by Block &rarr;</a>'+
      '<a href="https://drive.google.com/file/d/1kRkL78JUQAD1OUJZZ5ODJ5te84RoVSav/view" target="_blank" rel="noopener" style="display:inline-block;margin-top:10px;margin-left:7px;color:#fff;text-decoration:none;font-size:.78rem;font-weight:800;padding:8px 13px;border-radius:18px;border:1.5px solid rgba(255,255,255,.4)">Read our letter &#8599;</a>';
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
  // ---- download the card as a PDF ----
  var PDF_LIB='https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js';
  var pdfLoading=null;
  function loadPdfLib(){
    if(typeof window.jspdf!=='undefined') return Promise.resolve();
    if(pdfLoading) return pdfLoading;
    pdfLoading=new Promise(function(res,rej){
      var s=document.createElement('script');
      s.src=PDF_LIB; s.onload=function(){res();}; s.onerror=function(){rej(new Error('PDF library failed to load'));};
      document.head.appendChild(s);
    });
    return pdfLoading;
  }
  function cardPdfText(profile){
    var jsPDF=window.jspdf.jsPDF;
    var doc=new jsPDF({unit:'pt',format:'letter'});
    var W=612, M=54, cw=W-M*2, y=0, page=1;
    var navy=[13,27,75], orange=[244,121,32], ink=[51,51,51], muted=[107,103,96];

    var a=profile.address||{}, pluto=profile.pluto||{}, input=profile.input||'';
    var cb=validCommunityBoardCode(profile.foundCd)?String(profile.foundCd):String(a.communityDistrict||pluto.cd||'');
    var cbLabel=validCommunityBoardCode(cb)?boardLabel(cb):'Community Board not identified';
    var zones=collectZones(a,pluto), zDisp=zones.length?zones.join(' / '):'Not available from PLUTO';
    var spDists=collectSpecialDistricts(pluto), spDisp=spDists.length?spDists.join(' / '):'';
    var lUse=landUseLabel(pluto.landuse);
    var bbl=normalizeBbl(a.bbl)||normalizeBbl(pluto.bbl);
    var akaHit=AKA[liftNorm(input)], aka='';
    if(akaHit) aka=(typeof akaHit==='object')?(akaHit.full||('aka '+(akaHit.text||''))):('aka '+akaHit);

    function band(){
      doc.setFillColor(navy[0],navy[1],navy[2]); doc.rect(0,0,W,46,'F');
      doc.setFillColor(orange[0],orange[1],orange[2]); doc.rect(0,46,W,3,'F');
      doc.setTextColor(255,255,255); doc.setFont('helvetica','bold'); doc.setFontSize(13);
      doc.text('Brooklyn Community Board 6', M, 30);
      doc.setFont('helvetica','normal'); doc.setFontSize(9);
      doc.setTextColor(orange[0],orange[1],orange[2]);
      doc.text('ADDRESS CARD  \u00b7  bkcb6.app', W-M, 30, {align:'right'});
    }
    function foot(){
      doc.setFont('helvetica','normal'); doc.setFontSize(8);
      doc.setTextColor(muted[0],muted[1],muted[2]);
      doc.text('Built on public data from the Department of City Planning, NYC Open Data and Geoclient.', M, 762);
      doc.text('bkcb6.app/citywide-search.html', M, 774);
      doc.text('Page '+page, W-M, 774, {align:'right'});
    }
    function newPage(){ foot(); doc.addPage(); page++; band(); y=78; }
    function room(h){ if(y+h>736) newPage(); }
    function h2(t){
      room(30); doc.setFont('helvetica','bold'); doc.setFontSize(11);
      doc.setTextColor(navy[0],navy[1],navy[2]); doc.text(t, M, y); y+=6;
      doc.setDrawColor(229,226,219); doc.line(M,y,W-M,y); y+=14;
    }
    function para(t,size){
      if(!t) return;
      doc.setFont('helvetica','normal'); doc.setFontSize(size||9.5);
      doc.setTextColor(ink[0],ink[1],ink[2]);
      var lines=doc.splitTextToSize(String(t), cw);
      lines.forEach(function(ln){ room(14); doc.text(ln, M, y); y+=13; });
      y+=5;
    }
    function row(k,v){
      if(v===undefined||v===null||v==='') return;
      room(15);
      doc.setFont('helvetica','bold'); doc.setFontSize(8.5); doc.setTextColor(muted[0],muted[1],muted[2]);
      doc.text(String(k).toUpperCase(), M, y);
      doc.setFont('helvetica','normal'); doc.setFontSize(9.5); doc.setTextColor(ink[0],ink[1],ink[2]);
      var lines=doc.splitTextToSize(String(v), cw-150);
      doc.text(lines[0], M+150, y);
      y+=13;
      for(var i=1;i<lines.length;i++){ room(13); doc.text(lines[i], M+150, y); y+=13; }
      y+=3;
    }

    band(); y=80;

    doc.setFont('helvetica','bold'); doc.setFontSize(19); doc.setTextColor(navy[0],navy[1],navy[2]);
    doc.splitTextToSize(input, cw).forEach(function(ln){ doc.text(ln, M, y); y+=23; });
    if(aka){ doc.setFont('helvetica','bold'); doc.setFontSize(11); doc.setTextColor(orange[0],orange[1],orange[2]); doc.text(aka, M, y); y+=17; }
    doc.setFont('helvetica','bold'); doc.setFontSize(12); doc.setTextColor(navy[0],navy[1],navy[2]);
    doc.text('is in '+cbLabel, M, y); y+=22;

    // zoning band
    var bandH=spDists.length?76:60;
    room(bandH+10);
    doc.setFillColor(navy[0],navy[1],navy[2]); doc.roundedRect(M,y,cw,bandH,6,6,'F');
    doc.setFont('helvetica','bold'); doc.setFontSize(8); doc.setTextColor(orange[0],orange[1],orange[2]);
    doc.text('ZONED', M+16, y+20);
    doc.setFontSize(22); doc.setTextColor(255,255,255);
    doc.text(zDisp, M+16, y+45);
    if(spDists.length){
      doc.setFont('helvetica','normal'); doc.setFontSize(9); doc.setTextColor(201,210,230);
      doc.text('in the '+spDisp+' special district', M+16, y+64);
    }
    y+=bandH+20;

    h2('Districts');
    row('Community Board', cbLabel);
    row('Election District', a.electionDistrict||'');
    row('Assembly District', districtNumber(a.assemblyDistrict));
    row('Council District', districtNumber(a.cityCouncilDistrict));
    row('State Senate District', districtNumber(a.stateSenatorialDistrict));
    row('Congressional District', districtNumber(a.congressionalDistrict));
    row('School District', districtNumber(addressValue(a,['communitySchoolDistrict','schoolDistrict','schoolDistrictNumber'])||pluto.schooldist));
    row('Police Precinct', districtNumber(addressValue(a,['policePrecinct','policePrecinctCode','nycPolicePrecinct'])||pluto.policeprct));

    h2('The lot');
    row('BBL', bbl);
    row('Borough, block, lot', bbl?(BOROUGH_NAMES[bbl.slice(0,1)]||'')+', block '+parseInt(bbl.slice(1,6),10)+', lot '+parseInt(bbl.slice(6,10),10):'');
    row('Zoning district', zDisp);
    if(spDists.length) row('Special district', spDisp);
    row('Land use', lUse);
    row('Owner', pluto.ownername||pluto.owner||'');
    row('Year built', pluto.yearbuilt||'');
    row('Building class', pluto.bldgclass||'');
    row('Lot area', fmtNum(pluto.lotarea,' sq ft'));
    row('Building area', fmtNum(pluto.bldgarea,' sq ft'));
    row('Residential units', fmtNum(pluto.unitsres,''));
    row('Total units', fmtNum(pluto.unitstotal,''));
    var hd=(profile.landmarkStatus&&profile.landmarkStatus.historicDistricts)||[];
    row('Landmark status', hd.length?hd.join(' / '):'Not in an LPC historic district');

    h2('What the zoning means');
    zones.forEach(function(z){ para(z+': '+zoningPlain(z)); });
    para('Land use: '+landUsePlain(pluto.landuse,lUse));
    var gap=zoneUseNote(zones[0],pluto.landuse);
    if(gap) para(gap.head+': '+gap.text);
    if(spDists.length) para('Special district: '+specialDistrictExplain(spDisp,[pluto.spdist1,pluto.spdist2,pluto.spdist3]));

    foot();
    var name=String(input).replace(/[^A-Za-z0-9]+/g,'-').replace(/^-|-$/g,'').toLowerCase();
    doc.save('bkcb6-'+(name||'address-card')+'.pdf');
  }
  var H2C_LIB='https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
  var h2cLoading=null;
  function loadH2C(){
    if(typeof window.html2canvas!=='undefined') return Promise.resolve();
    if(h2cLoading) return h2cLoading;
    h2cLoading=new Promise(function(res,rej){
      var s=document.createElement('script');
      s.src=H2C_LIB; s.onload=function(){res();}; s.onerror=function(){rej(new Error('capture library failed'));};
      document.head.appendChild(s);
    });
    return h2cLoading;
  }
  // Render the card itself into the PDF so the file looks like what is on screen.
  function cardPdfVisual(result,profile){
    var card=result.querySelector('[data-cardtop]')||result;
    var hide=[];
    Array.prototype.forEach.call(card.querySelectorAll('.citywide-share-btn,.citywide-pdf-btn'),function(b){
      hide.push([b,b.style.display]); b.style.display='none';
    });
    return window.html2canvas(card,{backgroundColor:'#ffffff',scale:2,useCORS:true,allowTaint:false,logging:false,
      imageTimeout:6000,scrollX:0,scrollY:-window.scrollY}).then(function(canvas){
      hide.forEach(function(h){ h[0].style.display=h[1]; });
      var jsPDF=window.jspdf.jsPDF;
      var doc=new jsPDF({unit:'pt',format:'letter'});
      var W=612,H=792,M=30, cw=W-M*2;
      var navy=[13,27,75], orange=[244,121,32], muted=[107,103,96];
      var topH=46, botH=26;
      var avail=H-topH-botH-14;
      var input=profile&&profile.input||'';

      // one page: fit the whole card, scaled down if it is taller than the page
      var scale=Math.min(cw/canvas.width, avail/canvas.height);
      var drawW=canvas.width*scale, drawH=canvas.height*scale;
      var x=(W-drawW)/2;

      doc.setFillColor(navy[0],navy[1],navy[2]); doc.rect(0,0,W,36,'F');
      doc.setFillColor(orange[0],orange[1],orange[2]); doc.rect(0,36,W,3,'F');
      doc.setTextColor(255,255,255); doc.setFont('helvetica','bold'); doc.setFontSize(12);
      doc.text('Brooklyn Community Board 6', M, 24);
      doc.setFont('helvetica','normal'); doc.setFontSize(9);
      doc.setTextColor(orange[0],orange[1],orange[2]);
      doc.text('ADDRESS CARD  \u00b7  bkcb6.app', W-M, 24, {align:'right'});

      doc.addImage(canvas.toDataURL('image/jpeg',0.92),'JPEG',x,topH,drawW,drawH);

      doc.setFont('helvetica','normal'); doc.setFontSize(7.5);
      doc.setTextColor(muted[0],muted[1],muted[2]);
      doc.text('bkcb6.app/citywide-search.html  \u00b7  Built on public data from the Department of City Planning and NYC Open Data.', M, H-14);

      var name=String(input).replace(/[^A-Za-z0-9]+/g,'-').replace(/^-|-$/g,'').toLowerCase();
      doc.save('bkcb6-'+(name||'address-card')+'.pdf');
    },function(err){
      hide.forEach(function(h){ h[0].style.display=h[1]; });
      throw err;
    });
  }
  function bindPdf(result,profile){
    if(!result||!profile) return;
    var btn=result.querySelector('.citywide-pdf-btn');
    if(!btn||btn.dataset.pdfBound==='true') return;
    btn.dataset.pdfBound='true';
    btn.addEventListener('click',function(){
      var prev=btn.textContent;
      btn.textContent='Building PDF...';
      function done(){ btn.textContent=prev; }
      Promise.all([loadPdfLib(),loadH2C()])
        .then(function(){ return cardPdfVisual(result,profile); })
        .then(done)
        .catch(function(){
          try{ cardPdfText(profile); done(); }
          catch(e){ btn.textContent='PDF failed'; setTimeout(done,1800); }
        });
    });
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
        var qIn=q; LAST_PLACE='';
        q=nickAlias(q);
        q=await liftAlias(q);
        if(!/^\d/.test(q.trim())){
          if(status) status.textContent='Looking up '+qIn+'\u2026';
          var pl=await placeAlias(q);
          if(pl && pl.q) q=pl.q;
        }
        if(q!==qIn && status) status.textContent='Found '+qIn+' at '+q+'. Searching\u2026';
        var explicit=explicitBoroughInQuery(q);
        if(boroughName && explicit && explicit!==boroughName){
          if(status) status.textContent='This '+boroughName+' page searches '+boroughName+' addresses only. Use Citywide Search for '+explicit+' addresses.';
          result.hidden=true; result.innerHTML=''; return;
        }
        if(status) status.textContent='Searching full '+(boroughName||'citywide')+' address profile…';
        result.hidden=true; result.innerHTML='';
        try{var profile=await build(q,{boroughName:boroughName,shortLabel:boroughName}); result.innerHTML=profile.html; result.hidden=false; initResultMap(result); bindShare(result); injectCardBar(result); injectSiteNote(result); injectLiftBadge(result,q); injectAliasLine(result,LAST_PLACE,q); bindZoneLink(result); bindPdf(result,profile); stampUrl(q); if(status) status.textContent=profile.status || 'Search complete.'; try{ setTimeout(function(){ var t=result.querySelector('[data-cardtop]')||result; t.scrollIntoView({block:'start',behavior:'smooth'}); },60); }catch(e){}}catch(err){console.error(err); if(status) status.textContent=err&&err.message?err.message:'Address lookup failed. Please try a full NYC street address.'; result.hidden=true; result.innerHTML='';}
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
