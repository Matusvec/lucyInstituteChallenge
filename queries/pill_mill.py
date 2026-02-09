"""
Pill Mill Analysis — Prescriber Concentration & Outlier Detection.

CORE QUESTION
=============
Are Medicaid opioid prescriptions concentrated among a small number of
high-volume prescribers ("pill mills"), or spread broadly across normal
clinical practice?  And how does that compare to Non-Medicaid?

OUTPUT LAYERS (all cross-referenceable)
=======================================
1. **Prescriber-level rollup** — one row per prescriber with their opioid Rx
   totals, Medicaid share, drug diversity, and geographic info.
   Cross-refs: state → CDC overdose data, zip → Census demographics.

2. **State-level concentration metrics** — Gini coefficient, top-1%/5%/10%
   prescriber share, per state.  Merges directly with iqvia_cdc_merged_by_state.

3. **Specialty-level concentration** — which specialties have the most
   concentrated prescribing?  Merges with existing Q5 specialty data.

4. **Flagged outlier prescribers** — top-percentile prescribers with their
   state, specialty, drug mix, and Medicaid share.  Individual-level detail.

Run standalone:  python -m queries.pill_mill
Run via main:    python main.py pillmill
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

YEARS = list(range(1997, 2019))


def _query_by_year(sql_template: str, label: str) -> pd.DataFrame:
    """Run sql_template once per year, showing progress."""
    chunks = []
    t0_all = time.time()
    for i, yr in enumerate(YEARS, 1):
        t0 = time.time()
        sql = sql_template.format(year=yr)
        df = run_query(sql)
        elapsed = time.time() - t0
        print(f"       [{i}/{len(YEARS)}] {yr}  {len(df):>7,} rows  ({elapsed:.0f}s)", flush=True)
        if not df.empty:
            chunks.append(df)
    total = time.time() - t0_all
    result = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
    print(f"     ✅ {label} — {len(result):,} rows total in {total/60:.1f} min")
    return result


# ═════════════════════════════════════════════════════════════════════════════
# LAYER 1 — Prescriber-level rollup
# ═════════════════════════════════════════════════════════════════════════════
def prescriber_opioid_rollup() -> pd.DataFrame:
    """
    One row per prescriber: total opioid Rx, Medicaid Rx, drug diversity,
    quantity stats — enriched with state, specialty, zip from prescriber table.

    This is the foundation layer; all other analyses derive from it.

    Returns ~300K–500K rows (one per prescriber who wrote ≥1 opioid Rx).
    """
    med_ids = medicaid_ids_sql()
    opioid  = opioid_pgs_sql()

    # ── Fetch prescriber-level aggregates year-by-year ──────────────────
    # We grab: prescriber_key, Medicaid Rx, Non-Medicaid Rx, total qty,
    # distinct drug count (pg), new vs total Rx — all from main table.
    sql_t = f"""
        SELECT
            m.prescriber_key,
            SUM(m.total_rx)  / 1000.0                          AS total_rx,
            SUM(m.new_rx)    / 1000.0                          AS new_rx,
            SUM(m.total_qty) / 1000.0                          AS total_qty,
            SUM(CASE WHEN m.payor_plan_id IN {med_ids}
                     THEN m.total_rx ELSE 0 END) / 1000.0     AS medicaid_rx,
            SUM(CASE WHEN m.payor_plan_id IN {med_ids}
                     THEN m.total_qty ELSE 0 END) / 1000.0    AS medicaid_qty,
            COUNT(DISTINCT m.pg)                               AS distinct_drugs
        FROM main m
        WHERE m.pg IN {opioid} AND m.year = {{year}}
        GROUP BY m.prescriber_key;
    """
    df = _query_by_year(sql_t, "PillMill-prescriber-rollup")
    if df.empty:
        return df

    # ── Re-aggregate across all years (prescriber may appear in many years) ─
    print("     📊 Aggregating across all years …", flush=True)
    agg = df.groupby("prescriber_key", as_index=False).agg(
        total_rx=("total_rx", "sum"),
        new_rx=("new_rx", "sum"),
        total_qty=("total_qty", "sum"),
        medicaid_rx=("medicaid_rx", "sum"),
        medicaid_qty=("medicaid_qty", "sum"),
        distinct_drugs=("distinct_drugs", "max"),   # max across years ≈ breadth
        years_active=("prescriber_key", "count"),    # how many years they prescribed
    )

    # ── Derived metrics ────────────────────────────────────────────────
    agg["nonmedicaid_rx"]  = agg["total_rx"] - agg["medicaid_rx"]
    agg["pct_medicaid"]    = (agg["medicaid_rx"] / agg["total_rx"] * 100).round(2)
    agg["qty_per_rx"]      = np.where(agg["total_rx"] > 0,
                                       agg["total_qty"] / agg["total_rx"], 0).round(2)
    agg["new_rx_ratio"]    = np.where(agg["total_rx"] > 0,
                                       agg["new_rx"] / agg["total_rx"] * 100, 0).round(2)
    agg["rx_per_year"]     = (agg["total_rx"] / agg["years_active"]).round(1)

    # ── Enrich with prescriber state, specialty, zip ───────────────────
    print("     🔗 Enriching with prescriber demographics …", flush=True)
    t0 = time.time()
    unique_keys = agg["prescriber_key"].unique()

    prescriber_chunks = []
    batch_size = 50_000
    for start in range(0, len(unique_keys), batch_size):
        batch = tuple(unique_keys[start:start + batch_size].tolist())
        batch_sql = f"({batch[0]})" if len(batch) == 1 else str(batch)
        df_p = run_query(f"""
            SELECT prescriber_key, imsid, specialty, state, zip_code
            FROM prescriber_limited
            WHERE prescriber_key IN {batch_sql};
        """)
        prescriber_chunks.append(df_p)

    prescribers = pd.concat(prescriber_chunks, ignore_index=True).drop_duplicates("prescriber_key")
    agg = agg.merge(prescribers, on="prescriber_key", how="left")

    # zip3 for census cross-reference (census uses 5-digit, IQVIA has 5-digit)
    agg["zip3"] = agg["zip_code"].astype(str).str[:3]

    print(f"       Prescriber merge: {time.time()-t0:.1f}s  ({len(prescribers):,} prescribers)")

    # ── Volume percentile rank (for flagging outliers) ─────────────────
    agg["volume_percentile"] = agg["total_rx"].rank(pct=True).round(4) * 100

    return agg.sort_values("total_rx", ascending=False).reset_index(drop=True)


# ═════════════════════════════════════════════════════════════════════════════
# LAYER 2 — Concentration metrics (Gini, Top-N%) by state
#            → merges with iqvia_cdc_merged_by_state on "state"
# ═════════════════════════════════════════════════════════════════════════════
def _gini(values: np.ndarray) -> float:
    """Gini coefficient for an array of non-negative values."""
    v = np.sort(values)
    n = len(v)
    if n == 0 or v.sum() == 0:
        return 0.0
    index = np.arange(1, n + 1)
    return (2 * np.sum(index * v) - (n + 1) * np.sum(v)) / (n * np.sum(v))


def _top_pct_share(values: np.ndarray, pct: float) -> float:
    """What % of total is held by the top `pct`% of prescribers."""
    v = np.sort(values)[::-1]
    n = max(1, int(np.ceil(len(v) * pct / 100)))
    return v[:n].sum() / v.sum() * 100 if v.sum() > 0 else 0.0


def concentration_by_state(rollup: pd.DataFrame) -> pd.DataFrame:
    """
    Per-state prescriber concentration metrics.
    Columns: state, prescriber_count, gini_total, gini_medicaid,
             top1pct_share, top5pct_share, top10pct_share,
             avg_rx_per_prescriber, avg_medicaid_pct,
             pct_prescribers_any_medicaid.

    Cross-refs: state → CDC overdose rate, ACA expansion flag.
    """
    rows = []
    for state, grp in rollup.groupby("state"):
        if len(grp) < 10:
            continue  # skip tiny groups
        total_vals    = grp["total_rx"].values
        medicaid_vals = grp["medicaid_rx"].values

        rows.append({
            "state": state,
            "prescriber_count": len(grp),
            "total_opioid_rx": total_vals.sum(),
            "total_medicaid_rx": medicaid_vals.sum(),

            # Concentration — all opioid Rx
            "gini_total_rx": round(_gini(total_vals), 4),
            "top1pct_share_total":  round(_top_pct_share(total_vals, 1), 2),
            "top5pct_share_total":  round(_top_pct_share(total_vals, 5), 2),
            "top10pct_share_total": round(_top_pct_share(total_vals, 10), 2),

            # Concentration — Medicaid opioid Rx only
            "gini_medicaid_rx": round(_gini(medicaid_vals), 4),
            "top1pct_share_medicaid":  round(_top_pct_share(medicaid_vals, 1), 2),
            "top5pct_share_medicaid":  round(_top_pct_share(medicaid_vals, 5), 2),
            "top10pct_share_medicaid": round(_top_pct_share(medicaid_vals, 10), 2),

            # Prescriber averages
            "avg_rx_per_prescriber": round(total_vals.mean(), 1),
            "median_rx_per_prescriber": round(np.median(total_vals), 1),
            "avg_medicaid_pct": round(grp["pct_medicaid"].mean(), 2),
            "pct_prescribers_any_medicaid": round(
                (medicaid_vals > 0).sum() / len(grp) * 100, 2
            ),

            # Drug diversity
            "avg_distinct_drugs": round(grp["distinct_drugs"].mean(), 1),

            # Prescribing pattern
            "avg_new_rx_ratio": round(grp["new_rx_ratio"].mean(), 2),
            "avg_qty_per_rx": round(grp["qty_per_rx"].mean(), 2),
        })

    return pd.DataFrame(rows).sort_values("gini_total_rx", ascending=False).reset_index(drop=True)


# ═════════════════════════════════════════════════════════════════════════════
# LAYER 3 — Concentration by specialty
#            → merges with existing Q5 specialty data
# ═════════════════════════════════════════════════════════════════════════════
def concentration_by_specialty(rollup: pd.DataFrame) -> pd.DataFrame:
    """
    Per-specialty prescriber concentration metrics.
    Which specialties have the most concentrated (pill-mill-like) prescribing?
    """
    rows = []
    for spec, grp in rollup.groupby("specialty"):
        if len(grp) < 20:
            continue  # need reasonable sample
        total_vals    = grp["total_rx"].values
        medicaid_vals = grp["medicaid_rx"].values

        rows.append({
            "specialty": spec,
            "prescriber_count": len(grp),
            "total_opioid_rx": total_vals.sum(),

            "gini_total_rx": round(_gini(total_vals), 4),
            "top1pct_share_total": round(_top_pct_share(total_vals, 1), 2),
            "top5pct_share_total": round(_top_pct_share(total_vals, 5), 2),

            "gini_medicaid_rx": round(_gini(medicaid_vals), 4),
            "top1pct_share_medicaid": round(_top_pct_share(medicaid_vals, 1), 2),

            "avg_rx_per_prescriber": round(total_vals.mean(), 1),
            "avg_medicaid_pct": round(grp["pct_medicaid"].mean(), 2),
            "pct_prescribers_any_medicaid": round(
                (medicaid_vals > 0).sum() / len(grp) * 100, 2
            ),
        })

    return pd.DataFrame(rows).sort_values("gini_total_rx", ascending=False).reset_index(drop=True)


# ═════════════════════════════════════════════════════════════════════════════
# LAYER 4 — Flagged outlier prescribers (top 1%)
#            → individual-level detail for deep-dive
# ═════════════════════════════════════════════════════════════════════════════
def flag_outlier_prescribers(rollup: pd.DataFrame, pct_threshold: float = 99.0) -> pd.DataFrame:
    """
    Extract prescribers above the given volume percentile.
    Default: top 1% of all opioid prescribers.

    Output includes state, specialty, zip, Medicaid share, drug count,
    prescribing pattern — ready for case-study analysis or geographic overlay.
    """
    outliers = rollup[rollup["volume_percentile"] >= pct_threshold].copy()
    outliers = outliers.sort_values("total_rx", ascending=False).reset_index(drop=True)

    print(f"     🚨 {len(outliers):,} outlier prescribers (top {100 - pct_threshold:.0f}%)")
    print(f"        They wrote {outliers['total_rx'].sum():,.0f} total opioid Rx "
          f"({outliers['total_rx'].sum() / rollup['total_rx'].sum() * 100:.1f}% of all)")
    print(f"        Avg Medicaid %: {outliers['pct_medicaid'].mean():.1f}% "
          f"(vs {rollup['pct_medicaid'].mean():.1f}% overall)")

    return outliers


# ═════════════════════════════════════════════════════════════════════════════
# LAYER 5 — Summary statistics & cross-reference merge
# ═════════════════════════════════════════════════════════════════════════════
def merge_concentration_with_cdc(state_conc: pd.DataFrame) -> pd.DataFrame:
    """
    Merge state concentration metrics with CDC overdose data.
    Answers: Do states with more concentrated prescribing have higher OD rates?
    """
    cdc_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                            "output", "cdc", "iqvia_cdc_merged_by_state.csv")
    if not os.path.exists(cdc_path):
        print("     ⚠️  No CDC merged data found — skipping cross-reference")
        return state_conc

    cdc = pd.read_csv(cdc_path)
    merged = state_conc.merge(
        cdc[["state", "overdose_rate_per_100k", "aca_expansion", "pct_medicaid"]],
        on="state", how="left",
        suffixes=("_concentration", "_rx_share"),
    )
    # Rename to avoid confusion
    if "pct_medicaid_rx_share" in merged.columns:
        merged.rename(columns={"pct_medicaid_rx_share": "medicaid_rx_share_pct"}, inplace=True)

    return merged


def print_summary(rollup: pd.DataFrame, state_conc: pd.DataFrame):
    """Print headline findings from the pill mill analysis."""
    total = rollup["total_rx"].sum()
    med_total = rollup["medicaid_rx"].sum()

    # Nationally
    gini_all = _gini(rollup["total_rx"].values)
    gini_med = _gini(rollup["medicaid_rx"].values)
    top1_all = _top_pct_share(rollup["total_rx"].values, 1)
    top1_med = _top_pct_share(rollup["medicaid_rx"].values, 1)

    # Prescribers who write ANY Medicaid opioid Rx
    any_med = (rollup["medicaid_rx"] > 0).sum()
    pct_any_med = any_med / len(rollup) * 100

    # High-Medicaid prescribers (>50% of their Rx are Medicaid)
    high_med = rollup[rollup["pct_medicaid"] > 50]

    print("\n" + "═" * 70)
    print("📋  PILL MILL ANALYSIS — NATIONAL SUMMARY")
    print("═" * 70)
    print(f"  Total opioid prescribers:       {len(rollup):>10,}")
    print(f"  Total opioid Rx:                {total:>14,.0f}")
    print(f"  Total Medicaid opioid Rx:       {med_total:>14,.0f} ({med_total/total*100:.1f}%)")
    print()
    print(f"  ── Concentration (ALL opioid Rx) ──")
    print(f"  Gini coefficient:               {gini_all:.4f}")
    print(f"  Top 1% of prescribers write:    {top1_all:.1f}% of all opioid Rx")
    print(f"  Top 5% of prescribers write:    {_top_pct_share(rollup['total_rx'].values, 5):.1f}%")
    print(f"  Top 10% of prescribers write:   {_top_pct_share(rollup['total_rx'].values, 10):.1f}%")
    print()
    print(f"  ── Concentration (MEDICAID opioid Rx only) ──")
    print(f"  Gini coefficient:               {gini_med:.4f}")
    print(f"  Top 1% of prescribers write:    {top1_med:.1f}% of Medicaid opioid Rx")
    print(f"  Top 5% of prescribers write:    {_top_pct_share(rollup['medicaid_rx'].values, 5):.1f}%")
    print(f"  Top 10% of prescribers write:   {_top_pct_share(rollup['medicaid_rx'].values, 10):.1f}%")
    print()
    print(f"  ── Prescriber Behavior ──")
    print(f"  Prescribers writing ANY Medicaid: {any_med:,} ({pct_any_med:.1f}%)")
    print(f"  Prescribers >50% Medicaid:        {len(high_med):,} ({len(high_med)/len(rollup)*100:.2f}%)")
    print(f"  Avg Rx/prescriber (all):          {rollup['total_rx'].mean():.0f}")
    print(f"  Median Rx/prescriber (all):       {rollup['total_rx'].median():.0f}")
    print(f"  Avg distinct drugs/prescriber:    {rollup['distinct_drugs'].mean():.1f}")
    print()

    # Quick correlation with CDC if available
    if "overdose_rate_per_100k" in state_conc.columns:
        valid = state_conc.dropna(subset=["overdose_rate_per_100k", "gini_total_rx"])
        if len(valid) > 10:
            from scipy import stats
            r, p = stats.pearsonr(valid["gini_total_rx"], valid["overdose_rate_per_100k"])
            r_top1, p_top1 = stats.pearsonr(valid["top1pct_share_total"], valid["overdose_rate_per_100k"])
            print(f"  ── Cross-Reference: Concentration ↔ Overdose Deaths ──")
            print(f"  Gini ↔ OD rate:    r = {r:+.3f}  (p = {p:.4f})")
            print(f"  Top1% ↔ OD rate:   r = {r_top1:+.3f}  (p = {p_top1:.4f})")
            if p < 0.05:
                direction = "MORE" if r > 0 else "LESS"
                print(f"  ⚡ SIGNIFICANT: States with {direction} concentrated prescribing "
                      f"have {'higher' if r > 0 else 'lower'} overdose rates")
            else:
                print(f"  ❌ No significant relationship between concentration and overdose rates")
    print("═" * 70)


# ═════════════════════════════════════════════════════════════════════════════
# Run all
# ═════════════════════════════════════════════════════════════════════════════
def run_all(save: bool = True):
    results = {}
    t_start = time.time()

    # ── Layer 1: Prescriber rollup (the big DB query) ──────────────────
    print("\n🔍 PILL MILL ANALYSIS")
    print("─" * 50)
    print("\n💊 Layer 1 — Prescriber-level opioid rollup …")
    rollup = prescriber_opioid_rollup()
    results["rollup"] = rollup
    if save:
        export_to_csv(rollup, "pillmill_prescriber_rollup.csv", subdir="pillmill")

    # ── Layer 2: State concentration metrics ───────────────────────────
    print("\n📊 Layer 2 — Concentration metrics by state …")
    state_conc = concentration_by_state(rollup)
    print(state_conc.head(15).to_string(index=False))
    results["state_concentration"] = state_conc
    if save:
        export_to_csv(state_conc, "pillmill_concentration_by_state.csv", subdir="pillmill")

    # ── Layer 3: Specialty concentration metrics ───────────────────────
    print("\n📊 Layer 3 — Concentration metrics by specialty …")
    spec_conc = concentration_by_specialty(rollup)
    print(spec_conc.head(15).to_string(index=False))
    results["specialty_concentration"] = spec_conc
    if save:
        export_to_csv(spec_conc, "pillmill_concentration_by_specialty.csv", subdir="pillmill")

    # ── Layer 4: Outlier prescribers ───────────────────────────────────
    print("\n🚨 Layer 4 — Flagged outlier prescribers (top 1%) …")
    outliers = flag_outlier_prescribers(rollup, pct_threshold=99.0)
    results["outliers"] = outliers
    if save:
        export_to_csv(outliers, "pillmill_outlier_prescribers.csv", subdir="pillmill")

    # ── Layer 5: Cross-reference with CDC data ─────────────────────────
    print("\n🔗 Layer 5 — Merging concentration with CDC overdose data …")
    state_merged = merge_concentration_with_cdc(state_conc)
    results["state_merged"] = state_merged
    if save:
        export_to_csv(state_merged, "pillmill_state_concentration_with_cdc.csv", subdir="pillmill")

    # ── Summary ────────────────────────────────────────────────────────
    print_summary(rollup, state_merged)

    total = time.time() - t_start
    print(f"\n🏁 Pill mill analysis complete — total {total/60:.1f} min")
    return results


if __name__ == "__main__":
    run_all()
