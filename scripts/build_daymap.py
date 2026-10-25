"""The day map (bkcb6.app/daymap/): every event on the CB6 community calendar with a place, on a map.

Reads the CB6 calendar the apps carry (app/data/civic/cal/calendar-bk.json, built from bkcb6.app/calendar.html by
scripts/build_app_calendar.mjs; group "cb6" only, so it matches the calendar page), geocodes each event's location
with NYC Planning Labs geosearch (inside Brooklyn unless the location names another borough), after checking the
site's culture places and a few hand-checked places by name, and writes data/daymap/events.json. Locations are looked
up once: data/daymap/geocache.json keeps every answer.

python3 scripts/build_daymap.py"""
import json, os, re, subprocess, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'app/data/civic/cal/calendar-bk.json')
OUT_DIR = os.path.join(ROOT, 'data/daymap')
OUT = os.path.join(OUT_DIR, 'events.json')
CACHE = os.path.join(OUT_DIR, 'geocache.json')
# NYC, generously; anything outside is a bad match
BOX = (40.49, -74.27, 40.92, -73.68)
ADDR = re.compile(r'\b\d+[A-Za-z]?\s+[A-Z0-9][\w.]*\s+(St|Street|Ave|Avenue|Place|Pl|Road|Rd)\b')
# Places the calendar names by a business name only, looked up at their address (checked by hand)
ALIAS = {'principles coffee house': '139 9th Street, Brooklyn, NY', 'industry city': '220 36th Street, Brooklyn, NY'}
VIRTUAL = re.compile(r'\b(zoom|virtual|online|webinar|teleconference|livestream|remote)\b', re.I)


def slugify(s):
    s = (s or '').lower()
    s = re.sub(r"[‘’']", '', s)
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s[:80]


# Places the calendar names without an address, where geosearch finds the wrong thing (checked by hand)
KNOWN = {
    'washington park': (40.673212, -73.984731),        # Washington Park, Park Slope, beside the Old Stone House
    'carroll gardens library': (40.680311, -73.996449), # 396 Clinton Street
    'cobble hill park': (40.687862, -73.996236),
    'brooklyn bridge park': (40.700232, -73.996783),
    'coffey park': (40.677822, -74.007927),
    'gowanus dredgers canoe club boathouse': (40.67923, -73.99539),  # 165 2nd Street, Gowanus
    'nyc city hall': (40.712772, -74.006058),
}
# Locations too vague to pin (a whole avenue, a room with no building)
VAGUE = re.compile(r'^(5th avenue \u00b7 park slope|parish hall)$', re.I)
ORD = {'1': '1st', '2': '2nd', '3': '3rd'}


def ordinal(m):
    n = m.group(1)
    suf = 'th' if n[-2:] in ('11', '12', '13') else {'1': 'st', '2': 'nd', '3': 'rd'}.get(n[-1], 'th')
    return n + suf + ' ' + m.group(2)
OTHER_BORO = re.compile(r'manhattan|city hall|governors island|queens|bronx|staten island|upper east side|sunset park|industry city', re.I)
BK = {'boundary.rect.min_lat': 40.566, 'boundary.rect.min_lon': -74.05, 'boundary.rect.max_lat': 40.74, 'boundary.rect.max_lon': -73.83}


def known(loc):
    low = loc.lower()
    for p in re.split(r'\s+[\u00b7|]\s+|,', low):
        p = p.strip()
        if p in PLACES:
            return PLACES[p]
    for k, v in PLACES.items():
        if len(k) > 8 and low.startswith(k):
            return v
    return None


def clean(q):
    q = re.sub(r'\s*\((.*?)\)', '', q)
    q = re.sub(r'^(starts at|outside the|outside|meet outside the|meet at)\s+', '', q, flags=re.I)
    q = re.sub(r'\s*\u2192.*$', '', q)                 # "139 9th St, Gowanus -> Upper East Side": the start
    q = q.replace(', United States', '').replace('&', 'and')
    q = re.sub(r'\b(\d+) (Street|Avenue|St|Ave)\b', ordinal, q)   # "8 Street" -> "8th Street"
    q = re.sub(r' at (\d)', r' and \1', q)
    q = re.sub(r'\b(Ste|Suite|Floor|Fl)\.? ?\w+,?', '', q)
    m = re.match(r'^(.+?) between (.+?) and (.+?)(,|$)', q)  # a street segment: its first corner
    if m:
        q = m.group(1) + ' and ' + m.group(2)
    m = re.match(r'^([^,]+), (.+?) to (.+)$', q)            # "8 Street, 8 Avenue to Prospect Park West"
    if m and not re.match(r'^\d+\s+\w', m.group(1).replace(' Street', ' St')) or (m and re.search(r'(street|place|avenue)$', m.group(1), re.I)):
        q = m.group(1) + ' and ' + m.group(2)
    return q.strip(' ,')


def queries(loc):
    """The strings to try for one location, best first."""
    loc = re.sub(r'\s+', ' ', loc).strip()
    for k, v in ALIAS.items():
        if loc.lower().startswith(k):
            return [v]
    parts = [p.strip() for p in re.split(r'\s+[\u00b7|]\s+', loc) if p.strip()]
    out = [p for p in parts if re.match(r'^\d', p)] + parts[::-1] + [loc]
    seen, res = set(), []
    for q in out:
        q = clean(q)
        if not q or q.lower() in seen:
            continue
        seen.add(q.lower())
        res.append(q if re.search(r'brooklyn|manhattan|queens|bronx|staten|new york|\bny\b|governors island', q, re.I) else q + ', Brooklyn, NY')
    return res


NUMW = {'first': '1', 'second': '2', 'third': '3', 'fourth': '4', 'fifth': '5', 'sixth': '6', 'seventh': '7', 'eighth': '8', 'ninth': '9', 'tenth': '10'}
GENERIC = {'street', 'st', 'avenue', 'ave', 'place', 'pl', 'road', 'rd', 'the', 'of', 'and', 'at', 'brooklyn', 'ny', 'nyc',
           'new', 'york', 'usa', 'west', 'east', 'w', 'e', 'n', 's', 'north', 'south', 'boulevard', 'blvd', 'lane', 'ln'}
HOODS = re.compile(r'^(brooklyn|red hook|park slope|gowanus|carroll gardens|cobble hill|boerum hill|columbia waterfront|'
                   r'south brooklyn|tbd|brooklyn tbd)$', re.I)


def words(s):
    out = set()
    for w in re.findall(r"[a-z0-9]+", s.lower().replace('’', '').replace("'", '')):
        w = NUMW.get(w, w)
        w = re.sub(r'^(\d+)(st|nd|rd|th|[a-z])$', r'\1', w)
        if w not in GENERIC and len(w) > 1:
            out.add(w)
    return out


def plausible(q, hit):
    """A geosearch answer counts only when it names what was asked: every word of the place's name (before the first
    comma) is in the answer's label. Stops "Park Slope" landing on the Park Slope Armory and "5th Avenue Street
    Festival" on a housing project in Brownsville."""
    if not hit:
        return False
    segs = [x.strip() for x in re.split(r'\s+[\u00b7|]\s+|,', q) if x.strip()]
    core = next((x for x in segs if re.match(r'^\d', x)), segs[0] if segs else '')
    if HOODS.match(core.strip()):
        return False
    need = words(core)
    return bool(need) and need <= words(hit['label'])


def geosearch(q, anywhere):
    prm = {'text': q, 'size': 1}
    if not anywhere:
        prm.update(BK)
    u = 'https://geosearch.planninglabs.nyc/v2/search?' + urllib.parse.urlencode(prm)
    with urllib.request.urlopen(u, timeout=20) as r:
        d = json.load(r)
    time.sleep(0.15)
    f = (d.get('features') or [None])[0]
    if not f:
        return None
    lng, lat = f['geometry']['coordinates']
    if not (BOX[0] < lat < BOX[2] and BOX[1] < lng < BOX[3]):
        return None
    if not anywhere and f['properties'].get('borough') not in (None, 'Brooklyn'):
        return None
    return {'lat': round(lat, 6), 'lng': round(lng, 6), 'label': f['properties'].get('label', '')}


GEOCLIENT_KEY = 'b913bdfb9c47466589d0f08c99c75b21'


def corners(loc):
    """A street corner named in the location ("8 Street, 8 Avenue to Prospect Park West", "Pioneer Street between
    Van Brunt Street and Imlay Street", "4th St & 5th Ave", "5th Avenue at 4th Street"), as pairs of street names,
    every one the location could mean, best first."""
    out = []
    for p in re.split(r'\s+[\u00b7|]\s+', loc):
        p = re.sub(r'\s*\(.*?\)', '', p).strip()
        p = re.sub(r'^(meet at|meet outside|starts at)\s+', '', p, flags=re.I)
        m = (re.match(r'^(.+?) between (.+?) (?:and|&) (.+?)(,|$)', p) or re.match(r'^([^,]+?) from (.+?) to (.+?)(,|$)', p)
             or re.match(r'^([^,]+), (.+?) to (.+)$', p))
        if m:
            b = m.group(2).strip()
            if not re.search(r'\b(st|street|ave|avenue|pl|place|road|rd|boulevard|blvd|parkway|plaza|west|east)\.?$', b, re.I):
                b += ' Street'
            out.append((m.group(1).strip(), b))
            continue
        p = re.sub(r',\s*(Park Slope|Gowanus|Red Hook|Carroll Gardens|Cobble Hill|Brooklyn).*$', '', p)
        m = re.match(r'^(?:.*,\s*)?([^,]+?) (?:&|and|at) ([^,]+)$', p)
        if m and not re.match(r'^\d+[A-Za-z]?\s+[A-Z][a-z]+\s', m.group(1)):
            out.append((m.group(1).strip(), m.group(2).strip()))
    return out


def geoclient(a, b):
    u = 'https://api.nyc.gov/geoclient/v2/intersection.json?' + urllib.parse.urlencode(
        {'crossStreetOne': a, 'crossStreetTwo': b, 'borough': 'Brooklyn'})
    req = urllib.request.Request(u, headers={'Ocp-Apim-Subscription-Key': GEOCLIENT_KEY})
    with urllib.request.urlopen(req, timeout=20) as r:
        d = json.load(r).get('intersection', {})
    time.sleep(0.15)
    if d.get('latitude') and d.get('longitude'):
        return {'lat': round(float(d['latitude']), 6), 'lng': round(float(d['longitude']), 6), 'label': a + ' and ' + b}
    return None


def main():
    cal = json.load(open(SRC))
    types = cal.get('types', {})
    os.makedirs(OUT_DIR, exist_ok=True)
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    # every place on the site's culture map, by name, plus the hand-checked ones
    global PLACES
    PLACES = {k: v for k, v in KNOWN.items()}
    for p in json.load(open(os.path.join(ROOT, 'data/culture-places.json'))):
        if p.get('lat') and p.get('lng') and not p.get('approx') and p['lng'] < -73.855 and p['lat'] < 40.74:
            PLACES.setdefault(p['name'].lower(), (p['lat'], p['lng']))
    out, looked, placed = [], 0, 0
    # the app calendar file starts on the day it was built; earlier days come straight from calendar.html
    first = min((e['d'] for e in cal['events'] if e.get('g') == 'cb6'), default='9999')
    past = json.loads(subprocess.run(['node', os.path.join(ROOT, 'scripts/daymap_past.mjs'), first],
                                     capture_output=True, text=True, check=True).stdout)
    for p in past:
        p['g'], p['past'] = 'cb6', True
    for e in past + cal['events']:
        if e.get('g') != 'cb6':
            continue
        loc = (e.get('loc') or '').strip()
        rec = {'d': e['d'], 'l': e['l'], 't': e.get('t', ''), 'e': e.get('e', ''), 'loc': loc,
               'org': e.get('org', ''), 'k': e.get('k', ''), 'ev': e['d'] + '-' + slugify(e['l'])}
        if e.get('past'):
            for a in ('fl', 'ic', 'h'):
                if e.get(a):
                    rec[a] = e[a]
        ty = {} if e.get('past') else types.get(e.get('ty') or '', {})
        if ty.get('icon'):
            rec['ic'] = '/app/data/civic/cal/icons/' + ty['icon']
        if e.get('f') and not e.get('past'):
            rec['fl'] = '/app/data/civic/cal/flyers/' + e['f']
        if e.get('h') and not e.get('past'):
            rec['h'] = e['h']
        if loc and not (VIRTUAL.search(loc) and not ADDR.search(loc)) and not VAGUE.match(loc) and not re.search(r'agenda for the location', loc, re.I):
            hit = known(loc)
            hit = {'lat': hit[0], 'lng': hit[1]} if hit else None
            anywhere = bool(OTHER_BORO.search(loc))
            c = None if hit or anywhere or re.search(r'\d+[A-Za-z]?\s+[A-Z][a-z]+.*\b(St|Street|Ave|Avenue|Place|Pl)\b\.?,? ?(Brooklyn|NY|$)', loc) and not re.search(r' to | between ', loc) else corners(loc)
            for a, b in (c or []):
                key = 'X|' + a + '|' + b
                if key not in cache:
                    try:
                        cache[key] = geoclient(a, b)
                        looked += 1
                    except Exception:
                        continue
                hit = cache.get(key)
                if hit:
                    break
            for q in ([] if hit else queries(loc)):
                key = ('*' if anywhere else '') + q
                if key not in cache:
                    try:
                        cache[key] = geosearch(q, anywhere)
                    except Exception:
                        continue
                    looked += 1
                if plausible(q, cache[key]):
                    hit = cache[key]
                    break
            if hit:
                rec['lat'], rec['lng'] = hit['lat'], hit['lng']
                placed += 1
        out.append(rec)
    out.sort(key=lambda r: (r['d'], r['l']))
    json.dump({'built': time.strftime('%Y-%m-%d'), 'events': out}, open(OUT, 'w'), ensure_ascii=False, separators=(',', ':'))
    json.dump(cache, open(CACHE, 'w'), ensure_ascii=False, indent=0, sort_keys=True)
    print(json.dumps({'events': len(out), 'placed': placed, 'looked_up': looked}))


if __name__ == '__main__':
    main()
