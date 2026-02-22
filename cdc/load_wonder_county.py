"""
Load and clean the CDC WONDER Multiple Cause of Death CSV
(drug-induced overdose deaths by county & year, 2008-2017).

Source: https://wonder.cdc.gov  ->  Multiple Cause of Death, 1999-2020
Filters: Drug-induced causes (X40-X44, X60-X64, X85, Y10-Y14)
Grouped by: County (residence) x Year

Run standalone:  python -m cdc.load_wonder_county
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
from utils.db_utils import export_to_csv

BASE = os.path.dirname(os.path.dirname(__file__))

_CANDIDATES = [
    os.path.join(BASE, "Datasets", "Multiple Cause of Death, County, 2008-2017.csv"),
    os.path.join(BASE, "output", "cdc", "Multiple Cause of Death, 1999-2020 (9).csv"),
]


def _find_csv() -> str:
    for path in _CANDIDATES:
        if os.path.exists(path):
            return path
    raise FileNotFoundError(
        "CDC WONDER county-level file not found. Checked:\n"
        + "\n".join(f"  - {p}" for p in _CANDIDATES)
    )


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


def load_county_overdose_deaths() -> pd.DataFrame:
    """
    Load county-level CDC WONDER CSV and return a clean DataFrame:
        county, county_fips, state, year,
        overdose_deaths, population, overdose_rate_per_100k
    """
    csv_path = _find_csv()
    print(f"  Loading CDC WONDER county data from:\n   {csv_path}")

    df = pd.read_csv(csv_path, dtype=str, low_memory=False)
    print(f"   Raw rows: {len(df):,}")

    if "Notes" in df.columns:
        df = df[df["Notes"] != "Total"].copy()

    df = df[df["County"].notna() & (df["County"] != "")].copy()
    df = df[df["Year"].notna() & (df["Year"] != "")].copy()

    df = df.rename(columns={
        "County":      "county",
        "County Code": "county_fips",
        "Year":        "year",
        "Deaths":      "overdose_deaths",
        "Population":  "population",
        "Crude Rate":  "overdose_rate_per_100k",
    })

    df = df[["county", "county_fips", "year", "overdose_deaths",
             "population", "overdose_rate_per_100k"]].copy()

    # Extract state abbreviation from county name ("Baldwin County, AL" -> "AL")
    df["state"] = df["county"].str.extract(r",\s*(\w{2})$")

    df["county_fips"] = df["county_fips"].astype(str).str.zfill(5)

    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["overdose_deaths"] = _to_numeric_clean(df["overdose_deaths"]).astype("Int64")
    df["population"] = _to_numeric_clean(df["population"]).astype("Int64")
    df["overdose_rate_per_100k"] = _to_numeric_clean(df["overdose_rate_per_100k"])

    # Fill rate where deaths & population are known but rate was "Unreliable"
    mask = (
        df["overdose_rate_per_100k"].isna()
        & df["overdose_deaths"].notna()
        & (df["population"] > 0)
    )
    df.loc[mask, "overdose_rate_per_100k"] = (
        df.loc[mask, "overdose_deaths"] / df.loc[mask, "population"] * 100_000
    ).round(3)

    df = df.dropna(subset=["year", "county_fips"]).copy()

    non_suppressed = df["overdose_deaths"].notna()
    print(f"   Clean rows: {len(df):,}")
    print(f"   Counties: {df['county_fips'].nunique():,}")
    print(f"   Years: {df['year'].min()}-{df['year'].max()}")
    print(
        f"   Rows with death counts: {non_suppressed.sum():,} / {len(df):,} "
        f"({non_suppressed.mean() * 100:.1f}%)"
    )
    print(f"   Total reported deaths: {df['overdose_deaths'].sum():,}")

    return df


def load_county_overdose_2008_2017() -> pd.DataFrame:
    """Load and filter to 2008-2017 (matching IQVIA county panel range)."""
    df = load_county_overdose_deaths()
    df = df[(df["year"] >= 2008) & (df["year"] <= 2017)].copy()
    print(f"   Filtered to 2008-2017: {len(df):,} rows")
    return df


if __name__ == "__main__":
    df = load_county_overdose_deaths()

    print("\n-- Sample (first 15 rows with data) --")
    sample = df[df["overdose_deaths"].notna()].head(15)
    print(sample.to_string(index=False))

    print("\n-- National totals by year --")
    national = df.groupby("year").agg(
        total_deaths=("overdose_deaths", "sum"),
        total_pop=("population", "sum"),
        counties_with_data=("overdose_deaths", lambda x: x.notna().sum()),
    ).reset_index()
    national["national_rate"] = (
        national["total_deaths"] / national["total_pop"] * 100_000
    ).round(1)
    print(national.to_string(index=False))

    export_to_csv(df, "cdc_overdose_by_county_year.csv", subdir="cdc")
