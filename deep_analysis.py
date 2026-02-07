"""
Deep-dive cross-analysis of all IQVIA + CDC data.
Looks for unexpected patterns and connections across Q1-Q5 + CDC.

Usage:  python deep_analysis.py
"""

import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import chi2_contingency, spearmanr, pearsonr, linregress
import os, warnings
warnings.filterwarnings("ignore")

OUT = os.path.join(os.path.dirname(__file__), "output")

def load(name):
    return pd.read_csv(os.path.join(OUT, name))

def section(title):
    print(f"\n{'═'*70}")
    print(f"  {title}")
    print(f"{'═'*70}")

def subsection(title):
    print(f"\n  ── {title} ──")


# ═══════════════════════════════════════════════════════════════════════
#  LOAD ALL DATA
# ═══════════════════════════════════════════════════════════════════════
print("Loading all datasets...")
q1 = load("medicaid_vs_nonmedicaid_by_year.csv")
q2 = load("medicaid_pct_by_year.csv")
q3 = load("medicaid_vs_nonmedicaid_by_state.csv")
q4 = load("medicaid_vs_nonmedicaid_by_drug.csv")
q5 = load("medicaid_vs_nonmedicaid_by_specialty.csv")
cdc = load("cdc_overdose_by_state_year.csv")
merged = load("iqvia_cdc_merged_by_state.csv")
print("  ✅ All loaded.\n")


# ═══════════════════════════════════════════════════════════════════════
section("1. DRUG PORTFOLIO ANALYSIS — What drugs is each group getting?")
# ═══════════════════════════════════════════════════════════════════════

med_drugs = q4[q4["is_medicaid"] == "Medicaid"].copy()
non_drugs = q4[q4["is_medicaid"] == "Non-Medicaid"].copy()

# Market share within each group
med_drugs["pct_of_medicaid"] = (med_drugs["total_rx"] / med_drugs["total_rx"].sum() * 100)
non_drugs["pct_of_nonmedicaid"] = (non_drugs["total_rx"] / non_drugs["total_rx"].sum() * 100)

portfolio = med_drugs[["active_ingredient", "total_rx", "pct_of_medicaid", "avg_mme"]].merge(
    non_drugs[["active_ingredient", "total_rx", "pct_of_nonmedicaid", "avg_mme"]],
    on="active_ingredient", suffixes=("_med", "_non")
)
portfolio["share_ratio"] = portfolio["pct_of_medicaid"] / portfolio["pct_of_nonmedicaid"]
portfolio = portfolio.sort_values("share_ratio", ascending=False)

subsection("Drugs OVER-REPRESENTED in Medicaid (share ratio > 1 = more Medicaid)")
print(f"  {'Drug':<22s} {'Med%':>7s} {'NonMed%':>8s} {'Ratio':>6s}  {'MedMME':>7s} {'NonMME':>7s}")
for _, r in portfolio.iterrows():
    flag = "🔴" if r["share_ratio"] > 1.5 else "🟡" if r["share_ratio"] > 1.0 else "🟢"
    print(f"  {flag} {r['active_ingredient']:<20s} {r['pct_of_medicaid']:>6.2f}% {r['pct_of_nonmedicaid']:>7.2f}% "
          f"{r['share_ratio']:>5.2f}x  {r['avg_mme_med']:>7.1f} {r['avg_mme_non']:>7.1f}")

# Herfindahl-Hirschman Index (market concentration)
subsection("Drug Market Concentration (HHI)")
hhi_med = (med_drugs["pct_of_medicaid"]**2).sum()
hhi_non = (non_drugs["pct_of_nonmedicaid"]**2).sum()
print(f"  Medicaid HHI:     {hhi_med:.0f}")
print(f"  Non-Medicaid HHI: {hhi_non:.0f}")
if hhi_med > hhi_non:
    print(f"  → Medicaid prescribing is MORE concentrated in fewer drugs")
else:
    print(f"  → Non-Medicaid prescribing is MORE concentrated in fewer drugs")

# Top 3 drugs share
med_top3 = med_drugs.nlargest(3, "total_rx")["pct_of_medicaid"].sum()
non_top3 = non_drugs.nlargest(3, "total_rx")["pct_of_nonmedicaid"].sum()
print(f"  Top 3 drugs share — Medicaid: {med_top3:.1f}%  Non-Medicaid: {non_top3:.1f}%")


# ═══════════════════════════════════════════════════════════════════════
section("2. BUPRENORPHINE — Opioid Addiction Treatment Drug")
# ═══════════════════════════════════════════════════════════════════════
bup_med = med_drugs[med_drugs["active_ingredient"] == "buprenorphine"]
bup_non = non_drugs[non_drugs["active_ingredient"] == "buprenorphine"]
if len(bup_med) and len(bup_non):
    bup_med_rx = bup_med["total_rx"].values[0]
    bup_non_rx = bup_non["total_rx"].values[0]
    bup_pct = bup_med_rx / (bup_med_rx + bup_non_rx) * 100
    print(f"  Buprenorphine Medicaid Rx:     {bup_med_rx:>14,.0f}")
    print(f"  Buprenorphine Non-Medicaid Rx: {bup_non_rx:>14,.0f}")
    print(f"  Medicaid share of buprenorphine: {bup_pct:.1f}%")
    print(f"  (vs overall Medicaid share of ~3.5%)")
    if bup_pct > 5:
        print(f"  💡 Buprenorphine is DISPROPORTIONATELY Medicaid — suggests Medicaid")
        print(f"     is being used to fund opioid addiction TREATMENT, not just prescribing")


# ═══════════════════════════════════════════════════════════════════════
section("3. PROPOXYPHENE BAN EFFECT (pulled from market Nov 2010)")
# ═══════════════════════════════════════════════════════════════════════
# Q1 has year-level data — check if we can see the propoxyphene effect
# The year data has avg_mme by year — propoxyphene removal should show a dip
q1_med = q1[q1["is_medicaid"] == "Medicaid"].copy()
q1_non = q1[q1["is_medicaid"] == "Non-Medicaid"].copy()
if len(q1_med) > 0:
    print("  Total Rx Volume Changes Around 2010 (propoxyphene ban):")
    for label, grp in [("Medicaid", q1_med), ("Non-Medicaid", q1_non)]:
        for yr in [2009, 2010, 2011, 2012]:
            row = grp[grp["year"] == yr]
            if len(row):
                print(f"    {label:<14s} {yr}: {row['total_rx'].values[0]:>14,.0f} Rx")
    print("  (Look for a dip in 2011+ as propoxyphene Rx disappear)")


# ═══════════════════════════════════════════════════════════════════════
section("4. NEW Rx RATIO — Chronic vs Acute Prescribing by State")
# ═══════════════════════════════════════════════════════════════════════
q3_wide = q3.pivot_table(index="state", columns="is_medicaid", 
                          values=["total_rx", "new_rx"], aggfunc="sum").reset_index()
q3_wide.columns = ["_".join(c).strip("_") for c in q3_wide.columns]

# Calculate new Rx % for each state
if "new_rx_Medicaid" in q3_wide.columns and "total_rx_Medicaid" in q3_wide.columns:
    q3_wide["med_new_pct"] = q3_wide["new_rx_Medicaid"] / q3_wide["total_rx_Medicaid"] * 100
    q3_wide["non_new_pct"] = q3_wide["new_rx_Non-Medicaid"] / q3_wide["total_rx_Non-Medicaid"] * 100
    q3_wide["new_pct_diff"] = q3_wide["med_new_pct"] - q3_wide["non_new_pct"]
    
    # Filter to states with meaningful data
    q3_valid = q3_wide[q3_wide["total_rx_Medicaid"] > 10000].copy()
    
    print(f"  Analyzing {len(q3_valid)} states with significant Medicaid opioid volume\n")
    print(f"  National avg: Medicaid new Rx = {q3_valid['med_new_pct'].mean():.1f}%, "
          f"Non-Medicaid = {q3_valid['non_new_pct'].mean():.1f}%")
    
    subsection("States where Medicaid has MOST new Rx (least chronic prescribing)")
    top_new = q3_valid.nlargest(10, "med_new_pct")
    for _, r in top_new.iterrows():
        print(f"    {r['state']:>4s}  Medicaid new: {r['med_new_pct']:5.1f}%  "
              f"Non-Med new: {r['non_new_pct']:5.1f}%  (diff: {r['new_pct_diff']:+.1f})")
    
    subsection("States where Medicaid has LEAST new Rx (most chronic/refill prescribing)")
    bot_new = q3_valid.nsmallest(10, "med_new_pct")
    for _, r in bot_new.iterrows():
        print(f"    {r['state']:>4s}  Medicaid new: {r['med_new_pct']:5.1f}%  "
              f"Non-Med new: {r['non_new_pct']:5.1f}%  (diff: {r['new_pct_diff']:+.1f})")

    # Correlate new Rx % with overdose rates
    subsection("Does 'chronic prescribing' correlate with overdose deaths?")
    # Merge with CDC
    q3_cdc = q3_valid.merge(merged[["state", "overdose_rate_per_100k"]], on="state", how="inner")
    if len(q3_cdc) > 5:
        r_med, p_med = spearmanr(q3_cdc["med_new_pct"], q3_cdc["overdose_rate_per_100k"])
        r_non, p_non = spearmanr(q3_cdc["non_new_pct"], q3_cdc["overdose_rate_per_100k"])
        print(f"    Medicaid new Rx % vs OD rate:     ρ={r_med:+.3f}  p={p_med:.4f}  "
              f"{'✅' if p_med < 0.05 else '❌'}")
        print(f"    Non-Medicaid new Rx % vs OD rate: ρ={r_non:+.3f}  p={p_non:.4f}  "
              f"{'✅' if p_non < 0.05 else '❌'}")
        if p_non < 0.05 and r_non < 0:
            print(f"    💡 States where Non-Medicaid has more REFILLS have HIGHER overdose rates!")
            print(f"       → Chronic non-Medicaid prescribing may be a better predictor of overdose risk")


# ═══════════════════════════════════════════════════════════════════════
section("5. SPECIALTY CONCENTRATION — Who prescribes Medicaid opioids?")
# ═══════════════════════════════════════════════════════════════════════
med_spec = q5[q5["is_medicaid"] == "Medicaid"].copy()
non_spec = q5[q5["is_medicaid"] == "Non-Medicaid"].copy()

# Calculate Medicaid share for each specialty
spec_wide = q5.pivot_table(index="specialty", columns="is_medicaid", values="total_rx", aggfunc="sum").reset_index()
spec_wide.columns = ["specialty", "med_rx", "nonmed_rx"]
spec_wide = spec_wide.dropna()
spec_wide["total_rx"] = spec_wide["med_rx"].fillna(0) + spec_wide["nonmed_rx"].fillna(0)
spec_wide["pct_medicaid"] = spec_wide["med_rx"].fillna(0) / spec_wide["total_rx"] * 100
spec_wide = spec_wide[spec_wide["total_rx"] > 100000]  # meaningful volume only

subsection(f"Specialties with HIGHEST Medicaid opioid share (n={len(spec_wide)} with >100K Rx)")
top_med = spec_wide.nlargest(15, "pct_medicaid")
for _, r in top_med.iterrows():
    bar = "█" * int(r["pct_medicaid"] * 2)
    print(f"    {r['specialty']:<8s}  {r['pct_medicaid']:5.1f}% Medicaid  "
          f"(total: {r['total_rx']:>12,.0f} Rx)  {bar}")

subsection("Specialties with LOWEST Medicaid opioid share")
bot_med = spec_wide[spec_wide["total_rx"] > 1000000].nsmallest(10, "pct_medicaid")
for _, r in bot_med.iterrows():
    print(f"    {r['specialty']:<8s}  {r['pct_medicaid']:5.1f}% Medicaid  "
          f"(total: {r['total_rx']:>12,.0f} Rx)")

# Gini coefficient of Medicaid Rx across specialties
med_sorted = np.sort(med_spec["total_rx"].values)
n = len(med_sorted)
gini_med = (2 * np.sum(np.arange(1, n+1) * med_sorted) / (n * med_sorted.sum())) - (n+1)/n
non_sorted = np.sort(non_spec["total_rx"].values)
n2 = len(non_sorted)
gini_non = (2 * np.sum(np.arange(1, n2+1) * non_sorted) / (n2 * non_sorted.sum())) - (n2+1)/n2

subsection("Prescribing Concentration (Gini coefficient)")
print(f"    Medicaid Gini:     {gini_med:.3f}")
print(f"    Non-Medicaid Gini: {gini_non:.3f}")
print(f"    (Higher = more concentrated in fewer specialties)")
# Top 5 specialties share
med_top5_spec = med_spec.nlargest(5, "total_rx")["total_rx"].sum() / med_spec["total_rx"].sum() * 100
non_top5_spec = non_spec.nlargest(5, "total_rx")["total_rx"].sum() / non_spec["total_rx"].sum() * 100
print(f"    Top 5 specialties prescribe: Medicaid {med_top5_spec:.1f}%  Non-Medicaid {non_top5_spec:.1f}%")


# ═══════════════════════════════════════════════════════════════════════
section("6. QUANTITY PER Rx — Are Medicaid patients getting bigger fills?")
# ═══════════════════════════════════════════════════════════════════════
# By drug
q4_both = q4.pivot_table(index="active_ingredient", columns="is_medicaid",
                          values=["total_rx", "total_qty"], aggfunc="sum").reset_index()
q4_both.columns = ["_".join(c).strip("_") for c in q4_both.columns]
q4_both["qty_per_rx_med"] = q4_both["total_qty_Medicaid"] / q4_both["total_rx_Medicaid"]
q4_both["qty_per_rx_non"] = q4_both["total_qty_Non-Medicaid"] / q4_both["total_rx_Non-Medicaid"]
q4_both["qty_ratio"] = q4_both["qty_per_rx_med"] / q4_both["qty_per_rx_non"]
q4_both = q4_both.sort_values("qty_ratio", ascending=False)

print(f"  {'Drug':<22s} {'Med qty/Rx':>10s} {'NonMed qty/Rx':>13s} {'Ratio':>6s}")
for _, r in q4_both.head(15).iterrows():
    flag = "🔴" if r["qty_ratio"] > 1.1 else "🟢" if r["qty_ratio"] < 0.9 else "⚪"
    print(f"  {flag} {r['active_ingredient']:<20s} {r['qty_per_rx_med']:>10.1f} {r['qty_per_rx_non']:>13.1f} "
          f"{r['qty_ratio']:>5.2f}x")

# Paired test across drugs
t_qty, p_qty = stats.ttest_rel(q4_both["qty_per_rx_med"].dropna(), q4_both["qty_per_rx_non"].dropna())
print(f"\n  Paired t-test (qty per Rx, Med vs NonMed across {len(q4_both)} drugs):")
print(f"    t = {t_qty:.3f},  p = {p_qty:.4f}  {'✅ Significant' if p_qty < 0.05 else '❌ Not significant'}")


# ═══════════════════════════════════════════════════════════════════════
section("7. STATE-LEVEL MEDICAID SHARE vs OVERDOSE — Deeper Dive")
# ═══════════════════════════════════════════════════════════════════════
# Instead of total Medicaid %, look at specific metrics
q3_state = q3.pivot_table(index="state", columns="is_medicaid",
                           values=["total_rx", "new_rx", "total_qty"], aggfunc="sum").reset_index()
q3_state.columns = ["_".join(c).strip("_") for c in q3_state.columns]

# Only states with Medicaid data and significant volume
q3_state = q3_state[q3_state.get("total_rx_Medicaid", pd.Series([0])).fillna(0) > 10000].copy()
q3_state["med_pct"] = q3_state["total_rx_Medicaid"] / (q3_state["total_rx_Medicaid"] + q3_state["total_rx_Non-Medicaid"]) * 100
q3_state["qty_per_rx_med"] = q3_state["total_qty_Medicaid"] / q3_state["total_rx_Medicaid"]
q3_state["qty_per_rx_non"] = q3_state["total_qty_Non-Medicaid"] / q3_state["total_rx_Non-Medicaid"]
q3_state["qty_ratio"] = q3_state["qty_per_rx_med"] / q3_state["qty_per_rx_non"]

# Merge with CDC
state_cdc = q3_state.merge(merged[["state", "overdose_rate_per_100k", "aca_expansion"]], on="state", how="inner")

subsection("Correlation matrix — State-level metrics vs Overdose Rate")
metrics = {
    "Medicaid % of Rx": ("med_pct", state_cdc["med_pct"]),
    "Medicaid qty/Rx": ("qty_per_rx_med", state_cdc["qty_per_rx_med"]),
    "NonMed qty/Rx": ("qty_per_rx_non", state_cdc["qty_per_rx_non"]),
    "Qty ratio (Med/Non)": ("qty_ratio", state_cdc["qty_ratio"]),
    "Total Rx volume": ("total_rx_Non-Medicaid", state_cdc["total_rx_Non-Medicaid"]),
}
for name, (col, series) in metrics.items():
    valid = state_cdc[[col, "overdose_rate_per_100k"]].dropna()
    if len(valid) > 5:
        r, p = spearmanr(valid[col], valid["overdose_rate_per_100k"])
        sig = "✅ SIG" if p < 0.05 else "❌ ns "
        print(f"    {sig}  {name:<25s}  ρ={r:+.3f}  p={p:.4f}")


# ═══════════════════════════════════════════════════════════════════════
section("8. YEAR-OVER-YEAR CHANGE RATES — Acceleration/Deceleration")
# ═══════════════════════════════════════════════════════════════════════
for label in ["Medicaid", "Non-Medicaid"]:
    grp = q1[q1["is_medicaid"] == label].sort_values("year").copy()
    if len(grp) > 1:
        grp["rx_change_pct"] = grp["total_rx"].pct_change() * 100
        grp["mme_change"] = grp["avg_mme"].diff()
        subsection(f"{label} — Year-over-Year Changes")
        for _, r in grp.dropna(subset=["rx_change_pct"]).iterrows():
            rx_dir = "📈" if r["rx_change_pct"] > 0 else "📉"
            mme_dir = "⬆" if r["mme_change"] > 0 else "⬇"
            print(f"    {int(r['year'])}  Rx: {r['rx_change_pct']:+5.1f}% {rx_dir}   "
                  f"MME: {r['mme_change']:+.3f} {mme_dir}")


# ═══════════════════════════════════════════════════════════════════════
section("9. NATIONAL OVERDOSE TREND vs PRESCRIBING TREND")
# ═══════════════════════════════════════════════════════════════════════
# National overdose deaths by year
cdc_national = cdc.groupby("year").agg(
    total_deaths=("overdose_deaths", "sum"),
    total_pop=("population", "sum"),
).reset_index()
cdc_national["od_rate"] = cdc_national["total_deaths"] / cdc_national["total_pop"] * 100000

# Total opioid Rx by year (from Q1)
q1_total = q1.groupby("year")["total_rx"].sum().reset_index()
q1_total.columns = ["year", "total_opioid_rx"]

# Merge
trend = cdc_national.merge(q1_total, on="year", how="inner")
print(f"  {'Year':>4s}  {'OD Deaths':>10s}  {'OD Rate':>8s}  {'Opioid Rx':>14s}")
for _, r in trend.iterrows():
    print(f"  {int(r['year']):>4d}  {int(r['total_deaths']):>10,d}  {r['od_rate']:>8.1f}  {r['total_opioid_rx']:>14,.0f}")

# Correlation
if len(trend) > 3:
    r_rx_od, p_rx_od = pearsonr(trend["total_opioid_rx"], trend["od_rate"])
    print(f"\n  Correlation (Total Opioid Rx vs Overdose Rate):")
    print(f"    Pearson r = {r_rx_od:+.3f}  p = {p_rx_od:.4f}  {'✅' if p_rx_od < 0.05 else '❌'}")
    
    # Check if they DIVERGE after a certain year
    pre2012 = trend[trend["year"] <= 2012]
    post2012 = trend[trend["year"] > 2012]
    if len(pre2012) > 2 and len(post2012) > 2:
        r_pre, _ = pearsonr(pre2012["total_opioid_rx"], pre2012["od_rate"])
        r_post, _ = pearsonr(post2012["total_opioid_rx"], post2012["od_rate"])
        print(f"    Pre-2012 correlation:  r = {r_pre:+.3f}")
        print(f"    Post-2012 correlation: r = {r_post:+.3f}")
        if r_pre > 0 and r_post < 0:
            print(f"    💡 DIVERGENCE DETECTED: Before 2012 Rx and OD deaths moved together.")
            print(f"       After 2012 Rx went DOWN but OD deaths kept going UP.")
            print(f"       → Suggests post-2012 overdoses are driven by ILLICIT opioids (heroin/fentanyl),")
            print(f"         not prescription opioids. Major policy implication!")


# ═══════════════════════════════════════════════════════════════════════
section("10. METHADONE PARADOX — Treatment vs Pain Drug")
# ═══════════════════════════════════════════════════════════════════════
meth_med = q4[(q4["active_ingredient"] == "methadone") & (q4["is_medicaid"] == "Medicaid")]
meth_non = q4[(q4["active_ingredient"] == "methadone") & (q4["is_medicaid"] == "Non-Medicaid")]
if len(meth_med) and len(meth_non):
    med_mme = meth_med["avg_mme"].values[0]
    non_mme = meth_non["avg_mme"].values[0]
    med_rx = meth_med["total_rx"].values[0]
    non_rx = meth_non["total_rx"].values[0]
    med_share = med_rx / (med_rx + non_rx) * 100
    print(f"  Methadone Medicaid Rx:     {med_rx:>12,.0f}  (avg MME: {med_mme:.1f})")
    print(f"  Methadone Non-Medicaid Rx: {non_rx:>12,.0f}  (avg MME: {non_mme:.1f})")
    print(f"  Medicaid share: {med_share:.1f}%")
    print(f"  Medicaid avg MME is {'LOWER' if med_mme < non_mme else 'HIGHER'} ({med_mme:.1f} vs {non_mme:.1f})")
    if med_mme < non_mme:
        print(f"  💡 Lower Medicaid methadone MME may indicate it's used more for")
        print(f"     ADDICTION TREATMENT (lower doses) vs pain management (higher doses)")


# ═══════════════════════════════════════════════════════════════════════
section("SUMMARY — UNEXPECTED FINDINGS")
# ═══════════════════════════════════════════════════════════════════════
print("""
  This analysis has been saved to the terminal output.
  Key patterns to investigate further:
  
  1. Drug portfolio differences (formulary restrictions vs prescribing behavior)
  2. Buprenorphine/methadone as addiction treatment markers
  3. New Rx ratio as proxy for chronic vs acute prescribing
  4. Prescribing ↔ overdose divergence after 2012 (illicit opioid wave)
  5. Specialty concentration differences
  6. Quantity-per-Rx patterns across drugs
""")
