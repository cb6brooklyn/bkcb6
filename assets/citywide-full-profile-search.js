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
    'BPC':'The Special Battery Park City District covers land created by landfill and overseen by the Battery Park City Authority, a State public benefit corporation. The Authority holds the land and ground leases the parcels, so the zoning here works alongside the Authority\'s own master plan and design guidelines rather than in place of them.',
    'MID':'The Special Midtown District governs the core of Midtown Manhattan. It sets bulk, tower setback and street wall rules, protects daylight on the avenues, and carries subdistricts for Times Square, the Theater Subdistrict, Fifth Avenue and Grand Central, each with its own controls layered on top of the base commercial zoning.',
    'HY':'The Special Hudson Yards District was mapped to turn the far West Side rail yards into a dense mixed use district. It ties additional floor area to district improvement contributions that paid for the 7 train extension and the open space network, and it is organized into subdistricts with their own height and use rules.',
    'DB':'The Special Downtown Brooklyn District covers the Downtown Brooklyn core. It concentrates office and residential density near transit, sets street wall and ground floor retail requirements, and modifies the underlying zoning on use, bulk and parking.',
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
  // Joint interest areas: large parks and the airports belong to no single
  // community board, so the City maps them separately. Codes verified against
  // NYC Open Data 5crt-au7u by testing a known landmark inside each area.
  var JIA_NAMES={
    '164':'Central Park','226':'Van Cortlandt Park','227':'Bronx Park','228':'Pelham Bay Park',
    '355':'Prospect Park','356':'Floyd Bennett Field & Gateway','480':'LaGuardia Airport',
    '481':'Flushing Meadows Corona Park','482':'Forest Park','483':'John F. Kennedy Airport',
    '484':'Jamaica Bay','595':'Great Kills & Miller Field'
  };
  function jointInterestLabel(cd){
    cd=String(cd||'');
    var b=cd.charAt(0), n=parseInt(cd.slice(1),10);
    if(!BOROUGH_NAMES[b] || !(n>18)) return '';
    var nm=JIA_NAMES[cd];
    return BOROUGH_NAMES[b]+' Joint Interest Area '+n+(nm?', '+nm:'');
  }

  // On joint interest land the term itself carries the link, and one quiet line
  // says what it means. Deliberately not a call to action: the card is about the
  // address, not about sending the reader somewhere else.
  function areaLabelHtml(cd, label){
    if(!jointInterestLabel(cd)) return esc(label);
    return esc(label).replace('Joint Interest Area',
      '<a href="/jointinterest.html" style="color:inherit;text-decoration:underline;text-underline-offset:2px;text-decoration-thickness:1px">Joint Interest Area</a>');
  }
  function jointInterestNote(cd){
    if(!jointInterestLabel(cd)) return '';
    return '<div style="font-size:.8rem;line-height:1.5;color:#6b6760;margin-top:3px">Park and airport land that no single community board covers; the boards around it share an interest.</div>';
  }
  function areaLabel(cd){
    if(validCommunityBoardCode(cd)) return boardLabel(cd);
    var j=jointInterestLabel(cd);
    return j || 'Community Board not identified';
  }
  function boardLabel(cd){cd=String(cd||''); var b=cd.charAt(0), n=parseInt(cd.slice(1),10); return validCommunityBoardCode(cd) ? BOROUGH_NAMES[b] + ' Community Board ' + n : 'Community Board';}
  function boardSlug(cd){cd=String(cd||''); if(!validCommunityBoardCode(cd)) return ''; return 'cb-' + BOROUGH_SHORT[cd.charAt(0)] + '-' + parseInt(cd.slice(1),10) + '.html';}
  function districtNumber(value){var m=String(value||'').match(/\d+/); return m ? String(parseInt(m[0],10)) : '';}
  function normalizeBbl(value){var d=String(value||'').replace(/\D/g,''); if(d.length>10) d=d.slice(0,10); return d.length===10 ? d : '';}
  function addressValue(obj,names){obj=obj||{}; for(var i=0;i<names.length;i++){var v=obj[names[i]]; if(v!==undefined&&v!==null&&String(v).trim()!=='') return v;} return '';}
  function hasReal(value){var s=String(value==null?'':value).trim(); return !!(s && s!=='—' && !/^not available( from pluto)?$/i.test(s));}
  function miniTag(label,value,attr){return mini(label,value).replace('<div style="background:#fff','<div '+attr+' style="background:#fff');}
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
  // The owner on a tax lot is often not who you would guess. Explain the ones that mislead.
  var OWNER_NOTE={
    '4 PENN PLAZA':'The lot is recorded to the National Railroad Passenger Corporation, Amtrak, because the land and the station beneath it are railroad property. Madison Square Garden sits on a long term lease above Penn Station and operates the arena, but it is not the owner of record on the lot.',
    '620 ATLANTIC AVE':'Arena Nominee Sub B is the ownership entity for the arena parcel. The land under the Atlantic Yards site is largely public, assembled through Empire State Development, and leased to the project, so the record shows a project entity rather than the operator or the public landowner.',
    '1 E 161 ST':'The lot is recorded to the Department of Parks and Recreation, because the stadium was built on city parkland. The Yankees hold a long term lease and run the ballpark, but the land stayed in city ownership, which is also why the land use reads as open space and outdoor recreation.'
  };
  var OWNER_TYPE={
    C:'City owned.',
    M:'Owned by a mixed city and private arrangement.',
    O:'Owned by another public authority, the State or the federal government.',
    P:'Owned by a public utility company.',
    X:'Fully tax exempt, which usually means a public, institutional or authority owner.'
  };
  var ZONE_NOTE={
    '30 LAFAYETTE AVE':'C6-1 in the Special Downtown Brooklyn District. The opera house is five storeys and built to an FAR of 4.5, on a lot where commercial floor area is allowed up to 6.0 and community facility up to 6.5. In other words the zoning here anticipates a considerably bigger building than the one standing. What keeps BAM low rise is the building itself, not the rules.',
    '651 FULTON ST':'C6-4 in the Special Downtown Brooklyn District, one of the densest commercial districts mapped in Brooklyn. The Harvey is four storeys at an FAR of about 6.0, on a lot that allows 10.0 for commercial, community facility and residential alike. The theatre uses a little over half of what the zoning permits.',
    '653 FULTON ST':'C6-4 in the Special Downtown Brooklyn District, one of the densest commercial districts mapped in Brooklyn. The Harvey is four storeys at an FAR of about 6.0, on a lot that allows 10.0 for commercial, community facility and residential alike. The theatre uses a little over half of what the zoning permits.',
    '321 ASHLAND PL':'C6-1 in the Special Downtown Brooklyn District. BAM Fisher is built to an FAR of roughly 1.0 on a lot zoned for 6.0 commercial and 6.5 community facility. Almost the whole envelope the zoning allows here is unbuilt.'
  };
  function zoneNote(addr){ return ZONE_NOTE[liftNorm(addr)]||''; }
  function ownerNote(addr,owner,otype){
    var hit=OWNER_NOTE[liftNorm(addr)];
    if(hit) return hit;
    var t=OWNER_TYPE[String(otype||'').trim().toUpperCase()];
    var o=String(owner||'').toUpperCase();
    if(/\b(LLC|L\.?L\.?C|LP|CORP|INC|COMPANY|CO\b|TRUST|REALTY|ASSOCIATES|HOLDINGS?|NOMINEE)\b/.test(o))
      return 'The owner of record is the entity that holds title on the tax roll, which is often a holding company or single purpose entity rather than the business you see on the building. Leases and operating agreements do not appear here.'+(t?' '+t:'');
    if(/^NYC |^CITY OF NEW YORK|DEPARTMENT|AUTHORITY|BOARD OF|HOUSING AUTHORITY/.test(o))
      return 'This is public land. The agency named holds it on the tax roll, and a different operator may run what is on the site under a lease or agreement.'+(t?' '+t:'');
    return t||'';
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
    if(z==='BPC') return 'Battery Park City district';
    if(/^R/.test(z)) return 'Residential district';
    if(/^C/.test(z)) return 'Commercial district';
    if(/^M/.test(z)) return 'Manufacturing district';
    return 'Mapped zoning district';
  }
  function zoneBase(z){z=String(z||'').trim().toUpperCase(); if(!z) return '';
    if(z==='BPC') return 'the Battery Park City zoning district. The land is State owned, created by landfill and administered by the Battery Park City Authority, which ground leases the parcels and sets its own master plan and design guidelines alongside the zoning.';
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
  async function fetchArcgisPluto(safeBbl,lat,lng){try{var params=new URLSearchParams({f:'json',where:safeBbl?'BBL='+safeBbl:'1=1',outFields:'BBL,Address,LandUse,ZoneDist1,ZoneDist2,ZoneDist3,ZoneDist4,Overlay1,Overlay2,SPDist1,SPDist2,SPDist3,SplitZone,LtdHeight,YearBuilt,UnitsRes,UnitsTotal,BldgClass,LotArea,BldgArea,Borough,Block,Lot,CD,SchoolDist,Council,PolicePrct,OwnerName,Owner,OwnerType',returnGeometry:'false',outSR:'4326'}); if(!safeBbl&&Number.isFinite(lat)&&Number.isFinite(lng)){params.set('geometry',String(lng)+','+String(lat));params.set('geometryType','esriGeometryPoint');params.set('inSR','4326');params.set('spatialRel','esriSpatialRelIntersects');} var d=await fetchJsonOptional('https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services/MAPPLUTO/FeatureServer/0/query?'+params.toString()); var a=d&&d.features&&d.features[0]&&d.features[0].attributes; if(!a) return null; return {bbl:normalizeBbl(a.BBL||a.bbl||safeBbl),borough:a.Borough||'',block:a.Block||'',lot:a.Lot||'',address:a.Address||'',landuse:a.LandUse||'',zonedist1:a.ZoneDist1||'',zonedist2:a.ZoneDist2||'',zonedist3:a.ZoneDist3||'',zonedist4:a.ZoneDist4||'',overlay1:a.Overlay1||'',overlay2:a.Overlay2||'',spdist1:a.SPDist1||'',spdist2:a.SPDist2||'',spdist3:a.SPDist3||'',splitzone:a.SplitZone||'',yearbuilt:a.YearBuilt||'',unitsres:a.UnitsRes||'',unitstotal:a.UnitsTotal||'',bldgclass:a.BldgClass||'',lotarea:a.LotArea||'',bldgarea:a.BldgArea||'',cd:a.CD||'',council:a.Council||'',policeprct:a.PolicePrct||'',schooldist:a.SchoolDist||'',ownername:a.OwnerName||a.Owner||'', ownertype:a.OwnerType||'',owner:a.Owner||a.OwnerName||'',__lookupStatus:'ok_arcgis'};}catch(e){return null;}}
  async function fetchPluto(bbl,lat,lng){var safe=normalizeBbl(bbl); if(!safe) return await fetchArcgisPluto('',lat,lng) || {__lookupStatus:'invalid_bbl'}; try{var params=new URLSearchParams({'$where':"bbl='"+safe+"'",'$select':'bbl,borough,block,lot,address,landuse,zonedist1,zonedist2,zonedist3,zonedist4,overlay1,overlay2,spdist1,spdist2,spdist3,splitzone,ltdheight,yearbuilt,unitsres,unitstotal,bldgclass,lotarea,bldgarea,cd,council,policeprct,schooldist,ownername','$limit':'1'}); var rows=await fetchJson('https://data.cityofnewyork.us/resource/64uk-42ks.json?'+params.toString()); if(rows&&rows[0]){rows[0].__lookupStatus='ok'; return rows[0];}}catch(e){} return await fetchArcgisPluto(safe,lat,lng) || {__lookupStatus:'no_record'};}
  async function fetchLandmarks(bbl){bbl=normalizeBbl(bbl); if(!bbl) return {historicDistricts:[]}; try{var rows=await fetchJson('https://data.cityofnewyork.us/resource/gpmc-yuvp.json?'+new URLSearchParams({bbl:bbl,'$select':'hist_dist,lm_orig,lm_new,des_addres','$limit':'50'})); return {historicDistricts:Array.from(new Set((rows||[]).map(function(r){return String(r.hist_dist||'').trim();}).filter(function(n){return n&&n!=='0';})))};}catch(e){return {historicDistricts:[]};}}
  function distFt(a,b,c,d){var R=3959*5280, dLat=(c-a)*Math.PI/180, dLng=(d-b)*Math.PI/180; var x=Math.sin(dLat/2)**2+Math.cos(a*Math.PI/180)*Math.cos(c*Math.PI/180)*Math.sin(dLng/2)**2; return R*2*Math.atan2(Math.sqrt(x),Math.sqrt(1-x));}
  function distLabel(f){return !Number.isFinite(f)?'':(f<700?Math.round(f/25)*25+' ft':(f/5280).toFixed(1)+' mi');}
  function featurePoints(item){if(!item) return []; var g=item.geometry, p=item.properties||item, pts=[]; function add(c){if(Array.isArray(c)&&c.length>=2){var x=+c[0], y=+c[1]; if(Number.isFinite(x)&&Number.isFinite(y)) pts.push({lng:x,lat:y,properties:p});}} function walk(c){if(!Array.isArray(c)) return; if(typeof c[0]==='number') add(c); else c.forEach(walk);} if(g&&g.coordinates) walk(g.coordinates); var plat=parseFloat(p.lat||p.latitude||p.entrance_latitude||p.Latitude||p.LATITUDE), plng=parseFloat(p.lon||p.lng||p.longitude||p.entrance_longitude||p.Longitude||p.LONGITUDE); if(Number.isFinite(plat)&&Number.isFinite(plng)) pts.push({lat:plat,lng:plng,properties:p}); return pts;}
  function nearest(items,lat,lng,filterFn){return (items||[]).map(function(it){var pts=featurePoints(it); if(!pts.length) return null; var p=(it.properties||it||{}); if(filterFn&&!filterFn(p)) return null; var d=Math.min.apply(null,pts.map(function(pt){return distFt(lat,lng,pt.lat,pt.lng);})); return Number.isFinite(d)?{properties:p,distanceFeet:d}:null;}).filter(Boolean).sort(function(a,b){return a.distanceFeet-b.distanceFeet;})[0]||null;}
  var CULTURE_CACHE=null, cultureLoading=null;
  function loadCulture(){
    if(CULTURE_CACHE) return Promise.resolve(CULTURE_CACHE);
    if(cultureLoading) return cultureLoading;
    cultureLoading=fetch('/data/culture-places.json').then(function(r){return r.json();})
      .then(function(j){ CULTURE_CACHE=Array.isArray(j)?j:[]; return CULTURE_CACHE; })
      .catch(function(){ CULTURE_CACHE=[]; return CULTURE_CACHE; });
    return cultureLoading;
  }
  function nearestCulture(list,lat,lng,type){
    var best=null, bd=Infinity;
    (list||[]).forEach(function(x){
      if(String(x.type||'')!==type) return;
      var la=parseFloat(x.lat), ln=parseFloat(x.lng);
      if(!isFinite(la)||!isFinite(ln)) return;
      var d=liftDist(lat,lng,la,ln);
      if(d<bd){ bd=d; best=x; }
    });
    if(!best) return null;
    return {properties:best, distanceFeet:bd*3.28084};
  }
  async function nearby(lat,lng,foundCd,a){var out={}; var cd=String(foundCd||''); var b=cd.charAt(0), key=BOROUGH_KEY[b], short=BOROUGH_SHORT[b], n=parseInt(cd.slice(1),10); var transport=await fetchJsonOptional(short&&n?'transport-data/cb-'+short+'-'+n+'.json':''); var subway=transport&&transport.subway&&transport.subway.features||[], bus=transport&&transport.busstops&&transport.busstops.features||[]; out.subway=nearest(subway,lat,lng); out.bus=nearest(bus,lat,lng); var parks=await fetchJsonOptional(key?'data/topmap-parks-'+key+'.geojson':''); out.park=nearest(parks&&parks.features||[],lat,lng,function(p){return String(p.retired||'').toLowerCase()!=='true';}); var libs=await fetchJsonOptional('data/nyc_libraries.geojson'); out.library=nearest(libs&&libs.features||[],lat,lng,function(p){return String(p.status||'').toLowerCase().indexOf('closed')===-1;}) || nearest(libs&&libs.features||[],lat,lng); var culture=await loadCulture(); out.movies=nearestCulture(culture,lat,lng,'film'); out.museum=nearestCulture(culture,lat,lng,'museum'); var schools=await fetchJsonOptional('data/nyc_school_points.json'); out.school=nearest(Array.isArray(schools)?schools:[],lat,lng,function(p){return String(p.category||'').toLowerCase()!=='childcare' && (!key || String(p.borough||'').toLowerCase().replace(/[^a-z]/g,'')===key);}); var citi=await fetchJsonOptional('https://gbfs.citibikenyc.com/gbfs/en/station_information.json',15000) || await fetchJsonOptional('data/citibike_station_information.json',8000); out.citibike=nearest(citi&&citi.data&&citi.data.stations||[],lat,lng); var mayor=await fetchJsonOptional('data/cb6-ed-results.geojson'); var ed=parseInt(a&&a.electionDistrict,10), ad=parseInt(a&&(a.assemblyDistrict||a.stateLegislativeDistrict),10); if(mayor&&mayor.features&&Number.isFinite(ed)&&Number.isFinite(ad)){var wanted=String(ad).padStart(2,'0')+String(ed).padStart(3,'0'); var f=mayor.features.find(function(x){return String((x.properties||{}).elect_dist||'')===wanted;}); if(f) out.mayor=f.properties;} return out;}
  function service(label,item,nameFn,detailFn){if(!item) return mini(label,'Not available'); var p=item.properties||{}, v=(nameFn?nameFn(p):(p.name||p.stop_name||label))||label, d=distLabel(item.distanceFeet), detail=detailFn?detailFn(p):''; if(d) v+=' · '+d; if(detail) v+=' · '+detail; return mini(label,v);}
  function nearbyHtml(n){n=n||{}; return '<div style="margin-bottom:10px"><div style="font-size:.66rem;font-family:\'DM Mono\',monospace;text-transform:uppercase;letter-spacing:.08em;color:var(--muted,#6b6760);margin:0 0 5px">Nearby civic services</div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px">'+service('Closest Park',n.park,function(p){return p.signname||p.name311||'Park/Open Space';},function(p){return p.typecategory||p.location||p.address||'';})+service('Closest Subway',n.subway,function(p){return p.display_name||p.stop_name||'Subway station';},function(p){return p.daytime_routes||p.routes||'';})+service('Closest Bus Stop',n.bus,function(p){var r=Array.isArray(p.routes)?p.routes.join(', '):(p.routes||p.route_short_name||'Bus'); return r+' · '+(p.stop_name||'Bus stop');})+service('Closest Citi Bike',n.citibike,function(p){return p.name||p.station_name||'Citi Bike station';},function(p){return p.short_name||'';})+service('Closest Movie Theater',n.movies,function(p){return p.name||'Movie theater';},function(p){return p.category||'';})+service('Closest Museum',n.museum,function(p){return p.name||'Museum';},function(p){return p.aka_line||p.category_group||'';})+service('Closest Library',n.library,function(p){return p.name||'Library';},function(p){var b=[]; if(p.address)b.push(p.address); if(p.system)b.push(p.system); return b.join(' · ');})+service('Closest School',n.school,function(p){return p.name||'School';},function(p){return p.program_type||p.typecategory||p.address||'';})+'</div></div>';}
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

  // ---- use groups permitted in this district -------------------------------
  // Read straight off the same zoning matrix the card already loads for its
  // "what can be built here" grid. Y is as of right; L and S are allowed only
  // with limits or a special permit, so they are named separately.
  function useGroupLine(zones){
    if (!USEMATRIX || !USEMATRIX.matrix || !zones || !zones.length) return '';
    var z = String(zones[0]).toUpperCase();
    if (z === 'PARK') return '';
    var m = z.match(/^([RCM])(\d+)/);
    if (!m) return '';
    var base = m[1] + m[2];
    var asRight = [], limited = [];
    Object.keys(USEMATRIX.matrix).forEach(function(g){
      var v = USEMATRIX.matrix[g][base];
      if (v === 'Y') asRight.push(g);
      else if (v === 'L' || v === 'S') limited.push(g);
    });
    if (!asRight.length && !limited.length) return '';
    var out = '<div style="font-family:\'DM Mono\',monospace;font-size:.66rem;'
            + 'color:rgba(255,255,255,.82);margin-top:5px">use groups '
            + esc(asRight.join(', ')) + ' as of right';
    if (limited.length) out += ' &middot; ' + esc(limited.join(', ')) + ' with limits';
    return out + '</div>';
  }

  // ---- use group of this property, from what the lot is actually used for --
  // PLUTO land use code is the real world use. City of Yes (2024) consolidated
  // the Zoning Resolution into ten use groups; this names the one the existing
  // use falls into, in plain language, rather than listing what is permitted.
  var UG_BY_LANDUSE={
    '01':'II \u00b7 One and two family residential',
    '02':'II \u00b7 Multi-family walk-up residential',
    '03':'II \u00b7 Multi-family elevator residential',
    '04':'II and VI \u00b7 Residential with ground floor commercial',
    '05':'VI or VII \u00b7 Commercial, retail, service or office',
    '06':'X \u00b7 Manufacturing or industrial',
    '07':'Transportation or utility infrastructure',
    '08':'III \u00b7 Community facility such as a school, house of worship or hospital',
    '09':'I \u00b7 Open use, park or outdoor recreation',
    '10':'IX \u00b7 Parking',
    '11':'Vacant land, no use in place'
  };
  // Elected official logos, keyed to the district the address falls in.
  // Only numbers with a file in /elected are listed, and onerror hides any
  // tile whose image fails so a missing file never leaves a broken frame.
  var ELECTED_HAVE={
    CD:[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51],
    AD:[23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87],
    SD:[10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,47,59]
  };
  function electedTile(prefix,num,caption){
    var n=parseInt(num,10);
    if(!Number.isFinite(n) || ELECTED_HAVE[prefix].indexOf(n)===-1) return '';
    return '<figure style="margin:0;flex:0 0 auto;width:92px">'
      + '<img src="elected/'+prefix+n+'.png" alt="'+esc(caption)+'" loading="lazy" '
      + 'onerror="var f=this.parentNode; if(f) f.style.display=\'none\'" '
      + 'style="display:block;width:92px;height:92px;object-fit:cover;border-radius:7px;border:1.5px solid #e5e2db;background:#fff">'
      + '<figcaption style="font-family:\'DM Mono\',monospace;font-size:.58rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted,#6b6760);margin-top:4px;text-align:center">'+esc(caption)+'</figcaption>'
      + '</figure>';
  }
  function electedRow(council,assembly,senate){
    var t=electedTile('CD',council,'Council '+council)
        + electedTile('AD',assembly,'Assembly '+assembly)
        + electedTile('SD',senate,'Senate '+senate);
    if(!t) return '';
    return '<div style="display:flex;flex-wrap:wrap;gap:9px;margin:0 0 10px">'+t+'</div>';
  }

  // NYC land use colors, the same eleven the borough and district maps use.
  var LAND_USE_HERO_COLORS={'01':'#FEFFA8','02':'#FCB842','03':'#B16E00','04':'#ff8341','05':'#fc2929','06':'#E362FB','07':'#E0BEEB','08':'#44A3D5','09':'#78D271','10':'#BAB8B6','11':'#555555'};
  // Pick type color from the fill so every category stays legible.
  function heroInk(bg){
    var h=String(bg||'').replace('#','');
    if(h.length===3) h=h.charAt(0)+h.charAt(0)+h.charAt(1)+h.charAt(1)+h.charAt(2)+h.charAt(2);
    function lin(c){c=parseInt(c,16)/255; return c<=0.03928?c/12.92:Math.pow((c+0.055)/1.055,2.4);}
    var L=0.2126*lin(h.slice(0,2))+0.7152*lin(h.slice(2,4))+0.0722*lin(h.slice(4,6));
    // WCAG contrast against navy versus white; take whichever reads better.
    var navy=(L+0.05)/(0.0234+0.05), white=1.05/(L+0.05);
    return navy>=white
      ? {bg:bg,fg:'#0d1b4b',sub:'rgba(13,27,75,.8)',rule:'rgba(13,27,75,.45)'}
      : {bg:bg,fg:'#ffffff',sub:'rgba(255,255,255,.85)',rule:'rgba(255,255,255,.5)'};
  }

  // Land use gets the same visual weight as the zoning district: a block of the
  // same shape and type scale, in orange instead of navy, so the two read as a
  // pair. Zoned tells you what the lot may be. Land use tells you what it is.
  function landUseHero(code){
    var key=String(code||'').trim().padStart(2,'0');
    var name=LAND_USE_LABELS[key];
    if(!name) return '';
    var ug=UG_BY_LANDUSE[key]||'';
    var ugTxt=/^[IVX]+( and [IVX]+| or [IVX]+)? \u00b7 /.test(ug) ? 'use group '+ug.split(' \u00b7 ')[0] : '';
    var ink=heroInk(LAND_USE_HERO_COLORS[key]||'#BAB8B6');
    return '<div style="flex:1;min-width:0;background:'+ink.bg+';border-radius:7px;padding:11px 13px;align-self:stretch">'
      + '<div style="font-family:\'DM Mono\',monospace;font-size:.6rem;text-transform:uppercase;letter-spacing:.1em;color:'+ink.sub+';font-weight:700">land use</div>'
      + '<div style="font-size:1.05rem;font-weight:900;line-height:1.18;color:'+ink.fg+';margin-top:3px;word-break:normal;overflow-wrap:break-word;hyphens:auto">'+esc(name)+'</div>'
      + '<a href="#" data-zoomto-landuse="1" style="display:inline-block;margin-top:6px;font-size:.72rem;font-weight:700;color:'+ink.fg+';opacity:.9;text-decoration:none;border-bottom:1px solid '+ink.rule+'">See what this means &rarr;</a>'
      + (ugTxt?'<div style="font-family:\'DM Mono\',monospace;font-size:.66rem;color:'+ink.sub+';margin-top:5px">'+esc(ugTxt)+'</div>':'')
      + '</div>';
  }
  function useGroupMini(code,label){
    var v=UG_BY_LANDUSE[String(code||'').trim().padStart(2,'0')];
    if(!v) return label?mini('Use Group',String(label)):'';
    return mini('Use Group',v);
  }

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
  function render(input,a,foundCd,lat,lng,pluto,landmarks,n,context,facs){context=context||{}; pluto=pluto||{}; var ed=parseInt(a.electionDistrict,10), ad=parseInt(a.assemblyDistrict,10), council=districtNumber(a.cityCouncilDistrict), senate=districtNumber(a.stateSenatorialDistrict), cong=districtNumber(a.congressionalDistrict), school=districtNumber(addressValue(a,['communitySchoolDistrict','schoolDistrict','schoolDistrictNumber'])||pluto.schooldist), police=districtNumber(addressValue(a,['policePrecinct','policePrecinctCode','nycPolicePrecinct'])||pluto.policeprct); var bbl=normalizeBbl(a.bbl)||normalizeBbl(pluto.bbl), b=bbl.slice(0,1)||String(foundCd||'').charAt(0), block=bbl.slice(1,6), lot=bbl.slice(6,10); var cb=validCommunityBoardCode(foundCd)?String(foundCd):String(a.communityDistrict||pluto.cd||''); var cbLabel=areaLabel(cb||String(a.communityDistrict||pluto.cd||'')); var zones=collectZones(a,pluto), zDisp=zones.length?zones.join(' / '):'Not available from PLUTO'; var spDists=collectSpecialDistricts(pluto), spDisp=spDists.length?spDists.join(' / '):''; var lUse=landUseLabel(pluto.landuse); var hd=(landmarks&&landmarks.historicDistricts)||[]; var historic=hd.length?hd.join(' / '):'Not in an LPC historic district'; var dob=b&&block&&lot?'https://a810-bisweb.nyc.gov/bisweb/PropertyBrowseByBBLServlet?allborough='+encodeURIComponent(b)+'&allblock='+parseInt(block,10)+'&alllot='+parseInt(lot,10)+'&filetype=html&requestid=0':'#'; var zola=b&&block&&lot?'https://zola.planning.nyc.gov/l/lot/'+encodeURIComponent(b)+'/'+parseInt(block,10)+'/'+parseInt(lot,10):'#'; var acris=b&&block&&lot?'https://a836-acris.nyc.gov/DS/DocumentSearch/BBL?REQUEST_BBL='+encodeURIComponent(b)+block+lot:'#'; var zap=block&&lot?'https://zap.planning.nyc.gov/projects?block='+parseInt(block,10)+'&lot='+parseInt(lot,10):'#'; var enc=encodeURIComponent(input); var boardShort=validCommunityBoardCode(cb)?BOROUGH_SHORT[cb.charAt(0)]:'', boardNum=validCommunityBoardCode(cb)?parseInt(cb.slice(1),10):0;
    var cardLogo='';
    var siteIcon=SITE_ICON[liftNorm(input)]||null;
    if(!siteIcon && /HOUSING AUTHORITY|\bNYCHA\b/i.test(String(pluto.ownername||pluto.owner||''))) siteIcon=NYCHA_ICON;
    if(!siteIcon && isBroadwayAddr(input)) siteIcon=BROADWAY_ICON;
    if(!siteIcon && FERRY_ADDRS[liftNorm(input)]) siteIcon=FERRY_ICON;
    if(!siteIcon && PARK_ICONS[normalizeBbl(a.bbl)||normalizeBbl(pluto.bbl)]) siteIcon=PARK_ICONS[normalizeBbl(a.bbl)||normalizeBbl(pluto.bbl)];
    var logoImg='';
    if(cb==='306'){ logoImg='<img src="/cb6-logo-card.png" alt="Brooklyn Community Board 6" width="500" height="500" loading="lazy" style="display:block;width:74px;height:74px;border-radius:6px">'; }
    else if(boardShort&&boardNum){ logoImg='<img src="/banners/banner-'+boardShort+'-'+boardNum+'.png" alt="'+esc(cbLabel)+'" width="540" height="270" loading="lazy" style="display:block;width:124px;height:62px;border-radius:5px;background:#fff">'; }
    if(logoImg||siteIcon){
      var iconImg=siteIcon?'<img src="'+siteIcon.src+'" alt="'+esc(siteIcon.alt)+'" width="'+siteIcon.w+'" height="'+siteIcon.h+'" loading="lazy" style="display:block;width:'+(cb==='306'?74:124)+'px;height:auto;border-radius:4px;background:#fff">':'';
      cardLogo='<div style="display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:0 0 9px">'+logoImg+iconImg+'</div>';

    }
    var zInk=heroInk(zoneColor(zones.length?zones[0]:'')[1]);
    var cards=mini(zones.length>1?'Zoning Districts':'Zoning District',zDisp)+useGroupMini(pluto.landuse,lUse)+(spDists.length?mini(spDists.length>1?'Special Districts':'Special District',spDisp):'')+mini('Land Use',lUse)+mini('Landmark Status',historic)+mini('Election District',Number.isFinite(ed)?ed:'—')+mini('Assembly',repLabel('state_assembly',ad,'Assembly District'))+mini('City Council',repLabel('city_council',council,'Council District'))+mini('State Senate',repLabel('state_senate',senate,'State Senate District'))+mini('Congress',repLabel('congress',cong,'Congressional District'))+mini('School District',school?'CSD '+school:'—')+mini('Police Precinct',police?police+' Precinct':'—')+miniTag('Zoning Code Explanation',zones.length?zones.map(function(z){return z+': '+zoningPlain(z);}).join(' / '):'Check ZoLa for exact district controls.','data-zoneexplain')+miniTag('Use Group Explanation',landUsePlain(pluto.landuse,lUse),'data-landuseexplain')+propertyMini('Owner',pluto.ownername||pluto.owner||a.ownerName||a.ownername)+mini('Community Board',cbLabel)+mini('Borough',pluto.borough||a.firstBoroughName||BOROUGH_NAMES[b]||'—')+propertyMini('Year Built',fmtNum(pluto.yearbuilt,''))+propertyMini('Building Class',pluto.bldgclass)+propertyMini('Lot Area',fmtNum(pluto.lotarea,' sq ft'))+propertyMini('Building Area',fmtNum(pluto.bldgarea,' sq ft'))+propertyMini('Residential Units',fmtNum(pluto.unitsres,''))+propertyMini('Total Units',fmtNum(pluto.unitstotal,'')); return '<div data-cardtop style="scroll-margin-top:12px;position:relative;background:#f0f8f4;border:1.5px solid #a7f3d0;border-radius:8px;padding:12px 14px;margin-top:4px"><div data-cardaddr style="font-size:1.15rem;font-weight:900;line-height:1.2;color:var(--navy,#0d1b4b)">'+esc(input)+'</div><div style="font-size:.95rem;font-weight:600;line-height:1.35;color:var(--navy,#0d1b4b);margin-top:3px">is in <strong style="font-weight:900">'+areaLabelHtml(cb||String(a.communityDistrict||pluto.cd||''),cbLabel)+'</strong></div>'+jointInterestNote(cb||String(a.communityDistrict||pluto.cd||''))+'<div style="display:flex;align-items:flex-start;gap:10px;margin:10px 0 9px"><div style="flex:1;min-width:0;background:'+zInk.bg+';border-radius:7px;padding:11px 13px;align-self:stretch"><div style="font-family:\'DM Mono\',monospace;font-size:.6rem;text-transform:uppercase;letter-spacing:.1em;color:'+zInk.sub+';font-weight:700">zoned</div><div style="font-size:1.9rem;font-weight:900;line-height:1.12;color:'+zInk.fg+';margin-top:3px;word-break:normal;overflow-wrap:break-word">'+esc(zones.length?zDisp:'Not available from PLUTO')+'</div>'+(zones.length?'<a href="#" data-zoomto="1" style="display:inline-block;margin-top:6px;font-size:.72rem;font-weight:700;color:'+zInk.fg+';opacity:.9;text-decoration:none;border-bottom:1px solid '+zInk.rule+'">See what this means &rarr;</a>':'')+(spDists.length?'<div style="font-family:\'DM Mono\',monospace;font-size:.66rem;color:'+zInk.sub+';margin-top:5px">in the '+esc(spDisp)+' special district</div>':'')+'</div>'+landUseHero(pluto.landuse)+'</div>'+cardLogo+bizBlock(input)+'<div style="font-size:.75rem;color:var(--muted,#6b6760);margin-bottom:8px">ED '+(Number.isFinite(ed)?ed:'—')+' &middot; AD '+(Number.isFinite(ad)?ad:'—')+(council?' &middot; Council District '+esc(council):'')+(senate?' &middot; State Senate District '+esc(senate):'')+(cong?' &middot; Congressional District '+esc(cong):'')+(school?' &middot; School District '+esc(school):'')+(police?' &middot; Police Precinct '+esc(police):'')+'</div>'+electedRow(council,ad,senate)+'<div class="citywide-result-map" data-lat="'+lat+'" data-lng="'+lng+'" data-label="'+esc(input)+'" data-owner="'+esc(pluto.ownername||pluto.owner||'')+'" style="height:240px;border-radius:8px;border:1px solid #a7f3d0;margin-bottom:10px;background:#eef2f7"></div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:8px;margin-bottom:10px">'+cards+'</div><div style="background:#fff;border:1px solid #d1fae5;border-radius:6px;padding:9px 10px;margin-bottom:10px;font-size:.73rem;line-height:1.45;color:var(--navy,#0d1b4b)"><div><strong>Zoning:</strong> '+(zones.length?zones.map(function(z){return '<strong>'+esc(z)+'</strong>: '+esc(zoningPlain(z));}).join('<br>'):'Zoning was not available from PLUTO for this address.')+'</div><div style="margin-top:5px"><strong>Land use:</strong> '+esc(landUsePlain(pluto.landuse,lUse))+'</div>'+(function(){var zn=zoneNote(input); if(!zn) return '';
      return '<div style="margin-top:6px;padding:7px 9px;background:#f6f7fb;border-left:3px solid #2145a8;border-radius:0 5px 5px 0"><strong>Worth knowing about the zoning:</strong> '+esc(zn)+'</div>';})()+(function(){var on=ownerNote(input,pluto.ownername||pluto.owner,pluto.ownertype); if(!on) return '';
      return '<div style="margin-top:6px;padding:7px 9px;background:#f6f7fb;border-left:3px solid #2145a8;border-radius:0 5px 5px 0"><strong>Who owns it:</strong> '+esc(on)+'</div>';})()+(function(){var g=zoneUseNote(zones[0],pluto.landuse); if(!g) return '';
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
  // Shared with the pick map so the map preview and the full card use the same
  // colours, labels and board names.
  window.__bkcbCardBits={
    landUseLabel:landUseLabel,
    landUseColor:function(c){return LAND_USE_HERO_COLORS[String(c||'').trim().padStart(2,'0')]||'';},
    ugText:function(c){return UG_BY_LANDUSE[String(c||'').trim().padStart(2,'0')]||'';},
    heroInk:heroInk,
    zoneColor:zoneColor,
    boardLabel:function(cd){return validCommunityBoardCode(String(cd||''))?boardLabel(String(cd||'')):'';},
    bizFor:function(addr){return BIZ_SITES[liftNorm(addr)]||null;},
    bizBlock:bizBlock
  };
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
      var label=el.getAttribute('data-label')||'Searched address';
      var owner=el.getAttribute('data-owner')||'';
      var mi=markFor(label,owner);
      markerFor(label,lat,lng,owner).addTo(map).bindPopup(
        '<div style="font-family:\'DM Sans\',sans-serif;font-size:.85rem;line-height:1.45;color:#0d1b4b">'+
        '<b>'+esc(label)+'</b>'+(mi.alias?'<br><span style="color:#f47920;font-weight:700">'+esc(mi.alias)+'</span>':'')+
        (mi.kind?'<br><span style="font-family:\'DM Mono\',monospace;font-size:.66rem;color:#6b6760">'+esc(mi.kind.label)+'</span>':'')+
        '</div>');
      setTimeout(function(){map.invalidateSize();},120);
    }catch(e){console.error(e);}
  }
  window.__bkcbInitResultMap = initResultMap;

  function cardModeRequested(){
    try{return new URLSearchParams(location.search).get('card')==='1';}catch(e){return false;}
  }
  var SHARE_PAGES={'250 BALTIC ST':'/250baltic','1 E 161 ST':'/yankeestadium','427 5 AVE':'/barkslope','139 9 ST':'/principles'};
  function shareUrlFor(address,cardOnly){
    var key=liftNorm(address);
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
      .replace(/\b(\d+)(ST|ND|RD|TH)\b/g,'$1')
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
        // Proximity is not identity. Flag it so the badge can say "nearby"
        // instead of claiming this lot is on the list.
        var dm=liftDist(lat,lng,s.lat,s.lng);
        if(dm<=200){ hit=true; s={n:s.n,addr:s.addr,u:s.u,ag:s.ag,st:s.st,lat:s.lat,lng:s.lng,boro:s.boro,_near:true,_dist:Math.round(dm)}; }
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
    'BAM':'30 Lafayette Avenue, Brooklyn',
    'THE BAM':'30 Lafayette Avenue, Brooklyn',
    'BROOKLYN ACADEMY OF MUSIC':'30 Lafayette Avenue, Brooklyn',
    'BAM OPERA HOUSE':'30 Lafayette Avenue, Brooklyn',
    'PETER JAY SHARP BUILDING':'30 Lafayette Avenue, Brooklyn',
    'BAM HARVEY':'651 Fulton Street, Brooklyn',
    'BAM HARVEY THEATER':'651 Fulton Street, Brooklyn',
    'HARVEY THEATER':'651 Fulton Street, Brooklyn',
    'BAM FISHER':'321 Ashland Place, Brooklyn',
    'FISHER BUILDING':'321 Ashland Place, Brooklyn',
    'ATLANTIC YARDS':'620 Atlantic Avenue, Brooklyn',
    'THE ATLANTIC YARDS':'620 Atlantic Avenue, Brooklyn',
    'ATLANTIC YARDS/BARCLAYS CENTER':'620 Atlantic Avenue, Brooklyn',
    'PACIFIC PARK':'620 Atlantic Avenue, Brooklyn',
    'PACIFIC PARK BROOKLYN':'620 Atlantic Avenue, Brooklyn',
    'ATLANTIC TERMINAL':'139 Flatbush Avenue, Brooklyn',
    'PROSPECT PARK':'95 Prospect Park West, Brooklyn',
    'CENTRAL PARK':'830 5 Avenue, Manhattan',
    'CHRYSLER BUILDING':'405 Lexington Avenue, Manhattan',
    'THE CHRYSLER BUILDING':'405 Lexington Avenue, Manhattan',
    'CHRYSLER':'405 Lexington Avenue, Manhattan',
    'HUDSON YARDS':'30 Hudson Yards, Manhattan',
    'THE EDGE':'30 Hudson Yards, Manhattan',
    'THE VESSEL':'20 Hudson Yards, Manhattan',
    'VESSEL':'20 Hudson Yards, Manhattan',
    'BATTERY PARK CITY':'200 Liberty Street, Manhattan',
    'BATTERY PARK CITY AUTHORITY':'200 Liberty Street, Manhattan',
    'BPCA':'200 Liberty Street, Manhattan',
    'BROOKFIELD PLACE':'230 Vesey Street, Manhattan',
    'WORLD FINANCIAL CENTER':'230 Vesey Street, Manhattan',
    'THE CENTRAL PARK':'830 5 Avenue, Manhattan',
    'CENTRAL PARK CONSERVANCY':'830 5 Avenue, Manhattan',
    'THE ARSENAL':'830 5 Avenue, Manhattan',
    'SHEEP MEADOW':'830 5 Avenue, Manhattan',
    'THE RAMBLE':'830 5 Avenue, Manhattan',
    'BETHESDA TERRACE':'830 5 Avenue, Manhattan',
    'CENTRAL PARK ZOO':'830 5 Avenue, Manhattan',
    'THE PARK':'95 Prospect Park West, Brooklyn',
    'LONG MEADOW':'95 Prospect Park West, Brooklyn',
    'THE LONG MEADOW':'95 Prospect Park West, Brooklyn',
    'LITCHFIELD VILLA':'95 Prospect Park West, Brooklyn',
    'PROSPECT PARK BANDSHELL':'95 Prospect Park West, Brooklyn',
    'THE BANDSHELL':'95 Prospect Park West, Brooklyn',
    'PROSPECT PARK BOATHOUSE':'95 Prospect Park West, Brooklyn',
    'THE BOATHOUSE':'95 Prospect Park West, Brooklyn',
    'PROSPECT PARK ZOO':'95 Prospect Park West, Brooklyn',
    'LEFFERTS HISTORIC HOUSE':'95 Prospect Park West, Brooklyn',
    'PROSPECT PARK ALLIANCE':'95 Prospect Park West, Brooklyn',
    'STATEN ISLAND FERRY':'4 South Street, Manhattan',
    'SI FERRY':'4 South Street, Manhattan',
    'THE FERRY':'4 South Street, Manhattan',
    'WHITEHALL TERMINAL':'4 South Street, Manhattan',
    'WHITEHALL FERRY TERMINAL':'4 South Street, Manhattan',
    'STATEN ISLAND FERRY MANHATTAN':'4 South Street, Manhattan',
    'ST GEORGE FERRY TERMINAL':'1 Bay Street, Staten Island',
    'ST GEORGE TERMINAL':'1 Bay Street, Staten Island',
    'SAINT GEORGE FERRY TERMINAL':'1 Bay Street, Staten Island',
    'STATEN ISLAND FERRY STATEN ISLAND':'1 Bay Street, Staten Island',
    'PORT AUTHORITY':'625 8 Avenue, Manhattan',
    'PORT AUTHORITY BUS TERMINAL':'625 8 Avenue, Manhattan',
    'PABT':'625 8 Avenue, Manhattan',
    'THE PORT AUTHORITY':'625 8 Avenue, Manhattan',
    'MOYNIHAN':'421 8 Avenue, Manhattan',
    'MOYNIHAN TRAIN HALL':'421 8 Avenue, Manhattan',
    'MOYNIHAN HALL':'421 8 Avenue, Manhattan',
    'JAMAICA STATION':'93-02 Sutphin Boulevard, Queens',
    'SUTPHIN BOULEVARD STATION':'93-02 Sutphin Boulevard, Queens',
    'JAMAICA LIRR':'93-02 Sutphin Boulevard, Queens',
    'FULTON CENTER':'200 Broadway, Manhattan',
    'FULTON STREET STATION':'200 Broadway, Manhattan',
    'GWB BUS STATION':'4211 Broadway, Manhattan',
    'GEORGE WASHINGTON BRIDGE BUS STATION':'4211 Broadway, Manhattan',
    'MOMA':'11 West 53 Street, Manhattan',
    'THE MOMA':'11 West 53 Street, Manhattan',
    'MUSEUM OF MODERN ART':'11 West 53 Street, Manhattan',
    'THE MUSEUM OF MODERN ART':'11 West 53 Street, Manhattan',
    'GUGGENHEIM':'1071 5 Avenue, Manhattan',
    'THE GUGGENHEIM':'1071 5 Avenue, Manhattan',
    'GUGGENHEIM MUSEUM':'1071 5 Avenue, Manhattan',
    'SOLOMON R GUGGENHEIM MUSEUM':'1071 5 Avenue, Manhattan',
    'WHITNEY':'99 Gansevoort Street, Manhattan',
    'THE WHITNEY':'99 Gansevoort Street, Manhattan',
    'WHITNEY MUSEUM':'99 Gansevoort Street, Manhattan',
    'WHITNEY MUSEUM OF AMERICAN ART':'99 Gansevoort Street, Manhattan',
    'FRICK':'1 East 70 Street, Manhattan',
    'THE FRICK':'1 East 70 Street, Manhattan',
    'FRICK COLLECTION':'1 East 70 Street, Manhattan',
    'THE FRICK COLLECTION':'1 East 70 Street, Manhattan',
    'COOPER HEWITT':'2 East 91 Street, Manhattan',
    'COOPER HEWITT MUSEUM':'2 East 91 Street, Manhattan',
    'COOPER-HEWITT':'2 East 91 Street, Manhattan',
    'JEWISH MUSEUM':'1109 5 Avenue, Manhattan',
    'THE JEWISH MUSEUM':'1109 5 Avenue, Manhattan',
    'MCNY':'1220 5 Avenue, Manhattan',
    'MUSEUM OF THE CITY OF NEW YORK':'1220 5 Avenue, Manhattan',
    'EL MUSEO':'1230 5 Avenue, Manhattan',
    'EL MUSEO DEL BARRIO':'1230 5 Avenue, Manhattan',
    'STUDIO MUSEUM':'144 West 125 Street, Manhattan',
    'STUDIO MUSEUM IN HARLEM':'144 West 125 Street, Manhattan',
    'NEW MUSEUM':'235 Bowery, Manhattan',
    'THE NEW MUSEUM':'235 Bowery, Manhattan',
    'TENEMENT MUSEUM':'103 Orchard Street, Manhattan',
    'THE TENEMENT MUSEUM':'103 Orchard Street, Manhattan',
    'MUSEUM OF JEWISH HERITAGE':'36 Battery Place, Manhattan',
    '9/11 MEMORIAL':'180 Greenwich Street, Manhattan',
    '9/11 MUSEUM':'180 Greenwich Street, Manhattan',
    '911 MEMORIAL':'180 Greenwich Street, Manhattan',
    'SEPTEMBER 11 MEMORIAL':'180 Greenwich Street, Manhattan',
    '9/11 MEMORIAL AND MUSEUM':'180 Greenwich Street, Manhattan',
    'GROUND ZERO':'180 Greenwich Street, Manhattan',
    'MORGAN LIBRARY':'225 Madison Avenue, Manhattan',
    'THE MORGAN':'225 Madison Avenue, Manhattan',
    'MORGAN LIBRARY AND MUSEUM':'225 Madison Avenue, Manhattan',
    'NEUE GALERIE':'1048 5 Avenue, Manhattan',
    'THE NEUE GALERIE':'1048 5 Avenue, Manhattan',
    'MOMA PS1':'22-25 Jackson Avenue, Queens',
    'PS1':'22-25 Jackson Avenue, Queens',
    'PS 1':'22-25 Jackson Avenue, Queens',
    'QUEENS MUSEUM':'1 Flushing Meadows Corona Park, Queens',
    'THE QUEENS MUSEUM':'1 Flushing Meadows Corona Park, Queens',
    'MOMI':'36-01 35 Avenue, Queens',
    'MUSEUM OF THE MOVING IMAGE':'36-01 35 Avenue, Queens',
    'NOGUCHI':'9-01 33 Road, Queens',
    'NOGUCHI MUSEUM':'9-01 33 Road, Queens',
    'THE NOGUCHI MUSEUM':'9-01 33 Road, Queens',
    'BRONX MUSEUM':'1040 Grand Concourse, Bronx',
    'BRONX MUSEUM OF THE ARTS':'1040 Grand Concourse, Bronx',
    'STATEN ISLAND MUSEUM':'1000 Richmond Terrace, Staten Island',
    'NEW YORK HISTORICAL':'170 Central Park West, Manhattan',
    'NEW-YORK HISTORICAL':'170 Central Park West, Manhattan',
    'NEW YORK HISTORICAL SOCIETY':'170 Central Park West, Manhattan',
    'NY HISTORICAL SOCIETY':'170 Central Park West, Manhattan',
    'AL HIRSCHFELD THEATRE':'302 West 45 Street, Manhattan',
    'AL HIRSCHFELD':'302 West 45 Street, Manhattan',
    'THE AL HIRSCHFELD':'302 West 45 Street, Manhattan',
    'AL HIRSCHFELD THEATER':'302 West 45 Street, Manhattan',
    'AMBASSADOR THEATRE':'219 West 49 Street, Manhattan',
    'AMBASSADOR':'219 West 49 Street, Manhattan',
    'THE AMBASSADOR':'219 West 49 Street, Manhattan',
    'AMBASSADOR THEATER':'219 West 49 Street, Manhattan',
    'AUGUST WILSON THEATRE':'245 West 52 Street, Manhattan',
    'AUGUST WILSON':'245 West 52 Street, Manhattan',
    'THE AUGUST WILSON':'245 West 52 Street, Manhattan',
    'AUGUST WILSON THEATER':'245 West 52 Street, Manhattan',
    'BELASCO THEATRE':'111 West 44 Street, Manhattan',
    'BELASCO':'111 West 44 Street, Manhattan',
    'THE BELASCO':'111 West 44 Street, Manhattan',
    'BELASCO THEATER':'111 West 44 Street, Manhattan',
    'BERNARD B JACOBS THEATRE':'242 West 45 Street, Manhattan',
    'BERNARD B JACOBS':'242 West 45 Street, Manhattan',
    'THE BERNARD B JACOBS':'242 West 45 Street, Manhattan',
    'BERNARD B JACOBS THEATER':'242 West 45 Street, Manhattan',
    'BOOTH THEATRE':'222 West 45 Street, Manhattan',
    'BOOTH':'222 West 45 Street, Manhattan',
    'THE BOOTH':'222 West 45 Street, Manhattan',
    'BOOTH THEATER':'222 West 45 Street, Manhattan',
    'BROADHURST THEATRE':'235 West 44 Street, Manhattan',
    'BROADHURST':'235 West 44 Street, Manhattan',
    'THE BROADHURST':'235 West 44 Street, Manhattan',
    'BROADHURST THEATER':'235 West 44 Street, Manhattan',
    'BROADWAY THEATRE':'1681 Broadway, Manhattan',
    'BROADWAY':'1681 Broadway, Manhattan',
    'THE BROADWAY':'1681 Broadway, Manhattan',
    'BROADWAY THEATER':'1681 Broadway, Manhattan',
    'CIRCLE IN THE SQUARE THEATRE':'235 West 50 Street, Manhattan',
    'CIRCLE IN THE SQUARE':'235 West 50 Street, Manhattan',
    'THE CIRCLE IN THE SQUARE':'235 West 50 Street, Manhattan',
    'CIRCLE IN THE SQUARE THEATER':'235 West 50 Street, Manhattan',
    'ETHEL BARRYMORE THEATRE':'243 West 47 Street, Manhattan',
    'ETHEL BARRYMORE':'243 West 47 Street, Manhattan',
    'THE ETHEL BARRYMORE':'243 West 47 Street, Manhattan',
    'ETHEL BARRYMORE THEATER':'243 West 47 Street, Manhattan',
    'EUGENE O\'NEILL THEATRE':'230 West 49 Street, Manhattan',
    'EUGENE O\'NEILL':'230 West 49 Street, Manhattan',
    'THE EUGENE O\'NEILL':'230 West 49 Street, Manhattan',
    'EUGENE O\'NEILL THEATER':'230 West 49 Street, Manhattan',
    'GERALD SCHOENFELD THEATRE':'236 West 45 Street, Manhattan',
    'GERALD SCHOENFELD':'236 West 45 Street, Manhattan',
    'THE GERALD SCHOENFELD':'236 West 45 Street, Manhattan',
    'GERALD SCHOENFELD THEATER':'236 West 45 Street, Manhattan',
    'GERSHWIN THEATRE':'222 West 51 Street, Manhattan',
    'GERSHWIN':'222 West 51 Street, Manhattan',
    'THE GERSHWIN':'222 West 51 Street, Manhattan',
    'GERSHWIN THEATER':'222 West 51 Street, Manhattan',
    'HAYES THEATER':'240 West 44 Street, Manhattan',
    'HAYES':'240 West 44 Street, Manhattan',
    'THE HAYES':'240 West 44 Street, Manhattan',
    'HUDSON THEATRE':'141 West 44 Street, Manhattan',
    'HUDSON':'141 West 44 Street, Manhattan',
    'THE HUDSON':'141 West 44 Street, Manhattan',
    'HUDSON THEATER':'141 West 44 Street, Manhattan',
    'IMPERIAL THEATRE':'249 West 45 Street, Manhattan',
    'IMPERIAL':'249 West 45 Street, Manhattan',
    'THE IMPERIAL':'249 West 45 Street, Manhattan',
    'IMPERIAL THEATER':'249 West 45 Street, Manhattan',
    'JAMES EARL JONES THEATRE':'138 West 48 Street, Manhattan',
    'JAMES EARL JONES':'138 West 48 Street, Manhattan',
    'THE JAMES EARL JONES':'138 West 48 Street, Manhattan',
    'JAMES EARL JONES THEATER':'138 West 48 Street, Manhattan',
    'JOHN GOLDEN THEATRE':'252 West 45 Street, Manhattan',
    'JOHN GOLDEN':'252 West 45 Street, Manhattan',
    'THE JOHN GOLDEN':'252 West 45 Street, Manhattan',
    'JOHN GOLDEN THEATER':'252 West 45 Street, Manhattan',
    'LENA HORNE THEATRE':'256 West 47 Street, Manhattan',
    'LENA HORNE':'256 West 47 Street, Manhattan',
    'THE LENA HORNE':'256 West 47 Street, Manhattan',
    'LENA HORNE THEATER':'256 West 47 Street, Manhattan',
    'LONGACRE THEATRE':'220 West 48 Street, Manhattan',
    'LONGACRE':'220 West 48 Street, Manhattan',
    'THE LONGACRE':'220 West 48 Street, Manhattan',
    'LONGACRE THEATER':'220 West 48 Street, Manhattan',
    'LUNT-FONTANNE THEATRE':'205 West 46 Street, Manhattan',
    'LUNT-FONTANNE':'205 West 46 Street, Manhattan',
    'THE LUNT-FONTANNE':'205 West 46 Street, Manhattan',
    'LUNT-FONTANNE THEATER':'205 West 46 Street, Manhattan',
    'LYCEUM THEATRE':'149 West 45 Street, Manhattan',
    'LYCEUM':'149 West 45 Street, Manhattan',
    'THE LYCEUM':'149 West 45 Street, Manhattan',
    'LYCEUM THEATER':'149 West 45 Street, Manhattan',
    'LYRIC THEATRE':'214 West 43 Street, Manhattan',
    'LYRIC':'214 West 43 Street, Manhattan',
    'THE LYRIC':'214 West 43 Street, Manhattan',
    'LYRIC THEATER':'214 West 43 Street, Manhattan',
    'MAJESTIC THEATRE':'245 West 44 Street, Manhattan',
    'MAJESTIC':'245 West 44 Street, Manhattan',
    'THE MAJESTIC':'245 West 44 Street, Manhattan',
    'MAJESTIC THEATER':'245 West 44 Street, Manhattan',
    'MARQUIS THEATRE':'1535 Broadway, Manhattan',
    'MARQUIS':'1535 Broadway, Manhattan',
    'THE MARQUIS':'1535 Broadway, Manhattan',
    'MARQUIS THEATER':'1535 Broadway, Manhattan',
    'MINSKOFF THEATRE':'200 West 45 Street, Manhattan',
    'MINSKOFF':'200 West 45 Street, Manhattan',
    'THE MINSKOFF':'200 West 45 Street, Manhattan',
    'MINSKOFF THEATER':'200 West 45 Street, Manhattan',
    'MUSIC BOX THEATRE':'239 West 45 Street, Manhattan',
    'MUSIC BOX':'239 West 45 Street, Manhattan',
    'THE MUSIC BOX':'239 West 45 Street, Manhattan',
    'MUSIC BOX THEATER':'239 West 45 Street, Manhattan',
    'NEDERLANDER THEATRE':'208 West 41 Street, Manhattan',
    'NEDERLANDER':'208 West 41 Street, Manhattan',
    'THE NEDERLANDER':'208 West 41 Street, Manhattan',
    'NEDERLANDER THEATER':'208 West 41 Street, Manhattan',
    'NEIL SIMON THEATRE':'250 West 52 Street, Manhattan',
    'NEIL SIMON':'250 West 52 Street, Manhattan',
    'THE NEIL SIMON':'250 West 52 Street, Manhattan',
    'NEIL SIMON THEATER':'250 West 52 Street, Manhattan',
    'NEW AMSTERDAM THEATRE':'214 West 42 Street, Manhattan',
    'NEW AMSTERDAM':'214 West 42 Street, Manhattan',
    'THE NEW AMSTERDAM':'214 West 42 Street, Manhattan',
    'NEW AMSTERDAM THEATER':'214 West 42 Street, Manhattan',
    'PALACE THEATRE':'160 West 47 Street, Manhattan',
    'PALACE':'160 West 47 Street, Manhattan',
    'THE PALACE':'160 West 47 Street, Manhattan',
    'PALACE THEATER':'160 West 47 Street, Manhattan',
    'RICHARD RODGERS THEATRE':'226 West 46 Street, Manhattan',
    'RICHARD RODGERS':'226 West 46 Street, Manhattan',
    'THE RICHARD RODGERS':'226 West 46 Street, Manhattan',
    'RICHARD RODGERS THEATER':'226 West 46 Street, Manhattan',
    'SAMUEL J FRIEDMAN THEATRE':'261 West 47 Street, Manhattan',
    'SAMUEL J FRIEDMAN':'261 West 47 Street, Manhattan',
    'THE SAMUEL J FRIEDMAN':'261 West 47 Street, Manhattan',
    'SAMUEL J FRIEDMAN THEATER':'261 West 47 Street, Manhattan',
    'SHUBERT THEATRE':'225 West 44 Street, Manhattan',
    'SHUBERT':'225 West 44 Street, Manhattan',
    'THE SHUBERT':'225 West 44 Street, Manhattan',
    'SHUBERT THEATER':'225 West 44 Street, Manhattan',
    'ST JAMES THEATRE':'246 West 44 Street, Manhattan',
    'ST JAMES':'246 West 44 Street, Manhattan',
    'THE ST JAMES':'246 West 44 Street, Manhattan',
    'ST JAMES THEATER':'246 West 44 Street, Manhattan',
    'STEPHEN SONDHEIM THEATRE':'124 West 43 Street, Manhattan',
    'STEPHEN SONDHEIM':'124 West 43 Street, Manhattan',
    'THE STEPHEN SONDHEIM':'124 West 43 Street, Manhattan',
    'STEPHEN SONDHEIM THEATER':'124 West 43 Street, Manhattan',
    'STUDIO 54':'254 West 54 Street, Manhattan',
    'THE STUDIO 54':'254 West 54 Street, Manhattan',
    'TODD HAIMES THEATRE':'227 West 42 Street, Manhattan',
    'TODD HAIMES':'227 West 42 Street, Manhattan',
    'THE TODD HAIMES':'227 West 42 Street, Manhattan',
    'TODD HAIMES THEATER':'227 West 42 Street, Manhattan',
    'VIVIAN BEAUMONT THEATER':'150 West 65 Street, Manhattan',
    'VIVIAN BEAUMONT':'150 West 65 Street, Manhattan',
    'THE VIVIAN BEAUMONT':'150 West 65 Street, Manhattan',
    'WALTER KERR THEATRE':'219 West 48 Street, Manhattan',
    'WALTER KERR':'219 West 48 Street, Manhattan',
    'THE WALTER KERR':'219 West 48 Street, Manhattan',
    'WALTER KERR THEATER':'219 West 48 Street, Manhattan',
    'WINTER GARDEN THEATRE':'1634 Broadway, Manhattan',
    'WINTER GARDEN':'1634 Broadway, Manhattan',
    'THE WINTER GARDEN':'1634 Broadway, Manhattan',
    'WINTER GARDEN THEATER':'1634 Broadway, Manhattan',
    'EMPIRE STATE BUILDING':'338 5 Avenue, Manhattan',
    'THE EMPIRE STATE BUILDING':'338 5 Avenue, Manhattan',
    'ESB':'338 5 Avenue, Manhattan',
    'GRAND CENTRAL':'89 East 42 Street, Manhattan',
    'GRAND CENTRAL TERMINAL':'89 East 42 Street, Manhattan',
    'GRAND CENTRAL STATION':'89 East 42 Street, Manhattan',
    'ROCKEFELLER CENTER':'30 Rockefeller Plaza, Manhattan',
    '30 ROCK':'30 Rockefeller Plaza, Manhattan',
    'RADIO CITY':'1260 6 Avenue, Manhattan',
    'RADIO CITY MUSIC HALL':'1260 6 Avenue, Manhattan',
    'CARNEGIE HALL':'881 7 Avenue, Manhattan',
    'MADISON SQUARE GARDEN':'4 Penn Plaza, Manhattan',
    'THE GARDEN':'4 Penn Plaza, Manhattan',
    'LINCOLN CENTER':'60 Columbus Avenue, Manhattan',
    'APOLLO THEATER':'253 West 125 Street, Manhattan',
    'THE APOLLO':'253 West 125 Street, Manhattan',
    'MET MUSEUM':'1000 5 Avenue, Manhattan',
    'THE MET':'1000 5 Avenue, Manhattan',
    'METROPOLITAN MUSEUM OF ART':'1000 5 Avenue, Manhattan',
    'AMNH':'200 Central Park West, Manhattan',
    'MUSEUM OF NATURAL HISTORY':'200 Central Park West, Manhattan',
    'AMERICAN MUSEUM OF NATURAL HISTORY':'200 Central Park West, Manhattan',
    'ONE WORLD TRADE':'185 Greenwich Street, Manhattan',
    'ONE WORLD TRADE CENTER':'185 Greenwich Street, Manhattan',
    'FREEDOM TOWER':'185 Greenwich Street, Manhattan',
    'NYSE':'11 Wall Street, Manhattan',
    'NEW YORK STOCK EXCHANGE':'11 Wall Street, Manhattan',
    'CITY HALL':'52 Chambers Street, Manhattan',
    'BROOKLYN BOROUGH HALL':'225 Joralemon Street, Brooklyn',
    'BOROUGH HALL':'225 Joralemon Street, Brooklyn',
    'BROOKLYN MUSEUM':'186 Eastern Parkway, Brooklyn',
    'CENTRAL LIBRARY':'415 Flatbush Avenue, Brooklyn',
    'BROOKLYN PUBLIC LIBRARY':'415 Flatbush Avenue, Brooklyn',
    'OLD STONE HOUSE':'336 3 Street, Brooklyn',
    'GREENWOOD':'500 25 Street, Brooklyn',
    'GREEN-WOOD':'500 25 Street, Brooklyn',
    'GREEN-WOOD CEMETERY':'500 25 Street, Brooklyn',
    'BROOKLYN BRIDGE PARK':'334 Furman Street, Brooklyn',
    'BBP':'334 Furman Street, Brooklyn',
    'BROOKLYN NAVY YARD':'652 Kent Avenue, Brooklyn',
    'THE NAVY YARD':'652 Kent Avenue, Brooklyn',
    'INDUSTRY CITY':'472 2 Avenue, Brooklyn',
    'KINGS THEATRE':'1027 Flatbush Avenue, Brooklyn',
    'LUNA PARK':'1000 Surf Avenue, Brooklyn',
    'THE CYCLONE':'834 Surf Avenue, Brooklyn',
    'CONEY ISLAND CYCLONE':'834 Surf Avenue, Brooklyn',
    'IKEA':'21 Beard Street, Brooklyn',
    'IKEA RED HOOK':'21 Beard Street, Brooklyn',
    'RED HOOK BALL FIELDS':'597 Columbia Street, Brooklyn',
    'THE BALL FIELDS':'597 Columbia Street, Brooklyn',
    'CITI FIELD':'123-01 Roosevelt Avenue, Queens',
    'ARTHUR ASHE STADIUM':'56-01 Grand Central Parkway, Queens',
    'US OPEN':'56-01 Grand Central Parkway, Queens',
    'BRONX ZOO':'2300 Southern Boulevard, Bronx',
    'THE BRONX ZOO':'2300 Southern Boulevard, Bronx',
    'NEW YORK BOTANICAL GARDEN':'2600 Southern Boulevard, Bronx',
    'NYBG':'2600 Southern Boulevard, Bronx',
    'SNUG HARBOR':'1000 Snug Harbor Road, Staten Island'
  };
  var LAST_PLACE='';
  function titlePlace(t){t=String(t||''); if(/[a-z]/.test(t)) return t;
    return t.toLowerCase().replace(/(^|[^a-z'])([a-z])/g,function(m,a,b){return a+b.toUpperCase();})
      .replace(/\b(Of|The|And|At)\b/g,function(w){return w.toLowerCase();})
      .replace(/^./,function(c){return c.toUpperCase();});}
  function cleanPlace(l){return titlePlace(String(l||'').replace(/,\s*(Kings|Queens|New York|Bronx|Richmond)\s+County.*$/i,'').replace(/,\s*(Brooklyn|Manhattan|Queens|Bronx|Staten Island)?,?\s*NY,?\s*USA\s*$/i,'').replace(/,\s*(Brooklyn|Manhattan|Queens|Bronx|Staten Island)\s*$/i,'').trim());}
  // A generic search like "broadway show" is not an address. Offer the list instead.
  function broadwayList(){
    var seen={}, out=[];
    Object.keys(NICKNAMES).forEach(function(k){
      var addr=NICKNAMES[k], key=liftNorm(addr), a=AKA[key];
      if(typeof a==='string' && /Broadway theatre$/.test(a) && !seen[key]){
        seen[key]=1;
        out.push({name:a.replace(/^the /,'').replace(/,\s*a Broadway theatre$/,''), addr:addr});
      }
    });
    out.sort(function(x,y){ return x.name.localeCompare(y.name); });
    return out;
  }
  // NYCHA developments come from the same directory the NYCHA page uses.
  var NYCHA_DIR=null, nychaLoading=null;
  function loadNycha(){
    if(NYCHA_DIR) return Promise.resolve(NYCHA_DIR);
    if(nychaLoading) return nychaLoading;
    nychaLoading=fetch('/data/nycha-directory.json').then(function(r){return r.json();})
      .then(function(j){ NYCHA_DIR=Array.isArray(j)?j:[]; return NYCHA_DIR; })
      .catch(function(){ NYCHA_DIR=[]; return NYCHA_DIR; });
    return nychaLoading;
  }
  var BORO_TITLE={BROOKLYN:'Brooklyn',MANHATTAN:'Manhattan',BRONX:'Bronx',QUEENS:'Queens','STATEN ISLAND':'Staten Island'};
  function nychaList(filter){
    var out=[];
    (NYCHA_DIR||[]).forEach(function(x){
      var addr=(x.addrs&&x.addrs[0])||'';
      if(!addr || !/^\d/.test(addr)) return;
      if(filter && !filter(x)) return;
      var bn=BORO_TITLE[String(x.boro||'').toUpperCase()]||'';
      if(!bn && /^\d+-\d+/.test(addr)) bn='Queens';
      out.push({name:x.name+(bn?' \u00b7 '+bn:''), addr:addr+(bn?', '+bn:'')});
    });
    out.sort(function(a,b){ return a.name.localeCompare(b.name); });
    return out;
  }
  function transitList(){
    var seen={}, out=[];
    Object.keys(NICKNAMES).forEach(function(k){
      var addr=NICKNAMES[k], key=liftNorm(addr), a=AKA[key];
      if(typeof a==='string' && /terminal|train hall|station|ferry|bus terminal|fulton center/i.test(a) && !seen[key]){
        seen[key]=1; out.push({name:a.replace(/^the /,''), addr:addr});
      }
    });
    out.sort(function(x,y){ return x.name.localeCompare(y.name); });
    return out;
  }
  function museumList(){
    var seen={}, out=[];
    Object.keys(NICKNAMES).forEach(function(k){
      var addr=NICKNAMES[k], key=liftNorm(addr), a=AKA[key];
      if(typeof a==='string' && /museum|galerie|collection|historical|moma|ps1|guggenheim|whitney|frick|cooper hewitt|memorial/i.test(a) && !seen[key]){
        seen[key]=1;
        out.push({name:a.replace(/^the /,''), addr:addr});
      }
    });
    out.sort(function(x,y){ return x.name.localeCompare(y.name); });
    return out;
  }
  var GENERIC=[
    {re:/^(the\s+)?(transit|transit hubs?|transportation hubs?|train stations?|bus terminals?|ferry|ferries|transportation)$/i,
     title:'Transit hubs',
     note:'The big transportation hubs. Pick one to see its zoning, land use, districts and everything else on the lot.',
     items:transitList},
    {re:/^(the\s+)?(museums?|nyc museums?|new york museums?|art museums?)$/i,
     title:'Museums',
     note:'Major museums across the five boroughs. Pick one to see its zoning, land use, districts and everything else on the lot.',
     items:museumList},
    {re:/^(the\s+)?(nycha|nycha developments?|nycha houses|nycha buildings|nycha housing|public housing|nyc public housing|public housing developments?|city housing|housing projects|housing authority|nyc housing authority|new york city housing authority|nyc ha)$/i,
     title:'NYCHA developments',
     note:'Every NYCHA development in the city. Pick one to see its zoning, land use, districts and everything else on the lot.',
     items:function(){ return nychaList(null); },
     needs:loadNycha},
    {re:/^(nycha|public housing)\s+(in\s+)?(cb6|community board 6|brooklyn cb6|park slope|gowanus|red hook|carroll gardens|cobble hill)$/i,
     title:'NYCHA in CB6',
     note:'The NYCHA developments in Brooklyn Community Board 6.',
     items:function(){ return nychaList(function(x){ return (x.cds||[]).indexOf('306')>-1; }); },
     needs:loadNycha},
    {re:/^(nycha|public housing)\s+(in\s+)?(brooklyn|manhattan|queens|the bronx|bronx|staten island)$/i,
     title:'NYCHA developments',
     note:'NYCHA developments in that borough. Pick one to see the full record for its lot.',
     items:function(){ return nychaList(function(x){ return String(x.boro||'').toUpperCase()===String(this.boro||'').toUpperCase(); }.bind(this)); },
     needs:loadNycha,
     boroFrom:true},
    {re:/^(the\s+)?(broadway|b'?way)(\s+(shows?|musicals?|theatres?|theaters?|plays?|district))?$/i,
     title:'Broadway theatres',
     note:'There are 41 Broadway theatres. Pick one to see its zoning, land use, districts and everything else on the lot.',
     items:broadwayList},
    {re:/^(the\s+)?(theat(re|er)\s+district|times\s+square\s+theat(re|er)s?)$/i,
     title:'Broadway theatres',
     note:'The Theater District, and the 41 Broadway theatres in it. Pick one to see the full record for its lot.',
     items:broadwayList}
  ];
  function genericMatch(q){
    var t=String(q||'').trim();
    // an exact theatre name wins over the generic list
    var k=t.toUpperCase().replace(/\s+/g,' ').replace(/[.]/g,'');
    if(k!=='BROADWAY' && NICKNAMES[k]) return null;
    for(var i=0;i<GENERIC.length;i++){ if(GENERIC[i].re.test(t)) return GENERIC[i]; }
    return null;
  }
  function showPicker(result,input,g){
    var items=g.items();
    result.innerHTML='<div style="background:#f0f8f4;border:1.5px solid #a7f3d0;border-radius:8px;padding:14px">'+
      '<div style="font-size:1.05rem;font-weight:900;color:var(--navy,#0d1b4b)">'+esc(g.title)+'</div>'+
      '<div style="font-size:.83rem;line-height:1.55;color:#444;margin:5px 0 12px">'+esc(g.note)+'</div>'+
      '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:7px">'+
      items.map(function(it){
        return '<button type="button" data-pick="'+esc(it.addr)+'" style="text-align:left;cursor:pointer;'+
          'background:#fff;border:1px solid var(--border,#e5e2db);border-radius:6px;padding:8px 10px;font-family:inherit">'+
          '<span style="display:block;font-size:.85rem;font-weight:800;color:var(--navy,#0d1b4b)">'+esc(it.name)+'</span>'+
          '<span style="display:block;font-family:\'DM Mono\',monospace;font-size:.66rem;color:var(--muted,#6b6760);margin-top:2px">'+
          esc(it.addr.replace(/,\s*Manhattan$/,''))+'</span></button>';
      }).join('')+'</div></div>';
    result.hidden=false;
    result.addEventListener('click',function(ev){
      var b=ev.target.closest?ev.target.closest('[data-pick]'):null;
      if(!b) return;
      if(input){ input.value=b.getAttribute('data-pick'); }
      if(typeof g.onpick==='function') g.onpick();
    });
    try{ result.scrollIntoView({block:'start',behavior:'smooth'}); }catch(e){}
  }
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
  var NYCHA_ICON={src:'/site-icons/nycha.png',alt:'New York City Housing Authority',w:309,h:360};
  var PARK_ICONS={
    '3011170001':{src:'/site-icons/prospect-park.png',alt:'Prospect Park',w:400,h:399},
    '3002450015':{src:'/site-icons/brooklyn-bridge-park.png',alt:'Brooklyn Bridge Park',w:440,h:177},
    '3001990003':{src:'/site-icons/brooklyn-bridge-park.png',alt:'Brooklyn Bridge Park',w:440,h:177},
    '3002450029':{src:'/site-icons/brooklyn-bridge-park.png',alt:'Brooklyn Bridge Park',w:440,h:177}
  };
  var FERRY_ICON={src:'/site-icons/staten-island-ferry.png',alt:'Staten Island Ferry',w:520,h:130};
  var FERRY_ADDRS={'4 S ST':1,'1 BAY ST':1};
  var BROADWAY_ICON={src:'/site-icons/broadway-org.png',alt:'Broadway',w:520,h:91};
  function isBroadwayAddr(addr){ var a=AKA[liftNorm(addr)]; return typeof a==='string' && /Broadway theatre/i.test(a); }
  // Businesses at an address. These are a marker for a storefront in the
  // building, not a statement about the lot, so they render in their own block
  // under the board logo rather than beside it.
  var BIZ_SITES={
    '427 5 AVE':[{name:'Bark Slope Salon',kind:'Dog grooming salon',src:'/site-icons/bark-slope.png',w:258,h:436,href:'https://www.barkslopesalon.com/',plate:'#ffffff'}],
    '139 9 ST':[{name:'Principles Cafe',kind:'Coffee house',src:'/site-icons/principles-cafe.png',w:520,h:520,href:'https://principlesbk.nyc/',plate:'#3a3c3e'}]
  };
  // Business improvement districts. A BID covers a stretch of street, so this is
  // a district the address sits in, not a tenant of the building.
  var BID_SITES={
    '427 5 AVE':{name:'Park Slope Fifth Avenue BID',src:'/site-icons/bid-park-slope-fifth-ave.png',w:129,h:300,href:'https://parkslopefifthavenuebid.com',plate:'#ffffff'}
  };
  function bidBlock(input){
    var d=BID_SITES[liftNorm(input)];
    if(!d) return '';
    return '<div style="margin:0 0 10px">'+
      '<div style="font-family:\'DM Mono\',monospace;font-size:.6rem;text-transform:uppercase;letter-spacing:.1em;color:var(--muted,#6b6760);font-weight:700;margin-bottom:5px">In a business improvement district</div>'+
      '<a href="'+d.href+'" target="_blank" rel="noopener" style="display:flex;align-items:center;gap:12px;text-decoration:none;background:#fff;border:1px solid #d1fae5;border-radius:8px;padding:10px 12px">'+
        '<span style="flex:none;width:58px;height:58px;border-radius:7px;background:'+d.plate+';border:1px solid #e5e2db;display:flex;align-items:center;justify-content:center;overflow:hidden">'+
          '<img src="'+d.src+'" alt="'+esc(d.name)+'" width="'+d.w+'" height="'+d.h+'" loading="lazy" style="max-width:50px;max-height:50px;width:auto;height:auto;display:block">'+
        '</span>'+
        '<span style="flex:1;min-width:0">'+
          '<span style="display:block;font-size:.92rem;font-weight:900;color:var(--navy,#0d1b4b);line-height:1.25">'+esc(d.name)+'</span>'+
          '<span style="display:block;font-size:.73rem;color:var(--muted,#6b6760);line-height:1.4;margin-top:2px">A BID is a defined stretch of commercial street where property owners fund extra sanitation, streetscape and marketing work.</span>'+
        '</span>'+
        '<span style="flex:none;font-size:.72rem;font-weight:800;color:#fff;background:var(--orange,#f47920);border-radius:999px;padding:6px 12px;white-space:nowrap">Visit site &#8599;</span>'+
      '</a></div>';
  }
  function bizBlock(input){
    var list=BIZ_SITES[liftNorm(input)];
    if(!list||!list.length) return bidBlock(input);
    var rows=list.map(function(b){
      return '<a href="'+b.href+'" target="_blank" rel="noopener" style="display:flex;align-items:center;gap:12px;text-decoration:none;background:#fff;border:1px solid #d1fae5;border-radius:8px;padding:10px 12px">'+
        '<span style="flex:none;width:58px;height:58px;border-radius:7px;background:'+b.plate+';border:1px solid #e5e2db;display:flex;align-items:center;justify-content:center;overflow:hidden">'+
          '<img src="'+b.src+'" alt="'+esc(b.name)+'" width="'+b.w+'" height="'+b.h+'" loading="lazy" style="max-width:50px;max-height:50px;width:auto;height:auto;display:block">'+
        '</span>'+
        '<span style="flex:1;min-width:0">'+
          '<span style="display:block;font-size:.92rem;font-weight:900;color:var(--navy,#0d1b4b);line-height:1.25">'+esc(b.name)+'</span>'+
          '<span style="display:block;font-size:.73rem;color:var(--muted,#6b6760);line-height:1.4;margin-top:2px">'+esc(b.kind)+'</span>'+
        '</span>'+
        '<span style="flex:none;font-size:.72rem;font-weight:800;color:#fff;background:var(--orange,#f47920);border-radius:999px;padding:6px 12px;white-space:nowrap">Visit site &#8599;</span>'+
      '</a>';
    }).join('');
    return '<div style="margin:0 0 10px">'+
      '<div style="font-family:\'DM Mono\',monospace;font-size:.6rem;text-transform:uppercase;letter-spacing:.1em;color:var(--muted,#6b6760);font-weight:700;margin-bottom:5px">'+
        (list.length>1?'Businesses in this building':'Business in this building')+'</div>'+
      rows+'</div>'+bidBlock(input);
  }
  var SITE_ICON={
    '1 E 161 ST':{src:'/site-icons/yankee-stadium.png',alt:'Yankee Stadium',w:360,h:147},
    // Broadway houses: the Playbill cover for what is playing there now.
    '124 W 43 ST':{src:'/site-icons/playbill-stephen-sondheim-theatre.png',alt:'& Juliet at the Stephen Sondheim Theatre',w:360,h:568},
    '214 W 42 ST':{src:'/site-icons/playbill-new-amsterdam-theatre.png',alt:'Aladdin at the New Amsterdam Theatre',w:360,h:568},
    '236 W 45 ST':{src:'/site-icons/playbill-gerald-schoenfeld-theatre.png',alt:'Buena Vista Social Club at the Gerald Schoenfeld Theatre',w:360,h:567},
    '226 W 46 ST':{src:'/site-icons/playbill-richard-rodgers-theatre.png',alt:'Hamilton at the Richard Rodgers Theatre',w:360,h:567},
    '160 W 47 ST':{src:'/site-icons/playbill-palace-theatre.png',alt:'The Lost Boys at the Palace Theatre',w:360,h:568},
    '230 W 49 ST':{src:'/site-icons/playbill-eugene-o-neill-theatre.png',alt:'The Book of Mormon at the Eugene O\'Neill Theatre',w:360,h:568},
    '254 W 54 ST':{src:'/site-icons/playbill-studio-54.png',alt:'The Rocky Horror Show at the Studio 54',w:360,h:568},
    '256 W 47 ST':{src:'/site-icons/playbill-lena-horne-theatre.png',alt:'Six at the Lena Horne Theatre',w:360,h:568},
    '235 W 50 ST':{src:'/site-icons/playbill-circle-in-the-square-theatre.png',alt:'Just in Time at the Circle in the Square Theatre',w:360,h:568},
    '149 W 45 ST':{src:'/site-icons/playbill-lyceum-theatre.png',alt:'Oh, Mary! at the Lyceum Theatre',w:360,h:568},
    '220 W 48 ST':{src:'/site-icons/playbill-longacre-theatre.png',alt:'Two Strangers (Carry a Cake Across New York) at the Longacre Theatre',w:360,h:568},
    '250 W 52 ST':{src:'/site-icons/playbill-neil-simon-theatre.png',alt:'MJ at the Neil Simon Theatre',w:360,h:568},
    '242 W 45 ST':{src:'/site-icons/playbill-bernard-b-jacobs-theatre.png',alt:'The Outsiders at the Bernard B. Jacobs Theatre',w:360,h:568},
    '219 W 49 ST':{src:'/site-icons/playbill-ambassador-theatre.png',alt:'Chicago at the Ambassador Theatre',w:360,h:568},
    '245 W 52 ST':{src:'/site-icons/playbill-august-wilson-theatre.png',alt:'Paranormal Activity at the August Wilson Theatre',w:360,h:568},
    '208 W 41 ST':{src:'/site-icons/playbill-nederlander-theatre.png',alt:'Schmigadoon! at the Nederlander Theatre',w:360,h:568},
    '246 W 44 ST':{src:'/site-icons/playbill-st-james-theatre.png',alt:'Titaníque at the St. James Theatre',w:360,h:568},
    '111 W 44 ST':{src:'/site-icons/playbill-belasco-theatre.png',alt:'Maybe Happy Ending at the Belasco Theatre',w:360,h:568},
    // Broadway houses with no production running: the theatre's own header.
    '222 W 45 ST':{src:'/site-icons/playbill-booth-theatre.png',alt:'Booth Theatre',w:720,h:231},
    '235 W 44 ST':{src:'/site-icons/playbill-broadhurst-theatre.png',alt:'Broadhurst Theatre',w:720,h:231},
    '243 W 47 ST':{src:'/site-icons/playbill-ethel-barrymore-theatre.png',alt:'Ethel Barrymore Theatre',w:720,h:231},
    '240 W 44 ST':{src:'/site-icons/playbill-hayes-theater.png',alt:'Hayes Theater',w:720,h:231},
    '141 W 44 ST':{src:'/site-icons/playbill-hudson-theatre.png',alt:'Hudson Theatre',w:720,h:231},
    '249 W 45 ST':{src:'/site-icons/playbill-imperial-theatre.png',alt:'Imperial Theatre',w:720,h:231},
    '138 W 48 ST':{src:'/site-icons/playbill-james-earl-jones-theatre.png',alt:'James Earl Jones Theatre',w:720,h:231},
    '205 W 46 ST':{src:'/site-icons/playbill-lunt-fontanne-theatre.png',alt:'Lunt-Fontanne Theatre',w:720,h:231},
    '245 W 44 ST':{src:'/site-icons/playbill-majestic-theatre.png',alt:'Majestic Theatre',w:720,h:231},
    '239 W 45 ST':{src:'/site-icons/playbill-music-box-theatre.png',alt:'Music Box Theatre',w:720,h:231},
    '261 W 47 ST':{src:'/site-icons/playbill-samuel-j-friedman-theatre.png',alt:'Samuel J. Friedman Theatre',w:720,h:231},
    '225 W 44 ST':{src:'/site-icons/playbill-shubert-theatre.png',alt:'Shubert Theatre',w:720,h:231},
    '227 W 42 ST':{src:'/site-icons/playbill-todd-haimes-theatre.png',alt:'Todd Haimes Theatre',w:720,h:231},
    '150 W 65 ST':{src:'/site-icons/playbill-vivian-beaumont-theater.png',alt:'Vivian Beaumont Theater',w:720,h:231},
    '1634 BROADWAY':{src:'/site-icons/playbill-winter-garden-theatre.png',alt:'Winter Garden Theatre',w:720,h:231},
    '219 W 48 ST':{src:'/site-icons/playbill-walter-kerr-theatre.png',alt:'Hadestown at the Walter Kerr Theatre',w:360,h:568},
    '252 W 45 ST':{src:'/site-icons/playbill-john-golden-theatre.png',alt:'Operation Mincemeat at the John Golden Theatre',w:360,h:568},
    '222 W 51 ST':{src:'/site-icons/playbill-gershwin-theatre.png',alt:'Wicked at the Gershwin Theatre',w:360,h:568},
    '1681 BROADWAY':{src:'/site-icons/playbill-broadway-theatre.png',alt:'The Great Gatsby at the Broadway Theatre',w:360,h:568},
    '302 W 45 ST':{src:'/site-icons/playbill-al-hirschfeld-theatre.png',alt:'Moulin Rouge! at the Al Hirschfeld Theatre',w:360,h:568},
    '1535 BROADWAY':{src:'/site-icons/playbill-marquis-theatre.png',alt:'Stranger Things: The First Shadow at the Marquis Theatre',w:360,h:568},
    '214 W 43 ST':{src:'/site-icons/playbill-lyric-theatre.png',alt:'Harry Potter and the Cursed Child at the Lyric Theatre',w:360,h:568},
    '200 W 45 ST':{src:'/site-icons/playbill-minskoff-theatre.png',alt:'The Lion King at the Minskoff Theatre',w:360,h:545},
    '89 E 42 ST':{src:'/site-icons/grand-central.png',alt:'Grand Central Terminal',w:356,h:342},
    '11 W 53 ST':{src:'/site-icons/moma.png',alt:'Museum of Modern Art',w:440,h:122},
    '22-25 JACKSON AVE':{src:'/site-icons/moma-ps1.png',alt:'MoMA PS1',w:440,h:247},
    '1000 5 AVE':{src:'/site-icons/the-met.png',alt:'The Metropolitan Museum of Art',w:440,h:438},
    '830 5 AVE':{src:'/site-icons/central-park.png',alt:'Central Park',w:440,h:217},
    '200 CENTRAL PARK W':{src:'/site-icons/amnh.png',alt:'American Museum of Natural History',w:440,h:207},
    '1260 6 AVE':{src:'/site-icons/radio-city.png',alt:'Radio City Music Hall',w:440,h:70},
    '1260 AVE OF THE AMER':{src:'/site-icons/radio-city.png',alt:'Radio City Music Hall',w:440,h:70},
    '30 ROCKEFELLER PLAZA':{src:'/site-icons/rockefeller-center.png',alt:'Rockefeller Center',w:440,h:155},
    '1250 AVE OF THE AMER':{src:'/site-icons/rockefeller-center.png',alt:'Rockefeller Center',w:440,h:155},
    '881 7 AVE':{src:'/site-icons/carnegie-hall.png',alt:'Carnegie Hall',w:440,h:369},
    '338 5 AVE':{src:'/site-icons/empire-state.png',alt:'The Empire State Building',w:440,h:140},
    '185 GREENWICH ST':{src:'/site-icons/one-world-trade.png',alt:'One World Trade Center',w:440,h:202},
    '405 LEXINGTON AVE':{src:'/site-icons/chrysler.png',alt:'Chrysler Building',w:440,h:39},
    '30 HUDSON YARDS':{src:'/site-icons/hudson-yards.png',alt:'Hudson Yards',w:440,h:76},
    '20 HUDSON YARDS':{src:'/site-icons/hudson-yards.png',alt:'Hudson Yards',w:440,h:76},
    '200 LIBERTY ST':{src:'/site-icons/battery-park-city.png',alt:'Battery Park City',w:440,h:147},
    '230 VESEY ST':{src:'/site-icons/battery-park-city.png',alt:'Battery Park City',w:440,h:147},
    '95 PROSPECT PARK W':{src:'/site-icons/prospect-park.png',alt:'Prospect Park',w:400,h:399},
    '30 LAFAYETTE AVE':{src:'/site-icons/bam.png',alt:'Brooklyn Academy of Music',w:400,h:400},
    '651 FULTON ST':{src:'/site-icons/bam.png',alt:'BAM Harvey Theater',w:400,h:400},
    '653 FULTON ST':{src:'/site-icons/bam.png',alt:'BAM Harvey Theater',w:400,h:400},
    '321 ASHLAND PL':{src:'/site-icons/bam.png',alt:'BAM Fisher',w:400,h:400},
    '186 EASTERN PKWY':{src:'/site-icons/brooklyn-museum.png',alt:'Brooklyn Museum',w:440,h:348},
    '334 FURMAN ST':{src:'/site-icons/brooklyn-bridge-park.png',alt:'Brooklyn Bridge Park',w:440,h:177},
    '146 FURMAN ST':{src:'/site-icons/brooklyn-bridge-park.png',alt:'Brooklyn Bridge Park',w:440,h:177},
    '625 8 AVE':{src:'/site-icons/port-authority.png',alt:'Port Authority Bus Terminal',w:416,h:116},
    '421 8 AVE':{src:'/site-icons/moynihan.png',alt:'Moynihan Train Hall, Pennsylvania Station',w:460,h:195},
    '4 PENN PLAZA':{src:'/site-icons/madison-square-garden.png',alt:'Madison Square Garden, home of the Knicks and the Rangers',w:420,h:405}
  };
  var AKA={
    // Arenas and ballparks: on a stadium card the point is the venue and who
    // plays there, not the lot number.
    '41 SEAVER WAY':{text:'Citi Field, home of the Mets',bg:'#0d1b4b',fg:'#FFFFFF'},
    '126-01 ROOSEVELT AVE':{text:'Etihad Park, the future home of NYCFC',bg:'#0d1b4b',fg:'#FFFFFF'},
    '124-02 ROOSEVELT AVE':{text:'the USTA Billie Jean King National Tennis Center, home of the US Open',bg:'#0d1b4b',fg:'#FFFFFF'},
    '1 TENNIS PL':{text:'Forest Hills Stadium',bg:'#0d1b4b',fg:'#FFFFFF'},
    '1904 SURF AVE':{text:'Maimonides Park, home of the Brooklyn Cyclones',bg:'#0d1b4b',fg:'#FFFFFF'},
    '75 RICHMOND TERRACE':{text:'SIUH Community Park, home of the Staten Island FerryHawks',bg:'#0d1b4b',fg:'#FFFFFF'},
    '20 RANDALLS ISLAND':{text:'Icahn Stadium on Randall\u2019s Island',bg:'#0d1b4b',fg:'#FFFFFF'},
    '24-64 KANE ST':'Brooklyn Marine Terminal, or the BMT',
    '435 HOYT ST':'Gowanus Green, on the site long known as Public Place',
    '250 BALTIC ST':{full:'Location of the CB6 district office'},
    '1 E 161 ST':{text:'Yankee Stadium',bg:'#142448',fg:'#FFFFFF'},
    '139 FLATBUSH AVE':'Atlantic Terminal',
    '95 PROSPECT PARK W':'Prospect Park, 526 acres on one tax lot',
    '405 LEXINGTON AVE':'the Chrysler Building',
    '30 LAFAYETTE AVE':'the Brooklyn Academy of Music, the Peter Jay Sharp Building and the Howard Gilman Opera House',
    '651 FULTON ST':'the BAM Harvey Theater',
    '653 FULTON ST':'the BAM Harvey Theater',
    '321 ASHLAND PL':'BAM Fisher',
    '30 HUDSON YARDS':'30 Hudson Yards, the Edge observation deck, in the Hudson Yards development',
    '20 HUDSON YARDS':'20 Hudson Yards, the Shops and the Vessel, in the Hudson Yards development',
    '200 LIBERTY ST':'Battery Park City, built on landfill and governed by the Battery Park City Authority',
    '230 VESEY ST':'Brookfield Place, in Battery Park City',
    '830 5 AVE':'Central Park, 843 acres on one tax lot, and the Arsenal, the Parks Department headquarters',
    '4 S ST':'Whitehall Ferry Terminal, the Manhattan end of the Staten Island Ferry',
    '1 BAY ST':'St. George Ferry Terminal, the Staten Island end of the ferry',
    '625 8 AVE':'the Port Authority Bus Terminal',
    '421 8 AVE':'Moynihan Train Hall, the western half of Penn Station',
    '93-02 SUTPHIN BLVD':'Jamaica Station, where the LIRR, the subway and the AirTrain meet',
    '200 BROADWAY':'the Fulton Center',
    '4211 BROADWAY':'the George Washington Bridge Bus Station',
    '11 W 53 ST':'the Museum of Modern Art',
    '1071 5 AVE':'the Solomon R. Guggenheim Museum',
    '99 GANSEVOORT ST':'the Whitney Museum of American Art',
    '1 E 70 ST':'the Frick Collection',
    '2 E 91 ST':'the Cooper Hewitt',
    '1109 5 AVE':'the Jewish Museum',
    '1220 5 AVE':'the Museum of the City of New York',
    '1230 5 AVE':'El Museo del Barrio',
    '144 W 125 ST':'the Studio Museum in Harlem',
    '235 BOWERY':'the New Museum',
    '103 ORCHARD ST':'the Tenement Museum',
    '36 BATTERY PL':'the Museum of Jewish Heritage',
    '180 GREENWICH ST':'the 9/11 Memorial and Museum',
    '225 MADISON AVE':'the Morgan Library and Museum',
    '1048 5 AVE':'the Neue Galerie',
    '22-25 JACKSON AVE':'MoMA PS1',
    '1 FLUSHING MEADOWS CORONA PARK':'the Queens Museum',
    '36-01 35 AVE':'the Museum of the Moving Image',
    '9-01 33 RD':'the Noguchi Museum',
    '1040 GRAND CONCOURSE':'the Bronx Museum of the Arts',
    '1000 RICHMOND TERRACE':'the Staten Island Museum',
    '170 CENTRAL PARK W':'the New-York Historical',
    '302 W 45 ST':'the Al Hirschfeld Theatre, a Broadway theatre',
    '219 W 49 ST':'the Ambassador Theatre, a Broadway theatre',
    '245 W 52 ST':'the August Wilson Theatre, a Broadway theatre',
    '111 W 44 ST':'the Belasco Theatre, a Broadway theatre',
    '242 W 45 ST':'the Bernard B. Jacobs Theatre, a Broadway theatre',
    '222 W 45 ST':'the Booth Theatre, a Broadway theatre',
    '235 W 44 ST':'the Broadhurst Theatre, a Broadway theatre',
    '1681 BROADWAY':'the Broadway Theatre, a Broadway theatre',
    '235 W 50 ST':'the Circle in the Square Theatre, a Broadway theatre',
    '243 W 47 ST':'the Ethel Barrymore Theatre, a Broadway theatre',
    '230 W 49 ST':'the Eugene O\'Neill Theatre, a Broadway theatre',
    '236 W 45 ST':'the Gerald Schoenfeld Theatre, a Broadway theatre',
    '222 W 51 ST':'the Gershwin Theatre, a Broadway theatre',
    '240 W 44 ST':'the Hayes Theater, a Broadway theatre',
    '141 W 44 ST':'the Hudson Theatre, a Broadway theatre',
    '249 W 45 ST':'the Imperial Theatre, a Broadway theatre',
    '138 W 48 ST':'the James Earl Jones Theatre, a Broadway theatre',
    '252 W 45 ST':'the John Golden Theatre, a Broadway theatre',
    '256 W 47 ST':'the Lena Horne Theatre, a Broadway theatre',
    '220 W 48 ST':'the Longacre Theatre, a Broadway theatre',
    '205 W 46 ST':'the Lunt-Fontanne Theatre, a Broadway theatre',
    '149 W 45 ST':'the Lyceum Theatre, a Broadway theatre',
    '214 W 43 ST':'the Lyric Theatre, a Broadway theatre',
    '245 W 44 ST':'the Majestic Theatre, a Broadway theatre',
    '1535 BROADWAY':'the Marquis Theatre, a Broadway theatre',
    '200 W 45 ST':'the Minskoff Theatre, a Broadway theatre',
    '239 W 45 ST':'the Music Box Theatre, a Broadway theatre',
    '208 W 41 ST':'the Nederlander Theatre, a Broadway theatre',
    '250 W 52 ST':'the Neil Simon Theatre, a Broadway theatre',
    '214 W 42 ST':'the New Amsterdam Theatre, a Broadway theatre',
    '160 W 47 ST':'the Palace Theatre, a Broadway theatre',
    '226 W 46 ST':'the Richard Rodgers Theatre, a Broadway theatre',
    '261 W 47 ST':'the Samuel J. Friedman Theatre, a Broadway theatre',
    '225 W 44 ST':'the Shubert Theatre, a Broadway theatre',
    '246 W 44 ST':'the St. James Theatre, a Broadway theatre',
    '124 W 43 ST':'the Stephen Sondheim Theatre, a Broadway theatre',
    '254 W 54 ST':'Studio 54, a Broadway theatre',
    '227 W 42 ST':'the Todd Haimes Theatre, a Broadway theatre',
    '150 W 65 ST':'the Vivian Beaumont Theater, a Broadway theatre',
    '219 W 48 ST':'the Walter Kerr Theatre, a Broadway theatre',
    '1634 BROADWAY':'the Winter Garden Theatre, a Broadway theatre',
    '338 5 AVE':'the Empire State Building',
    '89 E 42 ST':'Grand Central Terminal',
    '1260 6 AVE':'Radio City Music Hall, its own tax lot at 1260 Avenue of the Americas, next door to 30 Rockefeller Plaza',
    '1260 AVE OF THE AMER':'Radio City Music Hall, its own tax lot at 1260 Avenue of the Americas, next door to 30 Rockefeller Plaza',
    '1250 AVE OF THE AMER':'30 Rockefeller Plaza, a separate tax lot from Radio City Music Hall next door',
    '30 ROCKEFELLER PLAZA':'30 Rockefeller Plaza, a separate tax lot from Radio City Music Hall next door',
    '881 7 AVE':'Carnegie Hall',
    '4 PENN PLAZA':{text:'Madison Square Garden, above Penn Station',bg:'#255792',fg:'#FFFFFF'},
    '60 COLUMBUS AVE':'Lincoln Center',
    '253 W 125 ST':'the Apollo Theater',
    '1000 5 AVE':'the Metropolitan Museum of Art, which sits on Central Park\'s tax lot',
    '200 CENTRAL PARK W':'the American Museum of Natural History',
    '185 GREENWICH ST':'One World Trade Center',
    '11 WALL ST':'the New York Stock Exchange',
    '52 CHAMBERS ST':{full:'City Hall, seat of the Mayor and the City Council'},
    '225 JORALEMON ST':{full:'Brooklyn Borough Hall, office of the Borough President'},
    '620 ATLANTIC AVE':'Barclays Center, on the Atlantic Yards site',
    '186 EASTERN PKWY':'the Brooklyn Museum',
    '415 FLATBUSH AVE':'the Central Library of the Brooklyn Public Library',
    '336 3 ST':'the Old Stone House',
    '500 25 ST':'Green-Wood Cemetery',
    '334 FURMAN ST':'Brooklyn Bridge Park',
    '652 KENT AVE':'the Brooklyn Navy Yard',
    '472 2 AVE':'Industry City',
    '1027 FLATBUSH AVE':'Kings Theatre',
    '1000 SURF AVE':'Luna Park, Coney Island',
    '834 SURF AVE':'the Cyclone, Coney Island',
    '21 BEARD ST':'IKEA Red Hook',
    '597 COLUMBIA ST':'the Red Hook ball fields',
    '123-01 ROOSEVELT AVE':'Citi Field',
    '56-01 GRAND CENTRAL PKWY':'Arthur Ashe Stadium, home of the US Open',
    '2300 SOUTHERN BLVD':'the Bronx Zoo',
    '2600 SOUTHERN BLVD':'the New York Botanical Garden',
    '1000 SNUG HARBOR RD':'Snug Harbor Cultural Center'
  };
  function bindZoneLink(result){
    if(!result) return;
    [['[data-zoomto]','[data-zoneexplain]'],['[data-zoomto-landuse]','[data-landuseexplain]']].forEach(function(pair){
      var link=result.querySelector(pair[0]), target=result.querySelector(pair[1]);
      if(!link||!target) return;
      link.addEventListener('click',function(ev){
        ev.preventDefault();
        try{ target.scrollIntoView({block:'start',behavior:'smooth'}); }catch(e){ target.scrollIntoView(); }
        target.style.boxShadow='0 0 0 2px #f47920';
        setTimeout(function(){ target.style.boxShadow=''; },1600);
      });
    });
  }
  // Every named place gets its own pin. An image where we have one, otherwise a marker
  // keyed to what the place is.
  var MARK_KINDS=[
    {re:/Broadway theatre/i,             glyph:'\u265B', bg:'#7a1f2b', label:'Broadway theatre',
      img:{src:'/site-icons/broadway-org.png',alt:'Broadway',w:520,h:91}},
    {re:/museum|galerie|collection|historical|moma|ps1|guggenheim|whitney|frick|cooper hewitt|memorial and museum|museo/i,
                                         glyph:'\u25F3', bg:'#4a3b7a', label:'Museum'},
    {re:/librar/i,                       glyph:'\u25A4', bg:'#1f5f4a', label:'Library'},
    {re:/zoo|botanic|garden of|cemetery|park\b/i, glyph:'\u2663', bg:'#2e6b30', label:'Open space'},
    {re:/stadium|arena|field|ball ?fields|cyclone|luna park|barclays/i, glyph:'\u25CF', bg:'#142448', label:'Stadium or arena'},
    {re:/terminal|station|penn|train hall|ferry|fulton center|bus station/i, glyph:'\u25AC', bg:'#0d1b4b', label:'Transit'},
    {re:/city hall|borough hall|district office/i, glyph:'\u2691', bg:'#0d1b4b', label:'Government'},
    {re:/stock exchange|world trade|empire state|rockefeller|carnegie|radio city|apollo|lincoln center|kings theatre|studio 54|old stone house|snug harbor|cultural/i,
                                         glyph:'\u2605', bg:'#8a5a10', label:'Landmark'},
    {re:/navy yard|industry city|ikea|marine terminal/i, glyph:'\u25A0', bg:'#7a4a12', label:'Industrial or waterfront'},
    {re:/gowanus green|public place|lift/i, glyph:'\u2302', bg:'#f47920', label:'Housing site'}
  ];
  function markFor(label,owner){
    var key=liftNorm(label);
    var img=SITE_ICON[key]||null;
    var byKind=null;
    var a=AKA[key];
    var txt=a?(typeof a==='object'?(a.full||a.text||''):String(a)):'';
    var kind=null;
    if(txt){ for(var i=0;i<MARK_KINDS.length;i++){ if(MARK_KINDS[i].re.test(txt)){ kind=MARK_KINDS[i]; break; } } }
    if(!img && FERRY_ADDRS[key]) img=FERRY_ICON;
    if(!img && BIZ_SITES[key] && BIZ_SITES[key][0]){
      var bz=BIZ_SITES[key][0];
      img={src:bz.src,alt:bz.name,w:bz.w,h:bz.h,plate:bz.plate};
      if(!kind) kind={label:bz.kind,bg:'#0d1b4b',glyph:'\u25cf'};
    }
    if(!img && /HOUSING AUTHORITY|\bNYCHA\b/i.test(String(owner||''))){
      img=NYCHA_ICON;
      if(!kind) kind={label:'NYCHA development',bg:'#8b2233',glyph:'\u2302'};
    }
    if(!img && kind && kind.img) img=kind.img;
    return {img:img, kind:kind, alias:txt.replace(/^the /,'')};
  }
  function markerFor(label,lat,lng,owner){
    var m=markFor(label,owner);
    if(m.img){
      var ratio=m.img.h/m.img.w, iw=64, ih=Math.round(iw*ratio);
      return L.marker([lat,lng],{icon:L.divIcon({className:'',iconSize:[iw,ih+10],iconAnchor:[iw/2,ih+10],
        html:'<div style="text-align:center"><img src="'+m.img.src+'" alt="'+esc(m.img.alt||'')+'" '+
          'style="width:'+iw+'px;height:'+ih+'px;display:block;background:'+(m.img.plate||'#fff')+';border:2px solid #0d1b4b;'+
          'border-radius:7px;box-shadow:0 2px 6px rgba(0,0,0,.28)"><div style="width:0;height:0;margin:0 auto;'+
          'border-left:6px solid transparent;border-right:6px solid transparent;border-top:9px solid #0d1b4b"></div></div>'})});
    }
    if(m.kind){
      return L.marker([lat,lng],{icon:L.divIcon({className:'',iconSize:[34,42],iconAnchor:[17,42],
        html:'<div style="text-align:center"><div style="width:34px;height:34px;border-radius:9px;background:'+m.kind.bg+';'+
          'border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.3);color:#fff;font-size:17px;line-height:32px;'+
          'font-family:\'DM Sans\',sans-serif">'+m.kind.glyph+'</div><div style="width:0;height:0;margin:0 auto;'+
          'border-left:5px solid transparent;border-right:5px solid transparent;border-top:8px solid '+m.kind.bg+'"></div></div>'})});
    }
    return L.marker([lat,lng]);
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
      var onList=hits.some(function(h){ return !h._near; });
      var name=LIFT_PLACE[liftNorm(s.addr)] || (hits.length>1 ? s.n.replace(/\s+(Building|Bldg|Phase)\s+\S+$/i,'') : s.n);
      if(!onList) name='Near '+name;
      var bits=[];
      if(units) bits.push(units.toLocaleString()+' homes planned');
      if(hits.length>1) bits.push(hits.length+' buildings');
      if(s.ag) bits.push(s.ag);
      if(s.st) bits.push(s.st);
      if(!onList){
        // Say plainly that this is a different lot, how far, and where.
        bits.unshift(s._dist+' m from this address');
        if(s.addr) bits.push('at '+s.addr);
      }
      var deep=LIFT_DEEP[liftNorm(s.addr)]||null;
      var box=document.createElement('div');
      box.className='lift-badge';
      box.setAttribute('style','margin:10px 0;padding:11px 13px;background:#0d1b4b;border-left:5px solid #f47920;border-radius:9px');
      box.innerHTML='<img src="/lift-badge-banner.jpg" alt="Block by Block, Land Inventory Fast Track (LIFT), Office of the Mayor" width="1173" height="342" loading="lazy" style="display:block;width:100%;height:auto;border-radius:5px;margin-bottom:9px">'+
        '<div style="font-family:\'DM Mono\',monospace;font-size:.56rem;text-transform:uppercase;letter-spacing:.1em;color:#f47920;font-weight:700;margin-bottom:5px">'+(onList?'On the LIFT list &middot; Block by Block':'Nearby LIFT site &middot; Block by Block')+'</div>'+
        '<div style="color:#fff;font-size:.9rem;font-weight:900;line-height:1.3">'+esc(name||'')+'</div>'+
        '<div style="color:rgba(255,255,255,.78);font-family:\'DM Mono\',monospace;font-size:.68rem;line-height:1.5;margin-top:4px">'+esc(bits.join(' \u00b7 '))+'</div>'+
        (deep?('<div style="margin-top:9px;padding-top:9px;border-top:1px solid rgba(255,255,255,.22);color:rgba(255,255,255,.86);font-size:.79rem;line-height:1.55">'+deep.note+'</div>'):'')+
        '<div style="display:flex;flex-wrap:wrap;gap:7px;margin-top:10px">'+
        (deep?('<a href="'+deep.href+'" style="background:#f47920;color:#fff;text-decoration:none;font-size:.73rem;font-weight:800;padding:6px 12px;border-radius:16px">'+deep.label+'</a>'):'')+
        '<a href="/blockbyblock/#foldAllSites" style="background:'+(deep?'transparent':'#f47920')+';color:#fff;text-decoration:none;font-size:.73rem;font-weight:800;padding:6px 12px;border-radius:16px'+(deep?';border:1.5px solid rgba(255,255,255,.35)':'')+'">See it on Block by Block &rarr;</a>'+
        '</div>';
      // Place it after the zoning band and district lines, not above them: on a
      // stadium card the zoning is the point, and a nearby LIFT site is context.
      var first=result.firstElementChild;
      var anchor=first && (first.querySelector('.citywide-result-map') || first.querySelector('.zoning-band'));
      if(anchor && anchor.parentNode){
        anchor.parentNode.insertBefore(box, anchor.nextSibling);
      } else if(first && first.firstElementChild && first.firstElementChild.nextElementSibling){
        first.insertBefore(box, first.firstElementChild.nextElementSibling.nextElementSibling);
      } else if(first) first.appendChild(box);
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
    var cbLabel=areaLabel(cb||String(a.communityDistrict||pluto.cd||''));
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
  // DM Sans and DM Mono, embedded so the bands print in the real typeface.
  var PDF_FONTS=null, pdfFontLoading=null;
  function loadPdfFonts(){
    if(PDF_FONTS) return Promise.resolve(PDF_FONTS);
    if(pdfFontLoading) return pdfFontLoading;
    pdfFontLoading=fetch('/assets/pdf-fonts.json').then(function(r){return r.json();})
      .then(function(j){ PDF_FONTS=j; return j; }).catch(function(){ PDF_FONTS=null; return null; });
    return pdfFontLoading;
  }
  function applyPdfFonts(doc){
    if(!PDF_FONTS) return false;
    try{
      doc.addFileToVFS('DMSans-Bold.ttf', PDF_FONTS['DMSans-Bold']);
      doc.addFont('DMSans-Bold.ttf','DMSans','bold');
      doc.addFileToVFS('DMMono-Medium.ttf', PDF_FONTS['DMMono-Medium']);
      doc.addFont('DMMono-Medium.ttf','DMMono','normal');
      return true;
    }catch(e){ return false; }
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
    // Compose a two column sheet off screen, then capture that. Same content as the card,
    // laid out for a 10.5 x 13 page.
    var stage=document.createElement('div');
    stage.setAttribute('style','position:fixed;left:-20000px;top:0;width:1040px;background:#ffffff;'+
      'font-family:\'DM Sans\',sans-serif;padding:0;z-index:-1');
    var clone=card.cloneNode(true);
    clone.style.background='#ffffff';
    clone.style.border='none';
    clone.style.borderRadius='0';
    clone.style.margin='0';
    clone.style.padding='0';
    clone.style.columnCount='2';
    clone.style.columnGap='18px';
    Array.prototype.forEach.call(clone.children,function(el){
      el.style.breakInside='avoid';
      el.style.pageBreakInside='avoid';
      el.style.marginBottom='10px';
    });
    Array.prototype.forEach.call(clone.querySelectorAll('.citywide-share-btn,.citywide-pdf-btn'),function(b){
      var wrap=b.parentNode; if(wrap) wrap.removeChild(b);
    });
    stage.appendChild(clone);
    document.body.appendChild(stage);

    // the cloned map is an empty div, so drop a picture of the live one in its place
    var liveMap=card.querySelector('.citywide-result-map');
    var cloneMap=clone.querySelector('.citywide-result-map');

    function cleanup(){ if(stage.parentNode) stage.parentNode.removeChild(stage); }

    var mapShot=liveMap
      ? Promise.race([
          window.html2canvas(liveMap,{backgroundColor:'#eef2f7',scale:1,useCORS:true,logging:false,imageTimeout:2500}),
          new Promise(function(r){ setTimeout(function(){ r(null); },3500); })
        ]).catch(function(){ return null; })
      : Promise.resolve(null);
    return mapShot
      .then(function(mapCanvas){
        if(cloneMap && mapCanvas){
          var mi=document.createElement('img');
          mi.src=mapCanvas.toDataURL('image/jpeg',0.9);
          mi.style.width='100%'; mi.style.height='auto'; mi.style.display='block';
          mi.style.borderRadius='8px'; mi.style.border='1px solid #a7f3d0';
          cloneMap.parentNode.replaceChild(mi,cloneMap);
        }
        return window.html2canvas(stage,{backgroundColor:'#ffffff',scale:1.6,useCORS:true,logging:false,imageTimeout:3000,
          windowWidth:1040,width:1040,removeContainer:true});
      })
      .then(function(canvas){
        cleanup();
        var jsPDF=window.jspdf.jsPDF;
        // 10.5 x 13 inches, in points
        var W=756, H=936;
        var doc=new jsPDF({unit:'pt',format:[W,H]});
        var navy=[13,27,75], orange=[244,121,32];
        var topH=58, botH=58, M=18;

        doc.setFillColor(navy[0],navy[1],navy[2]);
        doc.rect(0,0,W,topH,'F');
        doc.rect(0,H-botH,W,botH,'F');

        var haveFonts=applyPdfFonts(doc);
        function sans(sz){ doc.setFont(haveFonts?'DMSans':'helvetica','bold'); doc.setFontSize(sz); }
        function monoF(sz){ doc.setFont(haveFonts?'DMMono':'helvetica','normal'); doc.setFontSize(sz); }

        sans(25); doc.setTextColor(255,255,255);
        doc.text('CB6', M+6, topH/2+9);
        var cb6w=doc.getTextWidth('CB6');
        monoF(13); doc.setTextColor(orange[0],orange[1],orange[2]);
        doc.text('& BEYOND', M+14+cb6w, topH/2+8);
        sans(25);
        doc.text('bkcb6.app', W/2, topH/2+10, {align:'center'});

        sans(31);
        doc.text('bkcb6.app', W/2, H-botH/2+10, {align:'center'});

        var avail=H-topH-botH-M;
        var cw=W-M*2;
        var scale=Math.min(cw/canvas.width, avail/canvas.height);
        var dw=canvas.width*scale, dh=canvas.height*scale;
        doc.addImage(canvas.toDataURL('image/jpeg',0.86),'JPEG',(W-dw)/2,topH+8,dw,dh,undefined,'FAST');

        var input=profile&&profile.input||'';
        var name=String(input).replace(/[^A-Za-z0-9]+/g,'-').replace(/^-|-$/g,'').toLowerCase();
        doc.save('bkcb6-'+(name||'address-card')+'.pdf');
      },function(err){ cleanup(); throw err; });
  }
  // Draw the sheet natively. No screen capture, so it finishes in well under a second.
  function pdfImg(url){
    return new Promise(function(res){
      var i=new Image();
      i.crossOrigin='anonymous';
      i.onload=function(){
        try{
          var c=document.createElement('canvas');
          c.width=i.naturalWidth; c.height=i.naturalHeight;
          c.getContext('2d').drawImage(i,0,0);
          res({data:c.toDataURL('image/png'),w:i.naturalWidth,h:i.naturalHeight});
        }catch(e){ res(null); }
      };
      i.onerror=function(){ res(null); };
      i.src=url;
    });
  }
  function tileMap(lat,lng,zoom,tw,th){
    return new Promise(function(res){
      try{
        var n=Math.pow(2,zoom);
        var xf=(lng+180)/360*n;
        var yf=(1-Math.log(Math.tan(lat*Math.PI/180)+1/Math.cos(lat*Math.PI/180))/Math.PI)/2*n;
        var c=document.createElement('canvas'); c.width=tw; c.height=th;
        var ctx=c.getContext('2d');
        ctx.fillStyle='#eef2f7'; ctx.fillRect(0,0,tw,th);
        var cx=tw/2, cy=th/2, pending=0, finished=false;
        var x0=Math.floor(xf-(cx/256))-1, x1=Math.floor(xf+(cx/256))+1;
        var y0=Math.floor(yf-(cy/256))-1, y1=Math.floor(yf+(cy/256))+1;
        function done(){
          if(finished) return; finished=true;
          ctx.beginPath(); ctx.arc(cx,cy,7,0,Math.PI*2);
          ctx.fillStyle='#f47920'; ctx.fill();
          ctx.lineWidth=3; ctx.strokeStyle='#ffffff'; ctx.stroke();
          var url=null;
          try{ url=c.toDataURL('image/jpeg',0.85); }catch(e){ url=null; }
          res(url?{data:url,w:tw,h:th}:null);
        }
        var timer=setTimeout(done,2200);
        for(var x=x0;x<=x1;x++){
          for(var y=y0;y<=y1;y++){
            if(y<0||y>=n) continue;
            pending++;
            (function(tx,ty){
              var img=new Image(); img.crossOrigin='anonymous';
              img.onload=function(){
                ctx.drawImage(img, cx+(tx-xf)*256, cy+(ty-yf)*256, 256, 256);
                if(--pending===0){ clearTimeout(timer); done(); }
              };
              img.onerror=function(){ if(--pending===0){ clearTimeout(timer); done(); } };
              img.src='https://a.basemaps.cartocdn.com/light_all/'+zoom+'/'+((tx%n)+n)%n+'/'+ty+'.png';
            })(x,y);
          }
        }
        if(!pending){ clearTimeout(timer); done(); }
      }catch(e){ res(null); }
    });
  }
  function cardPdfNative(profile){
    var a=profile.address||{}, pluto=profile.pluto||{}, input=profile.input||'';
    var near=profile.nearby||{};
    var cb=validCommunityBoardCode(profile.foundCd)?String(profile.foundCd):String(a.communityDistrict||pluto.cd||'');
    var cbLabel=areaLabel(cb||String(a.communityDistrict||pluto.cd||''));
    var zones=collectZones(a,pluto), zDisp=zones.length?zones.join(' / '):'Not available from PLUTO';
    var spDists=collectSpecialDistricts(pluto), spDisp=spDists.length?spDists.join(' / '):'';
    var lUse=landUseLabel(pluto.landuse);
    var akaHit=AKA[liftNorm(input)], aka='';
    if(akaHit) aka=(typeof akaHit==='object')?(akaHit.full||('aka '+(akaHit.text||''))):('aka '+akaHit);
    var akaBg=(akaHit&&typeof akaHit==='object'&&akaHit.bg)?akaHit.bg:'#0d1b4b';
    var siteIcon=SITE_ICON[liftNorm(input)]||null;
    if(!siteIcon && /HOUSING AUTHORITY|\bNYCHA\b/i.test(String(pluto.ownername||pluto.owner||''))) siteIcon=NYCHA_ICON;
    if(!siteIcon && isBroadwayAddr(input)) siteIcon=BROADWAY_ICON;
    if(!siteIcon && FERRY_ADDRS[liftNorm(input)]) siteIcon=FERRY_ICON;
    if(!siteIcon && PARK_ICONS[normalizeBbl(a.bbl)||normalizeBbl(pluto.bbl)]) siteIcon=PARK_ICONS[normalizeBbl(a.bbl)||normalizeBbl(pluto.bbl)];
    var boardShort=validCommunityBoardCode(cb)?BOROUGH_SHORT[cb.charAt(0)]:'';
    var boardNum=validCommunityBoardCode(cb)?parseInt(cb.slice(1),10):0;
    var logoUrl=(cb==='306')?'/cb6-logo-card.png':(boardShort&&boardNum?'/banners/banner-'+boardShort+'-'+boardNum+'.png':'');
    var lat=parseFloat(profile.lat), lng=parseFloat(profile.lng);

    return Promise.all([
      logoUrl?pdfImg(logoUrl):Promise.resolve(null),
      siteIcon?pdfImg(siteIcon.src):Promise.resolve(null),
      (isFinite(lat)&&isFinite(lng))?tileMap(lat,lng,16,640,420):Promise.resolve(null),
      pdfImg('/qr-citywide-search.png')
    ]).then(function(assets){
      var logo=assets[0], icon=assets[1], map=assets[2], qr=assets[3];
      var jsPDF=window.jspdf.jsPDF;
      var W=756,H=936;
      var doc=new jsPDF({unit:'pt',format:[W,H]});
      var haveFonts=applyPdfFonts(doc);
      var NAVY=[13,27,75], ORANGE=[244,121,32], INK=[51,51,51], MUTED=[107,103,96];
      var M=26, topH=58, botH=58, qrStrip=102;
      var colGap=18, colW=(W-M*2-colGap)/2;
      var Lx=M, Rx=M+colW+colGap;
      var ly=topH+22, ry=topH+22;

      function sans(sz,color){ doc.setFont(haveFonts?'DMSans':'helvetica','bold'); doc.setFontSize(sz);
        doc.setTextColor(color[0],color[1],color[2]); }
      function mono(sz,color){ doc.setFont(haveFonts?'DMMono':'helvetica','normal'); doc.setFontSize(sz);
        doc.setTextColor(color[0],color[1],color[2]); }
      function body(sz,color){ doc.setFont('helvetica','normal'); doc.setFontSize(sz);
        doc.setTextColor(color[0],color[1],color[2]); }
      function hex(h){ h=String(h).replace('#',''); return [parseInt(h.slice(0,2),16),parseInt(h.slice(2,4),16),parseInt(h.slice(4,6),16)]; }

      // bands
      doc.setFillColor(NAVY[0],NAVY[1],NAVY[2]);
      doc.rect(0,0,W,topH,'F'); doc.rect(0,H-botH,W,botH,'F');
      sans(25,[255,255,255]); doc.text('CB6', M, topH/2+9);
      var cw6=doc.getTextWidth('CB6');
      mono(13,ORANGE); doc.text('& BEYOND', M+8+cw6, topH/2+8);
      sans(25,ORANGE); doc.text('bkcb6.app', W/2, topH/2+10, {align:'center'});
      sans(31,ORANGE); doc.text('bkcb6.app', W/2, H-botH/2+10, {align:'center'});

      // ---- left column ----
      sans(19,NAVY);
      doc.splitTextToSize(input, colW).forEach(function(ln){ doc.text(ln, Lx, ly); ly+=23; });
      if(aka){
        var pf=hex(akaBg);
        sans(12,[255,255,255]);
        var tw=doc.getTextWidth(aka);
        doc.setFillColor(pf[0],pf[1],pf[2]);
        doc.roundedRect(Lx, ly-12, Math.min(tw+24, colW), 24, 12,12,'F');
        doc.text(aka, Lx+12, ly+4);
        ly+=34;
      }
      sans(13,NAVY); doc.text('is in '+cbLabel, Lx, ly); ly+=24;

      var zh=spDists.length?96:78;
      doc.setFillColor(NAVY[0],NAVY[1],NAVY[2]);
      doc.roundedRect(Lx,ly,colW,zh,7,7,'F');
      mono(10,ORANGE); doc.text('ZONED', Lx+14, ly+22);
      sans(30,[255,255,255]); doc.text(zDisp, Lx+14, ly+56);
      if(spDists.length){ mono(9,[201,210,230]); doc.text('in the '+spDisp+' special district', Lx+14, ly+80); }
      ly+=zh+14;

      var gap=zoneUseNote(zones[0],pluto.landuse);
      if(gap){
        body(9,INK);
        var gl=doc.splitTextToSize(gap.head+': '+gap.text, colW-22);
        var gh=gl.length*12+18;
        doc.setFillColor(255,248,242); doc.rect(Lx,ly,colW,gh,'F');
        doc.setFillColor(ORANGE[0],ORANGE[1],ORANGE[2]); doc.rect(Lx,ly,4,gh,'F');
        body(9,INK);
        gl.forEach(function(ln,i){ doc.text(ln, Lx+14, ly+16+i*12); });
        ly+=gh+14;
      }

      if(map&&map.data){
        var mh=colW*map.h/map.w;
        doc.addImage(map.data,'JPEG',Lx,ly,colW,mh,undefined,'FAST');
        doc.setDrawColor(167,243,208); doc.roundedRect(Lx,ly,colW,mh,6,6,'S');
        ly+=mh+14;
      }

      function svc(label,item,nameFn,detailFn){
        if(!item) return;
        var p=item.properties||{}, v=(nameFn?nameFn(p):'')||label;
        var d=distLabel(item.distanceFeet), det=detailFn?detailFn(p):'';
        if(d) v+=' \u00b7 '+d; if(det) v+=' \u00b7 '+det;
        var lines=doc.splitTextToSize(v, colW-20);
        var h=18+lines.length*12;
        doc.setDrawColor(229,226,219); doc.roundedRect(Lx,ly,colW,h,5,5,'S');
        mono(7.5,MUTED); doc.text(String(label).toUpperCase(), Lx+10, ly+13);
        sans(9.5,NAVY); lines.forEach(function(ln,i){ doc.text(ln, Lx+10, ly+26+i*12); });
        ly+=h+7;
      }
      svc('Closest park',near.park,function(p){return p.signname||p.name311||'Park';},function(p){return p.typecategory||'';});
      svc('Closest subway',near.subway,function(p){return p.display_name||p.stop_name||'Subway';},function(p){return p.daytime_routes||p.routes||'';});
      svc('Closest bus stop',near.bus,function(p){var r=Array.isArray(p.routes)?p.routes.join(', '):(p.routes||''); return (r?r+' \u00b7 ':'')+(p.stop_name||'Bus stop');});
      svc('Closest citi bike',near.citibike,function(p){return p.name||'Citi Bike';},function(p){return p.short_name||'';});

      // ---- right column ----
      var logoH=0;
      if(logo&&logo.data){ logoH=Math.min(96, colW*0.42*logo.h/logo.w);
        var lw=logoH*logo.w/logo.h;
        doc.addImage(logo.data,'PNG',Rx+colW-lw,ry,lw,logoH); }
      if(icon&&icon.data){ var ih=Math.min(72, colW*0.42*icon.h/icon.w), iw=ih*icon.w/icon.h;
        doc.addImage(icon.data,'PNG',Rx+colW-iw,ry+logoH+8,iw,ih); ry+=logoH+ih+18; }
      else ry+=logoH+16;

      function tile(k,v,x,w){
        if(v===undefined||v===null||v==='') return 0;
        var lines=doc.splitTextToSize(String(v), w-18);
        var h=18+lines.length*13+6;
        doc.setDrawColor(229,226,219); doc.roundedRect(x,ry,w,h,5,5,'S');
        mono(7.5,MUTED); doc.text(String(k).toUpperCase(), x+9, ry+13);
        sans(10,NAVY); lines.forEach(function(ln,i){ doc.text(ln, x+9, ry+27+i*13); });
        return h;
      }
      var half=(colW-8)/2;
      function pair(k1,v1,k2,v2){
        var h1=tile(k1,v1,Rx,half), h2=tile(k2,v2,Rx+half+8,half);
        var h=Math.max(h1,h2); if(h) ry+=h+8;
      }
      pair('Owner', pluto.ownername||pluto.owner||'', 'Community board', cbLabel);
      pair('Borough', pluto.borough||a.firstBoroughName||'', 'Year built', pluto.yearbuilt||'');
      pair('Land use', lUse, 'Lot area', fmtNum(pluto.lotarea,' sq ft'));
      pair('Total units', fmtNum(pluto.unitstotal,''), 'Council district', districtNumber(a.cityCouncilDistrict));
      ry+=6;

      var bases=baseDistricts(zones[0]);
      if(USEMATRIX && bases.length){
        sans(12,NAVY);
        doc.text('What can be built here \u00b7 '+(bases.length>1?zones[0]:bases[0])+' rules', Rx, ry); ry+=16;
        var RANK={N:0,S:1,L:2,Y:3};
        USEMATRIX.goals.filter(function(g){return USE_SHOW.indexOf(g.id)>-1;}).forEach(function(g){
          if(ry>H-botH-qrStrip-24) return;
          var row=USEMATRIX.matrix[g.ug]; if(!row) return;
          var vs=bases.map(function(b){return row[b]||null;}).filter(Boolean);
          if(!vs.length) return;
          var v=vs.sort(function(x,y){return RANK[y]-RANK[x];})[0];
          var bg=hex(USE_BG[v]), fg=hex(USE_FG[v]);
          var lab=g.q.replace(/^I want to /,''); lab=lab.charAt(0).toUpperCase()+lab.slice(1);
          doc.setFillColor(bg[0],bg[1],bg[2]);
          doc.roundedRect(Rx,ry,78,17,4,4,'F');
          sans(8,fg); doc.text(USE_LBL[v], Rx+39, ry+11.5, {align:'center'});
          sans(10,NAVY); doc.text(lab, Rx+86, ry+12);
          ry+=22;
          doc.setDrawColor(240,237,232); doc.line(Rx,ry-4,Rx+colW,ry-4);
        });
      }

      // scan or type, above the footer band
      var qs=74, qy=H-botH-qs-14;
      var qx=M;
      if(qr&&qr.data){ doc.addImage(qr.data,'PNG',M,qy,qs,qs); qx=M+qs+14; }
      body(9.5,MUTED);
      doc.text('This is a one page summary. The full card online carries the rest: the interactive map,', qx, qy+14);
      doc.text('every district, ownership and building detail, what can be built here, and nearby services.', qx, qy+27);
      sans(12,NAVY); doc.text(qr&&qr.data?'For more info scan the QR code or go to:':'For more info go to:', qx, qy+48);
      sans(13,ORANGE); doc.text('bkcb6.app/citywide-search.html', qx, qy+67);

      var name=String(input).replace(/[^A-Za-z0-9]+/g,'-').replace(/^-|-$/g,'').toLowerCase();
      doc.save('bkcb6-'+(name||'address-card')+'.pdf');
    });
  }
  function bindPdf(result,profile){
    if(!result||!profile) return;
    var btn=result.querySelector('.citywide-pdf-btn');
    if(!btn||btn.dataset.pdfBound==='true') return;
    btn.dataset.pdfBound='true';
    btn.addEventListener('click',function(){
      var prev=btn.textContent, step=0;
      var ticker=setInterval(function(){
        step++;
        btn.textContent=step<3?'Building PDF...':(step<7?'Rendering the card...':'Almost there...');
      },900);
      btn.textContent='Building PDF...';
      function done(){ clearInterval(ticker); btn.textContent=prev; }
      Promise.all([loadPdfLib(),loadPdfFonts()])
        .then(function(){ return cardPdfNative(profile); })
        .then(done)
        .catch(function(){
          try{ cardPdfText(profile); done(); }
          catch(e){ clearInterval(ticker); btn.textContent='PDF failed'; setTimeout(function(){btn.textContent=prev;},1800); }
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
        var gen=genericMatch(q);
        if(gen){
          gen.onpick=function(){ runFull(); };
          if(gen.boroFrom){ var bm=q.match(/(brooklyn|manhattan|queens|bronx|staten island)/i); gen.boro=bm?bm[1].toUpperCase():''; }
          if(status) status.textContent='Loading the list...';
          await (gen.needs?gen.needs():Promise.resolve());
          var picks=gen.items();
          if(!picks.length){ if(status) status.textContent='Nothing found for that.'; return; }
          showPicker(result,input,gen);
          if(status) status.textContent='Pick one of the '+picks.length+'.';
          return;
        }
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
        try{var profile=await build(q,{boroughName:boroughName,shortLabel:boroughName}); result.innerHTML=profile.html; try{ if(typeof window.__bkcbPickMapGoTo==='function') window.__bkcbPickMapGoTo(profile.lat,profile.lng,q); }catch(e){} result.hidden=false; initResultMap(result); bindShare(result); injectCardBar(result); injectSiteNote(result); injectLiftBadge(result,q); injectAliasLine(result,LAST_PLACE,q); bindZoneLink(result); bindPdf(result,profile); stampUrl(q); if(status) status.textContent=profile.status || 'Search complete.'; try{ setTimeout(function(){ var t=result.querySelector('[data-cardtop]')||result; t.scrollIntoView({block:'start',behavior:'smooth'}); },60); }catch(e){}}catch(err){console.error(err); if(status) status.textContent=err&&err.message?err.message:'Address lookup failed. Please try a full NYC street address.'; result.hidden=true; result.innerHTML='';}
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
