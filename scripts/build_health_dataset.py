import json
from collections import Counter
from pathlib import Path

SRC = Path('/tmp/health_overpass.json')
OUT = Path('/home/ubuntu/work/bkcb6_repo_1776697502/data/health_services_cb6.json')
OUT.parent.mkdir(parents=True, exist_ok=True)

CATEGORY_MAP = {
    'hospital': 'Hospital / emergency care',
    'clinic': 'Clinic / urgent care',
    'doctors': 'Medical office',
    'pharmacy': 'Pharmacy',
    'social_facility': 'Social services',
}

EXCLUDED_AMENITIES = {'veterinary', 'dentist'}
EXCLUDED_NAMES = {
    'Blue Ridge Labs @Robin Hood',
}

with SRC.open() as f:
    raw = json.load(f)

records = []
seen = set()
for el in raw.get('elements', []):
    tags = el.get('tags', {})
    amenity = tags.get('amenity', '').strip()
    if amenity in EXCLUDED_AMENITIES:
        continue
    name = tags.get('name', '').strip()
    if not name or name in EXCLUDED_NAMES:
        continue
    lat = el.get('lat', el.get('center', {}).get('lat'))
    lon = el.get('lon', el.get('center', {}).get('lon'))
    if lat is None or lon is None:
        continue
    category = CATEGORY_MAP.get(amenity)
    if not category:
        continue
    specialty = tags.get('healthcare:speciality') or tags.get('social_facility') or tags.get('healthcare') or ''
    address_parts = [
        tags.get('addr:housenumber', '').strip(),
        tags.get('addr:street', '').strip(),
    ]
    address = ' '.join([p for p in address_parts if p]).strip()
    if tags.get('addr:postcode'):
        address = (address + ', Brooklyn, NY ' + tags['addr:postcode']).strip(', ')
    phone = tags.get('phone', '').strip()
    website = tags.get('website', '').strip()
    search_blob = ' | '.join(filter(None, [name, category, specialty, address]))
    key = (name.lower(), round(lat, 5), round(lon, 5))
    if key in seen:
        continue
    seen.add(key)
    records.append({
        'name': name,
        'category': category,
        'amenity': amenity,
        'specialty': specialty,
        'address': address,
        'phone': phone,
        'website': website,
        'lat': lat,
        'lon': lon,
        'search': search_blob.lower(),
    })

records.sort(key=lambda r: (r['category'], r['name']))
stats = Counter(r['category'] for r in records)
output = {
    'generated_from': 'OpenStreetMap Overpass API query for BKCB6 bounding area on 2026-04-20',
    'bbox': {'south': 40.660, 'west': -74.020, 'north': 40.690, 'east': -73.965},
    'total_sites': len(records),
    'stats': stats,
    'records': records,
}
with OUT.open('w') as f:
    json.dump(output, f, indent=2)

print(f'wrote {len(records)} records to {OUT}')
for category, count in stats.items():
    print(f'{category}: {count}')
