"""Download a reproducible monthly snapshot from NYC Open Data.

The source table contains transaction-level property sales.  This script
requests a monthly-by-borough aggregation so the repository stays compact
while preserving the demand signal used by the notebook.
"""

from __future__ import annotations

from pathlib import Path
import json

import pandas as pd
import requests
import urllib3


SOURCE_URL = "https://data.cityofnewyork.us/resource/w2pb-icbu.json"
OUTPUT_PATH = Path("nyc_property_sales_monthly_by_borough.csv")
METADATA_PATH = Path("snapshot_metadata.json")
QUERY = {
    "$select": (
        "date_extract_y(sale_date) as year, "
        "date_extract_m(sale_date) as month, borough, "
        "count(*) as sales_count, median(sale_price) as median_sale_price"
    ),
    "$where": "sale_price > 0",
    "$group": "date_extract_y(sale_date), date_extract_m(sale_date), borough",
    "$order": "year, month, borough",
    "$limit": 5000,
}


def main() -> None:
    # Some managed environments intercept HTTPS certificates.  A normal
    # verified request is attempted first; the fallback keeps the script
    # usable for the public endpoint in those environments.
    try:
        response = requests.get(SOURCE_URL, params=QUERY, timeout=120)
    except requests.exceptions.SSLError:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        response = requests.get(SOURCE_URL, params=QUERY, timeout=120, verify=False)
    if response.status_code >= 400:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        response = requests.get(SOURCE_URL, params=QUERY, timeout=120, verify=False)
    response.raise_for_status()
    records = response.json()
    if not records:
        raise RuntimeError("The NYC Open Data query returned no records.")

    frame = pd.DataFrame(records)
    frame["year"] = frame["year"].astype(int)
    frame["month"] = frame["month"].astype(int)
    frame["borough"] = frame["borough"].astype(str)
    frame["sales_count"] = frame["sales_count"].astype(int)
    frame["median_sale_price"] = pd.to_numeric(frame["median_sale_price"])
    frame["month_start"] = pd.to_datetime(
        frame["year"].astype(str) + "-" + frame["month"].astype(str) + "-01"
    )
    frame = frame.sort_values(["month_start", "borough"])
    frame = frame[
        [
            "month_start",
            "year",
            "month",
            "borough",
            "sales_count",
            "median_sale_price",
        ]
    ]
    frame.to_csv(OUTPUT_PATH, index=False)

    metadata = {
        "source_url": SOURCE_URL,
        "source_dataset": "NYC Citywide Annualized Calendar Sales Update (w2pb-icbu)",
        "query": QUERY,
        "snapshot_created_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "rows": int(len(frame)),
        "period_start": str(frame["month_start"].min().date()),
        "period_end": str(frame["month_start"].max().date()),
        "note": "Aggregated from transaction-level records with sale_price > 0.",
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Saved {len(frame):,} rows to {OUTPUT_PATH}")
    print(f"Period: {metadata['period_start']} to {metadata['period_end']}")


if __name__ == "__main__":
    main()
