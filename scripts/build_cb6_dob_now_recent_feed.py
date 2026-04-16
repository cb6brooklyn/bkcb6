#!/usr/bin/env python3
import json
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE_URL = "https://data.cityofnewyork.us/resource/rbx6-tga4.json"
SELECT_FIELDS = [
    "issued_date",
    "house_no",
    "street_name",
    "work_type",
    "applicant_first_name",
    "applicant_last_name",
    "permit_status",
    "job_filing_number",
    "tracking_number",
    "block",
    "lot",
    "bin",
    "latitude",
    "longitude",
]
WHERE = "borough='BROOKLYN' AND c_b_no='306' AND issued_date >= '2026-01-01T00:00:00.000'"
PAGE_SIZE = 50000

ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / "data" / "cb6_dob_now_recent.json"


def fetch_all_rows() -> list[dict]:
    rows: list[dict] = []
    offset = 0
    session = requests.Session()
    while True:
        params = {
            "$select": ",".join(SELECT_FIELDS),
            "$where": WHERE,
            "$order": "issued_date DESC, job_filing_number ASC",
            "$limit": str(PAGE_SIZE),
            "$offset": str(offset),
        }
        url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
        page = session.get(url, timeout=60)
        page.raise_for_status()
        batch = page.json()
        if not isinstance(batch, list):
            raise RuntimeError(f"Unexpected response type: {type(batch)!r}")
        rows.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return rows


def clean_row(row: dict) -> dict:
    return {
        "issued_date": row.get("issued_date", ""),
        "house_no": row.get("house_no", ""),
        "street_name": row.get("street_name", ""),
        "work_type": row.get("work_type", ""),
        "applicant_first_name": row.get("applicant_first_name", ""),
        "applicant_last_name": row.get("applicant_last_name", ""),
        "permit_status": row.get("permit_status", ""),
        "job_filing_number": row.get("job_filing_number", ""),
        "tracking_number": row.get("tracking_number", ""),
        "block": row.get("block", ""),
        "lot": row.get("lot", ""),
        "bin": row.get("bin", ""),
        "latitude": row.get("latitude", ""),
        "longitude": row.get("longitude", ""),
    }


def main() -> None:
    rows = [clean_row(row) for row in fetch_all_rows()]
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "NYC Open Data rbx6-tga4",
        "description": "CB6 Brooklyn DOB NOW permits issued on or after 2026-01-01.",
        "record_count": len(rows),
        "rows": rows,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {len(rows)} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
