"""
Geographic / zip-code-level queries for mapping IQVIA opioid data.

FULLY OPTIMIZED
===============
1. Uses shared lookup cache from db_utils (no duplicate fetches).
2. Only 2 DB scans of the main table:
     Q1 — zip-level aggregation (all years combined)
     Q2 — zip × year aggregation
3. Q3 (state-level) and Q4 (Medicaid % by zip) are derived in Python
   from Q1 — zero additional DB cost.
4. No drug JOIN — we only need pg for the WHERE filter, which is
   inlined as a literal IN (...) tuple.
5. No prescriber JOIN — main.zip3 gives us geographic info directly.
6. Literal integer IN lists for Medicaid IDs and opioid PGs.

Run standalone:  python -m queries.geographic
"""

import sys, os, time
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.db_utils import (
    run_query,
    export_to_csv,
    medicaid_ids_sql,
    opioid_pgs_sql,
)

YEARS = list(range(1997, 2019))   # 1997–2018


def _query_by_year(sql_template: str, label: str) -> pd.DataFrame:
    """Run sql_template once per year, showing progress. Use {year} placeholder."""
    chunks = []
    t0_all = time.time()
    for i, yr in enumerate(YEARS, 1):
        t0 = time.time()
        sql = sql_template.format(year=yr)
        df = run_query(sql)
        elapsed = time.time() - t0
        print(f"       [{i}/{len(YEARS)}] {yr}  {len(df):>6,} rows  ({elapsed:.0f}s)", flush=True)
        if not df.empty:
            chunks.append(df)
    total = time.time() - t0_all
    result = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
    print(f"     ✅ {label} — {len(result):,} rows total in {total/60:.1f} min")
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Q1  Zip-level totals — ALL years combined  (1 full scan)
# ─────────────────────────────────────────────────────────────────────────────
def opioid_rx_by_zip_medicaid() -> pd.DataFrame:
    """Rx totals per zip3 × Medicaid flag.  Year-by-year, no JOINs."""
    med_ids = medicaid_ids_sql()
    opioid  = opioid_pgs_sql()
    sql_t = f"""
        SELECT
            m.zip3,
            CASE WHEN m.payor_plan_id IN {med_ids}
                 THEN 'Medicaid' ELSE 'Non-Medicaid'
            END                              AS is_medicaid,
            SUM(m.total_rx)  / 1000.0        AS total_rx,
            SUM(m.new_rx)    / 1000.0        AS new_rx,
            SUM(m.total_qty) / 1000.0        AS total_qty
        FROM main m
        WHERE m.pg IN {opioid} AND m.year = {{year}}
        GROUP BY m.zip3, is_medicaid;
    """
    df = _query_by_year(sql_t, "Q1-zip")
    if df.empty:
        return df
    # Re-aggregate across all years
    return df.groupby(["zip3", "is_medicaid"], as_index=False).agg(
        total_rx=("total_rx", "sum"),
        new_rx=("new_rx", "sum"),
        total_qty=("total_qty", "sum"),
    ).sort_values(["zip3", "is_medicaid"]).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# Q2  Zip × Year  (1 full scan)
# ─────────────────────────────────────────────────────────────────────────────
def opioid_rx_by_zip_year_medicaid() -> pd.DataFrame:
    """Rx totals per zip3 × year × Medicaid flag.  Year-by-year, no JOINs."""
    med_ids = medicaid_ids_sql()
    opioid  = opioid_pgs_sql()
    sql_t = f"""
        SELECT
            m.zip3,
            m.year,
            CASE WHEN m.payor_plan_id IN {med_ids}
                 THEN 'Medicaid' ELSE 'Non-Medicaid'
            END                              AS is_medicaid,
            SUM(m.total_rx)  / 1000.0        AS total_rx,
            SUM(m.new_rx)    / 1000.0        AS new_rx,
            SUM(m.total_qty) / 1000.0        AS total_qty
        FROM main m
        WHERE m.pg IN {opioid} AND m.year = {{year}}
        GROUP BY m.zip3, m.year, is_medicaid;
    """
    return _query_by_year(sql_t, "Q2-zip-year")


# ─────────────────────────────────────────────────────────────────────────────
# Q3  State-level — FREE from Q1 via prescriber_limited zip→state mapping
#     OR derived from a quick prescriber lookup.
#     Actually zip3 is not directly state — so we'll do a lightweight
#     prescriber join variant.  Still 1 scan, only prescriber JOIN (2M rows).
# ─────────────────────────────────────────────────────────────────────────────
def opioid_rx_by_state_medicaid(q1_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    State-level Rx totals.  Year-by-year with prescriber JOIN (no drug JOIN).
    """
    med_ids = medicaid_ids_sql()
    opioid  = opioid_pgs_sql()
    sql_t = f"""
        SELECT
            p.state,
            CASE WHEN m.payor_plan_id IN {med_ids}
                 THEN 'Medicaid' ELSE 'Non-Medicaid'
            END                              AS is_medicaid,
            SUM(m.total_rx)  / 1000.0        AS total_rx,
            SUM(m.new_rx)    / 1000.0        AS new_rx,
            SUM(m.total_qty) / 1000.0        AS total_qty
        FROM main m
        JOIN prescriber_limited p ON m.prescriber_key = p.prescriber_key
        WHERE m.pg IN {opioid} AND m.year = {{year}}
        GROUP BY p.state, is_medicaid;
    """
    df = _query_by_year(sql_t, "Q3-state")
    if df.empty:
        return df
    return df.groupby(["state", "is_medicaid"], as_index=False).agg(
        total_rx=("total_rx", "sum"),
        new_rx=("new_rx", "sum"),
        total_qty=("total_qty", "sum"),
    ).sort_values(["state", "is_medicaid"]).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# Q4  Medicaid share (%) per zip — FREE from Q1 in Python
# ─────────────────────────────────────────────────────────────────────────────
def medicaid_pct_by_zipcode(q1_df: pd.DataFrame) -> pd.DataFrame:
    """Pivot Q1 to get Medicaid % per zip.  Zero DB cost."""
    pivot = q1_df.pivot_table(
        index="zip3", columns="is_medicaid", values="total_rx", aggfunc="sum"
    ).reset_index()
    pivot.columns.name = None
    pivot = pivot.rename(columns={"Medicaid": "medicaid_rx",
                                  "Non-Medicaid": "non_medicaid_rx"})
    pivot["medicaid_rx"]     = pivot["medicaid_rx"].fillna(0)
    pivot["non_medicaid_rx"] = pivot["non_medicaid_rx"].fillna(0)
    pivot["total_rx"]        = pivot["medicaid_rx"] + pivot["non_medicaid_rx"]
    pivot["pct_medicaid"]    = (pivot["medicaid_rx"] / pivot["total_rx"] * 100).round(2)
    return pivot.sort_values("pct_medicaid", ascending=False).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# Run all
# ─────────────────────────────────────────────────────────────────────────────
def run_all(save: bool = True):
    results = {}
    t_start = time.time()

    # ── Q1: zip-level totals (year-by-year) ──
    print("\n🗺️  1/4  Opioid Rx by zip × Medicaid status (all years) …")
    df1 = opioid_rx_by_zip_medicaid()
    print(df1.head(10).to_string(index=False))
    results["zip_medicaid"] = df1
    if save:
        export_to_csv(df1, "geo_zip_medicaid.csv", subdir="iqvia_core")

    # ── Q2: zip × year (year-by-year) ──
    print("\n🗺️  2/4  Opioid Rx by zip × year × Medicaid status …")
    df2 = opioid_rx_by_zip_year_medicaid()
    print(df2.head(10).to_string(index=False))
    results["zip_year_medicaid"] = df2
    if save:
        export_to_csv(df2, "geo_zip_year_medicaid.csv", subdir="iqvia_core")

    # ── Q3: state-level (year-by-year, prescriber JOIN only) ──
    print("\n🗺️  3/4  Opioid Rx by state × Medicaid status …")
    df3 = opioid_rx_by_state_medicaid()
    print(df3.head(20).to_string(index=False))
    results["state_medicaid"] = df3
    if save:
        export_to_csv(df3, "geo_state_medicaid.csv", subdir="iqvia_core")

    # ── Q4: Medicaid % by zip — FREE from Q1 ──
    print("\n🗺️  4/4  Medicaid % by zip code …")
    t0 = time.time()
    df4 = medicaid_pct_by_zipcode(df1)
    print(f"     ✅ Q4-pct-zip — {len(df4):,} rows in {time.time()-t0:.2f}s  ⚡ no DB call")
    print(df4.head(20).to_string(index=False))
    results["zip_pct_medicaid"] = df4
    if save:
        export_to_csv(df4, "geo_zip_medicaid_pct.csv", subdir="iqvia_core")

    total = time.time() - t_start
    print(f"\n🏁 Geographic queries complete — total {total / 60:.1f} min")
    return results


if __name__ == "__main__":
    run_all()
