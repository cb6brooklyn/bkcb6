# The Dean/Bergen feature set, generalized for the BQE pages. apply(html, scope) returns the page with the kit added.
import json, html as H, os, datetime
ROOT = '/home/claude/bkcb6'; HERE = os.path.dirname(os.path.abspath(__file__))
def A(u, t): return '<a href="%s" target="_blank" rel="noopener">%s</a>' % (H.escape(u), t)
def fmt(n): return f"{n:,}"
CONG = {'7': 'velazquez', '8': 'jeffries', '9': 'clarke', '10': 'goldman'}
def logo(k, i):
    if k == 'cd': return '' if int(i[1:]) >= 55 else '/elected/CB%d_540.png' % int(i[1:])
    return {'council': '/elected/CD%s.png' % i, 'senate': '/elected/SD%s.png' % i, 'assembly': '/elected/AD%s.png' % i, 'precinct': '/elected/precinct/%s.png' % i, 'congress': '/elected/%s.png' % CONG.get(i, '')}[k]
def dname(k, i):
    if k == 'cd': return ('Joint interest area %s' % i) if int(i[1:]) >= 55 else {'1': 'MNCB', '2': 'BXCB', '3': 'BKCB', '4': 'QNCB', '5': 'SICB'}.get(i[0], '') + str(int(i[1:]))
    if k == 'congress': return 'NY-' + i
    return {'council': 'Council ', 'senate': 'Senate ', 'assembly': 'Assembly ', 'precinct': ''}[k] + (i + ('th' if k == 'precinct' else '')) + (' Precinct' if k == 'precinct' else '')
MAYOR = 'https://www.nyc.gov/mayors-office/news/2026/08/after-decades-of-delay--mayor-mamdani-moves-to-fix-the-city-owne'
BQEC = 'https://www.nyc.gov/html/dot/html/infrastructure/bqecentral.shtml'
FMC = 'https://nycdotprojects.info/project-feedback-map/bqe-central-feedback-map'
FMS = 'https://nycdotprojects.info/project-feedback-map/bqe-south-feedback-map'
FMRH = 'https://nycdotprojects.info/project-feedback-map/red-hook-transportation-issues-map'
PANEL = 'https://www.buildingcongress.com/uploads/BQE_Expert_Panel_Report_v12_digital_distro_reduce.pdf'
AMNY = 'https://www.amny.com/nyc-transit/nyc-enforcing-weight-trucks-crumbling-bqe/'
BQEV = 'https://bqevision.com/'
TRMAP = 'https://bkcb6.app/truckroutes/?cd=306'
CHGPDF = 'https://www.nyc.gov/html/dot/downloads/pdf/truck-route-network-redesign-changes-2026.pdf'
SCOPES = {
    'cg': {'nbs': ['Carroll Gardens', 'Gowanus'], 'name': 'Carroll Gardens and Gowanus', 'short': 'these two neighborhoods', 'cds': ['306'], 'page': '/BQE/carrollgardens-gowanus/'},
    'cb6': {'nbs': None, 'name': 'Community District 6', 'short': 'CB6', 'cds': ['306', '302', '307', '308'], 'page': '/BQE/'},
}
def intro(scope, KB, KT):
    sc = SCOPES[scope]
    where = 'Carroll Gardens and Gowanus' if scope == 'cg' else 'CB6'
    return f'''<section class="intro" id="intro"><h2>The story so far</h2>
<p class="introlede">In August the Mayor announced a plan to rebuild the city-owned stretch of the BQE. The environmental review that will shape it is only now starting, and no design or traffic plan for the streets around the highway has been published. In the meantime, this page gathers what is known about the BQE and the trucks that leave it for {where}: the history, the truck route rules, what DOT has counted, and what the public record shows block by block.</p>
<p><b>What was announced.</b> On August 24, 2026, Mayor Zohran Mamdani announced a rehabilitation of BQE Central, the city-owned section "between Atlantic Avenue and Sands Street," at about $4 billion, a 10-year project with groundbreaking in 2030, including repairs to the triple cantilever and two temporary bypass structures, one on Furman Street ({A(MAYOR, "NYC Mayor's Office, August 24, 2026")}). NYC DOT says "The highway will remain two lanes and will not expand, nor will interchanges be altered," and lists construction from 2029 to 2040 ({A(BQEC, 'NYC DOT, BQE Central')}).</p>
<p><b>The back story.</b> DOT says the BQE was "Built between 1937 and 1964" and is "Brooklyn's only interstate highway" ({A(BQEC, 'NYC DOT')}). An expert panel convened by the city reported on the cantilever and its options in January 2020 ({A(PANEL, 'BQE Expert Panel Report')}). DOT has limited stress on the structure by "reducing traffic to two lanes on the triple cantilever" ({A(BQEC, 'NYC DOT')}), and in November 2023 the city began enforcing weight limits with sensors that are "only deployed on the city-owned section of the BQE between Atlantic Avenue and Sands Street" ({A(AMNY, 'amNY, November 9, 2023')}). South of Atlantic Avenue, next to Carroll Gardens, Gowanus and Red Hook, the highway is BQE South, owned by the state ({A(BQEV, 'BQE Corridor Vision')}). In early 2023 DOT ran public feedback maps for BQE Central and BQE South; both are now closed, with {A(FMC, '118')} and {A(FMS, '122')} comments.</p>
<p><b>Trucks and the streets.</b> A truck leaving the BQE is supposed to stay on designated truck routes until it is close to its destination (see the truck route rules below and the {A(TRMAP, 'bkcb6.app truck routes map')}). None of the 103 truck route changes DOT set for October 4, 2026 is in Community District 6 ({A(CHGPDF, 'NYC DOT list of changes')}). What the public record shows about trucks on these streets, the counts, 311 complaints, tickets and crashes, follows, every figure linked to its source.</p>
<p><b>What happens next.</b> DOT's schedule for the environmental review: scoping notice in September 2026, public scoping meetings in November 2026, a final scoping report early in 2027, a draft environmental impact statement with public meetings late in 2027, and the final statement early in 2028 ({A(BQEC, 'NYC DOT, BQE Central')}). DOT says the statement will study "construction, traffic, noise, air quality" and more. During scoping, "the public can comment on what the EIS should study" ({A(BQEC, 'NYC DOT')}).</p>
<div class="cta" id="comment"><div class="ctat"><b>Have a say.</b> DOT is holding sessions on BQE Central this fall: a virtual Q&amp;A on <b>October 6</b> (7 to 8 p.m.), an in-person session on <b>October 13</b> (4 to 7 p.m., Brooklyn Heights Library, 286 Cadman Plaza West) and a virtual Q&amp;A on <b>October 22</b> (11 a.m. to noon); the formal comment period on what the environmental review should study opens with scoping later this fall ({A(BQEC, 'NYC DOT')}). DOT's Red Hook Transportation Issues map is also open for comments on streets, trucks and transit in Red Hook ({A(FMRH, 'DOT')}).</div>
<div class="ctab"><a class="ctabtn" href="{BQEC}" target="_blank" rel="noopener">BQE Central: sessions and how to comment &rarr;</a><a class="ctalink" href="https://bit.ly/bqecentral-oct6" target="_blank" rel="noopener">Join October 6 (virtual)</a><a class="ctalink" href="https://bit.ly/bqecentral-oct22" target="_blank" rel="noopener">Join October 22 (virtual)</a><a class="ctalink" href="{FMRH}" target="_blank" rel="noopener">Red Hook Transportation Issues map</a><a class="ctalink" href="https://portal.311.nyc.gov/" target="_blank" rel="noopener">Report a truck off its route to 311</a></div></div>
</section>'''
def twbar(KT):
    my = lambda d: datetime.date.fromisoformat(d).strftime('%B %-d, %Y')
    return f'''<div class="twbar" id="twbar"><span class="lb">Time window</span><button class="tbtn active" data-p="12" onclick="kSetPreset('12')" style="--tc:#0d1b4b">Last 12 months</button><button class="tbtn" data-p="24" onclick="kSetPreset('24')" style="--tc:#0d1b4b">Last 2 years</button><button class="tbtn" data-p="36" onclick="kSetPreset('36')" style="--tc:#0d1b4b">Last 3 years</button><button class="tbtn" data-p="60" onclick="kSetPreset('60')" style="--tc:#0d1b4b">Last 5 years</button><button class="tbtn" data-p="all" onclick="kSetPreset('all')" style="--tc:#0d1b4b">Since 2013</button><button class="tbtn" data-p="custom" onclick="kSetPreset('custom')" style="--tc:#0d1b4b">Choose months</button>
<span class="fctl" id="tw-custom" style="display:none;flex:0"><select id="tw-from" onchange="kCustom()" aria-label="From month"></select><span class="lb">to</span><select id="tw-to" onchange="kCustom()" aria-label="To month"></select></span>
<span class="twnote">The block-by-block record below follows this window: crashes <span class="tw-lc">loading</span>; 311 and truck complaints <span class="tw-ls">loading</span>; tickets <span class="tw-lt">loading</span>. The NYPD crash file runs to {my(KT['crash_last'])}, the 311 file to {my(KT['s311_last'])}, the NYPD summons files to {my(KT['tk_last'])}. Tables elsewhere on the page that give years keep their own dates.</span></div>'''
def findbar(KB, scope):
    return '''<div class="findbar"><span class="lb">Find</span><select id="fmode" onchange="kMode(this.value)" aria-label="How to find a spot"><option value="block">Pick a block</option><option value="stretch">Pick a stretch: from one cross street to another</option><option value="addr">Search an address</option><option value="pin">Drop a pin on the map</option></select>
<div class="fctl" id="f-block"><select id="k-bst" onchange="kFillBlocks()" aria-label="Street"></select><select id="k-blk" onchange="kPick(this.value)" aria-label="Block"></select><button class="tbtn" onclick="kPick('')" style="--tc:#0d1b4b">Clear</button></div>
<div class="fctl" id="f-stretch" hidden><select id="k-sst" onchange="kFillStretch();kStretch()" aria-label="Street"></select><span class="lb">from</span><select id="k-sfr" onchange="kStretch()" aria-label="From cross street"></select><span class="lb">to</span><select id="k-sto" onchange="kStretch()" aria-label="To cross street"></select><button class="tbtn" onclick="kPick('')" style="--tc:#0d1b4b">Clear</button></div>
<div class="fctl" id="f-addr" hidden><input id="k-addr" type="text" placeholder="Street address in Brooklyn&hellip;" autocomplete="off"><button class="go" onclick="kSearch()">Search</button><button class="tbtn" onclick="kClearPin()" style="--tc:#0d1b4b">Clear</button></div>
<div class="fctl" id="f-pin" hidden><span class="hint">Tap anywhere on the map to drop a pin. It shows the districts there and the nearest block.</span><button class="tbtn" onclick="kClearPin()" style="--tc:#0d1b4b">Clear pin</button></div>
<a class="xlink" href="#record">The block-by-block record</a></div><div class="addr-result" id="k-res"></div><div class="blkcard" id="k-card" hidden></div>'''
def record(KB, KT, scope):
    sc = SCOPES[scope]
    bl = [b for b in KB['blocks'] if (sc['nbs'] is None or b['nb'] in sc['nbs'])]
    ft = sum(b['ft'] for b in bl); ns = len(set(b['street'] for b in bl))
    BJ = A('https://github.com/cb6brooklyn/bkcb6/blob/main/data/bqe/kit/blocks.json', 'blocks.json'); TJ = A('https://github.com/cb6brooklyn/bkcb6/blob/main/data/bqe/kit/ts.json', 'ts.json'); PY = A('https://github.com/cb6brooklyn/bkcb6/blob/main/tools/build_bqe_kit.py', 'build_bqe_kit.py')
    CS = A(KB['cscl_query'], 'NYC Street Centerline')
    return f'''<section class="sec" id="record"><h2>The record, block by block</h2>
<p class="lede">Every street block in {sc['name']}, {fmt(len(bl))} blocks on {ns} streets, {fmt(ft)} feet (calculated from the {CS}), with every NYPD crash, 311 request, 311 truck route complaint and NYPD truck route or size and weight ticket recorded within 100 feet of it, each counted once, on its nearest block, for the time window chosen at the top of the page ({BJ}, {TJ}, built by {PY}). Pick any block, stretch or address in the Find bar above the map to see its own record.</p></section>
<div id="k-tab"></div>
<div class="sub2"><h3>Trucks: 311 complaints and NYPD tickets by month</h3><p>"Truck Route Violation" requests to 311 ({A('https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2020-to-Present/erm2-nwe9', '311')}), and NYPD summonses under VTL 413 (truck routes) and VTL 385 (size and weight) ({A('https://data.cityofnewyork.us/Public-Safety/Moving-Violation-B-Summons-Historic-/bme5-7ty4', 'NYPD summonses, historic')} and {A('https://data.cityofnewyork.us/Public-Safety/Moving-Violation-B-Summons-Year-to-Date-/57p3-pdcj', 'year to date')}). The summons files begin in 2018 and run to {datetime.date.fromisoformat(KT['tk_last']).strftime('%B %-d, %Y')}; months after that show no tickets because none are published yet.</p></div>
<div class="chartbox" id="k-tm"></div>
<div class="sub2"><h3>Crashes by month</h3><p>All crashes, and those where NYPD recorded a truck among the vehicles (any vehicle type NYPD recorded that names a truck, tractor, trailer, dump truck, tanker, box truck, flatbed, delivery, concrete, garbage or tow vehicle; pick-up trucks and SUVs are not counted) ({A('https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95', 'NYPD crashes')}).</p></div>
<div class="chartbox" id="k-cm"></div>
<div class="sub2"><h3>311 requests by month</h3></div><div class="chartbox" id="k-sm"></div>
<div class="sub2"><h3>By year</h3><p>Calendar years inside the window; a year the window only partly covers is marked *.</p></div><div class="chartbox" id="k-yr"></div>
<div class="sub2"><h3>By day of the week and hour of the day</h3></div><div class="chartbox" id="k-dow"></div><div class="chartbox" id="k-hr"></div>
<div id="k-daywrap"><div class="sub2"><h3>By day</h3><p>Shown for windows of two years or less.</p></div><div class="chartbox" id="k-day"></div></div>
<div class="sub2"><h3>Against the districts around it and Brooklyn</h3><p>Per mile of street per year in this window. Whole-district counts are every record inside the district boundary; street miles are from the {A('https://data.cityofnewyork.us/City-Government/Centerline/inkn-q76z', 'NYC Street Centerline')}, streets only. Brooklyn is every record labeled Brooklyn.</p></div>
<div id="k-cmp"></div>
<div class="sub2"><h3>Ranked by block</h3><p id="k-rk-note"></p></div>
<div class="chartbox" id="k-rkt"></div><div class="chartbox" id="k-rkc"></div>
<details class="blkall"><summary><h3>Every block ({fmt(len(bl))})</h3><span>sortable by any column; tap a block to see it on the map</span></summary><div id="k-all"></div></details>
<div class="sub2"><h3>Where the boundaries come from</h3></div>
<ul class="pts">
<li><b>Blocks.</b> The street centerline between two cross streets as the city draws it ({CS}); pedestrian paths and highway ramps do not count as cross streets.</li>
<li><b>100 feet.</b> This page's own choice, not a city definition: it reaches across each intersection and to the building fronts on both sides. Records within 100 feet of two blocks count on the nearer one, so the blocks add up.</li>
<li><b>Neighborhoods.</b> The outlines used across bkcb6.app ({A('https://github.com/cb6brooklyn/bkcb6/blob/main/data/city-neighborhoods.geojson', 'city-neighborhoods.geojson')}), which are not official boundaries; a block belongs to the outline its midpoint is in.</li>
<li><b>Districts.</b> From the city's boundary files; a block is assigned to the district its midpoint falls in, and a block a boundary runs through lists both.</li>
</ul>'''
def layers_panel():
    return '<details class="lwrap" id="kitlayerswrap" open><summary><h2>More map layers</h2><span>Districts, transit, bike lanes, speed limits and blocks</span></summary><div class="layers" id="kitlayers"></div></details>'
def config(KB, scope):
    L = json.load(open(f'{ROOT}/data/bqe/kit/layers.json'))
    D = {}
    for f in L['districts']['features']:
        k, i = f['properties']['k'], f['properties']['id']; lg = logo(k, i)
        D.setdefault(k, {})[i] = [dname(k, i), lg if lg and os.path.exists(ROOT + lg) else '']
    return 'var KSCOPE=%s;var KDIST=%s;\n' % (json.dumps({'id': scope, 'nbs': SCOPES[scope]['nbs'], 'name': SCOPES[scope]['name'], 'cds': SCOPES[scope]['cds']}), json.dumps(D))
def apply(page, scope):
    KB = json.load(open(f'{ROOT}/data/bqe/kit/blocks.json')); KT = json.load(open(f'{ROOT}/data/bqe/kit/ts.json'))
    css = open(os.path.join(HERE, 'kit.css')).read()
    js = config(KB, scope) + open(os.path.join(HERE, 'kit_base.js')).read() + '\n' + open(os.path.join(HERE, 'kit_main.js')).read()
    page = page.replace('</head>', '<style>' + css + '</style>\n</head>', 1)
    # the Find bar replaces the host search box
    i = page.index('<div class="search-row">'); j = page.index('</div>', i) + 6
    page = page[:i] + findbar(KB, scope) + '<div hidden>' + page[i:j] + '</div>' + page[j:]
    # intro and time window at the top, after Mike's note if present, else after the top bar
    if 'class="mnote"' in page: anchor = page.index('</section>', page.index('class="mnote"')) + 10
    elif '<section class="mstrip"' in page: anchor = page.index('<section class="mstrip"')
    else: anchor = page.index('<div class="findbar">')
    page = page[:anchor] + '\n' + intro(scope, KB, KT) + '\n' + twbar(KT) + page[anchor:]
    # extra layers panel after the map
    ms = page.index('<div class="map-shell">'); ms_end = page.index('</div></div>', ms) + 12
    page = page[:ms_end] + '\n' + layers_panel() + page[ms_end:]
    # the record before Sources
    s = page.index('<section class="sec" id="sources">')
    page = page[:s] + record(KB, KT, scope) + '\n' + page[s:]
    # script after the host map script
    e = page.rindex('</script>')
    page = page[:e] + '\n' + js + '\n' + page[e:]
    return page
