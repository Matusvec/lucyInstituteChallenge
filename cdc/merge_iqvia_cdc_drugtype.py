"""
Merge IQVIA state×year opioid prescribing with CDC WONDER drug-type overdose data.

Inputs:
  output/extended/medicaid_vs_nonmedicaid_by_state_year.csv
  output/cdc/cdc_overdose_by_state_year_drug_type.csv
  output/cdc/cdc_illicit_overdose_by_state_year.csv

Output:
  output/cdc/iqvia_cdc_state_year_illicit_panel.csv

Run standalone:
  python -m cdc.merge_iqvia_cdc_drugtype
"""

import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.db_utils import export_to_csv
from cdc.load_wonder_drug_types import load_overdose_deaths_by_drug_type, build_illicit_spread_panel

BASE = os.path.dirname(os.path.dirname(__file__))
OUT = os.path.join(BASE, "output")

IQVIA_STATE_YEAR_CSV = os.path.join(OUT, "extended", "medicaid_vs_nonmedicaid_by_state_year.csv")
CDC_DRUGTYPE_CSV = os.path.join(OUT, "cdc", "cdc_overdose_by_state_year_drug_type.csv")
CDC_ILLICIT_CSV = os.path.join(OUT, "cdc", "cdc_illicit_overdose_by_state_year.csv")


STATE_ABBR_TO_NAME = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii",
    "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine",
    "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska",
    "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico",
    "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island",
    "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas",
    "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}


def _load_iqvia_state_year() -> pd.DataFrame:
    if not os.path.exists(IQVIA_STATE_YEAR_CSV):
        raise FileNotFoundError(
            f"IQVIA state-year CSV not found: {IQVIA_STATE_YEAR_CSV}\n"
            "Run: python main.py q6"
        )

    iqvia = pd.read_csv(IQVIA_STATE_YEAR_CSV)
    iqvia = iqvia[iqvia["state"].isin(STATE_ABBR_TO_NAME.keys())].copy()
    iqvia["year"] = pd.to_numeric(iqvia["year"], errors="coerce")

    med = iqvia[iqvia["is_medicaid"] == "Medicaid"].copy()
    non = iqvia[iqvia["is_medicaid"] == "Non-Medicaid"].copy()

    med = med.rename(columns={
        "total_rx": "medicaid_total_rx",
        "new_rx": "medicaid_new_rx",
        "total_qty": "medicaid_total_qty",
    })[["state", "year", "medicaid_total_rx", "medicaid_new_rx", "medicaid_total_qty"]]

    non = non.rename(columns={
        "total_rx": "nonmedicaid_total_rx",
        "new_rx": "nonmedicaid_new_rx",
        "total_qty": "nonmedicaid_total_qty",
    })[["state", "year", "nonmedicaid_total_rx", "nonmedicaid_new_rx", "nonmedicaid_total_qty"]]

    panel = non.merge(med, on=["state", "year"], how="outer")
    numeric_cols = [c for c in panel.columns if c not in ["state", "year"]]
    panel[numeric_cols] = panel[numeric_cols].fillna(0)
    panel["total_rx"] = panel["medicaid_total_rx"] + panel["nonmedicaid_total_rx"]
    panel["medicaid_rx_share_pct"] = (panel["medicaid_total_rx"] / panel["total_rx"] * 100).round(3)
    panel["state_name"] = panel["state"].map(STATE_ABBR_TO_NAME)

    return panel


def _load_or_build_cdc_panels() -> tuple[pd.DataFrame, pd.DataFrame]:
    if os.path.exists(CDC_DRUGTYPE_CSV):
        cdc_types = pd.read_csv(CDC_DRUGTYPE_CSV)
    else:
        cdc_types = load_overdose_deaths_by_drug_type()
        export_to_csv(cdc_types, "cdc_overdose_by_state_year_drug_type.csv", subdir="cdc")

    if os.path.exists(CDC_ILLICIT_CSV):
        cdc_illicit = pd.read_csv(CDC_ILLICIT_CSV)
    else:
        cdc_illicit = build_illicit_spread_panel(cdc_types, start_year=1999, end_year=2018)
        export_to_csv(cdc_illicit, "cdc_illicit_overdose_by_state_year.csv", subdir="cdc")

    cdc_types["year"] = pd.to_numeric(cdc_types["year"], errors="coerce")
    cdc_illicit["year"] = pd.to_numeric(cdc_illicit["year"], errors="coerce")
    return cdc_types, cdc_illicit


def merge_iqvia_cdc_drugtype() -> pd.DataFrame:
    iqvia = _load_iqvia_state_year()
    cdc_types, cdc_illicit = _load_or_build_cdc_panels()

    opioid_types = {
        "Heroin",
        "Synthetic opioids (non-methadone)",
        "Methadone",
        "Natural/Semi-synthetic opioids",
    }

    cdc_opioid = cdc_types[cdc_types["drug_type"].isin(opioid_types)].copy()
    cdc_opioid_panel = (
        cdc_opioid.groupby(["state", "year"], as_index=False)
        .agg(
            opioid_overdose_deaths=("overdose_deaths", "sum"),
            opioid_overdose_rate_per_100k=("overdose_rate_per_100k", "mean"),
        )
        .rename(columns={"state": "state_name"})
    )

    cdc_illicit = cdc_illicit.rename(columns={"state": "state_name"})

    merged = iqvia.merge(
        cdc_illicit[["state_name", "year", "illicit_overdose_deaths", "illicit_overdose_rate_per_100k"]],
        on=["state_name", "year"],
        how="left",
    )
    merged = merged.merge(
        cdc_opioid_panel,
        on=["state_name", "year"],
        how="left",
    )

    merged = merged[(merged["year"] >= 2008) & (merged["year"] <= 2018)].copy()
    merged = merged.sort_values(["state", "year"]).reset_index(drop=True)
    return merged


if __name__ == "__main__":
    df = merge_iqvia_cdc_drugtype()
    export_to_csv(df, "iqvia_cdc_state_year_illicit_panel.csv", subdir="cdc")

    print("\n── Merged panel sample ──")
    print(df.head(20).to_string(index=False))
    print(f"\nRows: {len(df):,}, states: {df['state'].nunique()}, years: {int(df['year'].min())}–{int(df['year'].max())}")