"""
MME vs Overdose Deaths scatter plot by county.
Requires: output/county/avg_mme_vs_overdose.csv (run merge_mme_overdose_county.py first)

Run: python -m visualizations.mme_vs_deaths_scatterplot
"""
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

BASE = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
import sys; sys.path.insert(0, BASE)
from visualizations.theme import DARK_BLUE, MID_BLUE, GOLD_BROWN, TEAL, DARK_TEAL
CSV_PATH = os.path.join(BASE, "output", "county", "avg_mme_vs_overdose.csv")
OUT_PATH = os.path.join(BASE, "output", "plots", "mme_vs_deaths_by_county.png")

if not os.path.exists(CSV_PATH):
    print(f"Missing: {CSV_PATH}")
    print("Run first: python -m visualizations.merge_mme_overdose_county")
    exit(1)

final_df = pd.read_csv(CSV_PATH)
final_df["Average MME"] = pd.to_numeric(final_df["Average MME"], errors="coerce")
final_df["Deaths"] = pd.to_numeric(final_df["Deaths"], errors="coerce")
final_df = final_df.dropna(subset=["Deaths", "Average MME"])

county_df = final_df.groupby("county_code").agg(
    Avg_MME=("Average MME", "mean"),
    Total_Deaths=("Deaths", "sum"),
).reset_index()

county_df["Highlight"] = county_df["county_code"].apply(
    lambda x: "County 18141" if str(x) == "18141" else "Other Counties"
)

r, p = stats.pearsonr(county_df["Avg_MME"], county_df["Total_Deaths"])
print(f"Pearson r: {r:.3f}, p-value: {p:.4f}")
print(f"Counties: {len(county_df)}")

sns.set_theme(style="whitegrid")
fig, ax = plt.subplots(figsize=(11, 7))
fig.patch.set_facecolor(DARK_BLUE)
ax.set_facecolor(DARK_BLUE)

sns.scatterplot(
    data=county_df, x="Avg_MME", y="Total_Deaths",
    hue="Highlight",
    palette={"Other Counties": MID_BLUE, "County 18141": GOLD_BROWN},
    size="Highlight",
    sizes={"Other Counties": 40, "County 18141": 120},
    alpha=0.6, edgecolor="white", linewidth=0.3,
    ax=ax,
)

sns.regplot(data=county_df, x="Avg_MME", y="Total_Deaths", scatter=False, color=GOLD_BROWN, line_kws={"linewidth": 1.5}, ax=ax)

targets = county_df[county_df["Highlight"] == "County 18141"]
if not targets.empty:
    t = targets.iloc[0]
    ax.annotate("St. Joseph County", xy=(t["Avg_MME"], t["Total_Deaths"]),
                 xytext=(10, 10), textcoords="offset points", fontsize=10,
                 color=GOLD_BROWN, fontweight="bold")

ax.set_title(f"Average MME vs. Total Overdose Deaths by County (2008–2017)\nPearson r = {r:.3f},  p = {p:.4f}", fontsize=14, color="white")
ax.set_xlabel("Average MME per County (mean across years)", fontsize=12, color="white")
ax.set_ylabel("Total Overdose Deaths per County (summed across years)", fontsize=12, color="white")
ax.tick_params(colors="white")
for spine in ax.spines.values():
    spine.set_color("white")
ax.legend(title="County", facecolor=DARK_BLUE, edgecolor="white", labelcolor="white")
plt.tight_layout()

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
plt.savefig(OUT_PATH, dpi=300)
print(f"Saved: {OUT_PATH}")
plt.show()
