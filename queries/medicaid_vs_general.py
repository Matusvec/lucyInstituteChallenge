"""
Medicaid vs Non-Medicaid opioid prescription comparison queries.

SUPER-OPTIMIZED VERSION
=======================
1. Pre-fetches Medicaid payor_plan_ids and opioid pg codes as LITERAL
   tuples from the tiny lookup tables BEFORE touching the 2.1B-row main.
   → PostgreSQL sees hardcoded integer lists, not subqueries.
2. Eliminates JOINs wherever possible — the drug JOIN is only used when
   we need active_ingredient or mme_per_unit; otherwise pure main-table scan.
3. Query 2 (% share) is computed in Python from Query 1 output — zero DB cost.
4. Queries 3 and 5 drop the drug JOIN entirely — one fewer table to scan.
5. Literal IN (...) tuples let PostgreSQL use index/hash lookups directly.

Run standalone:  python -m queries.medicaid_vs_general
"""

import sys, os, time
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.db_utils import (
    run_query,
    export_to_csv,
    medicaid_ids_sql,
    opioid_pgs_sql,
    get_pg_mme_map,
    get_pg_ingredient_map,
)


def _timed_call(label, func):
    t0 = time.time()
    print(f"     ⏳ Querying …", flush=True)
    df = func()
    elapsed = time.time() - t0
    print(f"     ✅ {label} — {len(df):,} rows in {elapsed/60:.1f} min")
    return df


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
# Q1: By YEAR  — NO drug JOIN.  Pure main-table scan.  Year-by-year.
#     avg_mme computed in Python from the cached pg→mme map.
# ─────────────────────────────────────────────────────────────────────────────
def opioid_rx_by_medicaid_status_year() -> pd.DataFrame:
    med  = medicaid_ids_sql()
    opg  = opioid_pgs_sql()
    sql_t = f"""
        SELECT
            m.year,
            m.pg,
            CASE WHEN m.payor_plan_id IN {med}
                 THEN 'Medicaid' ELSE 'Non-Medicaid'
            END                                AS is_medicaid,
            SUM(m.total_rx)  / 1000.0          AS total_rx,
            SUM(m.new_rx)    / 1000.0          AS new_rx,
            SUM(m.total_qty) / 1000.0          AS total_qty
        FROM main m
        WHERE m.pg IN {opg} AND m.year = {{year}}
        GROUP BY m.year, m.pg, is_medicaid
        ORDER BY is_medicaid;
    """
    df = _query_by_year(sql_t, "Q1-by-year")

    if df.empty:
        return df

    # Map pg → mme_per_unit in Python, compute qty-weighted avg
    mme_map = get_pg_mme_map()
    df["mme_per_unit"] = df["pg"].map(mme_map).fillna(0)

    # Collapse pg dimension → year × is_medicaid
    agg = df.groupby(["year", "is_medicaid"], as_index=False).apply(
        lambda g: pd.Series({
            "total_rx":  g["total_rx"].sum(),
            "new_rx":    g["new_rx"].sum(),
            "total_qty": g["total_qty"].sum(),
            "avg_mme":   (g["total_qty"] * g["mme_per_unit"]).sum()
                         / g["total_qty"].sum() if g["total_qty"].sum() else 0,
        })
    ).reset_index(drop=False)
    for c in agg.columns:
        if c.startswith("level_"):
            agg.drop(columns=c, inplace=True)
    return agg.sort_values(["year", "is_medicaid"]).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# Q2: % share — FREE, derived from Q1 in Python (no DB call)
# ─────────────────────────────────────────────────────────────────────────────
def opioid_rx_pct_medicaid_year(q1_df: pd.DataFrame) -> pd.DataFrame:
    pivot = q1_df.pivot_table(
        index="year", columns="is_medicaid", values="total_rx", aggfunc="sum"
    ).reset_index()
    pivot.columns.name = None
    pivot = pivot.rename(columns={"Medicaid": "medicaid_rx", "Non-Medicaid": "non_medicaid_rx"})
    pivot["total_rx"] = pivot["medicaid_rx"].fillna(0) + pivot["non_medicaid_rx"].fillna(0)
    pivot["pct_medicaid"] = (pivot["medicaid_rx"] / pivot["total_rx"] * 100).round(2)
    pivot["pct_non_medicaid"] = (pivot["non_medicaid_rx"] / pivot["total_rx"] * 100).round(2)
    return pivot.sort_values("year").reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# Q3: By STATE  (main + prescriber JOIN only — NO drug JOIN)
# ─────────────────────────────────────────────────────────────────────────────
def opioid_rx_medicaid_by_state() -> pd.DataFrame:
    med  = medicaid_ids_sql()
    opg  = opioid_pgs_sql()
    sql_t = f"""
        SELECT
            p.state,
            CASE WHEN m.payor_plan_id IN {med}
                 THEN 'Medicaid' ELSE 'Non-Medicaid'
            END                                AS is_medicaid,
            SUM(m.total_rx)  / 1000.0          AS total_rx,
            SUM(m.new_rx)    / 1000.0          AS new_rx,
            SUM(m.total_qty) / 1000.0          AS total_qty
        FROM main m
        JOIN prescriber_limited p ON m.prescriber_key = p.prescriber_key
        WHERE m.pg IN {opg} AND m.year = {{year}}
        GROUP BY p.state, is_medicaid
        ORDER BY p.state, is_medicaid;
    """
    df = _query_by_year(sql_t, "Q3-by-state")
    if df.empty:
        return df
    # Re-aggregate across all years
    return df.groupby(["state", "is_medicaid"], as_index=False).agg(
        total_rx=("total_rx", "sum"),
        new_rx=("new_rx", "sum"),
        total_qty=("total_qty", "sum"),
    ).sort_values(["state", "is_medicaid"]).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# Q4: By DRUG  (main + drug JOIN for ingredient name + mme)
# ─────────────────────────────────────────────────────────────────────────────
def opioid_rx_medicaid_by_drug() -> pd.DataFrame:
    med  = medicaid_ids_sql()
    opg  = opioid_pgs_sql()
    sql_t = f"""
        SELECT
            m.pg,
            CASE WHEN m.payor_plan_id IN {med}
                 THEN 'Medicaid' ELSE 'Non-Medicaid'
            END                                AS is_medicaid,
            SUM(m.total_rx) / 1000.0           AS total_rx,
            SUM(m.total_qty) / 1000.0          AS total_qty
        FROM main m
        WHERE m.pg IN {opg} AND m.year = {{year}}
        GROUP BY m.pg, is_medicaid
        ORDER BY total_rx DESC;
    """
    df = _query_by_year(sql_t, "Q4-by-drug")
    if df.empty:
        return df

    # Map pg → ingredient and mme in Python
    ing_map = get_pg_ingredient_map()
    mme_map = get_pg_mme_map()
    df["active_ingredient"] = df["pg"].map(ing_map)
    df["mme_per_unit"]      = df["pg"].map(mme_map).fillna(0)

    # Collapse to ingredient level across all years
    agg = df.groupby(["active_ingredient", "is_medicaid"], as_index=False).agg(
        total_rx=("total_rx", "sum"),
        total_qty=("total_qty", "sum"),
        avg_mme=("mme_per_unit", "mean"),
    )
    return agg.sort_values("total_rx", ascending=False).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# Q5: By SPECIALTY  (main + prescriber JOIN only — NO drug JOIN)
# ─────────────────────────────────────────────────────────────────────────────
def opioid_rx_medicaid_by_specialty() -> pd.DataFrame:
    med  = medicaid_ids_sql()
    opg  = opioid_pgs_sql()
    sql_t = f"""
        SELECT
            p.specialty,
            CASE WHEN m.payor_plan_id IN {med}
                 THEN 'Medicaid' ELSE 'Non-Medicaid'
            END                                AS is_medicaid,
            SUM(m.total_rx) / 1000.0           AS total_rx
        FROM main m
        JOIN prescriber_limited p ON m.prescriber_key = p.prescriber_key
        WHERE m.pg IN {opg} AND m.year = {{year}}
        GROUP BY p.specialty, is_medicaid
        ORDER BY total_rx DESC;
    """
    df = _query_by_year(sql_t, "Q5-by-specialty")
    if df.empty:
        return df
    # Re-aggregate across all years
    return df.groupby(["specialty", "is_medicaid"], as_index=False).agg(
        total_rx=("total_rx", "sum"),
    ).sort_values("total_rx", ascending=False).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# Run all
# ─────────────────────────────────────────────────────────────────────────────
def run_all(save: bool = True):
    results = {}
    t_start = time.time()

    # ── Q1: by year ──
    print("\n📊 1/5  Opioid Rx by Medicaid status & year …")
    df1 = opioid_rx_by_medicaid_status_year()
    print(df1.head(10).to_string(index=False))
    results["by_year"] = df1
    if save:
        export_to_csv(df1, "medicaid_vs_nonmedicaid_by_year.csv", subdir="iqvia_core")

    # ── Q2: % share (FREE from Q1) ──
    print("\n📊 2/5  Percentage Medicaid vs Non-Medicaid by year …")
    t0 = time.time()
    df2 = opioid_rx_pct_medicaid_year(df1)
    print(f"     ✅ Q2-pct — {len(df2):,} rows in {time.time()-t0:.2f}s  ⚡ no DB call")
    print(df2.to_string(index=False))
    results["pct_year"] = df2
    if save:
        export_to_csv(df2, "medicaid_pct_by_year.csv", subdir="iqvia_core")

    # ── Q3: by state ──
    print("\n📊 3/5  Medicaid vs Non-Medicaid by state …")
    df3 = opioid_rx_medicaid_by_state()
    print(df3.head(20).to_string(index=False))
    results["by_state"] = df3
    if save:
        export_to_csv(df3, "medicaid_vs_nonmedicaid_by_state.csv", subdir="iqvia_core")

    # ── Q4: by drug ──
    print("\n📊 4/5  Medicaid vs Non-Medicaid by drug (active ingredient) …")
    df4 = opioid_rx_medicaid_by_drug()
    print(df4.head(20).to_string(index=False))
    results["by_drug"] = df4
    if save:
        export_to_csv(df4, "medicaid_vs_nonmedicaid_by_drug.csv", subdir="iqvia_core")

    # ── Q5: by specialty ──
    print("\n📊 5/5  Medicaid vs Non-Medicaid by prescriber specialty …")
    df5 = opioid_rx_medicaid_by_specialty()
    print(df5.head(20).to_string(index=False))
    results["by_specialty"] = df5
    if save:
        export_to_csv(df5, "medicaid_vs_nonmedicaid_by_specialty.csv", subdir="iqvia_core")

    total = time.time() - t_start
    print(f"\n🏁 All 5 queries complete — total {total/60:.1f} min")
    return results


if __name__ == "__main__":
    run_all()
