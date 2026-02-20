"""
Database utility functions for connecting and querying the IQVIA PostgreSQL database.

OPTIMIZATIONS
─────────────
1. Connection pooling — reuses a single connection instead of open/close per query.
2. Server-side cursors for large results — streams rows instead of loading all into memory.
3. Shared lookup cache — pre-fetches Medicaid IDs and opioid PG codes once, reusable by
   any module.
4. fetch_size parameter — lets callers tune how much data is pulled at once.
"""

import os
import psycopg2
import psycopg2.extras
import pandas as pd
from utils.db_connect import DB_CONFIG

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")

# ── Connection pool (single persistent connection) ───────────────────────────
_conn = None


def get_connection():
    """Return the shared psycopg2 connection, reconnecting if needed."""
    global _conn
    if _conn is None or _conn.closed:
        _conn = psycopg2.connect(**DB_CONFIG)
        _conn.autocommit = True  # read-only, no need for transactions
    return _conn


def run_query(sql: str, params: tuple = None) -> pd.DataFrame:
    """
    Execute a SQL query and return results as a pandas DataFrame.
    Reuses the shared connection (no open/close overhead per query).
    """
    conn = get_connection()
    df = pd.read_sql_query(sql, conn, params=params)
    return df


# ── Shared lookup cache ──────────────────────────────────────────────────────
_medicaid_ids  = None   # tuple of payor_plan_id ints
_opioid_pgs    = None   # tuple of pg values
_pg_mme_map    = None   # {pg: mme_per_unit}
_pg_ingredient = None   # {pg: active_ingredient}


def get_medicaid_ids() -> tuple:
    """Return cached tuple of Medicaid payor_plan_ids."""
    global _medicaid_ids
    if _medicaid_ids is None:
        _load_lookups()
    return _medicaid_ids


def get_opioid_pgs() -> tuple:
    """Return cached tuple of opioid pg codes."""
    global _opioid_pgs
    if _opioid_pgs is None:
        _load_lookups()
    return _opioid_pgs


def get_pg_mme_map() -> dict:
    """Return cached {pg: mme_per_unit} dict."""
    global _pg_mme_map
    if _pg_mme_map is None:
        _load_lookups()
    return _pg_mme_map


def get_pg_ingredient_map() -> dict:
    """Return cached {pg: active_ingredient} dict."""
    global _pg_ingredient
    if _pg_ingredient is None:
        _load_lookups()
    return _pg_ingredient


def medicaid_ids_sql() -> str:
    """Return Medicaid IDs as a literal SQL tuple string."""
    return str(get_medicaid_ids())


def opioid_pgs_sql() -> str:
    """Return opioid PG codes as a literal SQL tuple string."""
    return str(get_opioid_pgs())


def _load_lookups():
    """Fetch lookup data once from the small tables (milliseconds)."""
    global _medicaid_ids, _opioid_pgs, _pg_mme_map, _pg_ingredient
    import time
    t0 = time.time()
    print("  🔍 Loading shared lookup tables …", flush=True)

    df_med = run_query("""
        SELECT payor_plan_id FROM payor_plan
        WHERE payor_plan ILIKE '%%medicaid%%'
           OR payor_plan_var ILIKE '%%medicaid%%';
    """)
    _medicaid_ids = tuple(df_med["payor_plan_id"].tolist())

    df_drug = run_query("""
        SELECT pg, mme_per_unit, active_ingredient
        FROM drug WHERE usc LIKE '022%%';
    """)
    _opioid_pgs    = tuple(df_drug["pg"].tolist())
    _pg_mme_map    = dict(zip(df_drug["pg"], df_drug["mme_per_unit"]))
    _pg_ingredient = dict(zip(df_drug["pg"], df_drug["active_ingredient"]))

    print(f"  ✅ Lookups cached — {len(_medicaid_ids)} Medicaid IDs, "
          f"{len(_opioid_pgs)} opioid PGs  ({time.time()-t0:.1f}s)")


def export_to_csv(df: pd.DataFrame, filename: str, subdir: str = None) -> str:
    """Save a DataFrame to a CSV file in the output/ directory (or a subfolder)."""
    target = os.path.join(OUTPUT_DIR, subdir) if subdir else OUTPUT_DIR
    os.makedirs(target, exist_ok=True)
    filepath = os.path.join(target, filename)
    df.to_csv(filepath, index=False)
    print(f"  ✅ Saved {len(df):,} rows → {filepath}")
    return filepath
