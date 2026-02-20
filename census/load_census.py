"""
Load and clean all five ACS 2018 Census tables into a single
per-zip-code demographics DataFrame.

Run standalone:  python -m census.load_census
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
from utils.db_utils import export_to_csv

# ── Paths to Census downloads ──────────────────────────────────────────────
DATASETS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Datasets")

S2704_DATA = os.path.join(DATASETS, "ACSST5Y2018.S2704_2026-02-06T171808",  "ACSST5Y2018.S2704-Data.csv")
B01003_DATA = os.path.join(DATASETS, "ACSDT5Y2018.B01003_2026-02-06T172313", "ACSDT5Y2018.B01003-Data.csv")
B19013_DATA = os.path.join(DATASETS, "ACSDT5Y2018.B19013_2026-02-06T172702", "ACSDT5Y2018.B19013-Data.csv")
S1701_DATA  = os.path.join(DATASETS, "ACSST5Y2018.S1701_2026-02-06T172946",  "ACSST5Y2018.S1701-Data.csv")
B02001_DATA = os.path.join(DATASETS, "ACSDT5Y2018.B02001_2026-02-06T173111", "ACSDT5Y2018.B02001-Data.csv")


def _extract_zip(geo_id: pd.Series) -> pd.Series:
    """Extract the 5-digit zip from GEO_ID like '8600000US00601' → '00601'."""
    return geo_id.str[-5:]


def _load_acs(path: str, columns: dict, skiprows=None) -> pd.DataFrame:
    """
    Load an ACS CSV, skip the header description row (row index 1),
    keep only requested columns, rename them, and extract zip_code.

    Parameters
    ----------
    path : str          Full path to the -Data.csv file.
    columns : dict      {original_column_code: friendly_name}
    """
    df = pd.read_csv(path, skiprows=[1], dtype=str, low_memory=False)
    keep = ["GEO_ID"] + list(columns.keys())
    # Only keep columns that exist (some tables might differ slightly)
    keep = [c for c in keep if c in df.columns]
    df = df[keep].copy()
    df["zip_code"] = _extract_zip(df["GEO_ID"])
    df.drop(columns=["GEO_ID"], inplace=True)
    df.rename(columns=columns, inplace=True)
    # Convert numeric columns
    for col in columns.values():
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


# ── Individual table loaders ───────────────────────────────────────────────

def load_population() -> pd.DataFrame:
    """B01003 — Total population per ZCTA."""
    return _load_acs(B01003_DATA, {
        "B01003_001E": "total_population",
    })


def load_insurance() -> pd.DataFrame:
    """S2704 — Public health insurance: Medicaid enrollment counts & %."""
    return _load_acs(S2704_DATA, {
        "S2704_C01_001E": "civilian_pop",
        "S2704_C01_006E": "medicaid_enrolled",
        "S2704_C01_007E": "medicaid_under19",
        "S2704_C01_008E": "medicaid_19to64",
        "S2704_C01_009E": "medicaid_65plus",
        "S2704_C03_006E": "pct_medicaid",
        "S2704_C01_014E": "below_138pct_poverty",
        "S2704_C01_015E": "above_138pct_poverty",
    })


def load_income() -> pd.DataFrame:
    """B19013 — Median household income per ZCTA."""
    return _load_acs(B19013_DATA, {
        "B19013_001E": "median_household_income",
    })


def load_poverty() -> pd.DataFrame:
    """S1701 — Poverty status per ZCTA."""
    return _load_acs(S1701_DATA, {
        "S1701_C01_001E": "poverty_universe",      # pop for whom poverty is determined
        "S1701_C02_001E": "below_poverty_count",    # count below poverty
        "S1701_C03_001E": "pct_below_poverty",      # % below poverty
    })


def load_race() -> pd.DataFrame:
    """B02001 — Racial composition per ZCTA."""
    return _load_acs(B02001_DATA, {
        "B02001_001E": "race_total",
        "B02001_002E": "white_alone",
        "B02001_003E": "black_alone",
        "B02001_004E": "aian_alone",       # American Indian / Alaska Native
        "B02001_005E": "asian_alone",
        "B02001_006E": "nhpi_alone",       # Native Hawaiian / Pacific Islander
        "B02001_007E": "other_race_alone",
        "B02001_008E": "two_or_more_races",
    })


# ── Combined loader ────────────────────────────────────────────────────────

def load_all_census() -> pd.DataFrame:
    """
    Load all five Census tables and merge into one DataFrame keyed on
    zip_code.  Returns ~33,000 rows with demographics per ZCTA.
    """
    print("📥 Loading Census ACS 2018 data …")

    pop = load_population()
    print(f"   B01003  (population)  : {len(pop):,} zips")

    ins = load_insurance()
    print(f"   S2704   (insurance)   : {len(ins):,} zips")

    inc = load_income()
    print(f"   B19013  (income)      : {len(inc):,} zips")

    pov = load_poverty()
    print(f"   S1701   (poverty)     : {len(pov):,} zips")

    race = load_race()
    print(f"   B02001  (race)        : {len(race):,} zips")

    # Merge all on zip_code (outer keeps every zip that appears anywhere)
    merged = pop
    for df in [ins, inc, pov, race]:
        merged = merged.merge(df, on="zip_code", how="outer")

    # Compute derived fields
    if "race_total" in merged.columns and "white_alone" in merged.columns:
        merged["pct_nonwhite"] = (
            (merged["race_total"] - merged["white_alone"])
            / merged["race_total"].replace(0, float("nan"))
            * 100
        ).round(2)

    # Fill missing medicaid_enrolled from age sub-groups (Census marks some totals as (X))
    if all(c in merged.columns for c in ["medicaid_enrolled", "medicaid_under19", "medicaid_19to64", "medicaid_65plus"]):
        age_sum = merged["medicaid_under19"].fillna(0) + merged["medicaid_19to64"].fillna(0) + merged["medicaid_65plus"].fillna(0)
        merged["medicaid_enrolled"] = merged["medicaid_enrolled"].fillna(age_sum)
        merged["medicaid_enrolled"] = merged["medicaid_enrolled"].replace(0, float("nan"))

    if "medicaid_enrolled" in merged.columns and "total_population" in merged.columns:
        merged["non_medicaid_pop"] = merged["total_population"] - merged["medicaid_enrolled"]

    print(f"\n✅ Combined Census dataset: {len(merged):,} zips × {len(merged.columns)} columns")
    return merged


def run_all(save: bool = True):
    """Load census data and optionally export to CSV."""
    df = load_all_census()
    print(f"\nSample rows:")
    print(df.head(5).to_string(index=False))
    if save:
        export_to_csv(df, "census_demographics_by_zip.csv")
    return df


if __name__ == "__main__":
    run_all()
