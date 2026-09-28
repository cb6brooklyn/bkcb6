# The Dean/Bergen feature set, generalized for the BQE pages. apply(html, scope) returns the page with the kit added.
import json, html as H, os, datetime, re, importlib.util as _iu0
_tsp = _iu0.spec_from_file_location('bqe_timeline', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'timeline.py')); TL = _iu0.module_from_spec(_tsp); _tsp.loader.exec_module(TL)
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
BHA18 = 'https://thebha.org/news/bha-statement-on-the-bqe-reconstruction-plan-by-dot/'
DOTBQE = 'https://www.nyc.gov/html/dot/html/infrastructure/bqe.shtml'
SB21 = 'https://nyc.streetsblog.org/2021/08/04/analysis-the-mayors-bold-plan-for-the-bqe-is-not-bold-but-is-really-a-long-punt'
ADAMS22 = 'https://www.nyc.gov/mayors-office/news/2022/12/mayor-adams-preliminary-design-concepts-re-envisioned-bqe-central-takes-major-step'
TRR = 'https://www.nyc.gov/html/dot/html/motorist/truckrouting.shtml'
SB23 = 'https://nyc.streetsblog.org/2023/03/20/analysis-city-ignored-bqe-panel-recs-to-ease-congestion-from-two-lane-conversion'
FLYNN = 'https://nyc.streetsblog.org/2026/09/23/opinion-the-toughest-choice-was-the-only-choice-on-the-bqe'
CHGPDF = 'https://www.nyc.gov/html/dot/downloads/pdf/truck-route-network-redesign-changes-2026.pdf'
SCOPES = {
    'cg': {'nbs': ['Carroll Gardens', 'Gowanus'], 'name': 'Carroll Gardens and Gowanus', 'short': 'these two neighborhoods', 'cds': ['306'], 'page': '/BQE/carrollgardens-gowanus/'},
    'cb6': {'nbs': None, 'name': 'Community District 6', 'short': 'CB6', 'cds': ['306', '302', '307', '308'], 'page': '/BQE/'},
}
def intro(scope, KB, KT):
    here = 'Carroll Gardens and Gowanus' if scope == 'cg' else 'CB6'
    SOUTH = (f', which in CB6 includes the below-ground stretch Streetsblog calls "the Carroll Gardens trench" ({A(SB23, "Streetsblog")})' if scope == 'cb6' else ', which runs past Carroll Gardens and Gowanus')
    if scope == 'cb6':
        y26 = f'''An approximately $4 billion, 10-year rehabilitation of BQE Central that keeps two lanes each way and breaks ground in 2030 ({A(MAYOR, "NYC Mayor's Office")}). <a href="#plan">The plan in detail</a>.'''
    else:
        y26 = f'''An approximately $4 billion, 10-year rehabilitation of BQE Central that breaks ground in 2030, with two temporary bypasses, one on Furman Street ({A(MAYOR, "NYC Mayor's Office")}). DOT says "The highway will remain two lanes and will not expand, nor will interchanges be altered" ({A(BQEC, 'NYC DOT')}).'''
    y26f = '<b>August 2026: rehabilitate what is there.</b> ' + y26
    return f'''<section class="intro" id="intro"><h2>From Moses to Mamdani</h2>
<p class="introlede">Robert Moses planned the BQE's route through Brooklyn, and it was finished in 1964. Its oldest stretch is now past its design life, and multiple mayors have put out plans to fix it.</p>
<details class="sfold"><summary><h3>What people may not know</h3><span>3 facts</span></summary>
<div class="facts">
<div class="fact"><b>The triple cantilever is a stacked highway.</b> For 0.4 miles, BQE Central is "two levels of highway with the Brooklyn Heights Promenade above and a local street, Furman Street, below" ({A(BQEC, 'NYC DOT')}).</div>
<div class="fact"><b>It is past its design life.</b> DOT says the structure is "more than 70 years old" ({A(BQEC, 'NYC DOT')}).</div>
<div class="fact"><b>Why it matters in {here}.</b> Limits on BQE Central, fewer lanes and weight enforcement, can push traffic off the highway and onto local streets. The rest of this page is what the public record shows about trucks on these streets.</div>
</div>
</details>
<details class="sfold"><summary><h3>Who controls which part</h3><span>City, state and federal</span></summary>
<div class="gov">
<div class="govc city"><span class="gl">City</span><b>BQE Central</b><p class="gsum">Owns BQE Central, about 1.5 miles from Atlantic Avenue to Sands Street, and runs this project.</p><details class="gmore"><summary>More</summary><p>About 1.5 miles, Atlantic Avenue to Sands Street, with the triple cantilever. "NYC DOT owns BQE Central (12% of the BQE in Brooklyn)" and leads this project and its city environmental review, CEQR ({A(BQEC, 'NYC DOT')}). The two lanes and the weight sensors on BQE Central are the city's ({A(AMNY, 'amNY')}). The city also sets the truck routes on local streets ({A(TRR, 'NYC DOT, Truck Routing')}).</p></details></div>
<div class="govc state"><span class="gl">State</span><b>BQE North and BQE South</b><p class="gsum">Owns the other 10.6 miles in Brooklyn: BQE North and BQE South.</p><details class="gmore"><summary>More</summary><p>"New York State owns the rest," the other 10.6 miles in Brooklyn ({A(BQEC, 'NYC DOT')}): BQE North, "from the Kosciuszko Bridge to Sands Street," and BQE South, "from Atlantic Avenue to the Verrazzano Bridge" ({A(BQEV, 'BQE Corridor Vision')}){SOUTH}. The city's plan is meant to let it "work with the State, which controls the northern and southern segments" ({A(MAYOR, "NYC Mayor's Office")}).</p></details></div>
<div class="govc fed"><span class="gl">Federal</span><b>All of it, as Interstate 278</b><p class="gsum">The whole BQE is Interstate 278, so changing it needs federal approval.</p><details class="gmore"><summary>More</summary><p>"The BQE is part of the federal interstate highway system," and "If we were to completely remove BQE Central, or alter even a single on- or off-ramp, it would require federal permission," DOT Commissioner Mike Flynn wrote. Among the reasons a bigger change is off the table now, he named "a federal administration with very different priorities" ({A(FLYNN, 'Streetsblog')}). The current plan stays inside what the city can do on its own: the interchanges will not be altered, and the project goes through the city's environmental review, CEQR, not a federal one ({A(BQEC, 'NYC DOT')}). The Adams plan had been headed for a federal review ({A(ADAMS22, "NYC Mayor's Office")}).</p></details></div>
</div>
</details>
<div class="sub2"><h3>The timeline, 1937 to 2040</h3><p>Tap any moment, or step through with the arrows.</p></div>
{TL.stepper(y26)}
<details class="sfold"><summary><h3>The story on film</h3><span>A 40-minute documentary</span></summary>{TL.film()}</details>
{TL.plans()}
</section>'''
def cta_block():
    return f'''<section class="ctatop" id="meetings"><div class="dotbrand"><a class="dbl" href="{BQEC}" target="_blank" rel="noopener"><img src="/assets/bqe/nycdot-logo.png" alt="New York City DOT" width="130" height="78"></a><div class="dbx"><a class="dbw" href="{BQEC}" target="_blank" rel="noopener"><img src="/assets/bqe/bqe-central-wordmark.png" alt="BQE Central" width="260" height="64"></a></div></div>
<p class="bqeblurb"><b>BQE Central</b> is the 1.5-mile, city-owned stretch of the BQE from Atlantic Avenue to Sands Street. The Mayor\'s plan: a $4 billion rehabilitation that keeps it at two lanes each way, breaking ground in 2030.</p>
<h2>Upcoming DOT meetings on BQE Central</h2>
<div class="cta" id="comment"><ul class="mtg">
<li><b>Tue, Oct 6</b><span>7 to 8 p.m. &middot; Virtual Q&amp;A</span><a class="ctalink" href="https://bit.ly/bqecentral-oct6" target="_blank" rel="noopener">Join</a></li>
<li><b>Tue, Oct 13</b><span>4 to 7 p.m. &middot; In person, Brooklyn Heights Library, 286 Cadman Plaza West</span></li>
<li><b>Thu, Oct 22</b><span>11 a.m. to noon &middot; Virtual Q&amp;A</span><a class="ctalink" href="https://bit.ly/bqecentral-oct22" target="_blank" rel="noopener">Join</a></li>
</ul>
<div class="ctat">Dates and links from {A(BQEC, 'NYC DOT')}.</div>
<div class="ctab"><a class="ctabtn" href="{BQEC}" target="_blank" rel="noopener">BQE Central: sessions and how to comment &rarr;</a><a class="ctalink" href="{FMRH}" target="_blank" rel="noopener">Red Hook Transportation Issues map</a><a class="ctalink" href="https://portal.311.nyc.gov/" target="_blank" rel="noopener">Report a truck off its route to 311</a></div></div>
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
<div class="sub2"><h3>Trucks: 311 complaints and NYPD tickets by month</h3><p>"Truck Route Violation" requests to 311 ({A('https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2020-to-Present/erm2-nwe9', '311')}), and NYPD summonses under VTL 413 (truck routes) and VTL 385 (size and weight) ({A('https://data.cityofnewyork.us/Public-Safety/Moving-Violation-B-Summons-Historic-/bme5-7ty4', 'NYPD summonses, historic')} and {A('https://data.cityofnewyork.us/Public-Safety/Moving-Violation-B-Summons-Year-to-Date-/57p3-pdcj', 'year to date')}). The summons files begin in 2018; months after they end (see the time window above) show no tickets because none are published yet.</p></div>
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

<li><b>Districts.</b> From the city's boundary files; a block is assigned to the district its midpoint falls in, and a block a boundary runs through lists both.</li>
</ul>'''
def layers_panel():
    return '<details class="lwrap" id="kitlayerswrap"><summary><h2>More map layers</h2><span>Districts, transit, bike lanes, speed limits and blocks</span></summary><div class="layers" id="kitlayers"></div></details>'
def config(KB, scope):
    L = json.load(open(f'{ROOT}/data/bqe/kit/layers.json'))
    D = {}
    for f in L['districts']['features']:
        k, i = f['properties']['k'], f['properties']['id']; lg = logo(k, i)
        D.setdefault(k, {})[i] = [dname(k, i), lg if lg and os.path.exists(ROOT + lg) else '']
    return 'var KSCOPE=%s;var KDIST=%s;\n' % (json.dumps({'id': scope, 'nbs': SCOPES[scope]['nbs'], 'name': SCOPES[scope]['name'], 'cds': SCOPES[scope]['cds'], 'cdOn': True}), json.dumps(D))
def apply(page, scope):
    KB = json.load(open(f'{ROOT}/data/bqe/kit/blocks.json')); KT = json.load(open(f'{ROOT}/data/bqe/kit/ts.json'))
    css = open(os.path.join(HERE, 'kit.css')).read()
    js = config(KB, scope) + open(os.path.join(HERE, 'kit_base.js')).read() + '\n' + open(os.path.join(HERE, 'kit_main.js')).read()
    page = page.replace('</head>', '<style>' + css + '</style>\n</head>', 1)
    # the Find bar replaces the host search box
    i = page.index('<div class="search-row">'); j = page.index('</div>', i) + 6
    page = page[:i] + findbar(KB, scope) + '<div hidden>' + page[i:j] + '</div>' + page[j:]
    # extra layers panel after the map
    ms = page.index('<div class="map-shell">'); ms_end = page.index('</div></div>', ms) + 12
    page = page[:ms_end] + '\n' + layers_panel() + page[ms_end:]
    # move the Find bar, map and layers to the top: after the top bar, behind the meetings box, with the time window
    fb = page.index('<div class="findbar">'); fe = page.index('<section', page.index('<div class="map-shell">'))
    seg = page[fb:fe]; page = page[:fb] + page[fe:]
    top = page.index('<section', page.index('class="top-bar"'))
    page = page[:top] + cta_block() + '\n' + seg + '\n' + '<details class="lwrap twwrap"><summary><h2>Time window</h2><span class="tw-sum">last 12 months</span></summary>' + twbar(KT) + '</details>' + '\n' + intro(scope, KB, KT) + '\n' + page[top:]
    # the record before Sources
    s = page.index('<section class="sec" id="sources">')
    page = page[:s] + record(KB, KT, scope) + '\n' + page[s:]
    # script after the host map script
    e = page.rindex('</script>')
    page = page[:e] + '\n' + js + '\n' + page[e:]
    # the I-278 road sign in the top bar
    tb = page.index('<div class="top-txt">')
    page = page[:tb] + '<img class="bqesign" src="/assets/bqe/bqe-road-sign.jpg" alt="Interstate 278, Brooklyn-Queens Expressway" width="150" height="46"><a class="bqeurl" href="https://bkcb6.app/bqe" title="bkcb6.app/bqe"><img src="/assets/bqe/bkcb6-app-bqe-wordmark.jpg" alt="bkcb6.app/bqe" width="190" height="46"></a>' + page[tb:]
    if 'property="og:image"' not in page:
        page = page.replace('</head>', '<meta property="og:image" content="https://bkcb6.app/assets/bqe/og-bkcb6-app-bqe.jpg">\n<meta name="twitter:image" content="https://bkcb6.app/assets/bqe/og-bkcb6-app-bqe.jpg">\n</head>', 1).replace('<meta name="twitter:card" content="summary">', '<meta name="twitter:card" content="summary_large_image">')
    # map icons: 311, NYPD, crash and DOT count points drawn as icons instead of dots; CB logos; no stacked neighborhood labels
    page = page.replace('L.circleMarker(', 'kMark(')
    page = page.replace('</head>', '<script>' + open(os.path.join(HERE, 'kit_icons.js')).read() + '</script>\n</head>', 1)
    page = page.replace(':escH(ci.lbl))', ':kCdLab(ci.lbl))')
    page = page.replace('function drawNb(){', 'function drawNb(){kNbReset();', 1)
    page = page.replace('if(z>=13){var c=L.geoJSON(f).getBounds().getCenter();', 'if(z>=13){var c=L.geoJSON(f).getBounds().getCenter();if(!kNbOk(c,f.properties.nb))return;', 1)
    # the top bar: the road sign and bkcb6.app/bqe already say BQE, so the title does not repeat it
    if scope == 'cb6':
        page = re.sub(r'<div class="top-txt"><h1>The <span>BQE</span></h1><p>.*?</p></div>', '<div class="top-txt"><h1 class="ksr">The BQE</h1></div>', page, count=1)
    else:
        page = re.sub(r'<div class="top-txt"><h1>The BQE &amp; Trucks in <span>Carroll Gardens &amp; Gowanus</span></h1><p>.*?</p></div>', '<div class="top-txt"><h1>Trucks in <span>Carroll Gardens &amp; Gowanus</span></h1></div>', page, count=1)
    # nothing said twice
    import importlib.util as _iu
    _sp = _iu.spec_from_file_location('dedupe', os.path.join(HERE, 'dedupe.py')); _dd = _iu.module_from_spec(_sp); _sp.loader.exec_module(_dd)
    page = _dd.run(page, scope)
    if scope == 'cb6':
        i = page.index('<div class="layers" id="layers">'); j = page.index('<div class="explain" id="explain"></div>')
        page = page[:i] + '<details class="lwrap" id="layerswrap"><summary><h2>Map layers</h2><span>BQE sections, counts, tickets, truck routes, boundaries</span></summary>' + page[i:j] + '</details><details class="lwrap"><summary><h2>What am I looking at?</h2><span>Every layer explained</span></summary>' + page[j:j + len('<div class="explain" id="explain"></div>')] + '</details>' + page[j + len('<div class="explain" id="explain"></div>'):]
        e = page.rindex('</script>')
        page = page[:e] + '\n' + open(os.path.join(HERE, 'collapse.js')).read() + '\n' + page[e:]
    i = page.index('<div class="legend-bar">'); j = page.index('</div>', i) + 6
    page = page[:i] + '<details class="lwrap lgwrap"><summary><h2>Map key</h2><span>What each line and icon means</span></summary>' + page[i:j] + '</details>' + page[j:]
    # one group below the map: layers, key and explanations
    i = page.index('<details class="lwrap lgwrap">'); j = page.index('</details>', i) + 10; lg = page[i:j]; page = page[:i] + page[j:]
    t = page.index('<details class="lwrap twwrap">'); page = page[:t] + lg + page[t:]
    a = page.index('<details class="lwrap" id="kitlayerswrap">'); t = page.index('<details class="lwrap twwrap">')
    page = page[:a] + '<details class="lwrap mapgrp"><summary><h2>Map layers and key</h2><span>Turn layers on and off; what each one means</span></summary>' + page[a:t] + '</details>' + page[t:]
    if '<div class="street-row">' in page:
        i = page.index('<div class="street-row">'); j = page.index('</div>', i) + 6
        page = page[:i] + '<details class="lwrap"><summary><h2>Find a street</h2><span>Any borough, by cross streets</span></summary>' + page[i:j] + '</details>' + page[j:]
    if '<nav class="toc">' in page:
        i = page.index('<nav class="toc">'); j = page.index('</nav>', i) + 6; page = page[:i] + page[j:]
    # the map opens with only the BQE and CB6; the BQE is marked with the I-278 sign
    SIGN = '<img class="bqesignmk" src="/assets/bqe/bqe-road-sign.jpg" alt="I-278 Brooklyn-Queens Expressway">'
    if scope == 'cg':
        page = re.sub(r"def\('(?!bqes')(\w+)',\{([^}]*?)on:true\}\)", lambda m: "def('%s',{%son:false})" % (m.group(1), m.group(2)), page)
        old = "html:'<div class=\"bqeb\"><img src=\"/site-icons/bqe-64.png\" alt=\"\"><div><b>'+t+'</b><span>'+sub+'</span></div></div>'"
        assert old in page
        page = page.replace(old, "html:'<div class=\"bqeb bqeb-sign\" title=\"'+sub.replace(/<br>/g,' · ')+'\">" + SIGN.replace("'", "\\'") + "</div>'")
    else:
        old = "function drawBQE(){bqeGroup.clearLayers();if(!LINES)return;"
        assert old in page
        page = page.replace(old, old + "L.geoJSON(LINES,{pane:'bqe',interactive:false,filter:function(f){var p=f.properties;return SECON[p.sec]&&p.k==='main';},style:{color:'#fff',weight:13,opacity:.95,lineCap:'round'}}).addTo(bqeGroup);", 1)
        page = page.replace("return p.k==='main'?{color:c,weight:6,opacity:.9,lineCap:'round'}", "return p.k==='main'?{color:c,weight:8,opacity:1,lineCap:'round'}", 1)
        for k in ('north', 'central', 'south'):
            page = page.replace("%s:'BQE %s" % (k, k.capitalize()), "%s:'%sBQE %s" % (k, SIGN.replace("'", "\\'"), k.capitalize()), 1)
    # NYC DOT branding last, so it wins over the host styles
    b = page.rindex('</body>')
    page = page[:b] + '<style>' + open(os.path.join(HERE, 'dot_theme.css')).read() + '</style>\n' + page[b:]
    return page
