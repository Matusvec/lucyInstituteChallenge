"""
Merge IQVIA county-level prescription panel with CDC county-level overdose deaths
and drug-type breakdowns into a single analysis-ready panel.

Merge key: (county_fips, year)

Output columns include:
  - IQVIA: total_rx, avg_mme, pct_medicaid, new_rx_ratio, prescribers, etc.
  - CDC:   overdose_deaths, population, overdose_rate_per_100k
  - Drug-type: fentanyl_deaths, heroin_deaths, rx_opioid_deaths, etc.
  - Derived: rx_per_capita, deaths_per_1000_rx, mme_x_death_rate

Run standalone:  python -m cdc.merge_iqvia_cdc_county
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import pandas as pd
from utils.db_utils import export_to_csv
from cdc.load_wonder_county import load_county_overdose_2008_2017

BASE = os.path.dirname(os.path.dirname(__file__))
IQVIA_COUNTY_CSV = os.path.join(BASE, "output", "county", "iqvia_county_year_panel.csv")


def _load_iqvia_county() -> pd.DataFrame:
    if not os.path.exists(IQVIA_COUNTY_CSV):
        raise FileNotFoundError(
            f"IQVIA county panel not found: {IQVIA_COUNTY_CSV}\n"
            "Run: python main.py county"
        )
    df = pd.read_csv(IQVIA_COUNTY_CSV, dtype={"county_fips": str, "state": str})
    df["county_fips"] = df["county_fips"].astype(str).str.zfill(5)
    print(f"  IQVIA county panel: {len(df):,} rows, "
          f"{df['county_fips'].nunique():,} counties")
    return df


def _load_drugtype_pivot() -> pd.DataFrame:
    """Pivot drug-type deaths to one row per (county_fips, year)."""
    try:
        from cdc.load_wonder_county_drugtype import load_county_overdose_by_drugtype
        dt = load_county_overdose_by_drugtype()
    except (FileNotFoundError, KeyError):
        print("  Drug-type data not available -- skipping.")
        return pd.DataFrame()

    pivot = dt.pivot_table(
        index=["county_fips", "year"],
        columns="drug_type",
        values="overdose_deaths",
        aggfunc="sum",
    ).reset_index()

    rename = {
        "Fentanyl (synthetic)": "fentanyl_deaths",
        "Heroin": "heroin_deaths",
        "Rx opioids": "rx_opioid_deaths",
        "Methadone": "methadone_deaths",
        "Cocaine": "cocaine_deaths",
        "Psychostimulants (meth)": "meth_deaths",
    }
    pivot = pivot.rename(columns=rename)
    pivot.columns.name = None
    print(f"  Drug-type pivot: {len(pivot):,} county-year rows")
    return pivot


def merge_county_panel() -> pd.DataFrame:
    """Merge IQVIA prescriptions + CDC deaths + drug-type at county x year."""

    iqvia = _load_iqvia_county()
    cdc = load_county_overdose_2008_2017()

    cdc_clean = cdc[["county", "county_fips", "year",
                      "overdose_deaths", "population",
                      "overdose_rate_per_100k"]].copy()
    cdc_clean["county_fips"] = cdc_clean["county_fips"].astype(str).str.zfill(5)

    merged = iqvia.merge(
        cdc_clean,
        on=["county_fips", "year"],
        how="outer",
        indicator=True,
    )

    both = (merged["_merge"] == "both").sum()
    iqvia_only = (merged["_merge"] == "left_only").sum()
    cdc_only = (merged["_merge"] == "right_only").sum()
    print(f"\n  Merge results:")
    print(f"    Both IQVIA + CDC: {both:,}")
    print(f"    IQVIA only:       {iqvia_only:,}")
    print(f"    CDC only:         {cdc_only:,}")

    merged = merged.drop(columns=["_merge"])

    # Drug-type columns
    drugtype = _load_drugtype_pivot()
    if not drugtype.empty:
        merged = merged.merge(drugtype, on=["county_fips", "year"], how="left")

    # Cast nullable Int64 to float to avoid NA-comparison issues
    for col in ["population", "overdose_deaths"]:
        if col in merged.columns:
            merged[col] = merged[col].astype(float)

    # ── Derived metrics ──
    pop = merged["population"].fillna(0)
    merged["rx_per_capita"] = np.where(
        pop > 0,
        merged["total_rx"] / pop * 1000,
        np.nan,
    )
    merged["deaths_per_1000_rx"] = np.where(
        merged["total_rx"].fillna(0) > 0,
        merged["overdose_deaths"].fillna(0) / merged["total_rx"],
        np.nan,
    )

    merged = merged.sort_values(["county_fips", "year"]).reset_index(drop=True)

    has_both = merged["total_rx"].notna() & merged["overdose_deaths"].notna()
    print(f"\n  Final panel: {len(merged):,} rows")
    print(f"  Counties with BOTH Rx + death data: "
          f"{merged.loc[has_both, 'county_fips'].nunique():,}")

    return merged


if __name__ == "__main__":
    panel = merge_county_panel()

    print("\n-- Sample (first 10 rows with both data sources) --")
    sample = panel[panel["total_rx"].notna() & panel["overdose_deaths"].notna()]
    cols = ["county", "county_fips", "state", "year",
            "total_rx", "avg_mme_per_unit", "pct_medicaid",
            "overdose_deaths", "overdose_rate_per_100k", "rx_per_capita"]
    cols = [c for c in cols if c in sample.columns]
    print(sample[cols].head(10).to_string(index=False))

    export_to_csv(panel, "iqvia_cdc_county_merged.csv", subdir="county")
