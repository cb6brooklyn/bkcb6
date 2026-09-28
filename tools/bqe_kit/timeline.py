# The BQE timeline (graphic and written) and the official plans by mayor. Imported by kit_sec.intro().
import html as H
def A(u, t): return '<a href="%s" target="_blank" rel="noopener">%s</a>' % (H.escape(u), t)
PARKS = 'https://www.nycgovparks.org/about/history/historical-signs/listings?id=11721'
BKWH = 'https://www.bkwaterfronthistory.org/story/an-expressway-and-a-promenade/'
DOT16 = 'https://www.nyc.gov/html/dot/downloads/pdf/bqe-atlantic-to-sands-nov2016.pdf'
BHA18 = 'https://thebha.org/news/bha-statement-on-the-bqe-reconstruction-plan-by-dot/'
DOTBQE = 'https://www.nyc.gov/html/dot/html/infrastructure/bqe.shtml'
PANEL = 'https://www.buildingcongress.com/uploads/BQE_Expert_Panel_Report_v12_digital_distro_reduce.pdf'
DOT21 = 'https://nyc.gov/html/dot/html/pr2021/pr21-031.shtml'
SB21 = 'https://nyc.streetsblog.org/2021/08/04/analysis-the-mayors-bold-plan-for-the-bqe-is-not-bold-but-is-really-a-long-punt'
ADAMS22 = 'https://www.nyc.gov/mayors-office/news/2022/12/mayor-adams-preliminary-design-concepts-re-envisioned-bqe-central-takes-major-step'
DOT23 = 'https://www.nyc.gov/html/dot/html/pr2023/bqe-design-concepts.shtml'
AMNY = 'https://www.amny.com/nyc-transit/nyc-enforcing-weight-trucks-crumbling-bqe/'
NSREP = 'https://bqevision.com/sites/default/files/2024-10/bqe-north-and-south-report-safe-sustainable-connected.pdf'
CREP = 'https://bqevision.com/sites/default/files/2024-12/bqe-central-vision-summary-report.pdf'
DEC24 = 'https://www.nyc.gov/html/dot/downloads/pdf/bqe-central-project-public-information-meeting-dec2024.pdf'
MAYOR = 'https://www.nyc.gov/mayors-office/news/2026/08/after-decades-of-delay--mayor-mamdani-moves-to-fix-the-city-owne'
BQEC = 'https://www.nyc.gov/html/dot/html/infrastructure/bqecentral.shtml'
FLYNN = 'https://nyc.streetsblog.org/2026/09/23/opinion-the-toughest-choice-was-the-only-choice-on-the-bqe'
FMC = 'https://nycdotprojects.info/project-feedback-map/bqe-central-feedback-map'
FMS = 'https://nycdotprojects.info/project-feedback-map/bqe-south-feedback-map'
FILM = 'https://www.segregationbydesign.com/brooklyn/tsotbqe'
IPA = 'https://instituteforpublicarchitecture.org/The-Story-of-the-Brooklyn-Queens-Expressway-Film'
RPA = 'https://rpa.org/events/the-story-of-the-bqe'
BGV = 'https://bqevision.com/about/background'

# (year position, era, short label for the graphic, written entry)
BUILT = [
 (1937, 'Construction begins', f'''<b>1937: construction begins.</b> The BQE was "first proposed in the mid-1930s"; work on what was then called the Brooklyn-Queens Connecting Roadway "started in 1937," and the Kosciuszko Bridge opened in 1939 ({A(PARKS, 'NYC Parks')}).'''),
 (1940, 'Moses plans the southern extension', f'''<b>1940: Robert Moses plans the route south.</b> "The Triborough Bridge and Tunnel Authority, under Chairman Robert Moses (1888–1981), detailed a plan in 1940" to extend the road south through Brooklyn ({A(PARKS, 'NYC Parks')}).'''),
 (1943, 'Brooklyn Heights wins a waterfront route', f'''<b>1943: the route moves to the waterfront.</b> One plan would have cut through the middle of Brooklyn Heights; opposition from groups like the Brooklyn Heights Association, and budget concerns, led planners "to opt instead for a waterfront route" ({A(BKWH, 'Brooklyn Waterfront History')}).'''),
 (1950.5, 'The Promenade is built', f'''<b>1946 to 1951: the Promenade.</b> Demolition of the waterfront warehouses began in 1946; the Promenade was built from 1950 to 1951 on top of the stacked highway ({A(BKWH, 'Brooklyn Waterfront History')}).'''),
 (1954, 'The cantilever opens', f'''<b>1954: the cantilever opens.</b> "The cantilevered section of the expressway opened in 1954 at Brooklyn Heights" ({A(PARKS, 'NYC Parks')}).'''),
 (1958, 'Becomes Interstate 278', f'''<b>1958: it becomes a federal highway.</b> "In 1958, the BQE was designated part of the federal highway system, and became known also as Interstate 278" ({A(PARKS, 'NYC Parks')}).'''),
 (1964, 'Completed', f'''<b>1964: completed.</b> "By the time the six-lane expressway was completed in 1964, the entire road cost $137 million" ({A(PARKS, 'NYC Parks')}).'''),
]
FIXING = [
 (2016.84, 'DOT project update: $1.7 billion', f'''<b>November 2016: the first rebuild estimate.</b> DOT put the reconstruction of the 1.5 miles from Atlantic Avenue to Sands Street at $1.7 billion and asked New York State to pay 38 percent ({A(DOT16, 'NYC DOT project update')}).'''),
 (2018.75, 'Two options, one on the Promenade', f'''<b>2018: two options.</b> DOT offered a "lane-by-lane reconstruction" or a "temporary 6-lane highway on the Promenade," and favored the second; the Brooklyn Heights Association objected to "the loss of the Promenade for six or more years" ({A(BHA18, 'Brooklyn Heights Association')}).'''),
 (2019.3, 'Expert panel convened', f'''<b>2019: an expert panel.</b> The city convened an expert panel to review the options ({A(DOTBQE, 'NYC DOT')}).'''),
 (2020.05, 'Panel report', f'''<b>January 2020: the panel reports.</b> It recommended cutting the highway to two lanes each way ({A(PANEL, 'BQE Expert Panel Report, p. 18')}).'''),
 (2021.6, 'De Blasio 20-year plan; two lanes', f'''<b>August 2021: a 20-year fix.</b> A plan "to extend the life of the Brooklyn-Queens Expressway (BQE) cantilever for at least another 20 years" ({A(DOTBQE, 'NYC DOT')}); on August 30, 2021 the lanes from Atlantic Avenue to the Brooklyn Bridge went from three to two each way ({A(DOT21, 'NYC DOT')}). The plan also called for "weigh-in-motion" sensors ({A(SB21, 'Streetsblog')}).'''),
 (2022.95, 'Adams design concepts', f'''<b>December 2022: a re-envisioned BQE Central.</b> The Adams administration released "preliminary design concepts for a re-envisioned BQE Central" ({A(ADAMS22, "NYC Mayor's Office")}).'''),
 (2023.16, 'Three refined designs', f'''<b>February 2023: three designs.</b> DOT showed "The Terraces, The Lookout, and The Stoop" and announced "a comprehensive traffic study of both two- and three-lane configurations" ({A(DOT23, 'NYC DOT')}). Its feedback maps drew {A(FMC, '118')} comments on BQE Central and {A(FMS, '122')} on BQE South.'''),
 (2023.87, 'Weight enforcement begins', f'''<b>November 2023: weight enforcement.</b> Sensors on BQE Central began ticketing overweight trucks ({A(AMNY, 'amNY')}).'''),
 (2024.8, 'North and South report', f'''<b>October 2024: the state-owned sections.</b> DOT's BQE North and South report proposed "streetscape and intersection redesigns, dedicated bike and bus infrastructure, highway capping, and new plazas" ({A(NSREP, 'NYC DOT')}).'''),
 (2024.95, 'Central report; options include removal', f'''<b>December 2024: BQE Central options.</b> DOT's public meeting listed options from "maintaining the structure" to "removing the highway, replacing it with a boulevard, or tunneling" ({A(DEC24, 'NYC DOT')}); the Central Vision report summarized the public input ({A(CREP, 'NYC DOT')}).'''),
 (2026.65, 'Mamdani: rehabilitate, $4 billion', None),   # filled per page
 (2026.73, 'DOT commissioner makes the case', f'''<b>September 2026: DOT makes its case.</b> Commissioner Mike Flynn wrote that the plan "isn't ideal" but that "We have years left, not decades" ({A(FLYNN, 'Streetsblog')}).'''),
]
MAYORS = [('de Blasio', 2014, 2022, '#64748b'), ('Adams', 2022, 2026, '#0f766e'), ('Mamdani', 2026, 2030.5, '#149a67')]

def graphic():
    def pos(y, a, b): return 100.0 * (y - a) / (b - a)
    # era 1: 1935 to 1966
    a1, b1 = 1935, 1966
    t1 = ''.join('<span class="tk" style="left:%.2f%%">%d</span>' % (pos(y, a1, b1), y) for y in (1940, 1950, 1960))
    def dots(items, a, b, pre):
        out, last, up = [], -99, False
        for i, (y, lab, _) in enumerate(items):
            p = pos(y, a, b); up = (not up) if p - last < 3.2 else False; last = p
            out.append('<a class="td%s" href="#tl-%s%d" style="left:%.2f%%" title="%s"><i>%d</i></a>' % (' up' if up else '', pre, i + 1, p, H.escape(lab), i + 1))
        return ''.join(out)
    d1 = dots(BUILT, a1, b1, 'b')
    # era 2: 2014 to 2030.5
    a2, b2 = 2014, 2030.5
    bands = ''.join('<span class="mb" style="left:%.2f%%;width:%.2f%%;--mc:%s">%s</span>' % (pos(s, a2, b2), pos(e, a2, b2) - pos(s, a2, b2), c, n) for n, s, e, c in MAYORS)
    t2 = ''.join('<span class="tk" style="left:%.2f%%">%d</span>' % (pos(y, a2, b2), y) for y in (2016, 2018, 2020, 2022, 2024, 2026, 2028, 2030))
    d2 = dots(FIXING, a2, b2, 'f')
    fut = ('<span class="fut" style="left:%.2f%%;width:%.2f%%" title="Environmental review, late 2026 to early 2028">Review</span>' % (pos(2026.75, a2, b2), pos(2028.3, a2, b2) - pos(2026.75, a2, b2)) +
           '<span class="fut c" style="left:%.2f%%;width:%.2f%%" title="Construction 2029 or 2030 to 2040">Build &rarr; 2040</span>' % (pos(2029.2, a2, b2), 100 - pos(2029.2, a2, b2)))
    return f'''<div class="tlg" aria-label="BQE timeline">
<div class="tlr"><div class="tll"><b>Building it</b><span>1937 to 1964</span></div><div class="tlt">{t1}<div class="axis"></div>{d1}</div></div>
<div class="tlr"><div class="tll"><b>Fixing it</b><span>2016 to today</span></div><div class="tlt">{bands}{t2}<div class="axis"></div>{d2}{fut}</div></div>
<p class="k">Numbers match the entries below. The shaded bands are mayoral terms.</p></div>'''

def written(y26):
    b = ''.join('<li id="tl-b%d"><span class="tn">%d</span><div>%s</div></li>' % (i + 1, i + 1, t) for i, (_, _, t) in enumerate(BUILT))
    f = ''.join('<li id="tl-f%d"><span class="tn">%d</span><div>%s</div></li>' % (i + 1, i + 1, t if t else y26) for i, (_, _, t) in enumerate(FIXING))
    return f'''<div class="tlw"><div><h4>Building it, 1937 to 1964</h4><ol class="tl2">{b}</ol></div><div><h4>Fixing it, 2016 to today</h4><ol class="tl2">{f}</ol></div></div>
<p class="k">The story on film: <i>The Story of the Brooklyn-Queens Expressway</i>, a 40-minute documentary by Adam Paul Susaneck of Segregation by Design, produced by the Institute for Public Architecture and NYU Schack, on how the highway's construction divided and displaced neighborhoods ({A(FILM, 'watch')}, {A(IPA, 'Institute for Public Architecture')}, {A(RPA, 'Regional Plan Association screening, November 5, 2025')}).</p>'''

PLANS = [
 ('Mayor de Blasio', '2014 to 2021', [
   ('November 2016', 'BQE Atlantic to Sands project update', DOT16, '$1.7 billion reconstruction estimate; asks the state for 38 percent.'),
   ('October 2018', 'DOT\'s two options, as published by the Brooklyn Heights Association', BHA18, 'Lane-by-lane reconstruction or a temporary highway on the Promenade.'),
   ('January 2020', 'BQE Expert Panel Report', PANEL, 'The city\'s expert panel; recommends two lanes each way.'),
   ('August 2021', 'Plan to extend the cantilever\'s life 20 years', DOTBQE, 'Two lanes, weight enforcement, repairs.'),
   ('August 2021', 'Lane change advisory', DOT21, 'Three lanes to two, Atlantic Avenue to the Brooklyn Bridge.'),
 ]),
 ('Mayor Adams', '2022 to 2025', [
   ('December 2022', 'Preliminary design concepts for BQE Central', ADAMS22, 'Start of the BQE Corridor Vision concepts.'),
   ('February 2023', 'Refined design concepts', DOT23, 'The Terraces, The Lookout and The Stoop; two- and three-lane traffic study.'),
   ('October 2024', 'BQE North and South report', NSREP, 'Proposals for the state-owned sections.'),
   ('December 2024', 'BQE Central public information meeting', DEC24, 'Options from repair to removal, a boulevard or a tunnel.'),
   ('December 2024', 'BQE Central Vision summary report', CREP, 'What the public said.'),
 ]),
 ('Mayor Mamdani', '2026 to today', [
   ('August 2026', 'BQE Central rehabilitation announcement', MAYOR, 'About $4 billion, 10 years, groundbreaking 2030.'),
   ('2026', 'NYC DOT BQE Central Project page', BQEC, 'Environmental review schedule and fall 2026 sessions.'),
 ]),
]
def plans():
    n = sum(len(p[2]) for p in PLANS)
    cols = ''.join('<div class="plc"><b>%s</b><span class="k">%s</span><ul>%s</ul></div>' % (m, yrs, ''.join('<li><span class="pd">%s</span> %s<br><span class="k">%s</span></li>' % (d, A(u, H.escape(t)), H.escape(w)) for d, t, u, w in items)) for m, yrs, items in PLANS)
    return f'''<details class="plans" open><summary><h3>Every official plan and report, by mayor ({n})</h3><span>Each links to the document itself</span></summary><div class="plg">{cols}</div></details>'''
