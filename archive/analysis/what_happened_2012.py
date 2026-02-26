"""What happened in 2012? Deep dive into the inflection point."""
import pandas as pd
import numpy as np

import os
_ROOT = os.path.dirname(os.path.dirname(__file__))
q1 = pd.read_csv(os.path.join(_ROOT, "output", "iqvia_core", "medicaid_vs_nonmedicaid_by_year.csv"))
q4 = pd.read_csv(os.path.join(_ROOT, "output", "iqvia_core", "medicaid_vs_nonmedicaid_by_drug.csv"))
q6 = pd.read_csv(os.path.join(_ROOT, "output", "extended", "medicaid_vs_nonmedicaid_by_state_year.csv"))
cdc = pd.read_csv(os.path.join(_ROOT, "output", "cdc", "cdc_overdose_by_state_year.csv"))

print("=" * 72)
print("  WHAT HAPPENED IN 2012? — Data forensics")
print("=" * 72)

# 1. Year-over-year changes around 2012
print("\n── TOTAL Rx AROUND THE INFLECTION ──")
for grp in ["Medicaid", "Non-Medicaid"]:
    g = q1[q1["is_medicaid"] == grp].sort_values("year")
    g["yoy"] = g["total_rx"].pct_change() * 100
    g["mme_chg"] = g["avg_mme"].diff()
    print(f"\n  {grp}:")
    print(f"  {'Year':>4s}  {'Total Rx':>14s}  {'YoY %':>7s}  {'Avg MME':>8s}  {'MME Δ':>7s}")
    for _, r in g[(g["year"] >= 2008) & (g["year"] <= 2015)].iterrows():
        yr = int(r["year"])
        marker = " ◄◄◄" if yr == 2012 else ""
        yoy = f"{r['yoy']:+.1f}%" if pd.notna(r["yoy"]) else "   N/A"
        print(f"  {yr}  {r['total_rx']:>14,.0f}  {yoy:>7s}  {r['avg_mme']:>8.2f}  {r['mme_chg']:>+7.3f}{marker}")

# 2. What about propoxyphene? It was pulled Nov 2010
print("\n── PROPOXYPHENE EFFECT ──")
print("  Propoxyphene (Darvon/Darvocet) was pulled from market Nov 19, 2010")
print("  by FDA due to cardiac risks.")
# Check propoxyphene's share from Q4
for grp in ["Medicaid", "Non-Medicaid"]:
    sub = q4[q4["is_medicaid"] == grp]
    total = sub["total_rx"].sum()
    prop = sub[sub["active_ingredient"].isin(["propoxyphene", "dextropropoxyphene"])]["total_rx"].sum()
    print(f"  {grp} propoxyphene share (all-time): {prop/total*100:.2f}% = {prop:,.0f} Rx")

# 3. MME drop in 2011 — is that the propoxyphene removal?
print("\n── MME DROP IN 2011 ──")
non = q1[q1["is_medicaid"] == "Non-Medicaid"].sort_values("year")
print("  Non-Medicaid avg MME:")
for _, r in non[(non["year"] >= 2009) & (non["year"] <= 2014)].iterrows():
    print(f"    {int(r['year'])}  MME: {r['avg_mme']:.3f}")
print("  The -0.652 MME drop in 2011 aligns with propoxyphene removal")
print("  (propoxyphene had ~18 MME avg, was 7.6% of Non-Medicaid Rx)")

# 4. Medicaid peaked in 2010, not 2012 — why?
print("\n── WHY DID MEDICAID PEAK 2 YEARS EARLIER (2010)? ──")
med = q1[q1["is_medicaid"] == "Medicaid"].sort_values("year")
print("  Medicaid Rx by year:")
for _, r in med.iterrows():
    yr = int(r["year"])
    peak = " ← PEAK" if yr == 2010 else ""
    print(f"    {yr}  {r['total_rx']:>14,.0f}{peak}")

# 5. State-level: which states flipped first?
print("\n── WHICH STATES PEAKED AND FLIPPED FIRST? ──")
q6_total = q6.groupby(["state", "year"])["total_rx"].sum().reset_index()
# Only real states with meaningful volume
state_totals = q6_total.groupby("state")["total_rx"].sum()
real = state_totals[state_totals > 1_000_000].index
q6f = q6_total[q6_total["state"].isin(real)]

peak_years = q6f.loc[q6f.groupby("state")["total_rx"].idxmax()][["state", "year", "total_rx"]]
peak_years.columns = ["state", "peak_year", "peak_rx"]
peak_dist = peak_years["peak_year"].value_counts().sort_index()
print("  Distribution of state peak prescribing years:")
for yr, ct in peak_dist.items():
    bar = "█" * ct
    print(f"    {int(yr)}: {ct:>2d} states  {bar}")

# Early peakers
print("\n  States that peaked BEFORE 2012:")
early = peak_years[peak_years["peak_year"] < 2012].sort_values("peak_year")
for _, r in early.iterrows():
    print(f"    {r['state']:>4s}  peaked {int(r['peak_year'])}")

print("\n  States that peaked IN 2012:")
y2012 = peak_years[peak_years["peak_year"] == 2012].sort_values("peak_rx", ascending=False)
for _, r in y2012.head(15).iterrows():
    print(f"    {r['state']:>4s}  peaked 2012  ({r['peak_rx']:>12,.0f} Rx)")

print("\n  States that peaked AFTER 2012:")
late = peak_years[peak_years["peak_year"] > 2012].sort_values("peak_year")
for _, r in late.iterrows():
    print(f"    {r['state']:>4s}  peaked {int(r['peak_year'])}  ({r['peak_rx']:>12,.0f} Rx)")

# 6. CDC overdose: what type of overdose was rising?
print("\n── CDC OVERDOSE DEATHS AROUND 2012 ──")
cdc_nat = cdc.groupby("year").agg(
    deaths=("overdose_deaths", "sum"),
    pop=("population", "sum")
).reset_index()
cdc_nat["rate"] = cdc_nat["deaths"] / cdc_nat["pop"] * 100000
cdc_nat["death_chg"] = cdc_nat["deaths"].pct_change() * 100
print(f"  {'Year':>4s}  {'Deaths':>8s}  {'Rate':>6s}  {'YoY Deaths':>11s}")
for _, r in cdc_nat[(cdc_nat["year"] >= 2009) & (cdc_nat["year"] <= 2018)].iterrows():
    chg = f"{r['death_chg']:+.1f}%" if pd.notna(r["death_chg"]) else "N/A"
    marker = " ◄" if int(r["year"]) == 2012 else ""
    print(f"  {int(r['year'])}  {int(r['deaths']):>8,d}  {r['rate']:>6.1f}  {chg:>11s}{marker}")

print("""
── TIMELINE OF KEY EVENTS ──

  2007: FDA sends warning letters about OxyContin marketing
  2010: ACA passes (Medicaid expansion effective 2014)
  2010: Nov — FDA pulls propoxyphene (Darvon/Darvocet)
  2010: Purdue reformulates OxyContin to abuse-deterrent
  2011: DEA pill mill crackdowns begin (esp. Florida)
  2012: CDC guidelines tighten; state PDMP mandates spread
  2012: Florida "pill mill" law takes full effect
  2012: ◄◄◄ NATIONAL PRESCRIBING PEAK ◄◄◄
  2013: Heroin supply surges as Rx access tightens
  2014: ACA Medicaid expansion begins (32 states)
  2014: Illicit fentanyl first detected in drug supply
  2016: CDC Guideline for Prescribing Opioids (formal)
  2017: HHS declares opioid public health emergency

  The 2012 inflection is a CONVERGENCE of:
    1. Propoxyphene already removed (2010) — lost ~8% of Rx volume
    2. OxyContin reformulated (2010) — abuse-deterrent, users shifted
    3. State PDMPs going mandatory — doctors can see patient history
    4. Florida pill mill crackdown — removed a major supply source
    5. DEA enforcement intensifying
    
  The UNINTENDED CONSEQUENCE:
    Patients (especially Medicaid) lost access to prescription opioids
    → Illicit market (heroin, then fentanyl) filled the demand
    → Overdose deaths ACCELERATED despite fewer prescriptions
""")
