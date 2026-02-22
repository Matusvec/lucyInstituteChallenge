"""
Load and clean the CDC WONDER Multiple Cause of Death CSV
(drug-induced overdose deaths by state & year, 1999-2020).

Source: https://wonder.cdc.gov  →  Multiple Cause of Death, 1999-2020
Filters: Drug-induced causes (X40-X44, X60-X64, X85, Y10-Y14)
Grouped by: State × Year

Run standalone:  python -m cdc.load_wonder
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
from utils.db_utils import export_to_csv

# ── Path to the downloaded CDC WONDER CSV ──────────────────────────────────
DATASETS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Datasets")
_CANDIDATES = [
    os.path.join(DATASETS, "cdc", "overdose_by_state_year_1999-2020.csv"),
    os.path.join(DATASETS, "Multiple Cause of Death, 1999-2020.csv"),
]
WONDER_CSV = next((p for p in _CANDIDATES if os.path.exists(p)), _CANDIDATES[0])


def load_overdose_deaths() -> pd.DataFrame:
    """
    Load the CDC WONDER CSV and return a clean DataFrame with columns:
        state, state_code, year, deaths, population, crude_rate_per_100k
    
    Drops the "Total" summary rows and any notes rows.
    """
    print(f"📂 Loading CDC WONDER data from:\n   {WONDER_CSV}")
    
    df = pd.read_csv(WONDER_CSV, dtype=str, low_memory=False)
    
    # Show raw shape
    print(f"   Raw rows: {len(df):,}")
    
    # Drop "Total" summary rows (Notes column contains "Total")
    df = df[df["Notes"] != "Total"].copy()
    
    # Drop rows where State is missing (trailing notes at end of file)
    df = df[df["State"].notna() & (df["State"] != "")].copy()
    
    # Drop rows where Year is missing
    df = df[df["Year"].notna() & (df["Year"] != "")].copy()
    
    # Rename and select columns
    df = df.rename(columns={
        "State":      "state",
        "State Code": "state_code",
        "Year":       "year",
        "Deaths":     "overdose_deaths",
        "Population": "population",
        "Crude Rate": "overdose_rate_per_100k",
    })
    
    # Keep only the columns we need
    df = df[["state", "state_code", "year", "overdose_deaths", 
             "population", "overdose_rate_per_100k"]].copy()
    
    # Convert types
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["overdose_deaths"] = pd.to_numeric(df["overdose_deaths"], errors="coerce").astype("Int64")
    df["population"] = pd.to_numeric(df["population"], errors="coerce").astype("Int64")
    df["overdose_rate_per_100k"] = pd.to_numeric(df["overdose_rate_per_100k"], errors="coerce")
    
    # Drop any remaining bad rows
    df = df.dropna(subset=["year", "state"]).copy()
    
    print(f"   Clean rows: {len(df):,}")
    print(f"   States: {df['state'].nunique()}")
    print(f"   Years: {df['year'].min()}–{df['year'].max()}")
    print(f"   Total overdose deaths in dataset: {df['overdose_deaths'].sum():,}")
    
    return df


def load_overdose_deaths_2008_2018() -> pd.DataFrame:
    """Load and filter to 2008-2018 only (matching IQVIA Medicaid data range)."""
    df = load_overdose_deaths()
    df = df[(df["year"] >= 2008) & (df["year"] <= 2018)].copy()
    print(f"   Filtered to 2008–2018: {len(df):,} rows")
    return df


# ── CLI ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    df = load_overdose_deaths()
    print("\n── Sample (first 10 rows) ──")
    print(df.head(10).to_string(index=False))
    
    print("\n── National totals by year ──")
    national = df.groupby("year").agg(
        total_deaths=("overdose_deaths", "sum"),
        total_pop=("population", "sum"),
    ).reset_index()
    national["national_rate"] = (national["total_deaths"] / national["total_pop"] * 100_000).round(1)
    print(national.to_string(index=False))
    
    export_to_csv(df, "cdc_overdose_by_state_year.csv", subdir="cdc")
