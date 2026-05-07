#!/usr/bin/env python3
"""
Fetch College Scorecard field-of-study data and flatten it for the app.

Data source:
https://collegescorecard.ed.gov/data/api/

This script reads the cleaned institution file, requests nested 4-digit CIP
program records for those institutions, and writes a compact CSV the Streamlit
app can join back to college rows.
"""

import csv
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path


BASE_URL = "https://api.data.gov/ed/collegescorecard/v1/schools"
API_KEY = os.environ.get("COLLEGE_SCORECARD_API_KEY", "DEMO_KEY")
PER_PAGE = 100
DEFAULT_MAX_PAGES = "3" if API_KEY == "DEMO_KEY" else "80"
MAX_PAGES = int(os.environ.get("PROGRAM_MAX_PAGES", DEFAULT_MAX_PAGES))

ROOT = Path(__file__).resolve().parents[1]
SCHOOL_PATH = ROOT / "data" / "processed" / "college_roi_clean.csv"
RAW_PATH = ROOT / "data" / "raw" / "college_programs_api_raw.jsonl"
CLEAN_PATH = ROOT / "data" / "processed" / "college_programs_clean.csv"

FIELDS = [
    "id",
    "school.name",
    "latest.programs.cip_4_digit",
]

OUTPUT_COLUMNS = [
    "unit_id",
    "school_name",
    "cip_code",
    "program_title",
    "credential_level",
    "credential_title",
    "awards_latest",
    "awards_previous",
    "earnings_1yr",
    "earnings_4yr",
    "earnings_5yr",
    "earnings_highest_1yr",
    "earnings_highest_2yr",
    "earnings_highest_3yr",
    "national_earnings_4yr",
    "program_median_debt",
    "program_debt_payment",
    "program_debt_count",
    "debt_to_earnings_1yr",
    "program_data_points",
]


def as_float(value):
    if value in (None, "PrivacySuppressed", "NULL", "null", ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def as_int(value):
    number = as_float(value)
    if number is None:
        return None
    return int(number)


def nested_get(value, path):
    current = value
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def school_ids():
    with SCHOOL_PATH.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        ids = [row["unit_id"] for row in reader if row.get("unit_id")]
    return ids


def fetch_page(unit_ids, page):
    params = {
        "api_key": API_KEY,
        "fields": ",".join(FIELDS),
        "keys_nested": "true",
        "all_programs_nested": "true",
        "per_page": PER_PAGE,
        "page": page,
        "id": ",".join(unit_ids),
    }
    url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def flatten_program(school_record, program):
    credential = program.get("credential") or {}
    earnings = program.get("earnings") or {}
    debt = program.get("debt") or {}
    counts = program.get("counts") or {}
    staff_debt = nested_get(debt, ["staff_grad_plus", "all", "eval_inst"]) or {}

    earnings_1yr = as_float(nested_get(earnings, ["1_yr", "overall_median_earnings"]))
    earnings_4yr = as_float(nested_get(earnings, ["4_yr", "overall_median_earnings"]))
    earnings_5yr = as_float(nested_get(earnings, ["5_yr", "overall_median_earnings"]))
    highest_1yr = as_float(nested_get(earnings, ["highest", "1_yr", "overall_median_earnings"]))
    highest_2yr = as_float(nested_get(earnings, ["highest", "2_yr", "overall_median_earnings"]))
    highest_3yr = as_float(nested_get(earnings, ["highest", "3_yr", "overall_median_earnings"]))
    median_debt = as_float(staff_debt.get("median"))
    debt_to_earnings = None
    if median_debt is not None and earnings_1yr and earnings_1yr > 0:
        debt_to_earnings = median_debt / earnings_1yr

    data_points = sum(
        value is not None
        for value in [
            earnings_1yr,
            earnings_4yr,
            earnings_5yr,
            highest_1yr,
            highest_2yr,
            highest_3yr,
            median_debt,
            as_int(counts.get("ipeds_awards1")),
        ]
    )

    return {
        "unit_id": as_int(program.get("unit_id") or school_record.get("id")),
        "school_name": school_record.get("school", {}).get("name") or school_record.get("school.name"),
        "cip_code": program.get("code"),
        "program_title": program.get("title"),
        "credential_level": as_int(credential.get("level")),
        "credential_title": credential.get("title"),
        "awards_latest": as_int(counts.get("ipeds_awards2")),
        "awards_previous": as_int(counts.get("ipeds_awards1")),
        "earnings_1yr": earnings_1yr,
        "earnings_4yr": earnings_4yr,
        "earnings_5yr": earnings_5yr,
        "earnings_highest_1yr": highest_1yr,
        "earnings_highest_2yr": highest_2yr,
        "earnings_highest_3yr": highest_3yr,
        "national_earnings_4yr": as_float(nested_get(earnings, ["4_yr", "overall_median_earnings_national"])),
        "program_median_debt": median_debt,
        "program_debt_payment": as_float(staff_debt.get("median_payment")),
        "program_debt_count": as_int(staff_debt.get("count")),
        "debt_to_earnings_1yr": debt_to_earnings,
        "program_data_points": data_points,
    }


def main():
    ids = school_ids()
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    CLEAN_PATH.parent.mkdir(parents=True, exist_ok=True)

    all_schools = []
    with RAW_PATH.open("w", encoding="utf-8") as raw_file:
        for page in range(MAX_PAGES):
            start = page * PER_PAGE
            page_ids = ids[start:start + PER_PAGE]
            if not page_ids:
                break
            payload = fetch_page(page_ids, page=0)
            records = payload.get("results", [])
            for record in records:
                raw_file.write(json.dumps(record) + "\n")
            all_schools.extend(records)
            print(f"Fetched program data for {len(all_schools):,} schools")
            time.sleep(0.2)

    rows = []
    for school in all_schools:
        programs = nested_get(school, ["latest", "programs", "cip_4_digit"]) or []
        for program in programs:
            rows.append(flatten_program(school, program))

    # Bachelor's rows are the most relevant to the current app, which defaults
    # to bachelor's institutions, but keep other credentials in the CSV so the
    # app can expand later.
    rows = [row for row in rows if row["program_title"] and row["credential_level"]]
    rows.sort(
        key=lambda row: (
            row["credential_level"] != 3,
            row["school_name"] or "",
            row["program_title"] or "",
        )
    )

    with CLEAN_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows):,} program rows to {CLEAN_PATH}")
    print("Tip: set COLLEGE_SCORECARD_API_KEY and PROGRAM_MAX_PAGES for a larger pull.")


if __name__ == "__main__":
    main()
