#!/usr/bin/env python3
"""Clean the cached College Scorecard API JSONL into the dashboard CSV."""

import csv
import json

from fetch_college_scorecard import (
    CLEAN_PATH,
    OUTPUT_COLUMNS,
    RAW_PATH,
    clean_record,
    has_core_roi_data,
)


def main():
    records = []
    with RAW_PATH.open(encoding="utf-8") as raw_file:
        for line in raw_file:
            if line.strip():
                records.append(json.loads(line))

    cleaned = [clean_record(record) for record in records]
    cleaned = [row for row in cleaned if has_core_roi_data(row)]
    cleaned.sort(key=lambda row: row["roi_index"] or 0, reverse=True)

    CLEAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CLEAN_PATH.open("w", newline="", encoding="utf-8") as clean_file:
        writer = csv.DictWriter(clean_file, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(cleaned)

    print(f"Read {len(records)} cached raw records")
    print(f"Wrote {len(cleaned)} cleaned rows to {CLEAN_PATH}")


if __name__ == "__main__":
    main()
