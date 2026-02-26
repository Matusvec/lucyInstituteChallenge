"""
Extended analysis on NEW query outputs:
  Q6 — Medicaid vs Non-Medicaid by State × Year  (output/extended/medicaid_vs_nonmedicaid_by_state_year.csv)
  Q7 — Medicaid vs Non-Medicaid by Sales Channel  (output/extended/medicaid_vs_nonmedicaid_by_sales_channel.csv)

Plus cross-references with:
  CDC overdose data   (output/cdc/cdc_overdose_by_state_year.csv)
  Core year data       (output/iqvia_core/medicaid_pct_by_year.csv)
  State-level merged   (output/cdc/iqvia_cdc_merged_by_state.csv)

Usage:  python extended_analysis.py
"""

import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import spearmanr, pearsonr, linregress
import os, warnings
warnings.filterwarnings("ignore")

OUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")

def load(name, subdir=None):
    if subdir:
        return pd.read_csv(os.path.join(OUT, subdir, name))
    direct = os.path.join(OUT, name)
    if os.path.exists(direct):
        return pd.read_csv(direct)
    for sub in os.listdir(OUT):
        candidate = os.path.join(OUT, sub, name)
        if os.path.isfile(candidate):
            return pd.read_csv(candidate)
    raise FileNotFoundError(f"Cannot find {name}")

def section(title):
    print(f"\n{'═'*72}")
    print(f"  {title}")
    print(f"{'═'*72}")

def subsection(title):
    print(f"\n  ── {title} ──")


# ═══════════════════════════════════════════════════════════════
#  LOAD
# ═══════════════════════════════════════════════════════════════
print("Loading datasets …")
q6     = load("medicaid_vs_nonmedicaid_by_state_year.csv", "extended")
q7     = load("medicaid_vs_nonmedicaid_by_sales_channel.csv", "extended")
cdc    = load("cdc_overdose_by_state_year.csv", "cdc")
merged = load("iqvia_cdc_merged_by_state.csv", "cdc")
pct_yr = load("medicaid_pct_by_year.csv", "iqvia_core")
print("  ✅ All loaded.\n")


# ═══════════════════════════════════════════════════════════════
section("A. STATE × YEAR — ACA MEDICAID EXPANSION NATURAL EXPERIMENT")
# ═══════════════════════════════════════════════════════════════
# Pivot Q6 so each row = (state, year) with both Medicaid & Non-Medicaid columns
med6 = q6[q6["is_medicaid"] == "Medicaid"].copy()
non6 = q6[q6["is_medicaid"] == "Non-Medicaid"].copy()

both = med6.rename(columns={"total_rx": "med_rx", "new_rx": "med_new_rx", "total_qty": "med_qty"}
         )[["state", "year", "med_rx", "med_new_rx", "med_qty"]].merge(
    non6.rename(columns={"total_rx": "non_rx", "new_rx": "non_new_rx", "total_qty": "non_qty"}
         )[["state", "year", "non_rx", "non_new_rx", "non_qty"]],
    on=["state", "year"], how="outer"
)
both["total_rx"] = both["med_rx"].fillna(0) + both["non_rx"].fillna(0)
both["med_pct"]  = both["med_rx"].fillna(0) / both["total_rx"] * 100
both["med_pct"]  = both["med_pct"].replace([np.inf, -np.inf], np.nan)

# Filter to real US states (drop AA, military, unknown codes) with meaningful volume
state_totals = both.groupby("state")["total_rx"].sum()
real_states = state_totals[state_totals > 100_000].index
both = both[both["state"].isin(real_states)].copy()

# ACA expansion lookup from merged file
aca_map = merged.set_index("state")["aca_expansion"].to_dict()
both["aca_expansion"] = both["state"].map(aca_map)

subsection("Medicaid opioid share: before vs after ACA expansion (2014)")
pre_aca  = both[(both["year"] >= 2009) & (both["year"] <= 2013)].copy()
post_aca = both[(both["year"] >= 2014) & (both["year"] <= 2018)].copy()

for label, subset in [("Pre-ACA (2009-2013)", pre_aca), ("Post-ACA (2014-2018)", post_aca)]:
    exp_states = subset[subset["aca_expansion"] == True]
    non_states = subset[subset["aca_expansion"] == False]
    exp_pct = exp_states["med_pct"].mean()
    non_pct = non_states["med_pct"].mean()
    print(f"  {label}:")
    print(f"    Expansion states avg Medicaid %:     {exp_pct:.2f}%")
    print(f"    Non-expansion states avg Medicaid %: {non_pct:.2f}%")
    print(f"    Gap: {exp_pct - non_pct:+.2f} pp")

# Difference-in-differences
subsection("Difference-in-Differences (ACA Expansion Impact)")
exp_pre  = pre_aca[pre_aca["aca_expansion"] == True]["med_pct"].mean()
exp_post = post_aca[post_aca["aca_expansion"] == True]["med_pct"].mean()
non_pre  = pre_aca[pre_aca["aca_expansion"] == False]["med_pct"].mean()
non_post = post_aca[post_aca["aca_expansion"] == False]["med_pct"].mean()
did = (exp_post - exp_pre) - (non_post - non_pre)
print(f"  Expansion states:     pre={exp_pre:.2f}%  post={exp_post:.2f}%  Δ={exp_post-exp_pre:+.2f} pp")
print(f"  Non-expansion states: pre={non_pre:.2f}%  post={non_post:.2f}%  Δ={non_post-non_pre:+.2f} pp")
print(f"  DiD estimate: {did:+.2f} pp")
if abs(did) > 0.5:
    direction = "INCREASED" if did > 0 else "DECREASED"
    print(f"  💡 ACA expansion {direction} Medicaid's opioid prescribing share by ~{abs(did):.1f} pp")
    print(f"     above what would have happened without expansion")


# ═══════════════════════════════════════════════════════════════
section("B. STATE × YEAR — WHICH STATES DROVE THE NATIONAL DECLINE?")
# ═══════════════════════════════════════════════════════════════
# Total Rx by state: peak year vs 2018
state_peak = both.groupby("state").agg(
    peak_rx=("total_rx", "max"),
    peak_year=("year", lambda x: x.loc[both.loc[x.index, "total_rx"].idxmax()])
).reset_index()
state_2018 = both[both["year"] == 2018].groupby("state")["total_rx"].sum().reset_index()
state_2018.columns = ["state", "rx_2018"]
decline = state_peak.merge(state_2018, on="state", how="inner")
decline["pct_decline"] = (decline["rx_2018"] - decline["peak_rx"]) / decline["peak_rx"] * 100
decline = decline.sort_values("pct_decline")

print(f"  {'State':>5s}  {'Peak Year':>9s}  {'Peak Rx':>14s}  {'2018 Rx':>14s}  {'% Decline':>10s}")
for _, r in decline.head(15).iterrows():
    print(f"  {r['state']:>5s}  {int(r['peak_year']):>9d}  {r['peak_rx']:>14,.0f}  {r['rx_2018']:>14,.0f}  {r['pct_decline']:>9.1f}%")

subsection("Do states with BIGGER Rx decline have SMALLER overdose increases?")
# Merge with CDC for overdose change
cdc_early = cdc[(cdc["year"] >= 2009) & (cdc["year"] <= 2013)].groupby("state").agg(
    early_od_rate=("overdose_rate_per_100k", "mean")).reset_index()
cdc_late  = cdc[(cdc["year"] >= 2014) & (cdc["year"] <= 2018)].groupby("state").agg(
    late_od_rate=("overdose_rate_per_100k", "mean")).reset_index()
od_change = cdc_early.merge(cdc_late, on="state")
od_change["od_change_pct"] = (od_change["late_od_rate"] - od_change["early_od_rate"]) / od_change["early_od_rate"] * 100

decline_od = decline.merge(od_change, on="state", how="inner")
if len(decline_od) > 5:
    r_val, p_val = spearmanr(decline_od["pct_decline"], decline_od["od_change_pct"])
    print(f"  Spearman ρ (Rx decline % vs OD rate change %): {r_val:+.3f}  p={p_val:.4f}")
    if p_val < 0.05:
        if r_val > 0:
            print(f"  💡 States that cut prescriptions MORE saw SMALLER overdose increases")
            print(f"     → Prescription reduction policies may be working")
        else:
            print(f"  💡 States that cut prescriptions MORE saw BIGGER overdose increases")
            print(f"     → Cutting scripts may push patients to illicit supply")
    else:
        print(f"  → No significant relationship — Rx cuts and OD changes are decoupled")
        print(f"    Supports the 'illicit opioid wave' hypothesis")


# ═══════════════════════════════════════════════════════════════
section("C. STATE × YEAR — YEARLY MEDICAID SHARE TRAJECTORIES")
# ═══════════════════════════════════════════════════════════════
# For each state, run a linear regression of med_pct ~ year (post-2009 only)
state_trends = []
for st in both["state"].unique():
    sub = both[(both["state"] == st) & (both["year"] >= 2009) & (both["med_pct"].notna())].copy()
    if len(sub) >= 4:
        slope, intercept, r, p, se = linregress(sub["year"], sub["med_pct"])
        state_trends.append({
            "state": st,
            "slope": slope,
            "r_squared": r**2,
            "p_value": p,
            "mean_med_pct": sub["med_pct"].mean(),
            "aca_expansion": aca_map.get(st)
        })
trends = pd.DataFrame(state_trends).sort_values("slope", ascending=False)

subsection("States where Medicaid opioid share is RISING fastest")
rising = trends[trends["slope"] > 0].head(10)
for _, r in rising.iterrows():
    sig = "✅" if r["p_value"] < 0.05 else "  "
    aca = "ACA" if r["aca_expansion"] else "   "
    print(f"    {sig} {r['state']:>4s} {aca}  slope={r['slope']:+.3f} pp/yr  "
          f"R²={r['r_squared']:.2f}  mean={r['mean_med_pct']:.1f}%")

subsection("States where Medicaid opioid share is FALLING fastest")
falling = trends[trends["slope"] < 0].tail(10)
for _, r in falling.iloc[::-1].iterrows():
    sig = "✅" if r["p_value"] < 0.05 else "  "
    aca = "ACA" if r["aca_expansion"] else "   "
    print(f"    {sig} {r['state']:>4s} {aca}  slope={r['slope']:+.3f} pp/yr  "
          f"R²={r['r_squared']:.2f}  mean={r['mean_med_pct']:.1f}%")

# Test: is rising Medicaid share correlated with ACA expansion?
if len(trends) > 10:
    aca_slopes = trends[trends["aca_expansion"] == True]["slope"]
    non_slopes = trends[trends["aca_expansion"] == False]["slope"]
    if len(aca_slopes) > 3 and len(non_slopes) > 3:
        t_aca, p_aca = stats.ttest_ind(aca_slopes, non_slopes, equal_var=False)
        print(f"\n  ACA expansion states avg slope: {aca_slopes.mean():+.3f} pp/yr")
        print(f"  Non-expansion states avg slope: {non_slopes.mean():+.3f} pp/yr")
        print(f"  Welch t = {t_aca:.3f}, p = {p_aca:.4f}  {'✅ Significant' if p_aca < 0.05 else '❌ Not significant'}")


# ═══════════════════════════════════════════════════════════════
section("D. STATE × YEAR — QUANTITY PER Rx TRENDS (Pill Burden)")
# ═══════════════════════════════════════════════════════════════
both["med_qty_per_rx"] = both["med_qty"] / both["med_rx"]
both["non_qty_per_rx"] = both["non_qty"] / both["non_rx"]

# National average by year
qty_by_year = both.groupby("year").agg(
    med_qty_total=("med_qty", "sum"),
    med_rx_total=("med_rx", "sum"),
    non_qty_total=("non_qty", "sum"),
    non_rx_total=("non_rx", "sum"),
).reset_index()
qty_by_year["med_qty_per_rx"]  = qty_by_year["med_qty_total"] / qty_by_year["med_rx_total"]
qty_by_year["non_qty_per_rx"]  = qty_by_year["non_qty_total"] / qty_by_year["non_rx_total"]

print(f"  {'Year':>4s}  {'Med qty/Rx':>10s}  {'Non qty/Rx':>10s}  {'Ratio':>6s}")
for _, r in qty_by_year.iterrows():
    if pd.notna(r["med_qty_per_rx"]):
        ratio = r["med_qty_per_rx"] / r["non_qty_per_rx"] if r["non_qty_per_rx"] else np.nan
        flag = "🔴" if ratio > 1.1 else "🟢" if ratio < 0.9 else "⚪"
        print(f"  {flag} {int(r['year']):>4d}  {r['med_qty_per_rx']:>10.1f}  {r['non_qty_per_rx']:>10.1f}  {ratio:>5.2f}x")
    else:
        print(f"     {int(r['year']):>4d}  {'N/A':>10s}  {r['non_qty_per_rx']:>10.1f}  {'N/A':>6s}")

# Trend test on qty/Rx gap
valid_qty = qty_by_year.dropna(subset=["med_qty_per_rx"])
if len(valid_qty) >= 3:
    slope_m, _, r_m, p_m, _ = linregress(valid_qty["year"], valid_qty["med_qty_per_rx"])
    slope_n, _, r_n, p_n, _ = linregress(valid_qty["year"], valid_qty["non_qty_per_rx"])
    print(f"\n  Medicaid qty/Rx trend:     slope={slope_m:+.2f} units/yr  p={p_m:.4f}")
    print(f"  Non-Medicaid qty/Rx trend: slope={slope_n:+.2f} units/yr  p={p_n:.4f}")


# ═══════════════════════════════════════════════════════════════
section("E. SALES CHANNEL — RETAIL vs MAIL ORDER OPIOID PATTERNS")
# ═══════════════════════════════════════════════════════════════
# Q7 columns: year, sales_category, is_medicaid, total_rx, new_rx, total_qty, sales_channel
retail = q7[q7["sales_channel"] == "Retail"].copy()
mail   = q7[q7["sales_channel"] == "Mail Order"].copy()

subsection("Volume Summary by Channel")
for ch_label, ch_data in [("Retail", retail), ("Mail Order", mail)]:
    total = ch_data["total_rx"].sum()
    med_rows = ch_data[ch_data["is_medicaid"] == "Medicaid"]
    non_rows = ch_data[ch_data["is_medicaid"] == "Non-Medicaid"]
    med_total = med_rows["total_rx"].sum()
    non_total = non_rows["total_rx"].sum()
    med_share = med_total / total * 100 if total > 0 else 0
    print(f"  {ch_label:>12s}:  Total Rx = {total:>16,.0f}  "
          f"Medicaid = {med_total:>14,.0f} ({med_share:.2f}%)")

subsection("Mail Order share of opioids over time")
# Combine retail + mail by year for total
yr_channel = q7.groupby(["year", "sales_channel"])["total_rx"].sum().reset_index()
yr_total = q7.groupby("year")["total_rx"].sum().reset_index().rename(columns={"total_rx": "yr_total"})
yr_channel = yr_channel.merge(yr_total, on="year")
yr_channel["pct_of_year"] = yr_channel["total_rx"] / yr_channel["yr_total"] * 100

mail_share = yr_channel[yr_channel["sales_channel"] == "Mail Order"]
print(f"  {'Year':>4s}  {'Mail Rx':>14s}  {'% of All Opioids':>16s}")
for _, r in mail_share.iterrows():
    bar = "█" * int(r["pct_of_year"] * 10)
    print(f"  {int(r['year']):>4d}  {r['total_rx']:>14,.0f}  {r['pct_of_year']:>5.2f}%  {bar}")

# Trend
if len(mail_share) >= 3:
    slope, _, r_val, p_val, _ = linregress(mail_share["year"], mail_share["pct_of_year"])
    print(f"\n  Mail order opioid trend: slope={slope:+.4f} pp/yr  p={p_val:.4f}")
    if slope > 0 and p_val < 0.05:
        print(f"  💡 Mail order opioids are GROWING as a share — possible monitoring gap")
    elif slope < 0 and p_val < 0.05:
        print(f"  💡 Mail order opioids are SHRINKING — tighter pharmacy controls working?")

subsection("Qty per Rx: Retail vs Mail Order (proxy for supply duration)")
for ch_label, ch_data in [("Retail", retail), ("Mail Order", mail)]:
    avg_qty_per_rx = ch_data["total_qty"].sum() / ch_data["total_rx"].sum()
    new_rx_pct = ch_data["new_rx"].sum() / ch_data["total_rx"].sum() * 100
    print(f"  {ch_label:>12s}:  avg qty/Rx = {avg_qty_per_rx:>8.1f}  new Rx % = {new_rx_pct:.1f}%")

# Compare retail vs mail by year
subsection("Retail vs Mail Order qty/Rx over time")
for ch_label, ch_data in [("Retail", retail), ("Mail Order", mail)]:
    by_yr = ch_data.groupby("year").agg(
        total_rx=("total_rx", "sum"), total_qty=("total_qty", "sum")
    ).reset_index()
    by_yr["qty_per_rx"] = by_yr["total_qty"] / by_yr["total_rx"]
    print(f"\n  {ch_label}:")
    print(f"    {'Year':>4s}  {'qty/Rx':>8s}")
    for _, r in by_yr.iterrows():
        print(f"    {int(r['year']):>4d}  {r['qty_per_rx']:>8.1f}")
    if len(by_yr) >= 3:
        sl, _, rv, pv, _ = linregress(by_yr["year"], by_yr["qty_per_rx"])
        print(f"    Trend: {sl:+.2f} units/yr  p={pv:.4f}  {'✅ Sig' if pv < 0.05 else '❌ ns'}")


# ═══════════════════════════════════════════════════════════════
section("F. CROSS-CHECK — STATE×YEAR CDC OVERDOSE vs PRESCRIBING TRENDS")
# ═══════════════════════════════════════════════════════════════
# For years with both Rx data and CDC data, correlate at the state-year level
q6_total = both.groupby(["state", "year"]).agg(
    total_rx=("total_rx", "sum"),
    med_pct=("med_pct", "first")
).reset_index()

cross = q6_total.merge(
    cdc[["state", "year", "overdose_rate_per_100k"]].rename(columns={"state": "state_code"}),
    left_on=["state", "year"], right_on=["state_code", "year"], how="inner"
)

if len(cross) > 10:
    subsection("Panel correlations (state-year level)")
    r1, p1 = spearmanr(cross["total_rx"], cross["overdose_rate_per_100k"])
    r2, p2 = spearmanr(cross["med_pct"].dropna(), 
                        cross.loc[cross["med_pct"].notna(), "overdose_rate_per_100k"])
    print(f"  Total Rx vs OD rate:      ρ={r1:+.3f}  p={p1:.4f}  {'✅' if p1 < 0.05 else '❌'}")
    print(f"  Medicaid % vs OD rate:    ρ={r2:+.3f}  p={p2:.4f}  {'✅' if p2 < 0.05 else '❌'}")

    # Year-by-year correlation strength
    subsection("Rx ↔ Overdose correlation BY YEAR")
    print(f"  {'Year':>4s}  {'ρ (Rx vs OD)':>12s}  {'p-value':>8s}  {'n':>4s}")
    for yr in sorted(cross["year"].unique()):
        sub = cross[cross["year"] == yr]
        if len(sub) > 5:
            rv, pv = spearmanr(sub["total_rx"], sub["overdose_rate_per_100k"])
            sig = "✅" if pv < 0.05 else "❌"
            print(f"  {yr:>4d}  {rv:>+12.3f}  {pv:>8.4f}  {len(sub):>4d}  {sig}")

    # Is the correlation WEAKENING over time? (supports illicit opioid theory)
    yearly_corr = []
    for yr in sorted(cross["year"].unique()):
        sub = cross[cross["year"] == yr]
        if len(sub) > 5:
            rv, _ = spearmanr(sub["total_rx"], sub["overdose_rate_per_100k"])
            yearly_corr.append({"year": yr, "rho": rv})
    if len(yearly_corr) >= 5:
        yc = pd.DataFrame(yearly_corr)
        sl, _, _, p_trend, _ = linregress(yc["year"], yc["rho"])
        print(f"\n  Trend in correlation strength: slope={sl:+.4f}/yr  p={p_trend:.4f}")
        if sl < 0 and p_trend < 0.05:
            print(f"  💡 The Rx-overdose link is WEAKENING over time!")
            print(f"     → Overdoses are increasingly driven by non-prescription sources")


# ═══════════════════════════════════════════════════════════════
section("SUMMARY OF NEW FINDINGS")
# ═══════════════════════════════════════════════════════════════
print("""
  New insights from extended queries:
  
  A. ACA Difference-in-Differences — Did Medicaid expansion change
     opioid prescribing patterns in expansion vs non-expansion states?
  
  B. Which states drove the national prescribing decline after peak?
     Are bigger Rx cuts associated with overdose changes?
  
  C. State-level Medicaid share trajectories — some states are
     trending opposite to the national pattern.
  
  D. Quantity per Rx (pill burden) — Are Medicaid patients getting
     larger fills over time? Is the gap widening or narrowing?
  
  E. Retail vs Mail Order — monitoring gap, supply duration 
     differences, trend in mail-order opioid share.
  
  F. Panel-level Rx-overdose correlation — is it weakening over
     time as illicit fentanyl displaces prescription opioids?
""")
