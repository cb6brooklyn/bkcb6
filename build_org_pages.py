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
MAPJS = 'v=20260828d'

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
   'The <b>Gowanus Canal Conservancy</b> is the environmental steward of the canal and of the watershed that drains into it, which in a combined sewer city is the same conversation. Its stated mission is ecologically sustainable parks and public spaces in the Gowanus lowlands, and a community of stewards to look after them.',
   'In a district where a Superfund cleanup, a rezoning and a combined sewer system all meet in the same few blocks, this is the organisation holding the environmental thread. It works with the EPA, the city Department of Environmental Protection, Riverkeeper and a string of universities on water quality, and it runs the green infrastructure and street tree work that decides whether rain falling on Gowanus ends up in the canal.',
 ],
 'does':[
   'It runs the <b>Lowlands Nursery</b>, growing native urban-adapted plants and selling them to residents, institutions and landscape designers, with proceeds going back into education and stewardship.',
   'It runs the <b>Gowanus Green Team</b>, paid high school apprentices doing conservation work, and the <b>Gowanus Tree Network</b>, which trains neighbours as Citizen Pruners to look after the street trees on their own blocks.',
   'It works out of the <b>Old American Can Factory</b>, a three storey 1890 complex at Third Street and Third Avenue that now houses artists, makers and non-profits. The lot is zoned <b>M1-4/R7X</b> inside the <b>Gowanus special district</b>, the mixed use zoning the 2021 rezoning brought in.',
 ],
 'kv':[('Community board','<a href="/cb-bk-6.html">Brooklyn Community Board 6</a>'),
       ('The building','<a href="/old-american-can-factory">The Old American Can Factory</a>'),
       ('Zoning','M1-4/R7X, Gowanus special district')],
 'links':[('Their site','https://gowanuscanalconservancy.org',True),
          ('The Old American Can Factory','/old-american-can-factory',False),
          ('The Gowanus rezoning','/gowanus.html',False),
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
<link rel="stylesheet" href="/assets/org-profile.css?v=1">
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

  <div class="sec"><h2>What it does</h2><div class="bio">{does}</div></div>

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
</body></html>
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
    fields = dict(o)
    # the record's own phone/email are raw values; the template wants the
    # rendered rows, so the built ones win
    fields.update(intro=intro, does=does, note=note, phone=phone, email=email,
                  kv=kv, links=links, mapjs=MAPJS,
                  addrflat=o['addr'].replace('<br>', ', '))
    html = TPL.format(**fields)
    d = os.path.join(ROOT, o['slug'])
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(html)
    print('built /%s' % o['slug'])
