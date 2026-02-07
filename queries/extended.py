"""
Extended queries — additional analyses for the Lucy Institute Challenge.

NEW QUERIES
===========
Q6  — State × Year: Medicaid vs Non-Medicaid opioid prescribing by state AND year
      (enables difference-in-differences around ACA 2014 expansion)
Q7  — Retail vs Mail Order: sales_category breakdown by Medicaid status & year
      (mail order = chronic/maintenance; retail = acute)
Q8  — Monthly Seasonality: month-level prescribing by Medicaid status
      (seasonal patterns, policy-change detection)
Q9  — Stratified 2018 Sample: ~2M row random sample for logistic regression
      (predict Medicaid Y/N from drug, specialty, state, quantity, MME)

All queries follow the same year-by-year scan pattern as medicaid_vs_general.py
to avoid memory issues with the 2.1B-row main table.

Run standalone:  python -m queries.extended
Run via main:    python main.py extended
"""

import sys, os, time
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.db_utils import (
    run_query,
    export_to_csv,
    medicaid_ids_sql,
    opioid_pgs_sql,
    get_pg_mme_map,
    get_pg_ingredient_map,
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
# Q6: State × Year — Medicaid vs Non-Medicaid
#     Like the existing Q3 (by state) but KEEPS the year dimension.
#     Enables: difference-in-differences, ACA expansion analysis, trend lines.
#     Requires prescriber JOIN for state mapping.
# ─────────────────────────────────────────────────────────────────────────────
def opioid_rx_by_state_year_medicaid() -> pd.DataFrame:
    """
    Opioid Rx totals by state × year × Medicaid status.
    Returns ~2,200 rows (≈51 states × 22 years × 2 groups).
    """
    med_ids = medicaid_ids_sql()
    opioid  = opioid_pgs_sql()
    sql_t = f"""
        SELECT
            p.state,
            m.year,
            CASE WHEN m.payor_plan_id IN {med_ids}
                 THEN 'Medicaid' ELSE 'Non-Medicaid'
            END                              AS is_medicaid,
            SUM(m.total_rx)  / 1000.0        AS total_rx,
            SUM(m.new_rx)    / 1000.0        AS new_rx,
            SUM(m.total_qty) / 1000.0        AS total_qty
        FROM main m
        JOIN prescriber_limited p ON m.prescriber_key = p.prescriber_key
        WHERE m.pg IN {opioid} AND m.year = {{year}}
        GROUP BY p.state, m.year, is_medicaid
        ORDER BY p.state, is_medicaid;
    """
    df = _query_by_year(sql_t, "Q6-state-year")
    if df.empty:
        return df
    return df.sort_values(["state", "year", "is_medicaid"]).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# Q7: Retail vs Mail Order — by Medicaid status & year
#     sales_category: 1 = Retail, 2 = Mail Order
#     Mail order typically means 90-day chronic fills.
#     No JOINs needed — pure main-table scan.
# ─────────────────────────────────────────────────────────────────────────────
def opioid_rx_by_sales_channel_year() -> pd.DataFrame:
    """
    Opioid Rx totals by sales_category × year × Medicaid status.
    Tests whether Medicaid has less mail-order (chronic) prescribing.
    """
    med_ids = medicaid_ids_sql()
    opioid  = opioid_pgs_sql()
    sql_t = f"""
        SELECT
            m.year,
            m.sales_category,
            CASE WHEN m.payor_plan_id IN {med_ids}
                 THEN 'Medicaid' ELSE 'Non-Medicaid'
            END                              AS is_medicaid,
            SUM(m.total_rx)  / 1000.0        AS total_rx,
            SUM(m.new_rx)    / 1000.0        AS new_rx,
            SUM(m.total_qty) / 1000.0        AS total_qty
        FROM main m
        WHERE m.pg IN {opioid} AND m.year = {{year}}
        GROUP BY m.year, m.sales_category, is_medicaid
        ORDER BY m.year, m.sales_category, is_medicaid;
    """
    df = _query_by_year(sql_t, "Q7-sales-channel")
    if df.empty:
        return df

    # Map numeric codes to readable labels
    channel_map = {1: "Retail", 2: "Mail Order"}
    df["sales_channel"] = df["sales_category"].map(channel_map).fillna("Unknown")

    return df.sort_values(["year", "sales_channel", "is_medicaid"]).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# Q8: Monthly Seasonality — by Medicaid status
#     Aggregates across ALL years to get the average monthly pattern.
#     No JOINs needed — pure main-table scan.
# ─────────────────────────────────────────────────────────────────────────────
def opioid_rx_by_month_medicaid() -> pd.DataFrame:
    """
    Opioid Rx totals by month × year × Medicaid status.
    Returns year × month × group detail; can be further aggregated for
    average monthly patterns or year-over-year monthly trends.
    """
    med_ids = medicaid_ids_sql()
    opioid  = opioid_pgs_sql()
    sql_t = f"""
        SELECT
            m.year,
            m.month,
            CASE WHEN m.payor_plan_id IN {med_ids}
                 THEN 'Medicaid' ELSE 'Non-Medicaid'
            END                              AS is_medicaid,
            SUM(m.total_rx)  / 1000.0        AS total_rx,
            SUM(m.new_rx)    / 1000.0        AS new_rx,
            SUM(m.total_qty) / 1000.0        AS total_qty
        FROM main m
        WHERE m.pg IN {opioid} AND m.year = {{year}}
        GROUP BY m.year, m.month, is_medicaid
        ORDER BY m.month, is_medicaid;
    """
    df = _query_by_year(sql_t, "Q8-monthly")
    if df.empty:
        return df
    return df.sort_values(["year", "month", "is_medicaid"]).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# Q9: Stratified Random Sample — 2018 only, ~2M rows
#     Pulls a ~2% stratified sample from 2018 for logistic regression.
#     Keeps Medicaid proportion intact (stratified by payor_plan_id bucket).
#     Enriches each row with: state, specialty, active_ingredient, mme.
#     This is the only query that returns ROW-LEVEL data (not aggregated).
# ─────────────────────────────────────────────────────────────────────────────
def stratified_sample_2018(target_rows: int = 2_000_000) -> pd.DataFrame:
    """
    Pull a stratified random sample from 2018 for logistic regression.

    Strategy: Use PostgreSQL's TABLESAMPLE or random() to draw ~2% of 2018 rows.
    Since TABLESAMPLE works on blocks (not exact row counts), we use
    ORDER BY random() with a LIMIT — run in month-by-month chunks to
    manage memory and keep the stratification natural.

    Each row gets enriched with prescriber state/specialty and drug info
    via Python-side mapping (no expensive DB JOINs).
    """
    med_ids = medicaid_ids_sql()
    opioid  = opioid_pgs_sql()

    # Estimate: ~100M rows in 2018, want ~2M → 2% sample
    # We'll pull ~167K per month (2M / 12) using random() + LIMIT
    rows_per_month = target_rows // 12
    remaining = target_rows - (rows_per_month * 12)  # distribute remainder

    chunks = []
    t0_all = time.time()

    for i, month in enumerate(range(1, 13), 1):
        t0 = time.time()
        limit = rows_per_month + (1 if i <= remaining else 0)

        sql = f"""
            SELECT
                m.prescriber_key,
                m.payor_plan_id,
                m.sales_category,
                m.pg,
                m.month,
                m.new_rx    / 1000.0  AS new_rx,
                m.total_rx  / 1000.0  AS total_rx,
                m.total_qty / 1000.0  AS total_qty,
                CASE WHEN m.payor_plan_id IN {med_ids}
                     THEN 1 ELSE 0
                END                   AS is_medicaid
            FROM main m
            WHERE m.pg IN {opioid}
              AND m.year = 2018
              AND m.month = {month}
            ORDER BY random()
            LIMIT {limit};
        """
        df = run_query(sql)
        elapsed = time.time() - t0
        print(f"       [{i}/12] Month {month:>2}  {len(df):>7,} rows  ({elapsed:.0f}s)", flush=True)
        if not df.empty:
            chunks.append(df)

    total_time = time.time() - t0_all
    sample = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
    print(f"     ✅ Q9-sample — {len(sample):,} rows total in {total_time/60:.1f} min")

    if sample.empty:
        return sample

    # ── Enrich with prescriber info (state, specialty) ──────────────────
    print("     🔗 Enriching with prescriber state & specialty …", flush=True)
    t0 = time.time()

    # Get unique prescriber keys from sample, fetch their info
    unique_keys = sample["prescriber_key"].unique()
    # Fetch in batches of 50K to avoid SQL length limits
    prescriber_chunks = []
    batch_size = 50_000
    for start in range(0, len(unique_keys), batch_size):
        batch = tuple(unique_keys[start:start + batch_size].tolist())
        if len(batch) == 1:
            batch_sql = f"({batch[0]})"
        else:
            batch_sql = str(batch)
        df_p = run_query(f"""
            SELECT prescriber_key, specialty, state, zip_code
            FROM prescriber_limited
            WHERE prescriber_key IN {batch_sql};
        """)
        prescriber_chunks.append(df_p)

    prescribers = pd.concat(prescriber_chunks, ignore_index=True).drop_duplicates("prescriber_key")
    sample = sample.merge(prescribers, on="prescriber_key", how="left")
    print(f"       Prescriber merge: {time.time()-t0:.1f}s  ({len(prescribers):,} unique prescribers)")

    # ── Enrich with drug info (ingredient, MME) ────────────────────────
    mme_map = get_pg_mme_map()
    ing_map = get_pg_ingredient_map()
    sample["mme_per_unit"]      = sample["pg"].map(mme_map).fillna(0)
    sample["active_ingredient"] = sample["pg"].map(ing_map).fillna("Unknown")

    # Derived features for the logistic regression
    sample["mme_total"]    = sample["total_qty"] * sample["mme_per_unit"]
    sample["qty_per_rx"]   = np.where(sample["total_rx"] > 0,
                                       sample["total_qty"] / sample["total_rx"], 0)
    sample["new_rx_ratio"] = np.where(sample["total_rx"] > 0,
                                       sample["new_rx"] / sample["total_rx"], 0)

    # Map sales category
    sample["sales_channel"] = sample["sales_category"].map(
        {1: "Retail", 2: "Mail_Order"}
    ).fillna("Unknown")

    print(f"     ✅ Enrichment complete — {len(sample):,} rows, "
          f"{sample['is_medicaid'].sum():,} Medicaid ({sample['is_medicaid'].mean()*100:.1f}%)")

    return sample


# ─────────────────────────────────────────────────────────────────────────────
# Run all extended queries
# ─────────────────────────────────────────────────────────────────────────────
def run_all(save: bool = True):
    results = {}
    t_start = time.time()

    # ── Q6: State × Year ──
    print("\n📊 Q6  Opioid Rx by state × year × Medicaid status …")
    df6 = opioid_rx_by_state_year_medicaid()
    print(df6.head(20).to_string(index=False))
    results["state_year"] = df6
    if save:
        export_to_csv(df6, "medicaid_vs_nonmedicaid_by_state_year.csv")

    # ── Q7: Retail vs Mail Order ──
    print("\n📊 Q7  Opioid Rx by sales channel (Retail vs Mail Order) × year …")
    df7 = opioid_rx_by_sales_channel_year()
    print(df7.head(20).to_string(index=False))
    results["sales_channel"] = df7
    if save:
        export_to_csv(df7, "medicaid_vs_nonmedicaid_by_sales_channel.csv")

    # ── Q8: Monthly Seasonality ──
    print("\n📊 Q8  Opioid Rx by month × year × Medicaid status …")
    df8 = opioid_rx_by_month_medicaid()
    print(df8.head(20).to_string(index=False))
    results["monthly"] = df8
    if save:
        export_to_csv(df8, "medicaid_vs_nonmedicaid_by_month.csv")

    # ── Q9: Stratified 2018 Sample ──
    print("\n📊 Q9  Stratified 2018 random sample (~2M rows) for logistic regression …")
    df9 = stratified_sample_2018(target_rows=2_000_000)
    print(f"     Shape: {df9.shape}")
    print(f"     Medicaid %: {df9['is_medicaid'].mean()*100:.2f}%")
    print(f"     Columns: {list(df9.columns)}")
    results["sample_2018"] = df9
    if save:
        export_to_csv(df9, "sample_2018_for_regression.csv")

    total = time.time() - t_start
    print(f"\n🏁 All extended queries complete — total {total/60:.1f} min")
    return results


if __name__ == "__main__":
    run_all()
