#!/usr/bin/env python3
"""A Google Street View photo of the place, for Directory listings with no logo or photo.

Reads a list of profile slugs (JSON) and the Street View Static API key from the file named in SV_KEY_FILE.
For each: the free metadata call first; where Google has an outdoor panorama, the picture is saved as
logos/sv-<slug>.jpg and recorded in data/cb6-audit/street-view.json. Listings Google has nothing for are
recorded in data/cb6-audit/street-view-none.json with the status it returned."""
import json, os, sys, io, urllib.parse, urllib.request, concurrent.futures as cf
from PIL import Image

A = 'data/cb6-audit'; LOGOS = 'app/data/civic/orgs/logos'; PROF = 'app/data/civic/orgs/orgs-profiles.json'
KEY = open(os.environ['SV_KEY_FILE']).read().strip()
B = 'https://maps.googleapis.com/maps/api/streetview'


def get(url):
    for i in range(3):
        try:
            return urllib.request.urlopen(url, timeout=40).read()
        except Exception as ex:
            err = ex
    raise err


def where(p):
    a = (p.get('addr') or '').strip()
    if a:
        return ', '.join(x for x in (a, (p.get('cityline') or '').strip() or 'New York, NY') if x)
    if p.get('lat') and p.get('lng'):
        return '%s,%s' % (p['lat'], p['lng'])
    return ''


def one(p):
    loc = where(p)
    if not loc: return p['slug'], None, 'NO_ADDRESS'
    q = urllib.parse.urlencode({'location': loc, 'source': 'outdoor', 'key': KEY})
    try:
        m = json.loads(get(B + '/metadata?' + q))
        if m.get('status') != 'OK': return p['slug'], None, m.get('status')
        q = urllib.parse.urlencode({'size': '640x640', 'fov': 70, 'pitch': 5, 'location': loc, 'source': 'outdoor', 'key': KEY})
        im = Image.open(io.BytesIO(get(B + '?' + q))).convert('RGB').resize((256, 256), Image.LANCZOS)
        fn = 'sv-%s.jpg' % p['slug']
        im.save(os.path.join(LOGOS, fn), quality=88)
        return p['slug'], {'file': fn, 'from': 'Google Street View of %s, %s' % (loc, m.get('date', '')), 'pano': m.get('pano_id', '')}, 'OK'
    except Exception as ex:
        return p['slug'], None, 'ERROR ' + type(ex).__name__


def main():
    todo = set(json.load(open(sys.argv[1])))
    SVF = os.path.join(A, 'street-view.json'); NF = os.path.join(A, 'street-view-none.json')
    SV = json.load(open(SVF)); NONE = json.load(open(NF)) if os.path.exists(NF) else {}
    P = [p for p in json.load(open(PROF))['profiles'] if p['slug'] in todo and p['slug'] not in SV and not str(NONE.get(p['slug'], 'ERROR')).startswith(('ZERO', 'NOT_FOUND', 'NO_ADDRESS'))]
    print(len(P), 'to ask', flush=True); n = 0
    with cf.ThreadPoolExecutor(12) as ex:
        for s, v, st in ex.map(one, P):
            n += 1
            if v: SV[s] = v; NONE.pop(s, None)
            else: NONE[s] = st
            if n % 500 == 0:
                print(n, len(SV), flush=True)
                json.dump(SV, open(SVF, 'w'), indent=0, ensure_ascii=False); json.dump(NONE, open(NF, 'w'), indent=0)
    json.dump(SV, open(SVF, 'w'), indent=0, ensure_ascii=False); json.dump(NONE, open(NF, 'w'), indent=0)
    import collections
    print(len(SV), 'photos on file;', collections.Counter(NONE.values()).most_common())


if __name__ == '__main__':
    main()
