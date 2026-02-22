"""
Load and clean CDC WONDER overdose deaths by drug type (state × year).

Expected input:
  Datasets/Multiple Cause of Death, Drug Type, 1999-2020.csv

The export should be from CDC WONDER Multiple Cause of Death with:
  - Group by: State, Year, Drug/Alcohol Induced Cause (or equivalent drug type field)
  - Measure columns: Deaths, Population, Crude Rate

Run standalone:
  python -m cdc.load_wonder_drug_types
"""

import os
import sys
import re
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.db_utils import export_to_csv

DATASETS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Datasets")
_DRUGTYPE_CANDIDATES = [
    os.path.join(DATASETS, "cdc", "overdose_by_state_drugtype_1999-2020.csv"),
    os.path.join(DATASETS, "Multiple Cause of Death, Drug Type, 1999-2020.csv"),
]
WONDER_DRUGTYPE_CSV = next(
    (p for p in _DRUGTYPE_CANDIDATES if os.path.exists(p)), _DRUGTYPE_CANDIDATES[0]
)


def _first_present(df: pd.DataFrame, candidates: list[str]) -> str:
    for col in candidates:
        if col in df.columns:
            return col
    raise KeyError(f"None of these columns found: {candidates}")


def _normalize_drug_type(value: str) -> str:
    if pd.isna(value):
        return "Unknown"
    text = str(value).strip().lower()

    if "heroin" in text:
        return "Heroin"
    if "synthetic opioid" in text and "methadone" not in text:
        return "Synthetic opioids (non-methadone)"
    if "methadone" in text:
        return "Methadone"
    if "natural" in text or "semi" in text or "prescription opioid" in text:
        return "Natural/Semi-synthetic opioids"
    if "cocaine" in text:
        return "Cocaine"
    if "psychostimulant" in text or "methamphetamine" in text:
        return "Psychostimulants"
    if "all" in text and "drug" in text:
        return "All drug overdoses"
    return str(value).strip()


def _is_illicit_proxy(drug_type: str) -> bool:
    illicit_set = {
        "Heroin",
        "Synthetic opioids (non-methadone)",
        "Cocaine",
        "Psychostimulants",
    }
    return drug_type in illicit_set


def load_overdose_deaths_by_drug_type(csv_path: str = WONDER_DRUGTYPE_CSV) -> pd.DataFrame:
    """
    Returns tidy state×year×drug_type overdose data with columns:
      state, state_code, year, drug_type, overdose_deaths, population,
      overdose_rate_per_100k, is_illicit_proxy
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(
            "CDC WONDER drug-type file not found. Expected: "
            f"{csv_path}\n"
            "Export from WONDER with State, Year, and drug-type grouping."
        )

    print(f"📂 Loading CDC WONDER drug-type data from:\n   {csv_path}")
    df = pd.read_csv(csv_path, dtype=str, low_memory=False)
    print(f"   Raw rows: {len(df):,}")

    notes_col = "Notes" if "Notes" in df.columns else None
    if notes_col:
        df = df[df[notes_col] != "Total"].copy()

    state_col = _first_present(df, ["State"])
    year_col = _first_present(df, ["Year"])
    state_code_col = _first_present(df, ["State Code", "State Code (FIPS)"])
    deaths_col = _first_present(df, ["Deaths"])
    pop_col = _first_present(df, ["Population"])
    rate_col = _first_present(df, ["Crude Rate", "Age-adjusted Rate"])
    drug_col = _first_present(
        df,
        [
            "Drug/Alcohol Induced Cause",
            "Drug/Poisoning Type",
            "Multiple Cause of death",
            "Injury mechanism & all other leading causes",
            "Cause of death",
        ],
    )

    df = df[df[state_col].notna() & (df[state_col] != "")].copy()
    df = df[df[year_col].notna() & (df[year_col] != "")].copy()
    df = df[df[drug_col].notna() & (df[drug_col] != "")].copy()

    df = df.rename(
        columns={
            state_col: "state",
            state_code_col: "state_code",
            year_col: "year",
            drug_col: "drug_type_raw",
            deaths_col: "overdose_deaths",
            pop_col: "population",
            rate_col: "overdose_rate_per_100k",
        }
    )

    df = df[
        [
            "state",
            "state_code",
            "year",
            "drug_type_raw",
            "overdose_deaths",
            "population",
            "overdose_rate_per_100k",
        ]
    ].copy()

    df["drug_type"] = df["drug_type_raw"].map(_normalize_drug_type)
    df["is_illicit_proxy"] = df["drug_type"].map(_is_illicit_proxy)

    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    def _to_numeric_clean(series: pd.Series) -> pd.Series:
        cleaned = (
            series.astype(str)
            .str.replace(",", "", regex=False)
            .str.replace("Not Applicable", "", regex=False)
            .str.replace("Unreliable", "", regex=False)
            .str.replace("Suppressed", "", regex=False)
        )
        cleaned = cleaned.str.replace(r"[^0-9.\-]", "", regex=True)
        return pd.to_numeric(cleaned, errors="coerce")

    df["overdose_deaths"] = _to_numeric_clean(df["overdose_deaths"]).astype("Int64")
    df["population"] = _to_numeric_clean(df["population"]).astype("Int64")
    df["overdose_rate_per_100k"] = _to_numeric_clean(df["overdose_rate_per_100k"])

    df = df.dropna(subset=["state", "year", "drug_type"]).copy()

    print(f"   Clean rows: {len(df):,}")
    print(f"   Drug types: {df['drug_type'].nunique()}")
    print(f"   States: {df['state'].nunique()}")
    print(f"   Years: {df['year'].min()}–{df['year'].max()}")
    return df


def build_illicit_spread_panel(df: pd.DataFrame, start_year: int = 1999, end_year: int = 2018) -> pd.DataFrame:
    """
    Aggregate illicit-proxy categories to state × year for mapping spread.
    NOTE: categories can overlap in CDC coding, so this is a proxy intensity panel.
    """
    filtered = df[(df["year"] >= start_year) & (df["year"] <= end_year)].copy()
    filtered = filtered[filtered["is_illicit_proxy"] == True].copy()

    panel = (
        filtered.groupby(["state", "state_code", "year"], as_index=False)
        .agg(
            illicit_overdose_deaths=("overdose_deaths", "sum"),
            population=("population", "max"),
            illicit_category_count=("drug_type", "nunique"),
        )
    )
    panel["illicit_overdose_rate_per_100k"] = (
        panel["illicit_overdose_deaths"] / panel["population"] * 100_000
    ).round(3)

    return panel.sort_values(["year", "state"]).reset_index(drop=True)


if __name__ == "__main__":
    all_types = load_overdose_deaths_by_drug_type()
    export_to_csv(all_types, "cdc_overdose_by_state_year_drug_type.csv", subdir="cdc")

    illicit_panel = build_illicit_spread_panel(all_types, start_year=1999, end_year=2018)
    export_to_csv(illicit_panel, "cdc_illicit_overdose_by_state_year.csv", subdir="cdc")

    print("\n── Illicit panel sample ──")
    print(illicit_panel.head(15).to_string(index=False))