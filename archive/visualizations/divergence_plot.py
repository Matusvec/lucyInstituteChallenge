import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

BASE    = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
CDC_DIR = os.path.join(BASE, "Datasets", "cdc")

# ── Colours ───────────────────────────────────────────────────────────────
DARK_BLUE = "#0C2340"   # Dark Blue
MID_BLUE  = "#3B5E8C"   # midpoint between #0C2340 and #E1E8F2
RX_DEATH_CLR = "#BFA15D"   # Golden Brown
FENT_CLR     = "#4EAE81"   # Teal

# ── 1. IQVIA prescriptions (county panel → aggregate nationally) ──────────
med_rx = pd.read_csv(
    os.path.join(BASE, "output", "county", "iqvia_county_year_panel.csv"),
    usecols=["county_fips", "year", "total_rx"],
)
med_rx = med_rx[(med_rx["year"] >= 2008) & (med_rx["year"] <= 2017)]
national_rx = med_rx.groupby("year", as_index=False)["total_rx"].sum()


# ── 2. CDC drug-type breakouts ────────────────────────────────────────────
# T40.2 = Other opioids (prescription: oxy/hydro)
# T40.4 = Other synthetic narcotics (fentanyl)
# Dropped: T40.1 heroin, T40.3 methadone, T40.5 cocaine, T43.6 meth
PRESCRIPTION_CODES = {"T40.2"}
FENTANYL_CODES     = {"T40.4"}
KEEP_CODES         = PRESCRIPTION_CODES | FENTANYL_CODES

def _load_drugtype_csv(filename: str) -> pd.DataFrame:
    """Load a CDC WONDER multiple-cause county file, filter to T40.2/T40.4,
    and aggregate to national deaths per year by drug type."""
    path = os.path.join(CDC_DIR, filename)
    raw  = pd.read_csv(path, dtype=str, low_memory=False)

    code_col = "Multiple Cause of death Code"
    raw = raw[raw[code_col].isin(KEEP_CODES)].copy()

    raw["Year"]       = pd.to_numeric(raw["Year"],       errors="coerce")
    raw["Deaths"]     = pd.to_numeric(raw["Deaths"].astype(str).str.replace(",", ""), errors="coerce")
    raw["Population"] = pd.to_numeric(raw["Population"].astype(str).str.replace(",", ""), errors="coerce")

    raw["drug_type"] = raw[code_col].map(
        {**{c: "prescription" for c in PRESCRIPTION_CODES},
         **{c: "fentanyl"     for c in FENTANYL_CODES}}
    )

    nat = raw.groupby(["Year", "drug_type"], as_index=False).agg(deaths=("Deaths", "sum"))

    # Population: sum unique county populations per year
    county_pop = raw.drop_duplicates(subset=["County Code", "Year", "Population"])
    pop_nat    = county_pop.groupby("Year", as_index=False)["Population"].sum()
    nat        = nat.merge(pop_nat, on="Year")
    nat["rate"] = nat["deaths"] / nat["Population"] * 100_000
    return nat.rename(columns={"Year": "year"})


# Concatenate both year-range files and pivot wide
drug_df = pd.concat([
    _load_drugtype_csv("overdose_by_county_drugtype_2008-2012.csv"),
    _load_drugtype_csv("overdose_by_county_drugtype_2013-2017.csv"),
], ignore_index=True)

drug_wide = drug_df.pivot_table(
    index="year", columns="drug_type",
    values=["deaths", "rate"], aggfunc="sum"
).reset_index()
drug_wide.columns = ["year"] + [
    f"{val}_{dtype}" for val, dtype in drug_wide.columns[1:]
]


# ── 3. Merge on year ──────────────────────────────────────────────────────
df = national_rx.merge(drug_wide, on="year", how="inner")
df = df.sort_values("year").reset_index(drop=True)


# ── 4. Plot ───────────────────────────────────────────────────────────────
base_year   = 2012
fig, ax1    = plt.subplots(figsize=(13, 6))
x           = np.arange(len(df))
diverge_idx = df.index[df["year"] == base_year][0]

# ── Left axis: total opioid prescriptions (bars) ──────────────────────────
ax1.bar(x, df["total_rx"] / 1_000_000, width=0.6,
        color=MID_BLUE, alpha=0.55, label="Opioid Prescriptions (IQVIA)")
ax1.set_ylabel("Total Prescriptions (millions)", color="black", fontsize=11)
ax1.tick_params(axis="y", labelcolor="black")
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}M"))

# ── Right axis: overdose deaths (lines) ───────────────────────────────────
ax2 = ax1.twinx()
ax2.plot(x, df["deaths_prescription"], "o-",  color=RX_DEATH_CLR, linewidth=2.5,
         markersize=7, label="Prescription Opioid Deaths")
ax2.plot(x, df["deaths_fentanyl"],     "s--", color=FENT_CLR,     linewidth=2.5,
         markersize=7, label="Fentanyl Deaths")
ax2.set_ylabel("Overdose Deaths", color="black", fontsize=11)
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{int(v):,}"))

# ── Divergence marker ─────────────────────────────────────────────────────
ymax_deaths = max(df["deaths_prescription"].max(), df["deaths_fentanyl"].max())
ax2.axvline(diverge_idx, linestyle=":", color="gray", alpha=0.7, linewidth=1.5)
ax2.annotate(
    "2012\nprescription peak",
    xy=(diverge_idx + 0.12, ymax_deaths * 0.92),
    fontsize=9, color=DARK_BLUE, va="top",
)

# ── X-axis ────────────────────────────────────────────────────────────────
ax1.set_xticks(x)
ax1.set_xticklabels(df["year"].astype(int), rotation=45, ha="right")
ax1.set_xlabel("Year", fontsize=11)

# ── Title ─────────────────────────────────────────────────────────────────
ax1.set_title(
    "Opioid Prescriptions vs. Overdose Deaths by Type (2008–2017)",
    fontsize=13, fontweight="bold",
)

# ── Combined legend ───────────────────────────────────────────────────────
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="center left", fontsize=9, framealpha=0.9)

# ── Grid (left axis only, subtle) ─────────────────────────────────────────
ax1.yaxis.grid(True, linestyle="--", alpha=0.3)
ax1.set_axisbelow(True)

plt.tight_layout()
plt.savefig(os.path.join(BASE, "output", "divergence_plot.png"), dpi=150, bbox_inches="tight")
plt.show()
print("Saved -> output/divergence_plot.png")
