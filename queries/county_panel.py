"""
County-Level IQVIA Opioid Prescription Panel (2008-2017).

PURPOSE
=======
Build a comprehensive county x year panel of opioid prescribing for every
US county, 2008 through 2017.  This is the IQVIA side of the county-level
analysis -- overdose deaths come separately from CDC WONDER and can be
merged on county_fips x year.

APPROACH
========
The IQVIA database has no county column.  The finest geography available is
prescriber_limited.zip_code (5-digit).  So we:

  1. Query main x prescriber_limited x drug  -> zip_code x year aggregates
  2. Download the Census 2010 ZCTA-to-County relationship file
  3. Map each 5-digit zip to its dominant county (highest population share)
  4. Re-aggregate to county x year

COLUMNS PRODUCED (county level)
===============================
  state, county_fips, year
  -- Volumes --
    total_rx, new_rx, total_qty, new_qty
  -- MME --
    avg_mme_per_unit   (qty-weighted average morphine-milligram-equivalent)
    total_mme          (total opioid burden = qty x mme_per_unit)
  -- Medicaid vs Non-Medicaid --
    medicaid_rx, medicaid_new_rx, medicaid_qty, medicaid_total_mme, medicaid_avg_mme
    nonmedicaid_rx, nonmedicaid_new_rx, nonmedicaid_qty, nonmedicaid_total_mme, nonmedicaid_avg_mme
    pct_medicaid
  -- Prescriber concentration --
    distinct_prescribers, distinct_opioid_products
  -- Sales channel --
    retail_rx, mail_order_rx, mail_order_pct
  -- Derived --
    new_rx_ratio  (% of prescriptions that are new starts)

PERFORMANCE NOTES
=================
- Each year scans ~100-200 M rows in main with TWO JOINs:
    prescriber_limited (2 M rows, for zip_code + state)
    drug               (4 K rows, for mme_per_unit)
- PostgreSQL session is tuned (work_mem raised) for faster hash joins.
- Year is excluded from GROUP BY (it's a constant per query).
- Each year's result is saved incrementally to output/county/_incremental/;
  if the run is interrupted, re-running resumes from the last completed year.
- Expect ~3-6 min per year -> 30-60 min total for 10 years.
- Output: ~40 K zips x 10 years = 400 K rows at zip level,
  then ~3,200 counties x 10 years = 32 K rows at county level.

Run standalone:  python -m queries.county_panel
Run via main:    python main.py county
"""

import sys
import os
import io
import time
import threading
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.db_utils import (
    get_connection,
    run_query,
    export_to_csv,
    medicaid_ids_sql,
    opioid_pgs_sql,
)

YEARS = list(range(2008, 2018))  # 2008-2017

CROSSWALK_URL = (
    "https://www2.census.gov/geo/docs/maps-data/data/rel/zcta_county_rel_10.txt"
)
CROSSWALK_LOCAL = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "Datasets",
    "zcta_county_rel_10.csv",
)
INCREMENTAL_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "output", "county", "_incremental",
)


# ─────────────────────────────────────────────────────────────────────────────
# DB tuning & query helpers
# ─────────────────────────────────────────────────────────────────────────────
def _tune_connection():
    """Raise work_mem for faster GROUP BY / hash-join performance."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SET work_mem = '128MB'")
    print("     [db] work_mem set to 128 MB for this session", flush=True)


def _query_year_with_spinner(sql: str, year: int):
    """
    Run a SQL query in a background thread while showing a live spinner
    with elapsed time.  Returns (DataFrame, elapsed_seconds).
    """
    result_holder = [None]
    error_holder = [None]

    def worker():
        try:
            result_holder[0] = run_query(sql)
        except Exception as e:
            error_holder[0] = e

    thread = threading.Thread(target=worker, daemon=True)
    t0 = time.time()
    thread.start()

    chars = ["|", "/", "-", "\\"]
    idx = 0
    while thread.is_alive():
        elapsed = time.time() - t0
        mins, secs = divmod(int(elapsed), 60)
        sys.stdout.write(
            f"\r       {chars[idx % 4]} Year {year} -- querying... "
            f"{mins}m {secs:02d}s   "
        )
        sys.stdout.flush()
        thread.join(timeout=0.25)
        idx += 1

    sys.stdout.write("\r" + " " * 60 + "\r")
    sys.stdout.flush()

    elapsed = time.time() - t0
    if error_holder[0]:
        raise error_holder[0]
    return result_holder[0], elapsed


# ─────────────────────────────────────────────────────────────────────────────
# Incremental save / resume
# ─────────────────────────────────────────────────────────────────────────────
def _incremental_path(year: int) -> str:
    return os.path.join(INCREMENTAL_DIR, f"zip_year_{year}.csv")


def _load_completed_years() -> dict:
    """Load previously saved per-year CSVs from the incremental directory."""
    completed = {}
    if not os.path.isdir(INCREMENTAL_DIR):
        return completed
    for yr in YEARS:
        path = _incremental_path(yr)
        if os.path.exists(path):
            try:
                df = pd.read_csv(path, dtype={"zip_code": str, "state": str})
                if not df.empty:
                    completed[yr] = df
            except Exception:
                pass  # corrupt / partial file -- will re-query
    return completed


def _save_year_incremental(df: pd.DataFrame, year: int):
    """Persist one year's zip-level result so we can resume later."""
    if df.empty:
        return
    os.makedirs(INCREMENTAL_DIR, exist_ok=True)
    df.to_csv(_incremental_path(year), index=False)


# ─────────────────────────────────────────────────────────────────────────────
# Main year-by-year query runner
# ─────────────────────────────────────────────────────────────────────────────
def _query_by_year(sql_template: str, label: str) -> pd.DataFrame:
    """
    Run *sql_template* once per year ({year} placeholder), with:
      - incremental save after each year (resume on restart)
      - live spinner during each query
      - progress bar after each year completes
    """
    cached = _load_completed_years()
    cached_years = sorted(cached.keys())
    remaining_years = [yr for yr in YEARS if yr not in cached]

    if cached_years:
        print(
            f"     >> Resuming -- {len(cached_years)} years already cached: "
            f"{cached_years}",
            flush=True,
        )

    chunks = list(cached.values())
    total_rows = sum(len(df) for df in chunks)
    total_years = len(YEARS)
    done = len(cached_years)
    query_times = []
    t0_all = time.time()

    if not remaining_years:
        print(f"     >> All {total_years} years cached -- skipping query.", flush=True)
    else:
        print(
            f"     >> {label} -- {len(remaining_years)} year(s) to query...",
            flush=True,
        )

    for yr in remaining_years:
        sql = sql_template.format(year=yr)
        df, elapsed = _query_year_with_spinner(sql, yr)

        df["year"] = yr
        query_times.append(elapsed)
        total_rows += len(df)
        done += 1

        if not df.empty:
            _save_year_incremental(df, yr)
            chunks.append(df)

        # ── progress bar ──
        pct = done / total_years * 100
        bar_w = 25
        filled = int(bar_w * done / total_years)
        bar = "#" * filled + "-" * (bar_w - filled)

        avg_s = sum(query_times) / len(query_times)
        eta_s = (total_years - done) * avg_s
        wall = time.time() - t0_all

        print(
            f"       [{bar}] {pct:5.1f}%  "
            f"Year {yr}: {len(df):>6,} rows  "
            f"({elapsed:.0f}s | avg {avg_s:.0f}s/yr | "
            f"ETA {eta_s / 60:.1f}m | wall {wall / 60:.1f}m)",
            flush=True,
        )

    result = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
    wall_total = time.time() - t0_all

    if query_times:
        print(
            f"     >> {label} done -- {len(result):,} rows in {wall_total / 60:.1f} min  "
            f"(fastest {min(query_times):.0f}s | slowest {max(query_times):.0f}s | "
            f"avg {sum(query_times) / len(query_times):.0f}s)",
        )
    else:
        print(f"     >> {label} done -- {len(result):,} rows (all from cache)")

    return result


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Zip × Year SQL query
# ─────────────────────────────────────────────────────────────────────────────
def opioid_zip_year_panel() -> pd.DataFrame:
    """
    Build a zip_code × year panel of opioid prescribing metrics.

    JOINs:
        main × prescriber_limited  (for zip_code, state)
        main × drug                (for mme_per_unit — drug table is only 4 K rows)

    Returns one row per (state, zip_code, year) — roughly 400 K rows.
    """
    med_ids = medicaid_ids_sql()
    opioid = opioid_pgs_sql()

    # Year is filtered in WHERE and added in Python after the query;
    # excluding it from GROUP BY reduces the hash-key width.
    sql_t = f"""
        SELECT
            p.state,
            p.zip_code,

            /* ── Overall prescription volumes ── */
            SUM(m.total_rx)  / 1000.0              AS total_rx,
            SUM(m.new_rx)    / 1000.0              AS new_rx,
            SUM(m.total_qty) / 1000.0              AS total_qty,
            SUM(m.new_qty)   / 1000.0              AS new_qty,

            /* ── MME burden (qty-weighted) ── */
            SUM(m.total_qty * COALESCE(d.mme_per_unit, 0))
                / NULLIF(SUM(m.total_qty), 0)      AS avg_mme_per_unit,
            SUM(m.total_qty * COALESCE(d.mme_per_unit, 0))
                / 1000.0                            AS total_mme,

            /* ── Medicaid subset ── */
            SUM(CASE WHEN m.payor_plan_id IN {med_ids}
                     THEN m.total_rx  ELSE 0 END)  / 1000.0  AS medicaid_rx,
            SUM(CASE WHEN m.payor_plan_id IN {med_ids}
                     THEN m.new_rx    ELSE 0 END)  / 1000.0  AS medicaid_new_rx,
            SUM(CASE WHEN m.payor_plan_id IN {med_ids}
                     THEN m.total_qty ELSE 0 END)  / 1000.0  AS medicaid_qty,
            SUM(CASE WHEN m.payor_plan_id IN {med_ids}
                     THEN m.total_qty * COALESCE(d.mme_per_unit, 0)
                     ELSE 0 END)                    / 1000.0  AS medicaid_total_mme,

            /* ── Prescriber concentration ── */
            COUNT(DISTINCT m.prescriber_key)        AS distinct_prescribers,
            COUNT(DISTINCT m.pg)                    AS distinct_opioid_products,

            /* ── Sales channel ── */
            SUM(CASE WHEN m.sales_category = 1
                     THEN m.total_rx ELSE 0 END)   / 1000.0  AS retail_rx,
            SUM(CASE WHEN m.sales_category = 2
                     THEN m.total_rx ELSE 0 END)   / 1000.0  AS mail_order_rx

        FROM main m
        JOIN prescriber_limited p ON m.prescriber_key = p.prescriber_key
        JOIN drug d               ON m.pg = d.pg
        WHERE m.pg IN {opioid}
          AND m.year = {{year}}
        GROUP BY p.state, p.zip_code
    """

    df = _query_by_year(sql_t, "county-panel-zip")
    if df.empty:
        return df

    # Ensure zip_code stays zero-padded after any CSV round-trip
    df["zip_code"] = df["zip_code"].astype(str).str.zfill(5)

    # ── Derived columns (Non-Medicaid = Total − Medicaid) ──────────────
    df["nonmedicaid_rx"]        = df["total_rx"]  - df["medicaid_rx"]
    df["nonmedicaid_new_rx"]    = df["new_rx"]    - df["medicaid_new_rx"]
    df["nonmedicaid_qty"]       = df["total_qty"] - df["medicaid_qty"]
    df["nonmedicaid_total_mme"] = df["total_mme"] - df["medicaid_total_mme"]

    # Avg MME per unit — Medicaid & Non-Medicaid
    df["medicaid_avg_mme"] = np.where(
        df["medicaid_qty"] > 0,
        df["medicaid_total_mme"] / df["medicaid_qty"],
        0,
    )
    df["nonmedicaid_avg_mme"] = np.where(
        df["nonmedicaid_qty"] > 0,
        df["nonmedicaid_total_mme"] / df["nonmedicaid_qty"],
        0,
    )

    # Percentages
    df["pct_medicaid"]   = np.where(
        df["total_rx"] > 0, df["medicaid_rx"] / df["total_rx"] * 100, 0
    ).round(2)
    df["new_rx_ratio"]   = np.where(
        df["total_rx"] > 0, df["new_rx"] / df["total_rx"] * 100, 0
    ).round(2)
    df["mail_order_pct"] = np.where(
        df["total_rx"] > 0, df["mail_order_rx"] / df["total_rx"] * 100, 0
    ).round(2)

    return df.sort_values(["state", "zip_code", "year"]).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — ZCTA → County crosswalk
# ─────────────────────────────────────────────────────────────────────────────
def get_zcta_county_crosswalk() -> pd.DataFrame:
    """
    Download (or load cached) the Census 2010 ZCTA-to-County relationship file.

    Source: https://www.census.gov/geographies/reference-files/time-series/geo/
            relationship-files.2010.html

    Returns a DataFrame with columns:
        zcta5, state_fips, county_fips_3, county_fips, pop_in_county,
        zcta_pop, alloc_factor
    """
    if os.path.exists(CROSSWALK_LOCAL):
        print(f"     Loading cached crosswalk: {CROSSWALK_LOCAL}")
        return pd.read_csv(CROSSWALK_LOCAL, dtype=str)

    print("     Downloading ZCTA-County crosswalk from Census Bureau ...")
    try:
        import urllib.request

        response = urllib.request.urlopen(CROSSWALK_URL, timeout=60)
        raw = response.read().decode("utf-8")
        df_raw = pd.read_csv(io.StringIO(raw), dtype=str)

        col_map = {}
        for c in df_raw.columns:
            cu = c.upper().strip()
            if cu == "ZCTA5":
                col_map[c] = "zcta5"
            elif cu == "STATE":
                col_map[c] = "state_fips"
            elif cu == "COUNTY":
                col_map[c] = "county_fips_3"
            elif cu == "GEOID":
                col_map[c] = "county_fips"
            elif cu == "POPPT":
                col_map[c] = "pop_in_county"
            elif cu == "ZPOP":
                col_map[c] = "zcta_pop"

        df = df_raw.rename(columns=col_map)
        keep = [v for v in col_map.values() if v in df.columns]
        df = df[keep].copy()

        df["pop_in_county"] = pd.to_numeric(df["pop_in_county"], errors="coerce").fillna(0)
        df["zcta_pop"]      = pd.to_numeric(df["zcta_pop"], errors="coerce").fillna(0)
        df["alloc_factor"]  = np.where(
            df["zcta_pop"] > 0, df["pop_in_county"] / df["zcta_pop"], 0
        )

        os.makedirs(os.path.dirname(CROSSWALK_LOCAL), exist_ok=True)
        df.to_csv(CROSSWALK_LOCAL, index=False)
        print(f"     Crosswalk cached -> {CROSSWALK_LOCAL}")
        return df

    except Exception as e:
        print(f"     WARNING: Could not download crosswalk: {e}")
        print(f"     Manually download from:\n          {CROSSWALK_URL}")
        print(f"     Save to: {CROSSWALK_LOCAL}")
        return pd.DataFrame()


def _dominant_county_map(crosswalk: pd.DataFrame) -> pd.DataFrame:
    """
    For each ZCTA, pick the county that contains its largest population share.
    Returns: DataFrame with columns [zcta5, county_fips, state_fips, alloc_factor].
    """
    if "alloc_factor" not in crosswalk.columns:
        crosswalk = crosswalk.copy()
        crosswalk["pop_in_county"] = pd.to_numeric(
            crosswalk["pop_in_county"], errors="coerce"
        ).fillna(0)
        crosswalk["zcta_pop"] = pd.to_numeric(
            crosswalk["zcta_pop"], errors="coerce"
        ).fillna(0)
        crosswalk["alloc_factor"] = np.where(
            crosswalk["zcta_pop"] > 0,
            crosswalk["pop_in_county"] / crosswalk["zcta_pop"],
            0,
        )

    dominant = (
        crosswalk.sort_values("alloc_factor", ascending=False)
        .drop_duplicates("zcta5", keep="first")[
            ["zcta5", "county_fips", "state_fips", "alloc_factor"]
        ]
        .copy()
    )
    return dominant


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Aggregate zip panel → county panel
# ─────────────────────────────────────────────────────────────────────────────
def aggregate_to_county(
    zip_df: pd.DataFrame,
    crosswalk: pd.DataFrame,
) -> pd.DataFrame:
    """
    Map 5-digit zip codes to counties and re-aggregate all metrics.

    Uses dominant-county mapping (each zip -> its largest-population county).
    This handles ~95 %+ of the US population correctly.  For the small
    fraction of zips that straddle county lines, the full prescription
    volume is assigned to the dominant county.

    Returns one row per (state, county_fips, year) — roughly 32 K rows.
    """
    if crosswalk.empty:
        print("     WARNING: No crosswalk available -- county aggregation skipped.")
        return pd.DataFrame()

    dominant = _dominant_county_map(crosswalk)
    print(f"     Dominant-county map: {len(dominant):,} ZCTAs -> counties")

    merged = zip_df.merge(
        dominant[["zcta5", "county_fips"]],
        left_on="zip_code",
        right_on="zcta5",
        how="left",
    )
    unmatched = merged["county_fips"].isna().sum()
    total = len(merged)
    print(
        f"     County match rate: {total - unmatched:,} / {total:,} "
        f"({(total - unmatched) / total * 100:.1f}%)"
    )

    matched = merged.dropna(subset=["county_fips"]).copy()

    # ── Aggregate to county × year ─────────────────────────────────────
    sum_cols = [
        "total_rx", "new_rx", "total_qty", "new_qty",
        "total_mme",
        "medicaid_rx", "medicaid_new_rx", "medicaid_qty", "medicaid_total_mme",
        "nonmedicaid_rx", "nonmedicaid_new_rx", "nonmedicaid_qty", "nonmedicaid_total_mme",
        "retail_rx", "mail_order_rx",
    ]
    agg_spec = {c: "sum" for c in sum_cols if c in matched.columns}
    agg_spec["distinct_prescribers"]     = "sum"
    agg_spec["distinct_opioid_products"] = "max"

    county = matched.groupby(
        ["state", "county_fips", "year"], as_index=False
    ).agg(agg_spec)

    # ── Recompute weighted-average MME at county level ────────────────
    county["avg_mme_per_unit"] = np.where(
        county["total_qty"] > 0,
        county["total_mme"] / county["total_qty"],
        0,
    )
    county["medicaid_avg_mme"] = np.where(
        county["medicaid_qty"] > 0,
        county["medicaid_total_mme"] / county["medicaid_qty"],
        0,
    )
    county["nonmedicaid_avg_mme"] = np.where(
        county["nonmedicaid_qty"] > 0,
        county["nonmedicaid_total_mme"] / county["nonmedicaid_qty"],
        0,
    )

    # ── Derived ratios ────────────────────────────────────────────────
    county["pct_medicaid"] = np.where(
        county["total_rx"] > 0,
        county["medicaid_rx"] / county["total_rx"] * 100,
        0,
    ).round(2)
    county["new_rx_ratio"] = np.where(
        county["total_rx"] > 0,
        county["new_rx"] / county["total_rx"] * 100,
        0,
    ).round(2)
    county["mail_order_pct"] = np.where(
        county["total_rx"] > 0,
        county["mail_order_rx"] / county["total_rx"] * 100,
        0,
    ).round(2)

    return county.sort_values(["state", "county_fips", "year"]).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# Run all
# ─────────────────────────────────────────────────────────────────────────────
def run_all(save: bool = True):
    """
    Full pipeline: SQL query -> zip panel -> county crosswalk -> county panel.

    Each year is saved incrementally; re-running after a failure resumes
    from the last completed year instead of starting over.
    """
    results = {}
    t_start = time.time()

    # Tune PostgreSQL session for analytical workload
    try:
        _tune_connection()
    except Exception:
        pass

    # ── 1. Zip × Year panel from IQVIA ──────────────────────────────────
    print("\n  1/3  Querying zip x year opioid panel (2008-2017) ...")
    print(f"         {len(YEARS)} years, 2 JOINs (prescriber + drug), ~3-6 min/year")
    df_zip = opioid_zip_year_panel()
    results["zip_panel"] = df_zip
    if save and not df_zip.empty:
        export_to_csv(df_zip, "iqvia_zip_year_panel.csv", subdir="county")
    if not df_zip.empty:
        print(
            f"         {len(df_zip):,} rows  |  "
            f"{df_zip['zip_code'].nunique():,} zips  |  "
            f"{df_zip['year'].nunique()} years"
        )

    # ── 2. Download / load ZCTA-County crosswalk ────────────────────────
    print("\n  2/3  Loading ZCTA -> County crosswalk ...")
    crosswalk = get_zcta_county_crosswalk()
    results["crosswalk"] = crosswalk

    # ── 3. Aggregate to county × year ───────────────────────────────────
    print("\n  3/3  Aggregating to county x year ...")
    if not crosswalk.empty and not df_zip.empty:
        df_county = aggregate_to_county(df_zip, crosswalk)
        results["county_panel"] = df_county
        if save and not df_county.empty:
            export_to_csv(df_county, "iqvia_county_year_panel.csv", subdir="county")
            print(
                f"         {len(df_county):,} rows  |  "
                f"{df_county['county_fips'].nunique():,} counties  |  "
                f"{df_county['year'].nunique()} years"
            )
    else:
        print("     WARNING: Skipped -- crosswalk or zip data missing.")
        results["county_panel"] = pd.DataFrame()

    total = time.time() - t_start
    print(f"\n  County panel complete -- total {total / 60:.1f} min")
    print(
        "\n  TIP: Merge with CDC WONDER county-level overdose deaths on "
        "(county_fips, year) to get the full picture."
    )
    return results


if __name__ == "__main__":
    run_all()
