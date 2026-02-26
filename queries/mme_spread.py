"""
MME (Morphine Milligram Equivalents) Spread Query for IQVIA Dataset.

PURPOSE
=======
Get the spread of MME across IQVIA opioid prescription data:
  - 5-number summary (min, Q1, median, Q3, max)
  - Range
  - Data for geographic spread map

DATA SOURCE
===========
Uses the county-level IQVIA panel (avg_mme_per_unit = qty-weighted MME per unit).
Loads from output/county/iqvia_county_year_panel.csv or iqvia_cdc_county_merged.csv.

Run standalone:  python -m queries.mme_spread
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.db_utils import export_to_csv

BASE = os.path.dirname(os.path.dirname(__file__))
IQVIA_COUNTY_CSV = os.path.join(BASE, "output", "county", "iqvia_county_year_panel.csv")
MERGED_CSV = os.path.join(BASE, "output", "county", "iqvia_cdc_county_merged.csv")


def load_mme_data() -> pd.DataFrame:
    """
    Load county-level MME data from IQVIA panel.
    Prefers merged panel; falls back to IQVIA-only county panel.
    """
    for path in [MERGED_CSV, IQVIA_COUNTY_CSV]:
        if os.path.exists(path):
            df = pd.read_csv(path, dtype={"county_fips": str, "state": str})
            df["county_fips"] = df["county_fips"].astype(str).str.zfill(5)
            if "avg_mme_per_unit" in df.columns:
                return df
    raise FileNotFoundError(
        f"No IQVIA county panel found.\n"
        f"  Expected: {IQVIA_COUNTY_CSV} or {MERGED_CSV}\n"
        f"  Run: python main.py county"
    )


def five_number_summary(series: pd.Series) -> dict:
    """Compute 5-number summary: min, Q1, median, Q3, max."""
    valid = series.dropna()
    if valid.empty:
        return {"min": np.nan, "q1": np.nan, "median": np.nan, "q3": np.nan, "max": np.nan}
    return {
        "min": float(valid.min()),
        "q1": float(valid.quantile(0.25)),
        "median": float(valid.median()),
        "q3": float(valid.quantile(0.75)),
        "max": float(valid.max()),
    }


def mme_spread_summary(df: pd.DataFrame = None) -> dict:
    """
    Compute MME spread summary from IQVIA county panel.

    Returns dict with:
      - five_number: {min, q1, median, q3, max}
      - range: max - min
      - n_counties: number of county-year observations
      - n_unique_counties: unique counties
    """
    if df is None:
        df = load_mme_data()

    mme = df["avg_mme_per_unit"]
    fns = five_number_summary(mme)
    rng = fns["max"] - fns["min"] if not np.isnan(fns["max"]) else np.nan

    return {
        "five_number": fns,
        "range": rng,
        "n_county_years": len(mme.dropna()),
        "n_unique_counties": df["county_fips"].nunique(),
        "years": sorted(df["year"].dropna().unique().astype(int).tolist()),
    }


def print_mme_summary(summary: dict = None) -> None:
    """Print formatted 5-number summary and range."""
    if summary is None:
        df = load_mme_data()
        summary = mme_spread_summary(df)

    fn = summary["five_number"]
    print("\n" + "=" * 50)
    print("  MME SPREAD — 5-NUMBER SUMMARY (IQVIA)")
    print("  Metric: avg_mme_per_unit (qty-weighted MME per prescription unit)")
    print("=" * 50)
    print(f"  Min:      {fn['min']:.2f}")
    print(f"  Q1:       {fn['q1']:.2f}")
    print(f"  Median:   {fn['median']:.2f}")
    print(f"  Q3:       {fn['q3']:.2f}")
    print(f"  Max:      {fn['max']:.2f}")
    print("-" * 50)
    print(f"  Range:    {summary['range']:.2f}  (max - min)")
    print("-" * 50)
    print(f"  County-years: {summary['n_county_years']:,}")
    print(f"  Unique counties: {summary['n_unique_counties']:,}")
    print(f"  Years: {summary['years']}")
    print("=" * 50 + "\n")


def run_all(save: bool = True) -> pd.DataFrame:
    """
    Load MME data, compute summary, print, and return panel for mapping.
    """
    df = load_mme_data()
    summary = mme_spread_summary(df)
    print_mme_summary(summary)

    if save:
        # Save summary stats to CSV
        fn = summary["five_number"]
        summary_df = pd.DataFrame([
            {"statistic": "min", "value": fn["min"]},
            {"statistic": "q1", "value": fn["q1"]},
            {"statistic": "median", "value": fn["median"]},
            {"statistic": "q3", "value": fn["q3"]},
            {"statistic": "max", "value": fn["max"]},
            {"statistic": "range", "value": summary["range"]},
        ])
        export_to_csv(summary_df, "mme_spread_summary.csv", subdir="county")

    return df


# ─────────────────────────────────────────────────────────────────────────────
# SQL query (for reference / direct DB use)
# ─────────────────────────────────────────────────────────────────────────────
MME_SPREAD_SQL_STATE = """
-- State-level MME spread (single year, fast)
-- Replace {year} with e.g. 2015
SELECT
    p.state,
    SUM(m.total_qty * COALESCE(d.mme_per_unit, 0)) / NULLIF(SUM(m.total_qty), 0) AS avg_mme_per_unit,
    SUM(m.total_qty * COALESCE(d.mme_per_unit, 0)) / 1000.0 AS total_mme,
    SUM(m.total_rx) / 1000.0 AS total_rx
FROM main m
JOIN prescriber_limited p ON m.prescriber_key = p.prescriber_key
JOIN drug d ON m.pg = d.pg
WHERE m.pg IN (SELECT pg FROM drug WHERE usc LIKE '022%%')
  AND m.year = {year}
GROUP BY p.state;
"""


if __name__ == "__main__":
    df = run_all(save=True)
    print(f"  Panel ready for map: {len(df):,} rows")
