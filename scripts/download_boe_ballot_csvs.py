#!/usr/bin/env python3
from pathlib import Path
import requests

ROOT = Path('/home/ubuntu/bkcb6_publish_20260414_2000')
OUT = ROOT / 'tmp_elections'
OUT.mkdir(parents=True, exist_ok=True)

URLS = {
    'ballot_q2_edlevel.csv': 'https://www.vote.nyc/sites/default/files/pdf/election_results/2025/20251104General%20Election/00050200000Citywide%20Proposed%20Charter%20Amendment_%20Fast%20Track%20Affordable%20Housing%20to%20Build%20More%20Affordable%20Housing%20Across%20the%20City%20Citywide%20EDLevel.csv',
    'ballot_q3_edlevel.csv': 'https://www.vote.nyc/sites/default/files/pdf/election_results/2025/20251104General%20Election/00050300000Citywide%20Proposed%20Charter%20Amendment_%20Simplify%20Review%20of%20Modest%20Housing%20and%20Infrastructure%20Projects%20Citywide%20EDLevel.csv',
    'ballot_q4_edlevel.csv': 'https://www.vote.nyc/sites/default/files/pdf/election_results/2025/20251104General%20Election/00050400000Citywide%20Proposed%20Charter%20Amendment_%20Establish%20an%20Affordable%20Housing%20Appeals%20Board%20with%20Council,%20Borough,%20and%20Citywide%20Representation%20%20Citywide%20EDLevel.csv',
}

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0'})

for filename, url in URLS.items():
    resp = session.get(url, timeout=60, verify=False)
    resp.raise_for_status()
    path = OUT / filename
    path.write_bytes(resp.content)
    print(filename, len(resp.content))
