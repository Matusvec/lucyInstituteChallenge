"""
Quick optimized test: Indiana, 2018.

Uses the same optimizations as the full pipeline:
  - Literal IN (...) tuples for Medicaid IDs and opioid PGs
  - Only 1 JOIN (prescriber) for zip/state — NO drug or payor_plan JOIN
  - pg→mme mapped in Python from cached lookup
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))

from utils.db_utils import (
    run_query, export_to_csv,
    medicaid_ids_sql, opioid_pgs_sql, get_pg_mme_map,
)

med  = medicaid_ids_sql()
opg  = opioid_pgs_sql()

sql = f"""
SELECT
    p.zip_code, p.state, m.pg,
    CASE WHEN m.payor_plan_id IN {med}
         THEN 'Medicaid' ELSE 'Non-Medicaid'
    END                              AS is_medicaid,
    SUM(m.total_rx)  / 1000.0       AS total_rx,
    SUM(m.total_qty) / 1000.0       AS total_qty
FROM main m
JOIN prescriber_limited p ON m.prescriber_key = p.prescriber_key
WHERE m.pg IN {opg}
  AND m.year = 2018
  AND p.state = 'IN'
GROUP BY p.zip_code, p.state, m.pg, is_medicaid
ORDER BY total_rx DESC;
"""

print("⏳ Running OPTIMIZED test query (Indiana, 2018) …")
t0 = time.time()
df = run_query(sql)
elapsed = time.time() - t0
print(f"✅ Query returned {len(df):,} rows in {elapsed:.1f}s\n")

# Map pg → mme in Python
mme_map = get_pg_mme_map()
df["mme_per_unit"] = df["pg"].map(mme_map).fillna(0)

# Collapse pg dimension → zip × medicaid
agg = df.groupby(["zip_code", "state", "is_medicaid"], as_index=False).agg(
    total_rx=("total_rx", "sum"),
    total_qty=("total_qty", "sum"),
    avg_mme=("mme_per_unit", "mean"),
)

print(agg.to_string(index=False))
print(f"\nRows: {len(agg)}")
export_to_csv(agg, "test_indiana_2018.csv")
