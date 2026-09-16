#!/usr/bin/env python3
"""Write data/vzr/cb6-311.json: street and traffic related 311 complaints in Brooklyn Community District 6,
the last 12 months, from NYC 311 Service Requests (Open Data erm2-nwe9), with coordinates.

Groups match the toggles on /visionzerocb6/:
  parking  Illegal Parking, Blocked Driveway
  street   Street Condition, Sidewalk Condition, Curb Condition, Street Light Condition, Highway Condition
  signal   Traffic Signal Condition, Street Sign damaged, missing or dangling, Bus Stop Shelter Complaint
  vehicle  Abandoned Vehicle, Derelict Vehicles, Noise - Vehicle, Traffic, Illegal Idling, Bike/Roller/Skate Chronic
"""
import json, os, datetime, urllib.request, urllib.parse, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = 'HvFoIfzodzpRML7a1104Ca2tM'
GROUPS = {
    'parking': ['Illegal Parking', 'Blocked Driveway'],
    'street': ['Street Condition', 'Sidewalk Condition', 'Curb Condition', 'Street Light Condition', 'Highway Condition'],
    'signal': ['Traffic Signal Condition', 'Street Sign - Damaged', 'Street Sign - Missing', 'Street Sign - Dangling', 'Bus Stop Shelter Complaint', 'Broken Muni Meter'],
    'vehicle': ['Abandoned Vehicle', 'Derelict Vehicles', 'Noise - Vehicle', 'Traffic', 'Illegal Idling', 'Bike/Roller/Skate Chronic'],
}
TYPES = [t for v in GROUPS.values() for t in v]
GOF = {t: g for g, v in GROUPS.items() for t in v}

since = (datetime.date.today() - datetime.timedelta(days=365)).isoformat()
where = ("community_board='06 BROOKLYN' AND created_date>='%s' AND latitude IS NOT NULL AND complaint_type in(%s)"
         % (since, ','.join("'" + t + "'" for t in TYPES)))
rows, off = [], 0
while True:
    q = urllib.parse.urlencode({'$select': 'complaint_type,descriptor,created_date,latitude,longitude,incident_address,status',
                                '$where': where, '$order': 'created_date', '$limit': 50000, '$offset': off, '$$app_token': TOKEN})
    batch = json.load(urllib.request.urlopen('https://data.cityofnewyork.us/resource/erm2-nwe9.json?' + q, timeout=300))
    rows += batch
    if len(batch) < 50000: break
    off += 50000

types = sorted({r['complaint_type'] for r in rows})
ti = {t: i for i, t in enumerate(types)}
out = [[round(float(r['latitude']), 5), round(float(r['longitude']), 5), ti[r['complaint_type']],
        r['created_date'][:10], (r.get('descriptor') or '')[:60], (r.get('incident_address') or '')[:50]] for r in rows]
counts = collections.Counter(GOF[r['complaint_type']] for r in rows)
json.dump({'generated': datetime.date.today().isoformat(), 'since': since,
           'source': 'NYC 311 Service Requests (Open Data erm2-nwe9), complaints in Brooklyn Community District 6 with coordinates, ' + since + ' to ' + datetime.date.today().isoformat(),
           'types': types, 'groups': {g: [ti[t] for t in v if t in ti] for g, v in GROUPS.items()},
           'counts': dict(counts), 'total': len(out), 'rows': out},
          open(os.path.join(ROOT, 'data', 'vzr', 'cb6-311.json'), 'w'), separators=(',', ':'))
print(len(out), 'complaints', dict(counts))
print(collections.Counter(r['complaint_type'] for r in rows).most_common())
