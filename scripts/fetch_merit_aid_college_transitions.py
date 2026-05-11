#!/usr/bin/env python3
"""
Fetch merit-aid data from College Transitions' public Average Merit Aid table.

Source:
    https://www.collegetransitions.com/dataverse/merit-aid/

The table is compiled by College Transitions from institutional Common Data Set
reports. The app treats these fields as an opportunity signal, not as a
guaranteed scholarship estimate.
"""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "processed" / "college_merit_aid_clean.csv"
SOURCE_URL = "https://www.collegetransitions.com/dataverse/merit-aid/"
SOURCE_YEAR = "2024-25 Common Data Set; College Transitions table updated November 2025"


def clean_money(value):
    text = str(value).replace("$", "").replace(",", "").replace("*", "").strip()
    if text.lower() in {"", "nan", "not reported"}:
        return None
    return pd.to_numeric(text, errors="coerce")


def clean_percent(value):
    text = str(value).replace("%", "").replace("*", "").strip()
    if text.lower() in {"", "nan", "not reported"}:
        return None
    return pd.to_numeric(text, errors="coerce")


def main():
    tables = pd.read_html(SOURCE_URL)
    if not tables:
        raise RuntimeError("No tables found on College Transitions merit-aid page.")

    table = max(tables, key=len).copy()
    table.columns = [str(column).strip() for column in table.columns]

    rename_map = {
        "Unit ID": "unit_id",
        "Institution": "institution",
        "Cost of Attendance (In-State)": "merit_cost_of_attendance_in_state",
        "Cost of Attendance (Out-of-State)": "merit_cost_of_attendance_out_of_state",
        "Percent Receiving Merit Aid (Freshmen w/o Need)": "merit_aid_percent",
        "Average Merit Award (Freshmen w/o Need)": "merit_aid_average_award",
    }
    table = table.rename(columns=rename_map)
    required = set(rename_map.values())
    missing = sorted(required - set(table.columns))
    if missing:
        raise RuntimeError(f"Missing expected columns: {missing}")

    clean = table[
        [
            "unit_id",
            "institution",
            "merit_cost_of_attendance_in_state",
            "merit_cost_of_attendance_out_of_state",
            "merit_aid_percent",
            "merit_aid_average_award",
        ]
    ].copy()
    clean["unit_id"] = pd.to_numeric(clean["unit_id"], errors="coerce")
    clean["merit_cost_of_attendance_in_state"] = clean["merit_cost_of_attendance_in_state"].apply(clean_money)
    clean["merit_cost_of_attendance_out_of_state"] = clean["merit_cost_of_attendance_out_of_state"].apply(clean_money)
    clean["merit_aid_percent"] = clean["merit_aid_percent"].apply(clean_percent)
    clean["merit_aid_average_award"] = clean["merit_aid_average_award"].apply(clean_money)
    clean["merit_aid_source_year"] = SOURCE_YEAR
    clean["merit_aid_source_url"] = SOURCE_URL
    clean = clean.dropna(subset=["unit_id"]).drop_duplicates("unit_id")
    clean["unit_id"] = clean["unit_id"].astype(int)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    clean.to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {len(clean):,} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
