"""
Merge IQVIA opioid prescribing data (by state) with CDC WONDER
overdose death data to answer:

  "Do states where Medicaid patients get more/less opioids
   also have higher/lower overdose death rates?"

Run standalone:  python -m cdc.merge_iqvia_cdc
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import numpy as np
from scipy import stats
from utils.db_utils import export_to_csv
from cdc.load_wonder import load_overdose_deaths

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")

# ── State abbreviation → full name mapping ─────────────────────────────────
STATE_ABBR_TO_NAME = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii",
    "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine",
    "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska",
    "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico",
    "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "PR": "Puerto Rico",
    "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
    "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
    "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming",
}
STATE_NAME_TO_ABBR = {v: k for k, v in STATE_ABBR_TO_NAME.items()}

# ── States that expanded Medicaid under ACA (effective 2014 or earlier) ────
# Source: KFF.org
ACA_EXPANSION_STATES = {
    "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "HI", "IL", "IN", "IA",
    "KY", "MD", "MA", "MI", "MN", "NV", "NH", "NJ", "NM", "NY", "ND",
    "OH", "OR", "PA", "RI", "VT", "WA", "WV", "WI",
}


def _load_iqvia_state_data() -> pd.DataFrame:
    """Load the Q3 state-level CSV if it exists."""
    csv_path = os.path.join(OUTPUT_DIR, "iqvia_core", "medicaid_vs_nonmedicaid_by_state.csv")
    if os.path.exists(csv_path):
        print(f"📂 Loading IQVIA state data from {csv_path}")
        return pd.read_csv(csv_path, dtype={"state": str})
    
    print("⚠  Q3 state CSV not found yet. Run main.py medicaid first.")
    print(f"   Expected: {csv_path}")
    return pd.DataFrame()


def merge_iqvia_cdc() -> pd.DataFrame:
    """
    Merge IQVIA state-level Medicaid vs Non-Medicaid opioid data
    with CDC WONDER overdose death rates.
    
    Returns a per-state DataFrame with:
      - IQVIA: medicaid_rx, nonmedicaid_rx, total_rx, pct_medicaid, avg_mme columns
      - CDC:   overdose_deaths (summed 2008-2018), avg_overdose_rate
      - Flag:  aca_expansion (True/False)
    """
    # ── Load IQVIA ─────────────────────────────────────────────────────────
    iqvia = _load_iqvia_state_data()
    if iqvia.empty:
        return pd.DataFrame()
    
    print(f"   IQVIA rows: {len(iqvia):,}, states: {iqvia['state'].nunique()}")
    
    # Pivot to wide: one row per state, Medicaid & Non-Medicaid side by side
    med = iqvia[iqvia["is_medicaid"] == "Medicaid"].copy()
    non = iqvia[iqvia["is_medicaid"] == "Non-Medicaid"].copy()
    
    med = med.rename(columns={
        "total_rx": "medicaid_rx",
        "new_rx": "medicaid_new_rx",
        "total_qty": "medicaid_qty",
    })[["state", "medicaid_rx", "medicaid_new_rx", "medicaid_qty"]]
    
    non = non.rename(columns={
        "total_rx": "nonmedicaid_rx",
        "new_rx": "nonmedicaid_new_rx",
        "total_qty": "nonmedicaid_qty",
    })[["state", "nonmedicaid_rx", "nonmedicaid_new_rx", "nonmedicaid_qty"]]
    
    merged = non.merge(med, on="state", how="left")
    merged["medicaid_rx"] = merged["medicaid_rx"].fillna(0)
    merged["total_rx"] = merged["nonmedicaid_rx"] + merged["medicaid_rx"]
    merged["pct_medicaid"] = (merged["medicaid_rx"] / merged["total_rx"] * 100).round(2)
    
    # Add full state name for CDC merge
    merged["state_name"] = merged["state"].map(STATE_ABBR_TO_NAME)
    
    # ── Load CDC WONDER ────────────────────────────────────────────────────
    cdc = load_overdose_deaths()
    cdc = cdc[(cdc["year"] >= 2008) & (cdc["year"] <= 2018)].copy()
    
    # Aggregate CDC to state level (sum deaths & pop across 2008-2018)
    cdc_agg = cdc.groupby("state").agg(
        total_overdose_deaths=("overdose_deaths", "sum"),
        total_pop_years=("population", "sum"),
        avg_annual_overdose_rate=("overdose_rate_per_100k", "mean"),
    ).reset_index()
    cdc_agg["overdose_rate_per_100k"] = (
        cdc_agg["total_overdose_deaths"] / cdc_agg["total_pop_years"] * 100_000
    ).round(2)
    cdc_agg = cdc_agg.rename(columns={"state": "state_name"})
    
    # ── Merge ──────────────────────────────────────────────────────────────
    final = merged.merge(cdc_agg, on="state_name", how="inner")
    
    # Add ACA expansion flag
    final["aca_expansion"] = final["state"].isin(ACA_EXPANSION_STATES)
    
    # Sort by overdose rate descending
    final = final.sort_values("overdose_rate_per_100k", ascending=False).reset_index(drop=True)
    
    print(f"\n✅ Merged dataset: {len(final)} states")
    print(f"   Columns: {list(final.columns)}")
    
    return final


def analyze_merged(df: pd.DataFrame) -> None:
    """Run statistical analysis on the merged IQVIA × CDC data."""
    if df.empty:
        print("⚠  No data to analyze.")
        return
    
    print("\n" + "═" * 60)
    print("  IQVIA × CDC WONDER: PRESCRIBING vs OVERDOSE DEATHS")
    print("═" * 60)
    
    # ── 1. Correlation: Medicaid % ↔ Overdose rate ─────────────────────────
    print("\n── Correlation: Medicaid Opioid % vs Overdose Death Rate ──")
    valid = df.dropna(subset=["pct_medicaid", "overdose_rate_per_100k"])
    r, p = stats.pearsonr(valid["pct_medicaid"], valid["overdose_rate_per_100k"])
    rho, p_rho = stats.spearmanr(valid["pct_medicaid"], valid["overdose_rate_per_100k"])
    print(f"  Pearson  r = {r:+.3f}  (p = {p:.4f})  {'✅ Significant' if p < 0.05 else '❌ Not significant'}")
    print(f"  Spearman ρ = {rho:+.3f}  (p = {p_rho:.4f})  {'✅ Significant' if p_rho < 0.05 else '❌ Not significant'}")
    if r > 0:
        print("  → States with HIGHER Medicaid opioid share tend to have HIGHER overdose rates")
    else:
        print("  → States with HIGHER Medicaid opioid share tend to have LOWER overdose rates")
    
    # ── 2. Correlation: Total Rx volume ↔ Overdose rate ────────────────────
    print("\n── Correlation: Total Opioid Rx Volume vs Overdose Death Rate ──")
    r2, p2 = stats.pearsonr(valid["total_rx"], valid["overdose_rate_per_100k"])
    print(f"  Pearson  r = {r2:+.3f}  (p = {p2:.4f})  {'✅ Significant' if p2 < 0.05 else '❌ Not significant'}")
    
    # ── 3. ACA Expansion vs Non-Expansion ──────────────────────────────────
    print("\n── ACA Medicaid Expansion States vs Non-Expansion ──")
    exp = df[df["aca_expansion"] == True]
    non_exp = df[df["aca_expansion"] == False]
    print(f"  Expansion states:     n={len(exp)}")
    print(f"    Avg overdose rate:  {exp['overdose_rate_per_100k'].mean():.1f} per 100K")
    print(f"    Avg Medicaid %:     {exp['pct_medicaid'].mean():.2f}%")
    print(f"  Non-expansion states: n={len(non_exp)}")
    print(f"    Avg overdose rate:  {non_exp['overdose_rate_per_100k'].mean():.1f} per 100K")
    print(f"    Avg Medicaid %:     {non_exp['pct_medicaid'].mean():.2f}%")
    
    t_stat, t_p = stats.ttest_ind(
        exp["overdose_rate_per_100k"].dropna(),
        non_exp["overdose_rate_per_100k"].dropna(),
        equal_var=False,
    )
    print(f"  Welch's t-test (overdose rate): t={t_stat:.3f}, p={t_p:.4f}  "
          f"{'✅ Significant' if t_p < 0.05 else '❌ Not significant'}")
    
    # ── 4. Top/Bottom states ───────────────────────────────────────────────
    print("\n── Top 10 States by Overdose Death Rate (per 100K) ──")
    top = df.nlargest(10, "overdose_rate_per_100k")
    for _, row in top.iterrows():
        flag = "🔵" if row["aca_expansion"] else "🔴"
        print(f"  {flag} {row['state_name']:22s}  OD rate: {row['overdose_rate_per_100k']:6.1f}  "
              f"Medicaid%: {row['pct_medicaid']:5.2f}%")
    
    print("\n── Bottom 10 States by Overdose Death Rate (per 100K) ──")
    bot = df.nsmallest(10, "overdose_rate_per_100k")
    for _, row in bot.iterrows():
        flag = "🔵" if row["aca_expansion"] else "🔴"
        print(f"  {flag} {row['state_name']:22s}  OD rate: {row['overdose_rate_per_100k']:6.1f}  "
              f"Medicaid%: {row['pct_medicaid']:5.2f}%")
    
    print("\n  🔵 = ACA expansion state   🔴 = Non-expansion state")
    
    # ── 5. Summary ─────────────────────────────────────────────────────────
    print("\n── Key Takeaways ──")
    if r > 0 and p < 0.05:
        print("  ⚠  Higher Medicaid opioid share is associated with MORE overdose deaths.")
    elif r < 0 and p < 0.05:
        print("  💡 Higher Medicaid opioid share is associated with FEWER overdose deaths.")
        print("     This supports the hypothesis that Medicaid prescribing is more conservative.")
    else:
        print("  📊 No statistically significant linear relationship between Medicaid opioid")
        print("     share and overdose death rates at the state level.")
    
    print("\n" + "═" * 60)
    print("  Done.")
    print("═" * 60)


# ── CLI ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    df = merge_iqvia_cdc()
    if not df.empty:
        export_to_csv(df, "iqvia_cdc_merged_by_state.csv")
        analyze_merged(df)
