#!/usr/bin/env python3
"""Build profile pages for the Gowanus-area community organisations, on the
same template as the Old Stone House: logo header, an intro in Mike's voice,
a map of the block, contact details, what the organisation runs, and links out.

Every fact here comes from the organisation's own site or from a page already
in this repo. Nothing is inferred.
"""
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
CSS = open(os.path.join(ROOT, 'assets/org-profile.css'), encoding='utf-8').read()
MAPJS = 'v=20260830a'

ORGS = [
{
 'slug':'van-alen-institute',
 'name':'Van Alen Institute',
 'seat':'Community based organisation &middot; Gowanus, Brooklyn',
 'title':'Van Alen Institute',
 'desc':'Van Alen Institute at 303 Bond Street in Gowanus. What it does, how to reach it, and the lot it stands on. Brooklyn Community Board 6 holds its meetings there.',
 'lat':'40.680056','lng':'-73.989233',
 'addr':'303 Bond Street','zip':'11231',
 'addr_note':'Between Union and Sackett Streets, on the west bank of the canal',
 'phone':'212-924-7000','tel':'2129247000',
 'email':'vai@vanalen.org','web':'vanalen.org','weburl':'https://www.vanalen.org',
 'since':'1894',
 'intro':[
   'The <b>Van Alen Institute</b> has been at this since <b>1894</b>, which makes it older than the Gowanus rezoning by about a century and a quarter. It works on community-led urban design, the premise being that the people who live somewhere know things about it that a designer parachuting in does not.',
   'What that means in practice is that it builds coalitions across designers, residents and city agencies, then backs them with scoping, hands-on guidance and seed money. It is explicit that its work is about power imbalances in how cities get made, and it partners with historically disinvested communities rather than the ones already well served.',
   'It moved to <b>303 Bond Street</b> in Gowanus, on the west bank of the canal, inside the area the 2021 rezoning reshaped. <b>Brooklyn Community Board 6 holds our meetings there</b>, which is a good arrangement for everyone: an organisation devoted to community-led design hosting the body whose whole job is community input on land use.',
 ],
 'does':[
   'Van Alen runs design competitions, public space projects, research and fellowships. The through line is that it does not just publish a report and leave; it puts money and staff behind the ideas it generates and stays with them.',
   'For CB6 the relevant thing is proximity and subject matter. This is a district with a Superfund canal, a major rezoning still being built out, a waterfront terminal decision coming, and six historic districts. An institution working on how communities shape the built environment is useful to have on the block.',
 ],
 'kv':[('Founded','1894'),('Community board','<a href="/cb-bk-6.html">Brooklyn Community Board 6</a>'),
       ('CB6 meetings','Brooklyn Community Board 6 holds its meetings here')],
 'links':[('Their site','https://www.vanalen.org',True),
          ('The CB6 calendar','/calendar.html',False),
          ('Brooklyn CB6','/cb-bk-6.html',False),
          ('The Gowanus rezoning','/gowanus.html',False)],
},
{
 'slug':'gowanus-canal-conservancy',
 'name':'Gowanus Canal Conservancy',
 'seat':'Community based organisation &middot; Gowanus, Brooklyn',
 'title':'Gowanus Canal Conservancy',
 'desc':'Gowanus Canal Conservancy at the Old American Can Factory, 248 Third Street. Stewardship of the canal watershed, the Lowlands Nursery, the Green Team and the Tree Network.',
 'lat':'40.67432','lng':'-73.987762',
 'addr':'The Old American Can Factory<br>248 Third Street','zip':'11215',
 'addr_note':'Third Street at Third Avenue. The city files the lot as 361 3 Avenue',
 'phone':'718-541-4378','tel':'7185414378',
 'email':'info@gowanuscanalconservancy.org',
 'web':'gowanuscanalconservancy.org','weburl':'https://gowanuscanalconservancy.org',
 'since':'',
 'intro':[
   'The <b>Gowanus Canal Conservancy</b> is the group that has done the work on the canal since 2006, out of the Old American Can Factory: volunteers in the rain gardens and tree pits, students in the watershed, and staff at every meeting where the canal&rsquo;s future gets decided, including ours. On the rezoning they were ahead of everyone, with a plan for the waterfront before the City had one, and they&rsquo;re on the Oversight Task Force now making sure the open space and stormwater commitments get built.',
   'Andrea Parker and her excellent team has run and met the moment for over a decade, and her team includes CB6 member Aurelia Casey. If you want to see what stewardship looks like in practice, go to the Salt Lot on a volunteer day.',
 ],
 'does_title':'What GCC does',
 'does':[
   'GCC runs the <b>Lowlands Nursery</b>, growing native urban-adapted plants and selling them to residents, institutions and landscape designers, with proceeds going back into education and stewardship.',
   'GCC runs the <b>Gowanus Green Team</b>, paid high school apprentices doing conservation work, and the <b>Gowanus Tree Network</b>, which trains neighbours as Citizen Pruners to look after the street trees on their own blocks.',
   'The Conservancy works out of the <b>Old American Can Factory</b>, a three storey 1890 complex at Third Street and Third Avenue that now houses artists, makers and non-profits. The lot is zoned <b>M1-4/R7X</b> inside the <b>Gowanus special district</b>, the mixed use zoning the 2021 rezoning brought in.',
 ],
 'kv':[('Community board','<a href="/cb-bk-6.html">Brooklyn Community Board 6</a>'),
       ('The building','<a href="/old-american-can-factory">The Old American Can Factory</a>'),
       ('Zoning','M1-4/R7X, Gowanus special district')],
 'brand':{'dark':'#4d8d96','mid':'#70a8b0','light':'#a0c8d0','wash':'#eef5f6','accent':'#f5a01c','ink':'#2f6a72'},
 'evorg':'gcc','evtitle':'Coming up at the Gowanus Canal Conservancy','evhref':'/o/gcc.html','evname':'The Gowanus Canal Conservancy calendar',
 'does_btns':[('Their events','https://gowanuscanalconservancy.org/events/',True),
              ('What is coming up','/o/gcc.html',False),
              ('Zoning and land use for the lot','/old-american-can-factory',False)],
 'extra':[('The rezoning, the BID and the Task Force',
           [('The Gowanus rezoning','/gowanus.html',False),
            ('Gowanus BID formation effort','https://gowanusimprovementdistrict.org/',True),
            ('Gowanus Oversight Task Force','https://gowanustaskforce.net/',True),
            ('Task Force meetings on the calendar','/o/gotf.html',False)])],
 'links':[('Their site','https://gowanuscanalconservancy.org',True),
          ('The Old American Can Factory','/old-american-can-factory',False),
          ('Their calendar','/o/gcc.html',False),
          ('Search an address','/citywide-search.html',False)],
},
{
 'slug':'fifth-avenue-committee',
 'name':'Fifth Avenue Committee',
 'seat':'Community based organisation &middot; Park Slope and Gowanus, Brooklyn',
 'title':'Fifth Avenue Committee',
 'desc':'Fifth Avenue Committee at 621 DeGraw Street. Affordable housing, organizing, adult education and workforce development since 1978.',
 'lat':'40.679108','lng':'-73.982738',
 'addr':'621 DeGraw Street','zip':'11217',
 'addr_note':'Second office at 132 32nd Street, Suite 106, Brooklyn, NY 11232',
 'phone':'718-237-2017','tel':'7182372017',
 'email':'fac@fifthave.org','web':'fifthave.org','weburl':'https://fifthave.org',
 'since':'1978',
 'intro':[
   'The <b>Fifth Avenue Committee</b> has been at this since <b>1978</b>, and it is one of the few organisations in the district that does development, organizing and services at the same time rather than picking one. It reaches more than <b>6,500</b> low and moderate income New Yorkers a year.',
   'Its stated aim is economic, social and racial justice, pursued through community-centred affordable housing, grassroots organizing, policy advocacy, and education and training. That combination is the point. An organisation that only builds housing does not have tenants organized; one that only organizes does not own anything.',
   'The lot at 621 DeGraw is owned by FAC Center Local Development Corporation, which tells you something. They own the building they organize from.',
 ],
 'does':[
   'On housing it builds and manages affordable and supportive housing, with a pipeline running to as many as <b>1,900 units</b>, and it has done the unglamorous work too: gut renovations of small rental buildings, LEED Gold mixed-income developments, and a public library, a public park and five Pre-K classrooms folded into its projects.',
   'On the ground it runs tenant counseling and organizing, foreclosure prevention and homebuyer counseling, and adult education including GED prep, English classes and digital literacy for over a thousand adults a year.',
   'Workforce development runs through its affiliate <b>Brooklyn Workforce Innovations</b>. <b>South Brooklyn Against Displacement</b> is its organizing arm.',
 ],
 'kv':[('Founded','1978'),('Executive Director','Michelle de la Uz'),
       ('Community board','<a href="/cb-bk-6.html">Brooklyn Community Board 6</a>'),
       ('Second office','132 32nd Street, Suite 106, Brooklyn, NY 11232')],
 'links':[('Their site','https://fifthave.org',True),
          ('Brooklyn CB6','/cb-bk-6.html',False),
          ('Park Slope 5th Avenue BID','/bid-park-slope-5th-avenue/',False),
          ('Search an address','/citywide-search.html',False)],
},
]

TPL = """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} &mdash; bkcb6.app</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="https://bkcb6.app/{slug}">
<meta property="og:site_name" content="Brooklyn Community Board 6"><meta property="og:type" content="profile">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="https://bkcb6.app/{slug}">
<meta property="og:image" content="https://bkcb6.app/site-icons/{slug}.png">
<meta name="twitter:card" content="summary">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,700;9..40,800;9..40,900&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/org-profile.css?v=1">{brandcss}
</head>
<body>
<div class="pwrap">

  <div class="phead">
    <span class="pmark"><img src="/site-icons/{slug}.png" alt="{name}"></span>
    <span>
      <div class="pcrumb"><a href="/" style="color:inherit">bkcb6.app</a> &middot; <a href="/govhub.html" style="color:inherit">Government</a></div>
      <h1>{name}</h1>
      <div class="pseat">{seat}</div>
    </span>
  </div>

  <div class="sec introsec"><div class="bio dmintro">{intro}
    <p class="sig">&mdash;<a href="mailto:Mike@bkcb6.org">Mike Racioppo</a></p></div></div>

  <div class="sec"><h2>Where it is</h2>
    <details class="mapwrap" open><summary>Map of the block<span class="msub">zoning, boundary, overlaps, land use</span><span class="marr2">&#9660;</span></summary>
    <div class="mapinner">
      <div class="mapttl">{addrflat} <span>the building, its block and the zoning around it</span></div>
      <div class="msearch"><input type="search" placeholder="Search an address to drop a pin" autocomplete="off"><button type="button">Find</button><button type="button" class="mreset" data-map-reset>Reset</button></div>
      <div class="pmap" id="map" data-profile-map data-bid-slug="park-slope-5th-avenue" data-point-lat="{lat}" data-point-lng="{lng}" data-point-zoom="17" data-point-icon="/site-icons/{slug}.png" data-point-icon-w="200" data-point-icon-h="200"></div>
      <div class="mstat" data-map-status></div>
      <button type="button" class="mtoggle" aria-expanded="false" data-map-toggle-btn><span style="flex:1;text-align:left">Add to the map</span><span class="marr">&#9660;</span></button>
      <div class="mtools" data-map-toggles hidden></div>
      <div class="mhint">Tap the map anywhere to drop a pin and open that lot.</div>
    </div></details>
  </div>

{events}  <div class="sec"><h2>{does_title}</h2><div class="bio">{does}{doesbtns}</div></div>
{extra}
  <div class="sec"><h2>Contact</h2><div class="bio"><ul class="kv">
    <li><span class="k">Address</span><span class="v">{addr}<br>Brooklyn, NY {zip}{note}</span></li>
    {phone}{email}
    <li><span class="k">Website</span><span class="v"><a href="{weburl}" target="_blank" rel="noopener">{web} &#8599;</a></span></li>
    {kv}
  </ul></div></div>

  <div class="sec"><h2>Go on</h2><div class="btns">{links}</div></div>

  <div class="pfoot">Mission, contact details and programme descriptions from the organisation&rsquo;s own site. Zoning and lot records from the Department of City Planning. Logos are the organisations&rsquo; own, used to identify them.<br>
  <a href="/govhub.html">The Government Hub</a> &middot; <a href="/directory">The Address Directory</a> &middot; <a href="/citywide-search.html">Search any address</a></div>
</div>
<script src="/assets/profile-map.js?{mapjs}"></script>
{evjs}</body></html>
"""


BRANDCSS = """
<style>
/* {name} brand palette: teal and orange from their own mark */
.phead{{background:{dark};border-bottom:4px solid {accent}}}
.pmark{{border-color:rgba(255,255,255,.5)}}
.pcrumb,.pcrumb a{{color:rgba(255,255,255,.8)}}
.pseat{{color:rgba(255,255,255,.9)}}
.dmintro{{border-left-color:{accent};background:{wash}}}
.dmintro b{{color:{ink}}}
.dmintro .sig a{{color:{ink};border-bottom-color:{accent}}}
.sec h2{{color:{ink}}}
.evsec h2{{color:{ink}}}
.evcard{{background:{dark};box-shadow:0 3px 14px rgba(77,141,150,.28)}}
.evthen li{{border-color:{light}}}
.evthen .ed{{background:{dark}}}
.evthen .eb .et{{color:{ink}}}
.evall{{color:{ink};border-bottom-color:{mid}}}
.evbtn{{border-color:rgba(255,255,255,.75)}}
.bio b{{color:{ink}}}
.bio a,.kv .v a{{text-decoration-color:{accent}}}
.cbtn{{border-color:{mid};color:{ink}}}
.btn{{border-color:{dark};color:{ink}}}
.btn.hot{{background:{accent};border-color:{accent};color:#fff}}
.mapwrap>summary{{border-color:{light};color:{ink}}}
.msearch button{{background:{accent}}}
.msearch input:focus{{border-color:{mid}}}
.mtog.on{{background:{dark};border-color:{dark}}}
.mtoggle{{border-color:{light};color:{ink}}}
.mapttl{{color:{ink}}}
.zoninglink{{border-left-color:{accent}}}
.pfoot a{{color:{ink}}}
</style>"""

EVJS = r"""
<script>
/* The next few events, read live out of calendar.html and data/calendar-events.json,
   the same two sources the calendar itself uses. Each one is checked against the
   clock and not just the date, so an event that started earlier today has
   already dropped off by the evening and the next one has taken its place. */
(function(){
  var ORG='__EVORG__', HREF='__EVHREF__', NAME='__EVNAME__', LOGO='/site-icons/__SLUG__.png';
  var slot=document.getElementById('orgEvents'), more=document.getElementById('orgMore');
  if(!slot) return;
  var MON=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  var DAY=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  var AHEAD=4;
  var bust='?_='+Math.floor(Date.now()/60000);
  function esc(v){ return String(v==null?'':v).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];}); }
  function literal(src, opener, closer){
    var i=src.indexOf(opener); if(i===-1) return null;
    var j=src.indexOf(closer,i); if(j===-1) return null;
    try { return (new Function('return '+src.slice(i+opener.length-1, j+closer.length)))(); } catch(e){ return null; }
  }
  function starts(e){
    var p=String(e.date||'').split('-');
    if(p.length!==3) return null;
    var d=new Date(+p[0], +p[1]-1, +p[2]);
    if(isNaN(d)) return null;
    var m=/^\s*(\d{1,2}):(\d{2})\s*([AaPp])/.exec(e.time||'');
    if(m){ var h=+m[1]%12; if(/[Pp]/.test(m[3])) h+=12; d.setHours(h, +m[2], 0, 0); }
    else { d.setHours(23,59,59,999); }
    return d;
  }
  function label(d, time){
    var t=new Date(); t.setHours(0,0,0,0);
    var days=Math.round((new Date(d.getFullYear(),d.getMonth(),d.getDate())-t)/86400000);
    var w = days===0 ? 'Today' : days===1 ? 'Tomorrow' : DAY[d.getDay()]+', '+MON[d.getMonth()]+' '+d.getDate();
    return w + (time ? ' \u00b7 '+esc(time) : '');
  }
  function empty(msg){
    slot.innerHTML='<div class="evcard"><div class="evkick">Coming up</div><div class="evline">'+msg+' <a href="'+HREF+'" style="color:#fff;font-weight:700">See their calendar</a>.</div></div>';
    more.innerHTML='<a class="evall" href="'+HREF+'">'+esc(NAME)+'</a>';
  }
  Promise.all([
    fetch('/calendar.html'+bust).then(function(r){ return r.ok ? r.text() : ''; }).catch(function(){ return ''; }),
    fetch('/data/calendar-events.json'+bust).then(function(r){ return r.ok ? r.json() : null; }).catch(function(){ return null; })
  ]).then(function(res){
    var src=res[0], live=res[1];
    var EVENTS = src ? literal(src, 'const EVENTS = {', '\n};') : null;
    if(!EVENTS){ empty('The calendar did not load.'); return; }
    var rows=[], seen={};
    function add(date, ev){
      if(!ev || ev.type!==ORG || !ev.label) return;
      var k=date+'|'+String(ev.label).replace(/\s+/g,' ').trim().toLowerCase();
      if(seen[k]) return; seen[k]=1;
      rows.push({date:date, title:ev.label, time:ev.time||'', loc:ev.location||'', href:ev.href||'', link:ev.linkText||'', desc:ev.desc||''});
    }
    Object.keys(EVENTS).forEach(function(d){ (EVENTS[d]||[]).forEach(function(ev){ add(d, ev); }); });
    if(live && Array.isArray(live.events)) live.events.forEach(function(ev){ if(ev && ev.date) add(ev.date, ev); });
    var now=new Date();
    var prog=rows.map(function(e){ e.__at=starts(e); return e; })
      .filter(function(e){ return e.__at && e.__at>now; })
      .sort(function(a,b){ return a.__at-b.__at; });
    if(!prog.length){ empty('Nothing on the calendar right now.'); return; }
    var e=prog[0];
    var html='<div class="evcard"><div class="evkick">Next up</div>'
      +'<div class="evhead"><span class="evlogo"><img src="'+LOGO+'" alt=""></span><span class="evttl">'+esc(e.title)+'</span></div>'
      +'<div class="evline">\uD83D\uDD52 '+label(e.__at, e.time)+'</div>'
      +(e.loc?'<div class="evline">\uD83D\uDCCD '+esc(e.loc)+'</div>':'')
      +(e.desc?'<div class="evdesc">'+esc(e.desc)+'</div>':'')
      +'<div class="evbtns">'
      +(e.href?'<a class="evbtn" href="'+esc(e.href)+'" target="_blank" rel="noopener">'+esc(e.link||'Details \u2197')+'</a>':'')
      +'<a class="evbtn" href="'+HREF+'">Their full calendar</a></div></div>';
    var rest=prog.slice(1, AHEAD);
    if(rest.length){
      html+='<ul class="evthen">';
      rest.forEach(function(x){
        var row='<span class="ed"><span class="em">'+MON[x.__at.getMonth()]+'</span><span class="en">'+x.__at.getDate()+'</span></span>'
          +'<span class="eb"><span class="et">'+esc(x.title)+'</span><span class="ew">'+label(x.__at, x.time)+'</span></span>';
        html+='<li>'+(x.href ? '<a href="'+esc(x.href)+'" target="_blank" rel="noopener">'+row+'</a>' : row)+'</li>';
      });
      html+='</ul>';
    }
    slot.innerHTML=html;
    var left=prog.length-Math.min(prog.length,AHEAD);
    more.innerHTML = left>0
      ? '<a class="evall" href="'+HREF+'">'+left+' more event'+(left===1?'':'s')+' on their CB6 calendar &rarr;</a>'
      : '<a class="evall" href="'+HREF+'">'+esc(NAME)+' &rarr;</a>';
  }).catch(function(){ empty('The calendar did not load.'); });
})();
</script>
"""

for o in ORGS:
    intro = ''.join('<p>' + p + '</p>' for p in o['intro'])
    does = ''.join('<p>' + p + '</p>' for p in o['does'])
    note = ('<br><span style="font-size:.78rem;color:var(--muted)">' + o['addr_note'] + '</span>') if o.get('addr_note') else ''
    phone = ('<li><span class="k">Phone</span><span class="v"><a href="tel:%s">%s</a></span></li>' % (o['tel'], o['phone'])) if o.get('phone') else ''
    email = ('<li><span class="k">Email</span><span class="v"><a href="mailto:%s">%s</a></span></li>' % (o['email'], o['email'])) if o.get('email') else ''
    kv = ''.join('<li><span class="k">%s</span><span class="v">%s</span></li>' % (k, v) for k, v in o['kv'])
    links = ''.join(
        '<a class="btn%s" href="%s"%s>%s%s</a>' % (
            ' hot' if hot else '', href,
            ' target="_blank" rel="noopener"' if hot else '',
            label, ' &#8599;' if hot else '')
        for label, href, hot in o['links'])
    def cbtns(items):
        return ''.join(
            '<a class="cbtn" href="%s"%s>%s%s</a>' % (
                href, ' target="_blank" rel="noopener"' if hot else '',
                label, ' &#8599;' if hot else '')
            for label, href, hot in items)
    events = ''
    evjs = ''
    if o.get('evorg'):
        events = ('  <div class="sec evsec"><h2>%s</h2><div id="orgEvents"><div class="evcard">'
                  '<div class="evline">Loading from the CB6 calendar\u2026</div></div></div>'
                  '<div class="secnote" id="orgMore"></div></div>\n\n') % o['evtitle']
        evjs = (EVJS.replace('__EVORG__', o['evorg']).replace('__EVHREF__', o['evhref'])
                .replace('__EVNAME__', o['evname']).replace('__SLUG__', o['slug']))
    doesbtns = ('<div class="contact">' + cbtns(o['does_btns']) + '</div>') if o.get('does_btns') else ''
    extra = ''.join(
        '\n  <div class="sec"><h2>%s</h2><div class="contact" style="margin-top:0">%s</div></div>\n' % (title, cbtns(items))
        for title, items in o.get('extra', []))
    brandcss = BRANDCSS.format(name=o['name'], **o['brand']) if o.get('brand') else ''
    does_title = o.get('does_title','What it does')
    fields = dict(o)
    # the record's own phone/email are raw values; the template wants the
    # rendered rows, so the built ones win
    fields.update(intro=intro, does=does, note=note, phone=phone, email=email,
                  kv=kv, links=links, mapjs=MAPJS, events=events, evjs=evjs,
                  doesbtns=doesbtns, extra=extra, brandcss=brandcss, does_title=does_title,
                  addrflat=o['addr'].replace('<br>', ', '))
    html = TPL.format(**fields)
    d = os.path.join(ROOT, o['slug'])
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(html)
    print('built /%s' % o['slug'])
