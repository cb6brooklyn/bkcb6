#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import shapefile
from pyproj import Transformer
from shapely.geometry import MultiPolygon, Polygon, shape
from shapely.ops import transform

ROOT = Path('/home/ubuntu/bkcb6_publish_20260414_2000')
CB_GEOJSON = ROOT / 'community-district-boundaries.geojson'
ED_SHP = ROOT / 'tmp_elections' / 'nyed_zip' / 'nyed_26a1' / 'nyed.shp'
OUT_DIR = ROOT / 'data'

QUESTION_META = {
    'Q2': {
        'slug': 'q2',
        'title': 'Question 2',
        'subtitle': 'Fast Track Affordable Housing',
        'csv': ROOT / 'tmp_elections' / 'ballot_q2_edlevel.csv',
    },
    'Q3': {
        'slug': 'q3',
        'title': 'Question 3',
        'subtitle': 'Simplify Review of Modest Housing',
        'csv': ROOT / 'tmp_elections' / 'ballot_q3_edlevel.csv',
    },
    'Q4': {
        'slug': 'q4',
        'title': 'Question 4',
        'subtitle': 'Affordable Housing Appeals Board',
        'csv': ROOT / 'tmp_elections' / 'ballot_q4_edlevel.csv',
    },
}

BOROUGHS = {
    '1': {'slug': 'manhattan', 'short': 'MN', 'name': 'Manhattan', 'valid_districts': set(range(1, 13))},
    '2': {'slug': 'bronx', 'short': 'BX', 'name': 'Bronx', 'valid_districts': set(range(1, 13))},
    '3': {'slug': 'brooklyn', 'short': 'BK', 'name': 'Brooklyn', 'valid_districts': set(range(1, 19))},
    '4': {'slug': 'queens', 'short': 'QN', 'name': 'Queens', 'valid_districts': set(range(1, 15))},
    '5': {'slug': 'statenisland', 'short': 'SI', 'name': 'Staten Island', 'valid_districts': set(range(1, 4))},
}

CSV_HEADER = [
    'AD', 'ED', 'County', 'EDAD Status', 'Event', 'Party/Independent Body',
    'Office/Position Title', 'District Key', 'VoteFor', 'Unit Name', 'Tally'
]

transformer = Transformer.from_crs('EPSG:4326', 'EPSG:2263', always_xy=True)


def normalize_boro_cd(raw: str) -> str:
    code = str(raw).strip()
    if code.endswith('.0'):
        code = code[:-2]
    if len(code) == 2:
        code = code[0] + code[1].zfill(2)
    return code


def label_from_boro_cd(boro_cd: str) -> str:
    borough = BOROUGHS[boro_cd[0]]
    district = int(boro_cd[1:])
    return f"{borough['short']}CB{district}"


def long_label_from_boro_cd(boro_cd: str) -> str:
    borough = BOROUGHS[boro_cd[0]]
    district = int(boro_cd[1:])
    return f"{borough['name']} Community Board {district}"


def pct(value: int, total: int) -> float:
    return round((value / total * 100.0) if total else 0.0, 1)


def build_ed_to_cb() -> dict[int, str]:
    cb_geo = json.loads(CB_GEOJSON.read_text(encoding='utf-8'))
    cb_polygons: dict[str, object] = {}
    for feat in cb_geo['features']:
        boro_cd = normalize_boro_cd(feat['properties']['boro_cd'])
        borough = BOROUGHS.get(boro_cd[0])
        district = int(boro_cd[1:]) if len(boro_cd) >= 3 else None
        if not borough or district not in borough['valid_districts']:
            continue
        geom = shape(feat['geometry'])
        cb_polygons[boro_cd] = transform(transformer.transform, geom)

    ed_to_cb: dict[int, str] = {}
    reader = shapefile.Reader(str(ED_SHP))
    for sr in reader.iterShapeRecords():
        elect_dist = int(sr.record[0])
        pts = sr.shape.points
        parts = list(sr.shape.parts) + [len(pts)]
        polys = []
        for i in range(len(parts) - 1):
            ring = pts[parts[i]:parts[i + 1]]
            if len(ring) >= 3:
                try:
                    polys.append(Polygon(ring))
                except Exception:
                    pass
        if not polys:
            continue
        geom = polys[0] if len(polys) == 1 else MultiPolygon(polys)
        centroid = geom.representative_point()
        for boro_cd, cb_geom in cb_polygons.items():
            if cb_geom.contains(centroid):
                ed_to_cb[elect_dist] = boro_cd
                break
    return ed_to_cb


def load_question_totals(csv_path: Path, ed_to_cb: dict[int, str]):
    cb_totals = defaultdict(lambda: {
        'yes': 0,
        'no': 0,
        'ed_results': defaultdict(lambda: {'yes': 0, 'no': 0}),
    })
    expected_cols = len(CSV_HEADER)
    with csv_path.open(newline='', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        for raw_row in reader:
            if len(raw_row) < expected_cols * 2:
                continue
            row = dict(zip(CSV_HEADER, raw_row[expected_cols:expected_cols * 2]))
            unit = (row.get('Unit Name') or '').strip().lower()
            if unit not in {'yes', 'no'}:
                continue
            try:
                ad = int(row['AD'])
                ed = int(row['ED'])
                tally = int(float(row['Tally'] or 0))
            except Exception:
                continue
            elect_dist = ad * 1000 + ed
            cb = ed_to_cb.get(elect_dist)
            if not cb:
                continue
            cb_totals[cb][unit] += tally
            cb_totals[cb]['ed_results'][elect_dist][unit] += tally
    return cb_totals


def build_question_payload(question_key: str, meta: dict, cb_geo: dict, ed_to_cb: dict):
    totals_by_cb = load_question_totals(meta['csv'], ed_to_cb)
    by_borough = {info['slug']: [] for info in BOROUGHS.values()}
    districts = {}
    max_margin = 0.0

    for feat in cb_geo['features']:
        boro_cd = normalize_boro_cd(feat['properties']['boro_cd'])
        borough = BOROUGHS.get(boro_cd[0])
        district_number = int(boro_cd[1:]) if len(boro_cd) >= 3 else None
        if not borough or district_number not in borough['valid_districts']:
            continue
        totals = totals_by_cb.get(boro_cd)
        if not totals:
            continue
        yes_votes = totals['yes']
        no_votes = totals['no']
        total_votes = yes_votes + no_votes
        winner = 'yes' if yes_votes >= no_votes else 'no'
        winner_name = 'Yes / Approve' if winner == 'yes' else 'No / Disapprove'
        loser_name = 'No / Disapprove' if winner == 'yes' else 'Yes / Approve'
        winner_votes = yes_votes if winner == 'yes' else no_votes
        loser_votes = no_votes if winner == 'yes' else yes_votes
        margin_pct = pct(winner_votes - loser_votes, total_votes)
        max_margin = max(max_margin, margin_pct)
        ed_results = totals['ed_results']
        winner_ed_count = sum(1 for vals in ed_results.values() if vals[winner] >= vals['no' if winner == 'yes' else 'yes'])
        summary = {
            'boro_cd': boro_cd,
            'borough_slug': borough['slug'],
            'borough_name': borough['name'],
            'district_number': district_number,
            'district_label': label_from_boro_cd(boro_cd),
            'district_name': long_label_from_boro_cd(boro_cd),
            'question': question_key,
            'question_title': meta['title'],
            'question_subtitle': meta['subtitle'],
            'winner': winner,
            'winner_name': winner_name,
            'loser_name': loser_name,
            'yes_votes': yes_votes,
            'no_votes': no_votes,
            'winner_votes': winner_votes,
            'loser_votes': loser_votes,
            'total_votes': total_votes,
            'yes_pct': pct(yes_votes, total_votes),
            'no_pct': pct(no_votes, total_votes),
            'margin_pct': round(margin_pct, 1),
            'winner_ed_count': winner_ed_count,
            'total_eds': len(ed_results),
        }
        by_borough[borough['slug']].append(summary)
        districts[boro_cd] = summary

    for slug, items in by_borough.items():
        items.sort(key=lambda item: item['district_number'])

    return {
        'question': question_key,
        'question_title': meta['title'],
        'question_subtitle': meta['subtitle'],
        'max_margin_pct': round(max_margin, 1),
        'boroughs': by_borough,
        'districts': districts,
    }


def main() -> None:
    cb_geo = json.loads(CB_GEOJSON.read_text(encoding='utf-8'))
    ed_to_cb = build_ed_to_cb()
    for question_key, meta in QUESTION_META.items():
        payload = build_question_payload(question_key, meta, cb_geo, ed_to_cb)
        out_path = OUT_DIR / f"ballot_{meta['slug']}_cb_winner_margin.json"
        out_path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
        district_count = sum(len(items) for items in payload['boroughs'].values())
        print(f"wrote {out_path} ({district_count} districts, max margin {payload['max_margin_pct']})")


if __name__ == '__main__':
    main()
