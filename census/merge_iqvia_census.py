"""
Merge IQVIA opioid prescription data with Census demographics.

Takes the aggregated IQVIA output (from queries/geographic.py or pre-saved
CSVs in output/) and joins it with the Census demographics DataFrame
produced by census/load_census.py.

The result is a single per-zip-code table with:
  - Opioid Rx counts (Medicaid & Non-Medicaid)
  - Medicaid enrollment from Census
  - Computed rates: Rx per 1,000 Medicaid enrollees, Rx per 1,000 non-Medicaid
  - Demographics: income, poverty %, race %

Run standalone:  python -m census.merge_iqvia_census
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import numpy as np
from utils.db_utils import export_to_csv
from census.load_census import load_all_census

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")


def _load_iqvia_zip_data() -> pd.DataFrame:
    """
    Load the IQVIA zip-level Medicaid vs Non-Medicaid data.
    Tries the pre-saved CSV first; if it doesn't exist, runs the query live.
    """
    csv_path = os.path.join(OUTPUT_DIR, "geo_zip_medicaid_vs_nonmedicaid.csv")
    if os.path.exists(csv_path):
        print(f"📂 Loading cached IQVIA zip data from {csv_path}")
        return pd.read_csv(csv_path, dtype={"zip_code": str})

    # Not cached yet — run the query (will take a while)
    print("⏳ No cached zip data found. Running IQVIA geographic query …")
    from queries.geographic import opioid_rx_by_zipcode_medicaid
    df = opioid_rx_by_zipcode_medicaid()
    export_to_csv(df, "geo_zip_medicaid_vs_nonmedicaid.csv")
    return df


def _load_iqvia_zip_pct() -> pd.DataFrame:
    """Load the Medicaid-% per zip CSV, or run the query."""
    csv_path = os.path.join(OUTPUT_DIR, "geo_zip_medicaid_pct.csv")
    if os.path.exists(csv_path):
        print(f"📂 Loading cached Medicaid-% zip data from {csv_path}")
        return pd.read_csv(csv_path, dtype={"zip_code": str})

    print("⏳ No cached zip-pct data found. Running query …")
    from queries.geographic import medicaid_pct_by_zipcode
    df = medicaid_pct_by_zipcode()
    export_to_csv(df, "geo_zip_medicaid_pct.csv")
    return df


def _pivot_iqvia(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot the IQVIA zip data from long (one row per zip × Medicaid status)
    to wide (one row per zip, with medicaid_rx / nonmedicaid_rx columns).
    """
    med = df[df["is_medicaid"] == "Medicaid"].copy()
    non = df[df["is_medicaid"] == "Non-Medicaid"].copy()

    med = med.rename(columns={
        "total_rx":        "medicaid_total_rx",
        "new_rx":          "medicaid_new_rx",
        "total_qty":       "medicaid_total_qty",
        "avg_mme":         "medicaid_avg_mme",
        "prescriber_count": "medicaid_prescriber_count",
    })[["zip_code", "state", "medicaid_total_rx", "medicaid_new_rx",
        "medicaid_total_qty", "medicaid_avg_mme", "medicaid_prescriber_count"]]

    non = non.rename(columns={
        "total_rx":        "nonmedicaid_total_rx",
        "new_rx":          "nonmedicaid_new_rx",
        "total_qty":       "nonmedicaid_total_qty",
        "avg_mme":         "nonmedicaid_avg_mme",
        "prescriber_count": "nonmedicaid_prescriber_count",
    })[["zip_code", "nonmedicaid_total_rx", "nonmedicaid_new_rx",
        "nonmedicaid_total_qty", "nonmedicaid_avg_mme", "nonmedicaid_prescriber_count"]]

    wide = med.merge(non, on="zip_code", how="outer")
    return wide


def merge_iqvia_census() -> pd.DataFrame:
    """
    Main merge function.

    Returns a DataFrame with one row per zip code containing:
      - IQVIA opioid Rx data (Medicaid & Non-Medicaid)
      - Census demographics
      - Computed rates (Rx per 1,000 enrollees)
    """
    # 1. Load IQVIA zip-level data
    iqvia_long = _load_iqvia_zip_data()
    iqvia_long["zip_code"] = iqvia_long["zip_code"].astype(str).str.zfill(5)
    iqvia_wide = _pivot_iqvia(iqvia_long)
    print(f"   IQVIA wide: {len(iqvia_wide):,} zip codes")

    # 2. Load Census demographics
    census = load_all_census()
    census["zip_code"] = census["zip_code"].astype(str).str.zfill(5)

    # 3. Merge on zip_code
    print("\n🔗 Merging IQVIA + Census on zip_code …")
    merged = iqvia_wide.merge(census, on="zip_code", how="inner")
    print(f"   Matched: {len(merged):,} zip codes")

    # 4. Compute per-capita rates
    # Medicaid opioid Rx per 1,000 Medicaid enrollees
    merged["medicaid_rx_per_1k_enrollees"] = np.where(
        merged["medicaid_enrolled"] > 0,
        (merged["medicaid_total_rx"] / merged["medicaid_enrolled"] * 1000).round(2),
        np.nan,
    )

    # Non-Medicaid opioid Rx per 1,000 non-Medicaid population
    merged["nonmedicaid_rx_per_1k_pop"] = np.where(
        merged["non_medicaid_pop"] > 0,
        (merged["nonmedicaid_total_rx"] / merged["non_medicaid_pop"] * 1000).round(2),
        np.nan,
    )

    # Ratio: how many times higher is one rate vs the other
    merged["rate_ratio_med_vs_nonmed"] = np.where(
        merged["nonmedicaid_rx_per_1k_pop"] > 0,
        (merged["medicaid_rx_per_1k_enrollees"] / merged["nonmedicaid_rx_per_1k_pop"]).round(3),
        np.nan,
    )

    # Average MME difference
    merged["mme_diff_med_minus_nonmed"] = (
        merged["medicaid_avg_mme"] - merged["nonmedicaid_avg_mme"]
    ).round(3)

    print(f"✅ Final merged dataset: {len(merged):,} rows × {len(merged.columns)} columns")
    return merged


def run_all(save: bool = True):
    """Execute the full merge pipeline and optionally save."""
    df = merge_iqvia_census()

    # Print summary stats
    print("\n" + "=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)

    rate_cols = ["medicaid_rx_per_1k_enrollees", "nonmedicaid_rx_per_1k_pop", "rate_ratio_med_vs_nonmed"]
    for col in rate_cols:
        if col in df.columns:
            print(f"\n  {col}:")
            print(f"    mean   = {df[col].mean():.2f}")
            print(f"    median = {df[col].median():.2f}")
            print(f"    std    = {df[col].std():.2f}")
            print(f"    min    = {df[col].min():.2f}")
            print(f"    max    = {df[col].max():.2f}")

    print(f"\n  Avg Medicaid MME     : {df['medicaid_avg_mme'].mean():.2f}")
    print(f"  Avg Non-Medicaid MME : {df['nonmedicaid_avg_mme'].mean():.2f}")

    if save:
        export_to_csv(df, "merged_iqvia_census_by_zip.csv")

    return df


if __name__ == "__main__":
    run_all()
