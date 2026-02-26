import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

BASE = os.path.dirname(os.path.dirname(__file__))
from visualizations.theme import DARK_BLUE, MID_BLUE, GOLD_BROWN, TEAL

# ── IQVIA prescription totals by year ──────────────────────────────────────
rx = pd.read_csv(os.path.join(BASE, "output", "iqvia_core", "medicaid_pct_by_year.csv"))

# ── CDC all-cause overdose deaths (aggregate to national) ─────────────────
cdc = pd.read_csv(os.path.join(BASE, "output", "cdc", "cdc_overdose_by_state_year.csv"))
cdc_national = cdc.groupby("year", as_index=False).agg(
    overdose_deaths=("overdose_deaths", "sum"),
    population=("population", "sum"),
)
cdc_national["od_rate"] = cdc_national["overdose_deaths"] / cdc_national["population"] * 100_000


# ── Helper: load a CDC drug-type CSV → national deaths per year ───────────
def _load_cdc_drug_csv(filename: str) -> pd.DataFrame:
    """Load a CDC WONDER drug-type CSV, filter to overdose rows, sum nationally."""
    path = os.path.join(BASE, "output", "cdc", filename)
    raw = pd.read_csv(path, dtype=str, low_memory=False)

    # Keep only drug-poisoning overdose rows (UCD codes D1–D4)
    ucd_col = "UCD - Drug/Alcohol Induced Cause Code"
    overdose_codes = {"D1", "D2", "D3", "D4"}
    raw = raw[raw[ucd_col].isin(overdose_codes)].copy()

    raw["Year"] = pd.to_numeric(raw["Year"], errors="coerce")
    raw["Deaths"] = pd.to_numeric(
        raw["Deaths"].astype(str).str.replace(",", ""), errors="coerce"
    )
    raw["Population"] = pd.to_numeric(
        raw["Population"].astype(str).str.replace(",", ""), errors="coerce"
    )

    nat = raw.groupby("Year", as_index=False).agg(
        deaths=("Deaths", "sum"),
        population=("Population", "max"),  # population is per-state; max avoids double-count label
    )
    # Recalculate population properly: sum unique state pops per year
    state_pop = raw.drop_duplicates(subset=["State", "Year", "Population"])
    state_pop_nat = state_pop.groupby("Year", as_index=False)["Population"].sum()
    nat = nat.drop(columns="population").merge(state_pop_nat, on="Year")
    nat["rate"] = nat["deaths"] / nat["Population"] * 100_000
    return nat.rename(columns={"Year": "year"})


# ── Load illicit & prescription drug death data ───────────────────────────
illicit = _load_cdc_drug_csv("Illicit_Drugs_1999-2018.csv")
prescription = _load_cdc_drug_csv("Prescription_Drugs_1999-2018.csv")

# ── Merge everything on year ──────────────────────────────────────────────
df = rx.merge(cdc_national[["year", "overdose_deaths", "od_rate"]], on="year", how="inner")
df = df.merge(illicit[["year", "deaths", "rate"]].rename(
    columns={"deaths": "illicit_deaths", "rate": "illicit_rate"}),
    on="year", how="left")
df = df.merge(prescription[["year", "deaths", "rate"]].rename(
    columns={"deaths": "rx_drug_deaths", "rate": "rx_drug_rate"}),
    on="year", how="left")

# ── Drop 2018 (incomplete in IQVIA) ──────────────────────────────────────
df = df[df["year"] != 2018].reset_index(drop=True)

# ── Index to 2012 = 100 (puts all series on same scale) ──────────────────
rx_2012 = df.loc[df["year"] == 2012, "total_rx"].values[0]
od_2012 = df.loc[df["year"] == 2012, "od_rate"].values[0]
ill_2012 = df.loc[df["year"] == 2012, "illicit_rate"].values[0]
rxd_2012 = df.loc[df["year"] == 2012, "rx_drug_rate"].values[0]

df["rx_index"] = df["total_rx"] / rx_2012 * 100
df["od_index"] = df["od_rate"] / od_2012 * 100
df["illicit_index"] = df["illicit_rate"] / ill_2012 * 100
df["rx_drug_index"] = df["rx_drug_rate"] / rxd_2012 * 100

# ── Two-panel chart ──────────────────────────────────────────────────────
x = np.arange(len(df))
width = 0.35

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 14), gridspec_kw={"height_ratios": [1, 1]})

# ═══ PANEL 1: Indexed (2012 = 100) ═══════════════════════════════════════
fig.patch.set_facecolor(DARK_BLUE)
for ax in (ax1, ax2):
    ax.set_facecolor(DARK_BLUE)
    ax.tick_params(colors="white")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.title.set_color("white")
    for spine in ax.spines.values():
        spine.set_color("white")

ax1.bar(x - width/2, df["rx_index"], width, label="Opioid Prescriptions (IQVIA)",
        color=MID_BLUE, alpha=0.85)
ax1.bar(x + width/2, df["od_index"], width, label="All Overdose Deaths",
        color=GOLD_BROWN, alpha=0.85)
ax1.plot(x, df["illicit_index"], "s-", color=TEAL, linewidth=2.5, markersize=6,
         label="Illicit Drug Deaths (heroin/fentanyl/cocaine/meth)")
ax1.plot(x, df["rx_drug_index"], "o--", color="#7AB89A", linewidth=2.5, markersize=6,
         label="Prescription Opioid Deaths (oxy/hydro/methadone)")

ax1.axhline(100, color=GOLD_BROWN, linestyle="--", alpha=0.5)
diverge_idx = list(df["year"]).index(2012)
ax1.axvline(diverge_idx, linestyle=":", color=GOLD_BROWN, alpha=0.6)
ax1.annotate("2012 divergence", xy=(diverge_idx, 105), fontsize=9, color=GOLD_BROWN,
             ha="center")

ax1.set_xticks(x)
ax1.set_xticklabels(df["year"].astype(int), rotation=45)
ax1.set_ylabel("Index (2012 = 100)")
ax1.set_title("Relative Change: Opioid Prescriptions vs Overdose Deaths (2012 = 100)")
ax1.legend(loc="upper left", fontsize=9, facecolor=DARK_BLUE, edgecolor="white", labelcolor="white")
ax1.grid(axis="y", alpha=0.2, color="white")

# ═══ PANEL 2: Raw counts ═════════════════════════════════════════════════
ax2.bar(x, df["overdose_deaths"], width * 1.6, label="All Overdose Deaths",
        color=GOLD_BROWN, alpha=0.45)
ax2.plot(x, df["illicit_deaths"], "s-", color=TEAL, linewidth=2.5, markersize=7,
         label="Illicit Drug Deaths (heroin/fentanyl/cocaine/meth)")
ax2.plot(x, df["rx_drug_deaths"], "o--", color="#7AB89A", linewidth=2.5, markersize=7,
         label="Prescription Opioid Deaths (oxy/hydro/methadone)")

# Prescriptions on secondary y-axis (different scale)
ax2b = ax2.twinx()
ax2b.set_facecolor(DARK_BLUE)
ax2b.plot(x, df["total_rx"], "^-", color=MID_BLUE, linewidth=2.5, markersize=7,
          label="Opioid Prescriptions (IQVIA)")
ax2b.tick_params(colors="white")
ax2b.yaxis.label.set_color("white")

ax2.axvline(diverge_idx, linestyle=":", color=GOLD_BROWN, alpha=0.6)
ax2.annotate("2012", xy=(diverge_idx, df["overdose_deaths"].max() * 0.95),
             fontsize=9, color=GOLD_BROWN, ha="center")

# Format y-axes with thousands separator
ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{int(v):,}"))
ax2b.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{int(v):,}"))

ax2.set_xticks(x)
ax2.set_xticklabels(df["year"].astype(int), rotation=45)
ax2.set_ylabel("Total Deaths", color=TEAL)
ax2b.set_ylabel("Total Prescriptions (IQVIA)", color=MID_BLUE)
ax2.set_title("Overdose Deaths & Opioid Prescriptions (Raw Counts)")

# Combine legends from both axes
lines1, labels1 = ax2.get_legend_handles_labels()
lines2, labels2 = ax2b.get_legend_handles_labels()
ax2.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=9,
           facecolor=DARK_BLUE, edgecolor="white", labelcolor="white")
ax2.grid(axis="y", alpha=0.2, color="white")

plt.tight_layout()
plt.show()