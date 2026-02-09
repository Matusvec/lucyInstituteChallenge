"""
Explore the payor_plan table to identify Medicaid vs non-Medicaid plan categories.

Run standalone:  python -m queries.explore_payors
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.db_utils import run_query, export_to_csv


def get_all_payor_plans() -> "pd.DataFrame":
    """Return every row in payor_plan (only ~15 k rows)."""
    sql = """
        SELECT payor_plan_id, payor_plan, payor_plan_var
        FROM payor_plan
        ORDER BY payor_plan, payor_plan_var;
    """
    return run_query(sql)


def get_payor_plan_summary() -> "pd.DataFrame":
    """Distinct payor_plan values and how many sub-variants each has."""
    sql = """
        SELECT payor_plan,
               COUNT(DISTINCT payor_plan_var) AS variant_count,
               COUNT(*)                       AS row_count
        FROM payor_plan
        GROUP BY payor_plan
        ORDER BY row_count DESC;
    """
    return run_query(sql)


def get_medicaid_plan_ids() -> "pd.DataFrame":
    """
    Return payor_plan rows whose name/variant suggests Medicaid.
    Uses ILIKE for case-insensitive matching.
    """
    sql = """
        SELECT payor_plan_id, payor_plan, payor_plan_var
        FROM payor_plan
        WHERE payor_plan ILIKE '%%medicaid%%'
           OR payor_plan_var ILIKE '%%medicaid%%';
    """
    return run_query(sql)


def run_all(save: bool = True):
    """Run all payor exploration queries and optionally save to CSV."""
    print("\n📋 Payor Plan Summary (distinct plan types):")
    summary = get_payor_plan_summary()
    print(summary.to_string(index=False))

    print("\n🏥 Medicaid-related plan IDs:")
    medicaid = get_medicaid_plan_ids()
    if medicaid.empty:
        print("  ⚠️  No plans matched 'medicaid'. Check full list for alternate names.")
    else:
        print(medicaid.to_string(index=False))

    if save:
        export_to_csv(summary,  "payor_plan_summary.csv", subdir="lookups")
        export_to_csv(medicaid, "medicaid_plan_ids.csv", subdir="lookups")

        # Also dump full table for reference
        full = get_all_payor_plans()
        export_to_csv(full, "payor_plan_full.csv", subdir="lookups")

    return summary, medicaid


if __name__ == "__main__":
    run_all()
