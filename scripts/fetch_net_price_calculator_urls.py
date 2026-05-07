#!/usr/bin/env python3
"""Backfill school website and net price calculator URLs into the cleaned CSV."""

import csv
import json
import os
import time
import urllib.parse
import urllib.request
from urllib.error import HTTPError
from pathlib import Path


BASE_URL = "https://api.data.gov/ed/collegescorecard/v1/schools"
API_KEY = os.environ.get("COLLEGE_SCORECARD_API_KEY", "DEMO_KEY")
PER_PAGE = 100

ROOT = Path(__file__).resolve().parents[1]
CLEAN_PATH = ROOT / "data" / "processed" / "college_roi_clean.csv"


def fetch_urls(unit_ids):
    lookup = {}
    for start in range(0, len(unit_ids), PER_PAGE):
        batch = unit_ids[start:start + PER_PAGE]
        params = {
            "api_key": API_KEY,
            "fields": "id,school.school_url,school.price_calculator_url",
            "per_page": PER_PAGE,
            "id": ",".join(batch),
        }
        url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
        try:
            with urllib.request.urlopen(url, timeout=45) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            if error.code == 429:
                print("Hit the API rate limit. Writing the URL records fetched so far.")
                break
            raise
        for record in payload.get("results", []):
            lookup[str(record.get("id"))] = {
                "school_url": record.get("school.school_url"),
                "net_price_calculator_url": record.get("school.price_calculator_url"),
            }
        print(f"Fetched URL data for {min(start + PER_PAGE, len(unit_ids)):,} / {len(unit_ids):,} schools")
        time.sleep(0.15)
    return lookup


def main():
    with CLEAN_PATH.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    for column in ["school_url", "net_price_calculator_url"]:
        if column not in fieldnames:
            fieldnames.append(column)

    unit_ids = [row["unit_id"] for row in rows if row.get("unit_id")]
    lookup = fetch_urls(unit_ids)

    updated = 0
    for row in rows:
        urls = lookup.get(row.get("unit_id"), {})
        for column in ["school_url", "net_price_calculator_url"]:
            if urls.get(column):
                row[column] = urls[column]
                updated += 1

    with CLEAN_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    calculator_count = sum(bool(row.get("net_price_calculator_url")) for row in rows)
    print(f"Updated {updated:,} URL fields")
    print(f"Rows with net price calculator URLs: {calculator_count:,} / {len(rows):,}")


if __name__ == "__main__":
    main()
