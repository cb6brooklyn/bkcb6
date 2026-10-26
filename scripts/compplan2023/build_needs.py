"""CB6 Statements of District Needs (FY2027, FY2026) lined up against the Borough President's
Comprehensive Plans (2025, 2023). Writes bkcompplan/needs.json.
Each item quotes the statement. u25/u23 list the plan actions/recommendations that ask for the same thing,
picked by reading both; the page shows each one's own text so the reader can check the fit."""
import json, re, os
ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
B = json.load(open(os.path.join(ROOT, 'bkcompplan/plan.json')))
A = json.load(open(os.path.join(ROOT, 'bkcompplan/plan2023.json')))

def slug(s): return re.sub(r'^-|-$', '', re.sub(r'[^a-z0-9]+', '-', s.lower().replace('&', 'and')))
ids25, ids23 = {}, {}
for P in B['parts']:
    if P['t'] != 'Elements': continue
    for E in P['c']:
        if E.get('y') != 'E': continue
        for O in E.get('c', []):
            if O.get('y') != 'o': continue
            for S in O.get('c', []):
                if S.get('y') != 's': continue
                for ai, Ac in enumerate(S.get('c', [])):
                    if Ac.get('y') == 'a':
                        ids25[Ac['t'].rstrip('.')] = f"el-{slug(E['t'])}-o{O['n']}-s{S['n']}-a{ai+1}"
for g in A['goals']:
    for oi, o in enumerate(g['obj']):
        for ri, r in enumerate(o['recs']):
            ids23[r['n'] + '|' + r['t'][:40]] = f"y23-g{g['n']}-o{oi+1}-r{ri+1}"

def a25(*titles):
    out = []
    for t in titles:
        k = [x for x in ids25 if x.startswith(t.rstrip('.'))]
        assert len(k) == 1, (t, k)
        out.append(ids25[k[0]])
    return out
def a23(*nums):
    out = []
    for n in nums:
        num, _, start = n.partition(' ')
        k = [x for x in ids23 if x.split('|')[0] == num and (not start or x.split('|')[1].startswith(start))]
        assert len(k) == 1, (n, k)
        out.append(ids23[k[0]])
    return out

C1, C2, C3, C4 = 'Land Use, Landmarks & Housing', 'Transportation, Parks & Public Infrastructure', 'Business Affairs & Licenses', 'Human Services & Environmental Sustainability'
P1, P2, P3 = 'Build and Preserve Housing', 'Invest in Infrastructure for Climate Resilience and Transportation', 'Increase Access to Social Services'

# k, committee (None = from the top priorities), priority, FY2027 heading, FY2027 words, FY2026 heading/words or None, 2025 actions, 2023 recommendations
ITEMS = [
 ('housing-loss', None, P1, 'Stop losing homes to consolidation',
  'CD6 has the highest unit loss in Brooklyn and the fourth highest citywide (after Manhattan Community Districts 2, 7, and 8), with 1,500 units lost to consolidations from 2010–2024.',
  None, a25('Evaluate a Maximum Dwelling Unit Factor in Consolidation Warning Areas', 'Study the effect of landmarking on housing production'), []),
 ('nycha-repair', C1, P1, 'Improve NYCHA housing',
  "Update and maintain NYCHA properties to serve a critical segment of the City's residents by allocating funds to improve NYCHA housing conditions, targeting mold remediation, plumbing repairs, and HVAC systems.",
  ('NYCHA Housing Maintenance', "Update and maintain NYCHA properties to serve a critical segment of the City's residents by allocating funds to improve NYCHA housing conditions, targeting mold remediation, plumbing repairs, and HVAC systems."),
  a25('Prioritize the Vacant Unit Readiness Program', 'Increase response times for housing quality complaints'), a23('2.3.4')),
 ('deep-afford', C1, P1, 'Support deeply affordable housing',
  'Increase budget allocations for affordable housing construction and subsidies for deep affordability (<30% AMI) in areas experiencing the most need and displacement pressure, with a special emphasis on needs for existing demographics, which includes an aging population (the +65 population doubled in the last 10 years) as well as family sized units.',
  ('Affordable Housing Development', 'Increase budget allocations for affordable housing construction and subsidies in areas experiencing the most need and displacement pressure, like Red Hook and Gowanus.'),
  a25('Build and preserve more senior housing with on-site social services', 'Develop a pathway for expedited review for 100% affordable projects'), a23('2.1.2', '2.1.3', '2.1.5')),
 ('market-rate', C1, P1, 'Improve conditions for market-rate housing',
  'BKCB6 seeks to address natural affordability, increased accessibility, and aging-in-place within market rate housing through multifamily preservation programs and incentives, as well as promoting additional density through adaptive reuse or new development within contextually rezoned and landmarked parts of the district to accompany industrial rezonings.',
  ('Market-Rate Housing (Theme 1)', "There is demand for responsibly developed market-rate housing that complements the district's infrastructure and affordability needs."),
  a25('Study the effect of landmarking on housing production', 'Expand the amount of eligible receiving sites for transfer of development rights from landmarked properties'), a23('2.3.1', '2.2.5')),
 ('zoning-funding', C1, P1, 'Increase affordability with better zoning and funding',
  'We urge the City to maximize the number and depth of affordability in new housing, particularly within rezoned areas. Following the model of Gowanus Green, we seek to see affordable housing maximized on City-owned sites.',
  ('Zoning Adjustments', 'Budget for rezoning initiatives to increase affordable units in mixed-income developments, especially near transit corridors.'),
  a25('Publish a regular assessment of vacant and underutilized public land', 'Proactively pursue zoning map amendments to increase residential density on City-owned land', 'Amend the Zoning Resolution to increase the density bonus for TOD-qualified sites'), a23('2.1.4', '2.2.4')),
 ('nycha-input', C1, P1, 'Prioritize community input for future NYCHA construction',
  'Inclusive, community-led visioning processes are necessary to generate fresh ideas for NYCHA campuses.',
  ('NYCHA Vision Setting', 'inclusive, community-led visioning processes are necessary to generate fresh ideas for NYCHA campuses.'),
  a25('Ensure each NYCHA development has an active TA'), a23('2.3.5')),
 ('temp-shelter', None, P1, 'Temporary, supportive and shelter housing',
  'The district needs more housing options that offer stability and supportive services to help individuals regain access to permanent housing.',
  ('Temporary Housing (Theme 1)', 'The district needs increased housing options that offer stability and supportive services to help individuals regain permanent housing.'),
  a25('Develop more supportive housing', 'Implement a Housing First model'), a23('2.1.8')),
 ('parks', C2, P2, 'Fund public parks',
  'Fully fund NYC Department of Parks and Recreation (committing to at least 5% of the City budget) so that parks may continue to function as key public spaces and resources for our district.',
  ('Adequate Funding for NYC Parks', 'Fully fund parks so that they may continue to function as key public spaces and resources for our district.'),
  [], []),
 ('bike-parking', C2, P2, 'Expand bicycle parking',
  'Expand on-street bicycle parking corrals in known hot spots where delivery cyclists congregate to keep sidewalks clear and accessible. Where possible, combine bicycle parking corrals with daylighting to maintain sightlines at intersections and improve pedestrian safety.',
  None, a25('Pass universal daylighting legislation for NYC'), a23('4.3.4')),
 ('citibike', C2, P2, 'Improve bikeshare affordability',
  "Expand Citi Bike's Reduced Fare Bike Share program to include public high school and CUNY students aged 16 and above, in order to help make biking an affordable transportation option for young people.",
  ('Improved Affordability for Citibike', 'Budget to expand the Reduced Fare Bike Share program to include public high school and CUNY students aged 16 and above, in order to help make biking an affordable transportation option for young people.'),
  a25('Expand Citi Bike discount programs', 'Expand the city’s bike share system and make it affordable'), a23('4.1.2')),
 ('school-streets', C2, P2, 'Improve safety on school streets',
  'Fund materials such as barriers and signage to expand school streets to improve safety, especially during busy drop-off and pickup times. Additionally, streamline the process for approving school streets so that all schools in CD6 have this asset.',
  None, a25('Implement School Streets at every public school in Brooklyn'), a23('4.2.3')),
 ('bqe', C2, P2, 'Fix the Brooklyn-Queens Expressway',
  'Continue the planning and design of long-term improvements that preserve the southern portion of the Brooklyn-Queens Expressway (BQE) while also improving street safety, promoting equity, and enhancing the public realm.',
  None, a25('Pursue a corridor-wide approach to repairing the BQE', 'Pursue highway capping proposals'), a23('4.4.4')),
 ('vz-corridors', C2, P2, 'Redesign Vision Zero priority corridors',
  'Prioritize the physical separation of modes, such as the proposed center-running bus lanes on Flatbush Avenue, as the best option to move people more efficiently while also decreasing injuries for vulnerable road users.',
  None, a25('Redesign SBS corridors to provide physical separation between bus lanes and other vehicle traffic', 'Build more bike lanes', 'Fulfill the mandates of the 2019 Streets'), a23('4.1.1')),
 ('transport-plan', C2, P2, 'Overhaul our transportation infrastructure',
  'Budget for a comprehensive transportation plan to discourage unnecessary automobile trips while addressing road safety, walkability, and bike infrastructure needs.',
  ('Comprehensive Transportation Planning', 'Budget for a comprehensive transportation plan to address road safety, walkability, and bike infrastructure needs.'),
  a25('Pilot a low-traffic neighborhood in Brooklyn', 'Expand Neighborhood Loading Zones, Truck Loading Zones, and Commercial Metered Parking', 'Advance the Blue Highways initiative for sustainable freight'), a23('4.3.2', '4.4.7')),
 ('transit', C2, P2, 'Enhance our subway and bus infrastructure',
  'Fund accessibility upgrades, such as elevators and ramps, at key subway stations serving CD6. Accessibility improvements are broadly needed; other than the 7th Avenue F/G station, no stations within CD6 are currently served by elevators. CD6 also lacks east-west bus service, and there is widespread support to reactivate the B71 route, which was discontinued in 2010.',
  ('Subway Enhancements', 'Fund accessibility upgrades, such as elevators and ramps, at key subway stations serving the district, especially at the Smith-9th Street subway station, which lacks elevators despite being the highest elevation transit station in the entire world.'),
  a25('Create new “Rush” Service between Gowanus, Red Hook, and Manhattan', 'Redesign SBS corridors to provide physical separation between bus lanes and other vehicle traffic'), a23('7.1.1')),
 ('enforcement', C2, P2, 'Increase traffic enforcement to improve public safety',
  'Hardened universal daylighting, coupled with dedicated loading zones are needed to increase visibility and safety and reduce commercial double parking which endangers pedestrians, cyclists and motorists. BKCB6 also supports the increase of red-light, speed, and bike-lane cameras at priority intersections throughout CD6, in addition to in-person enforcement.',
  ('Public Safety Traffic Enforcement', 'Budget for critical enforcement action throughout the district.'),
  a25('Secure expanded authorization from NYS to install cameras', 'Pass universal daylighting legislation for NYC', 'Redesign Brooklyn’s truck network'), a23('4.3.5', '4.4.2')),
 ('open-streets', C3, P3, 'Continue Open Streets programming',
  'Continue and expand support for the Open Streets program within CD6. Maintain outreach, funding, and support for permitting and upkeep of outdoor sheds and spaces.',
  ('Outdoor Spaces', 'Maintain outreach, funding, and support for permitting and physical maintenance of outdoor sheds and spaces for local restaurants and bars.'),
  a25('Lower administrative and legal burdens on Open Streets community partners', 'Reinstate year-round roadway cafes', 'Expedite the Approval Process for Outdoor Dining applications'), a23('4.2.1')),
 ('groceries', C3, P3, 'Promote greater access to affordable groceries',
  'Prioritize the expansion of affordable, high-quality grocery options across CD6. Red Hook in particular faces a higher-than-average rate of food insecurity and SNAP usage, making it a key area for investment.',
  None, a25('Create municipal grocery stores', 'Expand DoubleUp Food Bucks to Brooklyn'), []),
 ('biz-rent', C3, P3, 'Improve rent affordability for small businesses',
  'Support rent stabilization measures, vacancy taxes, and long-term lease assistance for small and legacy businesses across CD6. Encourage the preservation of discounted industrial space and affordable artist studios, particularly in Red Hook and Gowanus.',
  None, a25('Improve lease notification requirements for commercial tenants in City-leased properties', 'Establish Special Enhanced Commercial Districts'), a23('6.4.5', '6.4.6')),
 ('bids', C3, P3, 'Support Business Improvement Districts',
  "Increase outreach, funding, and support for community-based organizations to conduct Commercial District Needs Assessments that consider all transit modes and seasonal factors. Support the ongoing formation of the Gowanus BID, Merchants of Smith Street (MOSS), and other business improvement districts.",
  ('Business Improvement Districts', 'Increase program outreach, funding, and support for community-based development organizations to conduct a Commercial District Needs Assessment, define new Business Improvement Districts throughout the district, apply for Small Business Services funding, and make targeted improvements to the commercial districts throughout the district.'),
  a25('Strengthen BIDs and merchants associations', 'Coordinate potential zoning proposals with Small Business Services'), a23('6.4.4')),
 ('workforce', C3, P3, 'Expand local workforce development programs',
  'Fund programs and centers for workforce development within Red Hook, Gowanus, and the NYCHA facilities that are located in the district. This includes NYCHA direct-entry union training programs and workforce development programs related to local employment within Industrial Business Zones, with an emphasis on green manufacturing and skilled trades providing higher earning opportunities.',
  ('Workforce Development Programs', 'Fund programs and centers for workforce development within Red Hook, Gowanus, and the NYCHA facilities that are located in those neighborhoods.'),
  a25('Fund workforce organizations to provide wraparound services', 'Encourage local manufacturing of climate-friendly products'), a23('6.3.3', '6.3.4')),
 ('childcare', C4, P3, 'Expand childcare',
  'Increase the number of childcare programs for children under the age of 5 which are either fully funded by the city or subsidized using city vouchers and cash assistance. Expand the distribution of childcare subsidies.',
  ('Expansion of Childcare Programs', 'Increase the number of childcare programs for children under the age of 5 which are either fully funded by the city or subsidized using city vouchers and cash assistance. Expand the distribution of childcare subsidies.'),
  a25('Expand access to free childcare', 'Support universal free childcare'), a23('1.3.5')),
 ('healthcare', C4, P3, 'Expand healthcare options',
  'Budget for permanent healthcare facilities in areas like Red Hook, Gowanus, and Columbia Waterfront, focusing on accessible, low-cost services.',
  ('Health Facility Funding', 'Budget for permanent healthcare facilities in areas like Red Hook, Gowanus, and Columbia Waterfront, focusing on accessible, low-cost services.'),
  a25('Expand the Neighborhood Health Action Center model'), a23('1.1.1', '1.2.1')),
 ('healthy-food', C4, P3, 'Increase access to healthy food',
  "Provide budget for community gardens, urban farms, and affordable food programs to reduce food insecurity in underserved neighborhoods. Expand DOHMH's Shop Healthy! food access programs to improve access to healthy affordable foods, especially in Red Hook, which is not currently eligible for these programs.",
  ('Healthy Food Access Initiatives', 'Provide budget for community gardens, urban farms, and affordable food programs to reduce food insecurity in underserved neighborhoods.'),
  a25('Enroll more eligible New Yorkers in food benefits and lower the threshold for eligibility', 'Create cold storage options for local food pantries'), a23('4.5.3', '4.5.5')),
 ('homeless', C4, P3, 'Support people experiencing homelessness',
  'Increase funding for shelters, mental health services, and job training programs to support homeless populations within CD6. We must house our fair share of the unhoused population, and to do so, more permanent facilities are needed.',
  ('Homelessness Services', 'Increase funding for shelters, mental health services, and job training programs to support homeless populations within the district.'),
  a25('Implement a Housing First model', 'Develop more supportive housing'), a23('2.1.8', '1.3.8')),
 ('dv', C4, P3, 'Support victims of domestic and sexual abuse',
  'Continue funding domestic violence shelters (including shelters that house women and children) and programs that serve those impacted by family violence, child violence, and domestic violence.',
  None, a25('Restore City funding to the Crime Victim Assistance Program'), a23('1.4.1')),
 ('community-centers', C4, P3, 'Build and maintain community center facilities and programming',
  'Allocate sufficient funds for community spaces within large residential developments, including NYCHA complexes such as the Red Hook Houses, to compensate for the many community spaces eliminated as part of FEMA construction work.',
  ('Community Center Spaces, Facilities, and Open Spaces', 'Allocate sufficient funds for community center spaces within large residential developments, including NYCHA complexes such as the Red Hook Houses, to compensate for the 457 trees, 14 water sprinkler systems and many community spaces eliminated as part of FEMA construction work.'),
  a25('Open NYCHA community centers', 'Invest in NYCHA tenant activities and programs'), a23('1.4.2')),
 ('flood-barriers', C4, P2, 'Protect vulnerable areas against flooding',
  'Allocate funds for fixed and deployable flood barriers in vulnerable areas to prevent damage during heavy storms, including as part of the Red Hook Coastal Resiliency initiative and the tentatively selected plan in the NY & NJ Harbor & Tributaries Focus Area Feasibility Study (HATS).',
  ('Flood Protection Infrastructure', 'Allocate funds for fixed and deployable flood barriers in vulnerable areas to prevent damage during heavy storms, including as part of the Red Hook Coastal Resiliency initiative.'),
  a25('Bolster Brooklyn’s infrastructure'), a23('3.4.1')),
 ('extreme-weather', C4, P2, 'Improve local resilience to extreme weather events',
  'Fund emergency response resources, including heating and cooling centers, to assist residents during severe weather, particularly in low-lying or otherwise vulnerable areas of CD6.',
  ('Emergency Preparedness for Extreme Weather', 'Fund emergency response resources, including heating and cooling centers, to assist residents during severe weather, particularly in low-lying or otherwise vulnerable areas of the district.'),
  a25('Expand community-based preparedness efforts', 'Expand the Cool Roofs program'), a23('3.3.2', '3.4.4')),
 ('green-infra', C4, P2, 'Upgrade green infrastructure and stormwater systems',
  'Increase funds for the areawide installation of green infrastructure including, but not limited to, bioswales, rain gardens, offline retention facilities, rain barrels, pervious surface treatments, street trees, and other best management practices to aggressively prevent storm water from entering into the sewer system, particularly in Red Hook and Gowanus.',
  ('Green Infrastructure and Stormwater System Upgrades', 'Sufficient funds are requested for the areawide installation of green infrastructure including, but not limited to, bioswales, rain gardens, offline retention facilities, rain barrels, pervious surface treatments, and other best management practices to aggressively prevent storm water from entering into the sewer system.'),
  a25('Support nature-based solutions for flood management', 'Plant more trees, especially in high-heat-vulnerability neighborhoods'), a23('3.4.5', '3.4.6')),
 ('power', None, P2, 'Protect electric infrastructure and expand local solar',
  "Protecting electric infrastructure and expanding local power generation with solar and energy storage systems to protect residents from power outages and reduce energy burden. Red Hook's power grid is highly vulnerable and susceptible to power outages, and must be modernized.",
  ('Climate Resilience (Theme 2)', 'Protecting electric infrastructure and expanding local power generation with solar and energy storage systems to protect residents from power outages'),
  a25('Increase access to solar for low- and moderate-income Brooklynites', 'Support community ownership models for Distributed Energy Resources'), a23('3.4.8')),
 ('libraries', None, P3, 'Greater access to public libraries',
  'Greater access to public libraries, which provide myriad social benefits, with a targeted request of 0.5% of the city budget going toward extending library hours, enhancing library programs, and ensuring access to library resources and heating/cooling centers in cases when libraries must close for renovations.',
  None, a25('Support Brooklyn’s libraries'), a23('5.3.4')),
]

APX = [  # FY2027 Appendix IV: maps CB6 reproduced from the 2025 plan -> where they are in the 2025 plan
 ('4.1', 'Access to Opportunity Index', [['p', 27]]), ('4.2', 'Access to Opportunity Subindexes', [['p', 28]]),
 ('4.3', 'Neighborhood Density Targets; Difference Between Actual and Target Density', [['p', 122]]),
 ('4.4', 'New Capacity Priority Areas', [['p', 62]]), ('4.5', 'Housing Consolidation Warning Areas', [['p', 64]]),
 ('4.6', 'Amenity-Rich Areas by NTA; by Census Block', [['p', 65]]),
 ('4.7', 'Market-Rate and Income-Restricted Housing Units Built, 2014–2024', [['p', 107]]),
 ('4.8', 'NYCHA Development Resident Population; NYCHA 20-Year Capital Needs Estimate', [['p', 118]]),
 ('4.9', 'Life Expectancy in Brooklyn; Healthy Eating + Active Living Index', [['p', 133]]),
 ('4.10', 'Residents Lacking Health Insurance; Self-Reported Mental Health', [['p', 136], ['p', 141]]),
 ('4.11', 'Access to Jobs', [['p', 67]]), ('4.12', 'Jobs in Commercial Centers', [['p', 74]]),
 ('4.13', 'Neighborhood Corridors', [['p', 75]]), ('4.14', 'Neighborhood Corridor Vacancy Analysis', [['p', 76]]),
 ('4.15', 'Bus Priority Corridors + Street Grid', [['p', 86]]),
 ('4.16', 'Outdoor Temperature Deviation; Pollution Risk Index', [['p', 157]]),
 ('4.17', 'Unemployment Rate; Poverty Rate; Median Household Income', [['p', 186], ['p', 188]]),
 ('4.18', 'Median Age; Population Change', [['m', '1.2'], ['m', '1.8']]),
 ('4.19', 'Life Expectancy; Access to Healthcare', [['m', '2.1'], ['m', '2.2']]),
 ('4.20', 'Housing Unit Change; Median Rent Change', [['m', '4.3'], ['m', '4.4']]),
 ('4.21', 'Housing Tenure; Rent Burden', [['m', '4.5'], ['m', '4.6']]),
 ('4.22', 'Overcrowded Households; Vacant Units', [['m', '4.7'], ['m', '4.8']]),
 ('4.23', 'Future Floodplain; Stormwater Flooding', [['m', '6.1'], ['m', '6.2']]),
 ('4.24', 'Street Types; Commute to Work by Driving', [['m', '7.7'], ['m', '7.8']]),
 ('4.25', 'Commute to Work by Transit; No Vehicles Available', [['m', '7.9'], ['m', '7.10']]),
 ('4.26', 'Motor Vehicle Collisions: Pedestrians; Cyclists', [['m', '7.11'], ['m', '7.12']]),
]
mids = {m['id'] for m in B['maps']}
for _, _, tg in APX:
    for k, v in tg:
        assert k == 'p' or v in mids, v

out = {
 'docs': [
  {'fy': 'FY2027', 'date': 'November 13, 2025', 'approved': 'approved unanimously at the November 2025 Full Board meeting',
   'priorities': [P1, P2, P3]},
  {'fy': 'FY2026', 'date': 'November 14, 2024', 'approved': 'approved unanimously at the November 2024 Full Board meeting',
   'priorities': ['Additional Housing', 'Climate Resilience', 'Comprehensive Transportation Assessment', 'Greater Access to Social Services']},
 ],
 'cite27': 'According to the Office of the Brooklyn Borough President, CD6 is below its targets for density in areas suitable for more housing, relative to most Brooklyn neighborhoods.',
 'items': [{'k': k, 'c': c, 'pr': pr, 't': t, 'x': x, 'y26': (None if y26 is None else {'t': y26[0], 'x': y26[1]}), 'u25': u25, 'u23': u23}
           for k, c, pr, t, x, y26, u25, u23 in ITEMS],
 'only26': [{'c': C3, 't': 'Cannabis Licenses', 'x': 'Increase outreach and program support to accelerate the licensing of unlicensed marijuana retail stores throughout the district, especially for census tracts classified by New York State as "Communities Disproportionately Impacted" by cannabis enforcement, which historically have been located in Red Hook and Gowanus.'}],
 'apx': [{'n': n, 't': t, 'to': tg} for n, t, tg in APX],
}
json.dump(out, open(os.path.join(ROOT, 'bkcompplan/needs.json'), 'w'), ensure_ascii=False, indent=0)
print(len(ITEMS), 'items;', sum(1 for i in ITEMS if i[6]), 'with 2025;', sum(1 for i in ITEMS if i[7]), 'with 2023;', sum(1 for i in ITEMS if i[5]), 'also FY2026')
