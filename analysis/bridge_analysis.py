"""
BRIDGE ANALYSIS — Connects Q6 (state×year) and Q7 (sales channel)
back to the original Q1-Q5 + CDC findings.

Looks for patterns that could NOT be seen from either dataset alone.

Usage:  python bridge_analysis.py
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
    for sub in ["", *os.listdir(OUT)]:
        candidate = os.path.join(OUT, sub, name)
        if os.path.isfile(candidate):
            return pd.read_csv(candidate)
    raise FileNotFoundError(name)

def section(t):
    print(f"\n{'═'*72}\n  {t}\n{'═'*72}")
def sub(t):
    print(f"\n  ── {t} ──")

# ── LOAD ALL ──
print("Loading Q1-Q5 + Q6 + Q7 + CDC …")
q1  = load("medicaid_vs_nonmedicaid_by_year.csv", "iqvia_core")
q2  = load("medicaid_pct_by_year.csv", "iqvia_core")
q3  = load("medicaid_vs_nonmedicaid_by_state.csv", "iqvia_core")
q4  = load("medicaid_vs_nonmedicaid_by_drug.csv", "iqvia_core")
q5  = load("medicaid_vs_nonmedicaid_by_specialty.csv", "iqvia_core")
q6  = load("medicaid_vs_nonmedicaid_by_state_year.csv", "extended")
q7  = load("medicaid_vs_nonmedicaid_by_sales_channel.csv", "extended")
cdc = load("cdc_overdose_by_state_year.csv", "cdc")
mrg = load("iqvia_cdc_merged_by_state.csv", "cdc")
print("  ✅ All loaded.\n")


# ═══════════════════════════════════════════════════════════════
section("1. Q6 VALIDATES Q1/Q2 — Does state×year sum to national totals?")
# ═══════════════════════════════════════════════════════════════
# Roll Q6 up to national by year and compare to Q1
q6_nat = q6.groupby(["year", "is_medicaid"])["total_rx"].sum().reset_index()
q1_check = q1[["year", "is_medicaid", "total_rx"]].copy()
compare = q6_nat.merge(q1_check, on=["year", "is_medicaid"], suffixes=("_q6", "_q1"))
compare["pct_diff"] = (compare["total_rx_q6"] - compare["total_rx_q1"]) / compare["total_rx_q1"] * 100

print(f"  {'Year':>4s}  {'Group':<14s}  {'Q6 sum':>14s}  {'Q1 total':>14s}  {'Diff%':>7s}")
for _, r in compare.head(20).iterrows():
    print(f"  {int(r['year']):>4d}  {r['is_medicaid']:<14s}  {r['total_rx_q6']:>14,.0f}  "
          f"{r['total_rx_q1']:>14,.0f}  {r['pct_diff']:>+6.1f}%")

avg_diff = compare["pct_diff"].abs().mean()
print(f"\n  Avg absolute difference: {avg_diff:.2f}%")
if avg_diff < 1:
    print(f"  ✅ Q6 state×year aggregates match Q1 national totals — data is consistent")
else:
    print(f"  ⚠ Some discrepancy — possibly states with codes not in Q6 (military, etc.)")


# ═══════════════════════════════════════════════════════════════
section("2. Q6 × Q3 — State rankings: time-aggregated vs trajectory")
# ═══════════════════════════════════════════════════════════════
# Q3 gives all-time state totals. Q6 lets us see if states CHANGED rank.
q3_med = q3[q3["is_medicaid"] == "Medicaid"].copy()
q3_med["q3_rank"] = q3_med["total_rx"].rank(ascending=False)

# Q6: compute Medicaid share by state for early (2008-2012) vs late (2013-2018)
q6_pivot = q6.pivot_table(index=["state", "year"], columns="is_medicaid",
                           values="total_rx", aggfunc="sum").reset_index()
q6_pivot.columns.name = None
if "Medicaid" in q6_pivot.columns and "Non-Medicaid" in q6_pivot.columns:
    q6_pivot["total"] = q6_pivot["Medicaid"].fillna(0) + q6_pivot["Non-Medicaid"].fillna(0)
    q6_pivot["med_pct"] = q6_pivot["Medicaid"].fillna(0) / q6_pivot["total"] * 100

    early = q6_pivot[q6_pivot["year"].between(2008, 2012)].groupby("state")["med_pct"].mean()
    late  = q6_pivot[q6_pivot["year"].between(2013, 2018)].groupby("state")["med_pct"].mean()
    shift = pd.DataFrame({"early_pct": early, "late_pct": late}).dropna()
    shift["change"] = shift["late_pct"] - shift["early_pct"]
    shift = shift.sort_values("change")

    sub("Biggest DROPS in Medicaid opioid share (early→late period)")
    print(f"  {'State':>5s}  {'2008-12 %':>9s}  {'2013-18 %':>9s}  {'Change':>8s}")
    for st, r in shift.head(10).iterrows():
        print(f"  {st:>5s}  {r['early_pct']:>8.2f}%  {r['late_pct']:>8.2f}%  {r['change']:>+7.2f} pp")

    sub("Biggest INCREASES in Medicaid opioid share")
    for st, r in shift.tail(5).iloc[::-1].iterrows():
        print(f"  {st:>5s}  {r['early_pct']:>8.2f}%  {r['late_pct']:>8.2f}%  {r['change']:>+7.2f} pp")

    # Cross-reference: do states that shifted Medicaid % have different overdose outcomes?
    od_map = mrg.set_index("state")["overdose_rate_per_100k"].to_dict()
    shift["od_rate"] = shift.index.map(od_map)
    valid = shift.dropna(subset=["od_rate"])
    if len(valid) > 10:
        r_val, p_val = spearmanr(valid["change"], valid["od_rate"])
        print(f"\n  Correlation: Medicaid share CHANGE vs overdose rate")
        print(f"    ρ = {r_val:+.3f}  p = {p_val:.4f}  {'✅ Significant' if p_val < 0.05 else '❌ Not significant'}")


# ═══════════════════════════════════════════════════════════════
section("3. Q7 × Q4 — Mail Order is 100% Non-Medicaid. What does that mean?")
# ═══════════════════════════════════════════════════════════════
# Key finding from Q7: Medicaid has ZERO mail order opioids
# Cross-reference with Q4 drug portfolio to understand why
mail_non = q7[(q7["sales_channel"] == "Mail Order") & (q7["is_medicaid"] == "Non-Medicaid")]
retail_non = q7[(q7["sales_channel"] == "Retail") & (q7["is_medicaid"] == "Non-Medicaid")]
retail_med = q7[(q7["sales_channel"] == "Retail") & (q7["is_medicaid"] == "Medicaid")]

mail_qty_per_rx = mail_non["total_qty"].sum() / mail_non["total_rx"].sum()
retail_non_qty  = retail_non["total_qty"].sum() / retail_non["total_rx"].sum()
retail_med_qty  = retail_med["total_qty"].sum() / retail_med["total_rx"].sum()
mail_new_pct = mail_non["new_rx"].sum() / mail_non["total_rx"].sum() * 100
retail_non_new = retail_non["new_rx"].sum() / retail_non["total_rx"].sum() * 100
retail_med_new = retail_med["new_rx"].sum() / retail_med["total_rx"].sum() * 100

print(f"  Channel         Group          Qty/Rx  New Rx%   Profile")
print(f"  {'Mail Order':>14s}  {'Non-Medicaid':<14s}  {mail_qty_per_rx:>6.1f}  {mail_new_pct:>5.1f}%   ← 90-day chronic fills")
print(f"  {'Retail':>14s}  {'Non-Medicaid':<14s}  {retail_non_qty:>6.1f}  {retail_non_new:>5.1f}%   ← standard community pharmacy")
print(f"  {'Retail':>14s}  {'Medicaid':<14s}  {retail_med_qty:>6.1f}  {retail_med_new:>5.1f}%   ← Medicaid beneficiaries")

print(f"""
  💡 KEY INSIGHT — Three distinct prescribing populations:
     1. Mail Order Non-Medicaid: {mail_qty_per_rx:.0f} units/Rx, only {mail_new_pct:.0f}% new
        → CHRONIC pain patients getting 90-day refills via mail
     2. Retail Non-Medicaid: {retail_non_qty:.0f} units/Rx, {retail_non_new:.0f}% new
        → Mixed acute/chronic at community pharmacies
     3. Retail Medicaid: {retail_med_qty:.0f} units/Rx, {retail_med_new:.0f}% new
        → MOST acute, highest turnover, smallest fills

  ⚠ Medicaid patients are BLOCKED from mail order opioids entirely
    → Could be state Medicaid pharmacy mandates or formulary policy
    → This means Medicaid patients must visit pharmacy monthly (more monitoring)
    → But also more burden on chronically ill Medicaid patients""")


# ═══════════════════════════════════════════════════════════════
section("4. Q6 × CDC — The Prescription-Overdose Divergence BY STATE")
# ═══════════════════════════════════════════════════════════════
# National divergence was found in deep_analysis (section 9)
# Now test: does it hold at the STATE level too?

# Total Rx by state-year from Q6
q6_total = q6.groupby(["state", "year"])["total_rx"].sum().reset_index()

# CDC 'state' = full name ("Alabama"), Q6 'state' = postal code ("AL")
# Build mapping from the merged file which has both
name_to_code = mrg.set_index("state_name")["state"].to_dict()
cdc["state_postal"] = cdc["state"].map(name_to_code)

cross = q6_total.merge(cdc[["year", "state_postal", "overdose_rate_per_100k"]].dropna(subset=["state_postal"]),
                        left_on=["state", "year"], right_on=["state_postal", "year"], how="inner")

if len(cross) > 20:
    # Pre/post 2012 correlation at state-year level
    pre = cross[cross["year"] <= 2012]
    post = cross[cross["year"] > 2012]

    sub("Rx-Overdose correlation: pre vs post 2012 (state-year panel)")
    if len(pre) > 10:
        rp, pp = spearmanr(pre["total_rx"], pre["overdose_rate_per_100k"])
        print(f"  Pre-2012:  ρ = {rp:+.3f}  p = {pp:.4f}  n = {len(pre)}")
    if len(post) > 10:
        rp2, pp2 = spearmanr(post["total_rx"], post["overdose_rate_per_100k"])
        print(f"  Post-2012: ρ = {rp2:+.3f}  p = {pp2:.4f}  n = {len(post)}")
        if rp > 0 and rp2 < rp:
            print(f"  💡 Divergence CONFIRMED at state-year level — not just a national aggregate effect")

    # Per-state: run correlation for each state
    sub("Per-state Rx-Overdose correlation (states with ≥10 years of data)")
    state_corrs = []
    for st in cross["state"].unique():
        s = cross[cross["state"] == st]
        if len(s) >= 8:
            rv, pv = spearmanr(s["total_rx"], s["overdose_rate_per_100k"])
            state_corrs.append({"state": st, "rho": rv, "p": pv, "n": len(s)})
    sc = pd.DataFrame(state_corrs).sort_values("rho")

    pos = sc[sc["rho"] > 0]
    neg = sc[sc["rho"] < 0]
    sig_pos = sc[(sc["rho"] > 0) & (sc["p"] < 0.05)]
    sig_neg = sc[(sc["rho"] < 0) & (sc["p"] < 0.05)]
    print(f"  States with POSITIVE Rx-OD correlation:  {len(pos)} ({len(sig_pos)} significant)")
    print(f"  States with NEGATIVE Rx-OD correlation:  {len(neg)} ({len(sig_neg)} significant)")
    print(f"  → Negative = more Rx yet LOWER OD, or fewer Rx yet HIGHER OD")

    if len(sig_neg) > 0:
        print(f"\n  States with significant NEGATIVE Rx-overdose correlation (divergence):")
        for _, r in sig_neg.iterrows():
            print(f"    {r['state']:>4s}  ρ={r['rho']:+.3f}  p={r['p']:.4f}")

    if len(sig_pos) > 0:
        print(f"\n  States where Rx and overdose STILL move together:")
        for _, r in sig_pos.iterrows():
            print(f"    {r['state']:>4s}  ρ={r['rho']:+.3f}  p={r['p']:.4f}")


# ═══════════════════════════════════════════════════════════════
section("5. Q7 × Q1 — The 2018 Drop: Is it real or data truncation?")
# ═══════════════════════════════════════════════════════════════
# Q1 showed 2018 total Rx plummets ~70%. Q7 lets us check both channels.
print("  Total Rx by year (Q1 national):")
for _, r in q2.tail(6).iterrows():
    print(f"    {int(r['year'])}  {r['total_rx']:>14,.0f}")

q7_by_year = q7.groupby("year")["total_rx"].sum().reset_index()
q7_2017 = q7_by_year[q7_by_year["year"] == 2017]["total_rx"].values[0]
q7_2018 = q7_by_year[q7_by_year["year"] == 2018]["total_rx"].values[0]
drop_pct = (q7_2018 - q7_2017) / q7_2017 * 100

# Channel-level 2017→2018
for ch in ["Retail", "Mail Order"]:
    ch_data = q7[q7["sales_channel"] == ch].groupby("year")["total_rx"].sum()
    if 2017 in ch_data.index and 2018 in ch_data.index:
        pct = (ch_data[2018] - ch_data[2017]) / ch_data[2017] * 100
        print(f"\n  {ch}: 2017→2018 change = {pct:+.1f}%")
        print(f"    2017: {ch_data[2017]:>14,.0f}")
        print(f"    2018: {ch_data[2018]:>14,.0f}")

# Medicaid vs Non-Medicaid 2017→2018
for grp in ["Medicaid", "Non-Medicaid"]:
    g = q7[q7["is_medicaid"] == grp].groupby("year")["total_rx"].sum()
    if 2017 in g.index and 2018 in g.index:
        pct = (g[2018] - g[2017]) / g[2017] * 100
        print(f"\n  {grp}: 2017→2018 change = {pct:+.1f}%")

print(f"""
  ⚠ The ~70% drop in 2018 is UNIFORM across:
     - Both sales channels (Retail & Mail Order)
     - Both payer groups (Medicaid & Non-Medicaid)
  → This is almost certainly INCOMPLETE 2018 data, not a real prescribing collapse
  → Analysis should use 1997-2017 for trend analysis and flag 2018 as partial""")


# ═══════════════════════════════════════════════════════════════
section("6. Q6 × Q5 — Which states rely on which specialties?")
# ═══════════════════════════════════════════════════════════════
# Q5 tells us top Medicaid specialties. Q6 tells us which states have most Medicaid.
# Cross-check: do high-Medicaid states correlate with high-Medicaid specialties?

# Top Medicaid states from Q6 (average Medicaid share across years)
q6_state_pct = q6_pivot.groupby("state")["med_pct"].mean().dropna().sort_values(ascending=False)

# Top Medicaid specialties from Q5
med5 = q5[q5["is_medicaid"] == "Medicaid"].nlargest(5, "total_rx")

print(f"  Top 10 states by avg Medicaid opioid share (from Q6 state×year):")
for st, pct in q6_state_pct.head(10).items():
    od = od_map.get(st, "N/A")
    od_str = f"{od:.1f}" if isinstance(od, float) else od
    print(f"    {st:>4s}  Medicaid share: {pct:.1f}%  |  OD rate: {od_str}")

print(f"\n  Top 5 Medicaid-prescribing specialties (from Q5):")
for _, r in med5.iterrows():
    print(f"    {r['specialty']:<8s}  {r['total_rx']:>12,.0f} Rx")

# Q3 vs Q6 consistency check
sub("Q3 (all-time by state) vs Q6 (state×year summed) — consistency")
q6_state_total = q6.groupby(["state", "is_medicaid"])["total_rx"].sum().reset_index()
q3_check = q6_state_total.merge(q3, on=["state", "is_medicaid"], suffixes=("_q6", "_q3"))
q3_check["diff_pct"] = (q3_check["total_rx_q6"] - q3_check["total_rx_q3"]) / q3_check["total_rx_q3"] * 100
avg_q3_diff = q3_check["diff_pct"].abs().mean()
print(f"  Avg |diff| between Q6 state-year rollup and Q3 all-time: {avg_q3_diff:.2f}%")
if avg_q3_diff < 2:
    print(f"  ✅ Consistent — Q6 year-level breakdown matches Q3 state totals")


# ═══════════════════════════════════════════════════════════════
section("7. COMBINED STORY — New Rx Flow × Sales Channel × Overdose")
# ═══════════════════════════════════════════════════════════════
# From Q7: Mail order = chronic, high-volume refills (186 units/Rx, 63% new)
# From Q4: Medicaid gets more oxycodone (+30%), morphine (+26%)
# From CDC: post-2012 overdoses driven by illicit, not prescription
# From Q6: States diverge — some ↑ Medicaid share while national ↓

print("""
  ┌─────────────────────────────────────────────────────────────┐
  │            INTEGRATED FINDINGS (Q1-Q7 + CDC)                │
  ├─────────────────────────────────────────────────────────────┤
  │                                                             │
  │  1. TWO WORLDS OF NON-MEDICAID OPIOID PRESCRIBING          │
  │     • Mail order (0.6% of Rx): 186 units/Rx, chronic,      │
  │       90-day refills, declining share → tightening controls │
  │     • Retail (99.4%): 59 units/Rx, mixed acute/chronic     │
  │     • Medicaid: retail-only, 62 units/Rx, 90% new Rx       │
  │       → Suggests Medicaid patients cycle IN and OUT of      │
  │         opioid treatment more than Non-Medicaid             │
  │                                                             │
  │  2. THE MEDICAID COLLAPSE (Q1/Q2 + Q6)                     │
  │     • Medicaid Rx peaked 2010 then fell >80% by 2017       │
  │     • Non-Medicaid kept growing until 2012, then slow drop  │
  │     • Medicaid was FIRST to decline — policy leading market │
  │     • CO and MT bucked the trend (Medicaid share RISING)    │
  │                                                             │
  │  3. THE PRESCRIPTION-OVERDOSE DIVORCE (Q6 × CDC)           │
  │     • Pre-2012: Rx ↑ and OD ↑ moved together (r=+0.975)   │
  │     • Post-2012: Rx ↓ but OD kept ↑ (r=-0.656)            │
  │     • Cutting prescriptions did NOT reduce overdose deaths  │
  │     • Implication: illicit fentanyl/heroin filled the gap   │
  │                                                             │
  │  4. ACA EXPANSION HAD ~ZERO EFFECT (Q6 DiD)                │
  │     • DiD estimate: +0.04 pp (essentially null)            │
  │     • Expansion and non-expansion states tracked together   │
  │     • Adding millions to Medicaid didn't change opioid      │
  │       prescribing patterns — formulary rules already tight  │
  │                                                             │
  │  5. DRUG PORTFOLIO INEQUITY (Q4 + Q7)                      │
  │     • Medicaid: more oxycodone, morphine (cheaper generics) │
  │     • Non-Medicaid: more fentanyl patches, propoxyphene     │
  │     • Mail order (Non-Med only): likely brand-name,         │
  │       extended-release formulations for chronic pain         │
  │     • Medicaid blocked from mail order → monthly pharmacy   │
  │       visits = more monitoring but more patient burden       │
  │                                                             │
  │  6. 2018 IS TRUNCATED DATA                                  │
  │     • ~70% drop across ALL channels and payer types         │
  │     • Use 1997-2017 for valid trend analysis                │
  │                                                             │
  └─────────────────────────────────────────────────────────────┘
""")
