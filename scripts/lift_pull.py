import json, os, ssl, urllib.request, urllib.parse, traceback

OUT = 'data/lift'
os.makedirs(OUT, exist_ok=True)
LOG = []
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = {'User-Agent': 'Mozilla/5.0 (compatible; bkcb6-civic-data/1.0)'}


def log(*a):
    s = ' '.join(str(x) for x in a)
    print(s, flush=True)
    LOG.append(s)


def get(url, timeout=120):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=timeout, context=CTX).read()


def getjson(url, timeout=120):
    return json.loads(get(url, timeout))


WEBMAP = '70bd4dc0d246454d82e0784a8ab9c265'
OTHER = {
    '01800cd22b1647849dbbf4b3a086db97': 'Actively Used Land',
    '08a084ba1a7d4542b6c57859179cddbb': 'Residential Land',
    'b2169f40d13b478a9f9b4cfcf3010dd6': 'Vacant Property',
    'c3866494abf7438d907282a3dee912d7': 'All Uses',
    'e6710c01704e45878df09bc1f83748ec': 'Cultural and Recreational Use',
}


def walk_urls(node, found, title=None):
    """Recursively collect every service url in a web map definition."""
    if isinstance(node, dict):
        t = node.get('title') or node.get('name') or title
        u = node.get('url')
        if isinstance(u, str) and ('FeatureServer' in u or 'MapServer' in u):
            found.append((t, u))
        for k, v in node.items():
            if k != 'url':
                walk_urls(v, found, t)
    elif isinstance(node, list):
        for v in node:
            walk_urls(v, found, title)


def expand(title, url):
    """A service root with no layer index gets expanded into its layers."""
    tail = url.rstrip('/').rsplit('/', 1)[-1]
    if tail.isdigit():
        return [(title, url)]
    try:
        meta = getjson(url + '?f=json', 60)
    except Exception as e:
        log('   meta failed', url, e)
        return [(title, url)]
    out = []
    for lyr in (meta.get('layers') or []) + (meta.get('tables') or []):
        out.append((lyr.get('name') or title, '%s/%s' % (url.rstrip('/'), lyr.get('id'))))
    return out or [(title, url)]


def query_all(url):
    """Page through a layer and return every feature with all fields."""
    feats = []
    off = 0
    while True:
        q = url.rstrip('/') + '/query?' + urllib.parse.urlencode({
            'where': '1=1', 'outFields': '*', 'returnGeometry': 'true',
            'outSR': '4326', 'f': 'json',
            'resultOffset': off, 'resultRecordCount': 1000,
        })
        j = getjson(q)
        if j.get('error'):
            raise RuntimeError(json.dumps(j['error'])[:400])
        fs = j.get('features') or []
        feats.extend(fs)
        log('   +%d (total %d)' % (len(fs), len(feats)))
        if len(fs) < 1000 or not j.get('exceededTransferLimit'):
            if len(fs) < 1000:
                break
        off += 1000
        if off > 200000:
            break
    return feats


def do_map(item, label):
    url = 'https://www.arcgis.com/sharing/rest/content/items/%s/data?f=json' % item
    raw = get(url, 90)
    open(os.path.join(OUT, 'webmap-%s.json' % item), 'wb').write(raw)
    d = json.loads(raw)
    found = []
    walk_urls(d, found)
    log('%s (%s): %d raw urls' % (label, item, len(found)))
    layers = []
    seen = set()
    for t, u in found:
        for t2, u2 in expand(t, u):
            if u2 not in seen:
                seen.add(u2)
                layers.append((t2, u2))
    for t, u in layers:
        log('   layer:', t, '->', u)
    return layers


results = {}
try:
    layers = do_map(WEBMAP, 'LIFT Tracker Map')
except Exception:
    log('tracker map failed')
    log(traceback.format_exc())
    layers = []

if not layers:
    for item, label in OTHER.items():
        try:
            layers += do_map(item, label)
        except Exception:
            log('failed', label)
            log(traceback.format_exc())

for t, u in layers:
    log('pulling', t, u)
    try:
        feats = query_all(u)
    except Exception as e:
        log('   query failed:', e)
        continue
    if not feats:
        log('   empty')
        continue
    key = u.replace('https://', '').replace('/', '_')
    results[key] = {'title': t, 'url': u, 'count': len(feats)}
    json.dump({'title': t, 'url': u, 'features': feats},
              open(os.path.join(OUT, 'raw-%s.json' % key[-60:]), 'w'))
    log('   saved %d features, fields: %s' % (
        len(feats), ','.join(sorted(feats[0].get('attributes', {}).keys()))))

json.dump(results, open(os.path.join(OUT, 'index.json'), 'w'), indent=1)
open(os.path.join(OUT, 'log.txt'), 'w').write('\n'.join(LOG))
log('done', len(results), 'layers with data')
