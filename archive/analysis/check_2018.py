"""Quick check: why does 2018 drop so much?"""
import pandas as pd

import os
_ROOT = os.path.dirname(os.path.dirname(__file__))
q6 = pd.read_csv(os.path.join(_ROOT, "output", "extended", "medicaid_vs_nonmedicaid_by_state_year.csv"))

print("=== STATES REPORTING PER YEAR ===")
states_per_year = q6.groupby("year")["state"].nunique()
for yr, n in states_per_year.items():
    print(f"  {yr}: {n} states")

print("\n=== 2017 vs 2018 TOTAL RX BY STATE (Non-Medicaid, top 10) ===")
non = q6[q6["is_medicaid"] == "Non-Medicaid"]
y17 = non[non["year"] == 2017].set_index("state")["total_rx"]
y18 = non[non["year"] == 2018].set_index("state")["total_rx"]
comp = pd.DataFrame({"rx_2017": y17, "rx_2018": y18}).dropna()
comp["ratio"] = comp["rx_2018"] / comp["rx_2017"]
comp = comp.sort_values("rx_2017", ascending=False)
print(f"  States in both years: {len(comp)}")
print(f"  Avg 2018/2017 ratio: {comp['ratio'].mean():.3f}")
print(f"  Median ratio: {comp['ratio'].median():.3f}")
print(f"  Min ratio: {comp['ratio'].min():.3f}  Max: {comp['ratio'].max():.3f}")
for st, r in comp.head(10).iterrows():
    print(f"  {st:>4s}  2017: {r['rx_2017']:>12,.0f}  2018: {r['rx_2018']:>12,.0f}  ratio: {r['ratio']:.3f}")

frac = comp["rx_2018"].sum() / comp["rx_2017"].sum()
print(f"\n=== 2018 IS ~{frac*12:.1f} MONTHS OF DATA ===")
print(f"  2018/2017 total ratio: {frac:.3f}")
print(f"  If 2017 = 12 months, then 2018 ≈ {frac*12:.1f} months")

# Also check Medicaid
print("\n=== MEDICAID 2017 vs 2018 ===")
med = q6[q6["is_medicaid"] == "Medicaid"]
m17 = med[med["year"] == 2017]["total_rx"].sum()
m18 = med[med["year"] == 2018]["total_rx"].sum()
print(f"  Medicaid 2017: {m17:>12,.0f}")
print(f"  Medicaid 2018: {m18:>12,.0f}")
print(f"  Ratio: {m18/m17:.3f} (~{m18/m17*12:.1f} months)")

# Check per-year totals from Q1 for full picture
q1 = pd.read_csv(os.path.join(_ROOT, "output", "iqvia_core", "medicaid_vs_nonmedicaid_by_year.csv"))
print("\n=== FULL TIMELINE (Q1) - Total Rx ===")
totals = q1.groupby("year")["total_rx"].sum()
for yr in range(2013, 2019):
    if yr in totals.index:
        val = totals[yr]
        prev = totals.get(yr-1, None)
        chg = f"  ({(val-prev)/prev*100:+.1f}%)" if prev else ""
        print(f"  {yr}: {val:>14,.0f}{chg}")

# Check if the drop is uniform per state or if some states just stop reporting
print("\n=== STATES THAT EXIST IN 2017 BUT NOT 2018 ===")
s17 = set(non[non["year"] == 2017]["state"].unique())
s18 = set(non[non["year"] == 2018]["state"].unique())
missing = s17 - s18
print(f"  States in 2017: {len(s17)}")
print(f"  States in 2018: {len(s18)}")
print(f"  Missing from 2018: {missing if missing else 'None — all states present'}")
