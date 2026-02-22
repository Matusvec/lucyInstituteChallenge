"""
Load and clean CDC WONDER county-level overdose deaths broken out by drug type.

The raw CDC export is split into two files (WONDER caps rows per query):
  - 2008-2012 batch
  - 2013-2017 batch

Both have columns: County, County Code, Year, Multiple Cause of death,
Multiple Cause of death Code, Deaths, Population, Crude Rate.

Drug codes (ICD-10 Multiple Cause):
  T40.1 - Heroin
  T40.2 - Natural/semi-synthetic opioids (oxycodone, hydrocodone)
  T40.3 - Methadone
  T40.4 - Synthetic opioids other than methadone (fentanyl)
  T40.5 - Cocaine
  T43.6 - Psychostimulants (methamphetamine)

Run standalone:  python -m cdc.load_wonder_county_drugtype
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
from utils.db_utils import export_to_csv

BASE = os.path.dirname(os.path.dirname(__file__))

# Pairs of (candidate paths) for each batch — checked in order
_BATCH_CANDIDATES = [
    # 2008-2012 batch
    [
        os.path.join(BASE, "Datasets", "cdc", "overdose_by_county_drugtype_2008-2012.csv"),
        os.path.join(BASE, "output", "cdc", "Multiple Cause of Death, 2008-2012 (10).csv"),
    ],
    # 2013-2017 batch
    [
        os.path.join(BASE, "Datasets", "cdc", "overdose_by_county_drugtype_2013-2017.csv"),
        os.path.join(BASE, "output", "cdc", "Multiple Cause of Death, 2013-2017 (11).csv"),
    ],
]

DRUG_CODE_LABELS = {
    "T40.1": "Heroin",
    "T40.2": "Rx opioids",
    "T40.3": "Methadone",
    "T40.4": "Fentanyl (synthetic)",
    "T40.5": "Cocaine",
    "T43.6": "Psychostimulants (meth)",
}


def _find_batch(candidates: list[str]) -> str | None:
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def _to_numeric_clean(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("Suppressed", "", regex=False)
        .str.replace("Unreliable", "", regex=False)
        .str.replace("Not Applicable", "", regex=False)
    )
    cleaned = cleaned.str.replace(r"[^0-9.\-]", "", regex=True)
    return pd.to_numeric(cleaned, errors="coerce")


def load_county_overdose_by_drugtype() -> pd.DataFrame:
    """
    Combine both batches and return a clean DataFrame:
        county, county_fips, state, year,
        drug_code, drug_type,
        overdose_deaths, population, overdose_rate_per_100k
    """
    frames = []
    for i, candidates in enumerate(_BATCH_CANDIDATES):
        path = _find_batch(candidates)
        if path is None:
            print(f"  WARNING: Batch {i + 1} not found. Checked:")
            for c in candidates:
                print(f"    - {c}")
            continue
        print(f"  Loading batch {i + 1}: {os.path.basename(path)}")
        df = pd.read_csv(path, dtype=str, low_memory=False)
        frames.append(df)

    if not frames:
        raise FileNotFoundError("No county drug-type CDC files found.")

    raw = pd.concat(frames, ignore_index=True)
    print(f"  Combined raw rows: {len(raw):,}")

    if "Notes" in raw.columns:
        raw = raw[raw["Notes"] != "Total"].copy()

    raw = raw[raw["County"].notna() & (raw["County"] != "")].copy()
    raw = raw[raw["Year"].notna() & (raw["Year"] != "")].copy()

    # Identify the drug-type columns (name varies slightly between exports)
    drug_col = None
    drug_code_col = None
    for c in raw.columns:
        if "multiple cause of death code" in c.lower():
            drug_code_col = c
        elif "multiple cause of death" in c.lower():
            drug_col = c

    if drug_code_col is None:
        raise KeyError(f"Drug code column not found. Columns: {list(raw.columns)}")

    rename_map = {
        "County": "county",
        "County Code": "county_fips",
        "Year": "year",
        drug_code_col: "drug_code",
        "Deaths": "overdose_deaths",
        "Population": "population",
        "Crude Rate": "overdose_rate_per_100k",
    }
    if drug_col:
        rename_map[drug_col] = "drug_type_raw"

    raw = raw.rename(columns=rename_map)

    keep = ["county", "county_fips", "year", "drug_code",
            "overdose_deaths", "population", "overdose_rate_per_100k"]
    if "drug_type_raw" in raw.columns:
        keep.append("drug_type_raw")
    raw = raw[keep].copy()

    raw["state"] = raw["county"].str.extract(r",\s*(\w{2})$")
    raw["county_fips"] = raw["county_fips"].astype(str).str.zfill(5)
    raw["drug_type"] = raw["drug_code"].map(DRUG_CODE_LABELS).fillna("Other")

    raw["year"] = pd.to_numeric(raw["year"], errors="coerce").astype("Int64")
    raw["overdose_deaths"] = _to_numeric_clean(raw["overdose_deaths"]).astype("Int64")
    raw["population"] = _to_numeric_clean(raw["population"]).astype("Int64")
    raw["overdose_rate_per_100k"] = _to_numeric_clean(raw["overdose_rate_per_100k"])

    mask = (
        raw["overdose_rate_per_100k"].isna()
        & raw["overdose_deaths"].notna()
        & (raw["population"] > 0)
    )
    raw.loc[mask, "overdose_rate_per_100k"] = (
        raw.loc[mask, "overdose_deaths"] / raw.loc[mask, "population"] * 100_000
    ).round(3)

    raw = raw.dropna(subset=["year", "county_fips", "drug_code"]).copy()

    print(f"  Clean rows: {len(raw):,}")
    print(f"  Counties: {raw['county_fips'].nunique():,}")
    print(f"  Years: {raw['year'].min()}-{raw['year'].max()}")
    print(f"  Drug types: {raw['drug_type'].value_counts().to_dict()}")

    return raw


def load_fentanyl_county(min_year: int = 2008, max_year: int = 2017) -> pd.DataFrame:
    """Filter to T40.4 (fentanyl / synthetic opioids) only."""
    df = load_county_overdose_by_drugtype()
    fent = df[(df["drug_code"] == "T40.4")
              & (df["year"] >= min_year)
              & (df["year"] <= max_year)].copy()
    print(f"  Fentanyl rows (T40.4): {len(fent):,}")
    print(f"  Counties with fentanyl data: {fent['county_fips'].nunique():,}")
    return fent


def load_heroin_county(min_year: int = 2008, max_year: int = 2017) -> pd.DataFrame:
    """Filter to T40.1 (heroin) only."""
    df = load_county_overdose_by_drugtype()
    heroin = df[(df["drug_code"] == "T40.1")
                & (df["year"] >= min_year)
                & (df["year"] <= max_year)].copy()
    print(f"  Heroin rows (T40.1): {len(heroin):,}")
    print(f"  Counties with heroin data: {heroin['county_fips'].nunique():,}")
    return heroin


if __name__ == "__main__":
    df = load_county_overdose_by_drugtype()

    print("\n-- Sample (first 15 rows) --")
    print(df.head(15).to_string(index=False))

    print("\n-- Deaths by drug type (all years) --")
    summary = df.groupby("drug_type").agg(
        total_deaths=("overdose_deaths", "sum"),
        county_year_rows=("overdose_deaths", "count"),
    ).sort_values("total_deaths", ascending=False)
    print(summary.to_string())

    print("\n-- Fentanyl (T40.4) by year --")
    fent = df[df["drug_code"] == "T40.4"].groupby("year").agg(
        deaths=("overdose_deaths", "sum"),
        counties=("county_fips", "nunique"),
    ).reset_index()
    print(fent.to_string(index=False))

    export_to_csv(df, "cdc_overdose_by_county_drugtype.csv", subdir="cdc")
