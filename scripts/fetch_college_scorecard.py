#!/usr/bin/env python3
"""
Fetch and clean a starter College Scorecard dataset for College Value Lab.

Data source:
https://collegescorecard.ed.gov/data/api/

The default DEMO_KEY is enough for a small starter pull. For heavier use,
request a free key from data.gov and set COLLEGE_SCORECARD_API_KEY.
"""

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
DEFAULT_MAX_PAGES = "10" if API_KEY == "DEMO_KEY" else "70"
MAX_PAGES = int(os.environ.get("MAX_PAGES", DEFAULT_MAX_PAGES))

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "college_scorecard_api_raw.jsonl"
CLEAN_PATH = ROOT / "data" / "processed" / "college_roi_clean.csv"

FIELDS = [
    "id",
    "school.name",
    "school.city",
    "school.state",
    "school.ownership",
    "school.school_url",
    "school.price_calculator_url",
    "school.degrees_awarded.predominant",
    "latest.student.size",
    "latest.admissions.admission_rate.overall",
    "latest.cost.attendance.academic_year",
    "latest.cost.tuition.in_state",
    "latest.cost.tuition.out_of_state",
    "latest.cost.avg_net_price.overall",
    "latest.cost.net_price.public.by_income_level.0-30000",
    "latest.cost.net_price.public.by_income_level.30001-48000",
    "latest.cost.net_price.public.by_income_level.48001-75000",
    "latest.cost.net_price.public.by_income_level.75001-110000",
    "latest.cost.net_price.public.by_income_level.110001-plus",
    "latest.cost.net_price.private.by_income_level.0-30000",
    "latest.cost.net_price.private.by_income_level.30001-48000",
    "latest.cost.net_price.private.by_income_level.48001-75000",
    "latest.cost.net_price.private.by_income_level.75001-110000",
    "latest.cost.net_price.private.by_income_level.110001-plus",
    "latest.completion.rate_suppressed.overall",
    "latest.completion.rate_suppressed.four_year",
    "latest.completion.rate_suppressed.lt_four_year",
    "latest.completion.completion_rate_4yr_100nt",
    "latest.completion.completion_rate_less_than_4yr_100nt",
    "latest.aid.median_debt.completers.overall",
    "latest.earnings.1_yr_after_completion.median",
    "latest.earnings.4_yrs_after_completion.median",
    "latest.earnings.5_yrs_after_completion.median",
    "latest.earnings.6_yrs_after_entry.median",
    "latest.earnings.10_yrs_after_entry.median",
]

OUTPUT_COLUMNS = [
    "unit_id",
    "name",
    "city",
    "state",
    "ownership",
    "predominant_degree",
    "school_url",
    "net_price_calculator_url",
    "student_size",
    "admission_rate",
    "annual_cost",
    "tuition_in_state",
    "tuition_out_of_state",
    "avg_net_price",
    "net_price_income_0_30000",
    "net_price_income_30001_48000",
    "net_price_income_48001_75000",
    "net_price_income_75001_110000",
    "net_price_income_110001_plus",
    "graduation_rate",
    "on_time_completion_rate",
    "median_debt",
    "median_earnings_1yr_after_completion",
    "median_earnings_4yr_after_completion",
    "median_earnings_5yr_after_completion",
    "median_earnings_6yr_after_entry",
    "median_earnings_10yr",
    "estimated_4yr_net_cost",
    "earnings_to_cost_ratio",
    "roi_index",
]

OWNERSHIP_LABELS = {
    1: "Public",
    2: "Private nonprofit",
    3: "Private for-profit",
}

DEGREE_LABELS = {
    0: "Not classified",
    1: "Certificate",
    2: "Associate",
    3: "Bachelor",
    4: "Graduate",
}


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


def get(record, field):
    return record.get(field)


def fetch_page(page):
    params = {
        "api_key": API_KEY,
        "fields": ",".join(FIELDS),
        "per_page": PER_PAGE,
        "page": page,
        "school.operating": 1,
        "school.degrees_awarded.predominant": "2,3,4",
    }
    url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        if error.code == 429:
            print("Hit the API rate limit. Cleaning the records fetched so far.")
            return None
        raise


def clean_record(record):
    net_price = as_float(get(record, "latest.cost.avg_net_price.overall"))
    annual_cost = as_float(get(record, "latest.cost.attendance.academic_year"))
    earnings_1yr_completion = as_float(get(record, "latest.earnings.1_yr_after_completion.median"))
    earnings_4yr_completion = as_float(get(record, "latest.earnings.4_yrs_after_completion.median"))
    earnings_5yr_completion = as_float(get(record, "latest.earnings.5_yrs_after_completion.median"))
    earnings_6yr_entry = as_float(get(record, "latest.earnings.6_yrs_after_entry.median"))
    earnings = as_float(get(record, "latest.earnings.10_yrs_after_entry.median"))
    degree_code = as_int(get(record, "school.degrees_awarded.predominant"))
    if degree_code == 3:
        grad_rate = as_float(get(record, "latest.completion.rate_suppressed.four_year"))
        on_time_completion_rate = as_float(get(record, "latest.completion.completion_rate_4yr_100nt"))
    elif degree_code == 2:
        grad_rate = as_float(get(record, "latest.completion.rate_suppressed.lt_four_year"))
        on_time_completion_rate = as_float(get(record, "latest.completion.completion_rate_less_than_4yr_100nt"))
    else:
        grad_rate = as_float(get(record, "latest.completion.rate_suppressed.overall"))
        on_time_completion_rate = None
    median_debt = as_float(get(record, "latest.aid.median_debt.completers.overall"))

    estimated_4yr_net_cost = net_price * 4 if net_price is not None else None
    earnings_to_cost_ratio = None
    roi_index = None

    if earnings and estimated_4yr_net_cost and estimated_4yr_net_cost > 0:
        # A small number of colleges report extremely low average net prices.
        # The floor keeps the starter index from being dominated by tiny denominators.
        cost_for_ratio = max(estimated_4yr_net_cost, 20000)
        earnings_to_cost_ratio = earnings / cost_for_ratio
        roi_index = earnings_to_cost_ratio * (grad_rate if grad_rate is not None else 1)

    ownership_code = as_int(get(record, "school.ownership"))
    ownership_label = OWNERSHIP_LABELS.get(ownership_code, ownership_code)
    net_price_group = "public" if ownership_label == "Public" else "private"

    return {
        "unit_id": as_int(get(record, "id")),
        "name": get(record, "school.name"),
        "city": get(record, "school.city"),
        "state": get(record, "school.state"),
        "ownership": ownership_label,
        "predominant_degree": DEGREE_LABELS.get(degree_code, degree_code),
        "school_url": get(record, "school.school_url"),
        "net_price_calculator_url": get(record, "school.price_calculator_url"),
        "student_size": as_int(get(record, "latest.student.size")),
        "admission_rate": as_float(get(record, "latest.admissions.admission_rate.overall")),
        "annual_cost": annual_cost,
        "tuition_in_state": as_float(get(record, "latest.cost.tuition.in_state")),
        "tuition_out_of_state": as_float(get(record, "latest.cost.tuition.out_of_state")),
        "avg_net_price": net_price,
        "net_price_income_0_30000": as_float(get(record, f"latest.cost.net_price.{net_price_group}.by_income_level.0-30000")),
        "net_price_income_30001_48000": as_float(get(record, f"latest.cost.net_price.{net_price_group}.by_income_level.30001-48000")),
        "net_price_income_48001_75000": as_float(get(record, f"latest.cost.net_price.{net_price_group}.by_income_level.48001-75000")),
        "net_price_income_75001_110000": as_float(get(record, f"latest.cost.net_price.{net_price_group}.by_income_level.75001-110000")),
        "net_price_income_110001_plus": as_float(get(record, f"latest.cost.net_price.{net_price_group}.by_income_level.110001-plus")),
        "graduation_rate": grad_rate,
        "on_time_completion_rate": on_time_completion_rate,
        "median_debt": median_debt,
        "median_earnings_1yr_after_completion": earnings_1yr_completion,
        "median_earnings_4yr_after_completion": earnings_4yr_completion,
        "median_earnings_5yr_after_completion": earnings_5yr_completion,
        "median_earnings_6yr_after_entry": earnings_6yr_entry,
        "median_earnings_10yr": earnings,
        "estimated_4yr_net_cost": estimated_4yr_net_cost,
        "earnings_to_cost_ratio": earnings_to_cost_ratio,
        "roi_index": roi_index,
    }


def has_core_roi_data(row):
    return (
        row["name"]
        and row["avg_net_price"] is not None
        and row["graduation_rate"] is not None
        and row["median_earnings_10yr"] is not None
        and row["student_size"] is not None
        and row["student_size"] >= 250
    )


def main():
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    CLEAN_PATH.parent.mkdir(parents=True, exist_ok=True)

    all_records = []
    total = None

    with RAW_PATH.open("w", encoding="utf-8") as raw_file:
        for page in range(MAX_PAGES):
            payload = fetch_page(page)
            if payload is None:
                break
            metadata = payload.get("metadata", {})
            total = metadata.get("total", total)
            records = payload.get("results", [])
            if not records:
                break

            for record in records:
                raw_file.write(json.dumps(record) + "\n")
            all_records.extend(records)

            print(f"Fetched page {page + 1}: {len(all_records)} / {total or '?'} records")
            if total and len(all_records) >= total:
                break
            time.sleep(0.2)

    cleaned = [clean_record(record) for record in all_records]
    cleaned = [row for row in cleaned if has_core_roi_data(row)]
    cleaned.sort(key=lambda row: row["roi_index"] or 0, reverse=True)

    with CLEAN_PATH.open("w", newline="", encoding="utf-8") as clean_file:
        writer = csv.DictWriter(clean_file, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(cleaned)

    print(f"Wrote {len(cleaned)} cleaned rows to {CLEAN_PATH}")
    print(f"Raw API records saved to {RAW_PATH}")


if __name__ == "__main__":
    main()
