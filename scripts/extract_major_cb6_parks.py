import json
from pathlib import Path

SOURCE = Path('/home/ubuntu/work/bkcb6_repo_1776697502/Parks_Properties_20260414.geojson')
OUTPUT = Path('/home/ubuntu/work/bkcb6_repo_1776697502/major_parks_cb6.geojson')

TARGET_EXACT = {
    'Prospect Park',
    'Louis Valentino, Jr. Park and Pier'
}
TARGET_CONTAINS = [
    'Red Hook Park'
]

features = []
with SOURCE.open() as f:
    for line in f:
        line = line.strip()
        if not line or not line.startswith('{'):
            continue
        if line.endswith(','):
            line = line[:-1]
        try:
            feature = json.loads(line)
        except json.JSONDecodeError:
            continue
        props = feature.get('properties', {})
        name = (props.get('signname') or props.get('name311') or '').strip()
        if not name:
            continue
        if name in TARGET_EXACT or any(token in name for token in TARGET_CONTAINS):
            features.append({
                'type': 'Feature',
                'geometry': feature.get('geometry'),
                'properties': {
                    'name': name,
                    'typecategory': props.get('typecategory', ''),
                    'subcategory': props.get('subcategory', ''),
                    'location': props.get('location', props.get('address', '')),
                    'acres': props.get('acres', '')
                }
            })

OUTPUT.write_text(json.dumps({'type': 'FeatureCollection', 'features': features}))
print(f'wrote {len(features)} features to {OUTPUT}')
