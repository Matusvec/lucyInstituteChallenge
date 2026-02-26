"""
Heroin vs Synthetic-Opioid (Fentanyl) Overdose Deaths — National Trend

Data: CDC WONDER Multiple Cause of Death, 1999-2018
  • T40.1  → Heroin
  • T40.4  → Other synthetic narcotics (fentanyl & analogues)

Run:
  python -m visualizations.heroinVsFentanyl
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import os

BASE = os.path.dirname(os.path.dirname(__file__))
from visualizations.theme import DARK_BLUE, MID_BLUE, GOLD_BROWN, TEAL, DARK_TEAL

# ── Load data ─────────────────────────────────────────────────────────────
df = pd.read_csv(os.path.join(BASE, "output", "cdc", "heroin_vs_fentanyl_1999-2018.csv"))

x = np.arange(len(df))
width = 0.38

# ── Color palette (theme) ─────────────────────────────────────────────────
CLR_HEROIN = TEAL
CLR_FENTANYL = MID_BLUE
CLR_TOTAL = GOLD_BROWN

# ── Two-panel figure ─────────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(
    2, 1, figsize=(16, 13),
    gridspec_kw={"height_ratios": [1, 1]},
)
fig.patch.set_facecolor(DARK_BLUE)
for ax in (ax1, ax2):
    ax.set_facecolor(DARK_BLUE)
    ax.tick_params(colors="white")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.title.set_color("white")
    ax.spines["bottom"].set_color("white")
    ax.spines["top"].set_color("white")
    ax.spines["left"].set_color("white")
    ax.spines["right"].set_color("white")

# ═══ PANEL 1 — Side-by-side bar chart (raw counts) ═══════════════════════
bars_h = ax1.bar(
    x - width / 2, df["heroin_deaths"], width,
    label="Heroin (T40.1)", color=CLR_HEROIN, alpha=0.85,
)
bars_f = ax1.bar(
    x + width / 2, df["synthetic_opioid_deaths"], width,
    label="Synthetic Opioids / Fentanyl (T40.4)", color=CLR_FENTANYL, alpha=0.85,
)

# Crossover annotation
cross_year = 2016
cross_idx = list(df["year"]).index(cross_year)
ax1.axvline(cross_idx, linestyle=":", color=GOLD_BROWN, alpha=0.6)
ax1.annotate(
    "2016: Fentanyl surpasses Heroin",
    xy=(cross_idx, df.loc[df["year"] == cross_year, "synthetic_opioid_deaths"].values[0]),
    xytext=(cross_idx - 4, 28000),
    fontsize=10, fontweight="bold", color=GOLD_BROWN,
    arrowprops=dict(arrowstyle="->", color=GOLD_BROWN, lw=1.5),
)

ax1.set_xticks(x)
ax1.set_xticklabels(df["year"].astype(int), rotation=45)
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
ax1.set_ylabel("Deaths")
ax1.set_title(
    "Heroin vs Synthetic Opioid (Fentanyl) Overdose Deaths — United States, 1999-2018",
    fontsize=14, fontweight="bold",
)
ax1.grid(axis="y", alpha=0.2, color="white")
ax1.legend(loc="upper left", fontsize=11, facecolor=DARK_BLUE, edgecolor="white", labelcolor="white")

# ═══ PANEL 2 — Indexed to 2012 = 100 + area fill ═════════════════════════
base_h = df.loc[df["year"] == 2012, "heroin_deaths"].values[0]
base_f = df.loc[df["year"] == 2012, "synthetic_opioid_deaths"].values[0]

df["heroin_index"] = df["heroin_deaths"] / base_h * 100
df["fentanyl_index"] = df["synthetic_opioid_deaths"] / base_f * 100

ax2.fill_between(
    x, df["heroin_index"], alpha=0.15, color=CLR_HEROIN
)
ax2.fill_between(
    x, df["fentanyl_index"], alpha=0.15, color=CLR_FENTANYL
)
ax2.plot(
    x, df["heroin_index"], "o-", color=CLR_HEROIN, linewidth=2.5,
    markersize=6, label="Heroin (T40.1)",
)
ax2.plot(
    x, df["fentanyl_index"], "s-", color=CLR_FENTANYL, linewidth=2.5,
    markersize=6, label="Synthetic Opioids / Fentanyl (T40.4)",
)

ax2.axhline(100, color=GOLD_BROWN, linestyle="--", alpha=0.5)
baseline_idx = list(df["year"]).index(2012)
ax2.axvline(baseline_idx, linestyle=":", color=GOLD_BROWN, alpha=0.6)
ax2.annotate("2012 baseline", xy=(baseline_idx, 105), fontsize=9, color=GOLD_BROWN, ha="center")

# Fentanyl peak annotation
peak_yr = df.loc[df["fentanyl_index"].idxmax(), "year"]
peak_val = df["fentanyl_index"].max()
peak_idx = list(df["year"]).index(peak_yr)
ax2.annotate(
    f"Fentanyl: {peak_val:.0f}",
    xy=(peak_idx, peak_val),
    xytext=(peak_idx - 3, peak_val + 80),
    fontsize=10, color=CLR_FENTANYL, fontweight="bold",
    arrowprops=dict(arrowstyle="->", color=CLR_FENTANYL, lw=1.5),
)

ax2.set_xticks(x)
ax2.set_xticklabels(df["year"].astype(int), rotation=45)
ax2.set_ylabel("Index (2012 = 100)")
ax2.set_title(
    "Relative Growth: Heroin vs Fentanyl Deaths (2012 = 100)",
    fontsize=14, fontweight="bold",
)
ax2.legend(loc="upper left", fontsize=11, facecolor=DARK_BLUE, edgecolor="white", labelcolor="white")
ax2.grid(axis="y", alpha=0.2, color="white")

plt.tight_layout()
plt.show()
