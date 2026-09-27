"""Context for the corridor's crash and 311 counts: the same counts for all of CB6 and Brooklyn, and street miles
to turn them into rates. Adds a 'context' key to data/bergendean/summary.json."""
import json, os, urllib.request, urllib.parse, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'data', 'bergendean', 'summary.json'); S = json.load(open(P))
NYC = 'https://data.cityofnewyork.us/resource/'
def url(ds, q): return NYC + ds + '.json?' + urllib.parse.urlencode(q)
def get(u): return json.load(urllib.request.urlopen(u, timeout=600))
END = (datetime.date.fromisoformat(S['s311_last']) + datetime.timedelta(days=1)).isoformat() + 'T00:00:00'  # the day after the corridor's last 311 record, so the periods match
W = S['wkt']['cb6']
C = {}
# street miles from the NYC Street Centerline: rw_type 1 = streets (not highways, bridges, paths, driveways)
u = url('inkn-q76z', {'$select': 'sum(segmentlength) as ft,count(*) as n', '$where': "boroughcode='3' AND rw_type='1'"}); r = get(u)[0]
C['bk_street_mi'] = {'url': u, 'mi': round(float(r['ft']) / 5280, 1), 'segments': int(r['n'])}
u = url('inkn-q76z', {'$select': 'sum(segmentlength) as ft,count(*) as n', '$where': "rw_type='1' AND within_polygon(the_geom,'%s')" % W}); r = get(u)[0]
C['cb6_street_mi'] = {'url': u, 'mi': round(float(r['ft']) / 5280, 1), 'segments': int(r['n'])}
# 311 in CB6 and Brooklyn, same dates as the corridor counts
u = url('erm2-nwe9', {'$select': 'count(*) as n', '$where': f"created_date>='2020-01-01T00:00:00' AND created_date<'{END}' AND within_polygon(location,'{W}')"}); C['cb6_311'] = {'url': u, 'n': int(get(u)[0]['n'])}
u = url('erm2-nwe9', {'$select': 'complaint_type,count(*) as n', '$where': f"created_date>='2020-01-01T00:00:00' AND created_date<'{END}' AND within_polygon(location,'{W}')", '$group': 'complaint_type', '$order': 'n DESC', '$limit': 5}); C['cb6_311_types'] = {'url': u, 'types': [[x['complaint_type'], int(x['n'])] for x in get(u)]}
u = url('erm2-nwe9', {'$select': 'count(*) as n', '$where': f"created_date>='2020-01-01T00:00:00' AND created_date<'{END}' AND borough='BROOKLYN'"}); C['bk_311'] = {'url': u, 'n': int(get(u)[0]['n'])}
u = url('erm2-nwe9', {'$select': 'complaint_type,count(*) as n', '$where': f"created_date>='2020-01-01T00:00:00' AND created_date<'{END}' AND borough='BROOKLYN'", '$group': 'complaint_type', '$order': 'n DESC', '$limit': 5}); C['bk_311_types'] = {'url': u, 'types': [[x['complaint_type'], int(x['n'])] for x in get(u)]}
# crashes in Brooklyn by the borough field (many crash records carry no borough, so this is a floor), same dates as the corridor
u = url('h9gi-nx95', {'$select': 'count(*) as crashes,sum(number_of_persons_injured) as injured,sum(number_of_cyclist_injured) as cyc_inj,sum(number_of_persons_killed) as killed', '$where': f"crash_date>='2020-01-01T00:00:00' AND crash_date<'{END}' AND borough='BROOKLYN'"}); r = get(u)[0]
C['bk_crash'] = {'url': u, 'crashes': int(r['crashes']), 'injured': int(float(r['injured'])), 'cyc_inj': int(float(r['cyc_inj'])), 'killed': int(float(r['killed']))}
u = url('h9gi-nx95', {'$select': 'count(*) as n', '$where': f"crash_date>='2020-01-01T00:00:00' AND crash_date<'{END}' AND borough IS NULL"}); C['crash_noboro'] = {'url': u, 'n': int(get(u)[0]['n'])}
u = url('h9gi-nx95', {'$select': 'count(*) as n', '$where': f"crash_date>='2020-01-01T00:00:00' AND crash_date<'{END}'"}); C['crash_all'] = {'url': u, 'n': int(get(u)[0]['n'])}
# periods in years
d0 = datetime.date(2020, 1, 1)
C['crash_years'] = round((datetime.date.fromisoformat(S['crash_last']) - d0).days / 365.25, 2)
C['s311_years'] = round((datetime.date.fromisoformat(S['s311_last']) - d0).days / 365.25, 2)
S['context'] = C
json.dump(S, open(P, 'w'), separators=(',', ':'))
print(json.dumps({k: (v if not isinstance(v, dict) else {kk: vv for kk, vv in v.items() if kk != 'url'}) for k, v in C.items()}))
