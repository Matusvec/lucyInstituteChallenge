import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

BASE = os.path.dirname(os.path.dirname(__file__))

#prescription totals by year

rx = pd.read_csv(os.path.join(BASE, "output", "iqvia_core", "medicaid_pct_by_year.csv"))
# Columns: year, medicaid_rx, non_medicaid_rx, total_rx, pct_medicaid, pct_non_medicaid

# CDC overdose deaths by state & year (aggregate to national with groupby)
cdc = pd.read_csv(os.path.join(BASE, "output", "cdc", "cdc_overdose_by_state_year.csv"))
# Columns: state, state_code, year, overdose_deaths, population, overdose_rate_per_100k
cdc_national = cdc.groupby("year", as_index=False).agg(
    overdose_deaths=("overdose_deaths", "sum"),
    population=("population", "sum"),
)
cdc_national["od_rate"] = cdc_national["overdose_deaths"] / cdc_national["population"] * 100_000

#merge them
df = rx.merge(cdc_national[["year", "od_rate"]], on="year", how="inner")

# ── Index to 2012 = 100 (puts both on same scale) ──
rx_2012 = df.loc[df["year"] == 2012, "total_rx"].values[0]
od_2012 = df.loc[df["year"] == 2012, "od_rate"].values[0]
df["rx_index"] = df["total_rx"] / rx_2012 * 100
df["od_index"] = df["od_rate"] / od_2012 * 100

# ── Side-by-side bars ──
x = np.arange(len(df))
width = 0.38

fig, ax = plt.subplots(figsize=(14, 7))
ax.bar(x - width/2, df["rx_index"], width, label="Opioid Prescriptions")
ax.bar(x + width/2, df["od_index"], width, label="Overdose Death Rate")

ax.set_xticks(x)
ax.set_xticklabels(df["year"], rotation=45)
ax.axhline(100, color="gray", linestyle="--", alpha=0.5)   # 2012 baseline
ax.axvline(list(df["year"]).index(2012), linestyle=":", color="gray")  # divergence line
ax.set_ylabel("Index (2012 = 100)")
ax.legend()
plt.tight_layout()
plt.show()