"""
Simple scatter: Average MME vs Overdose Deaths (2012–2016).
Hardcoded national-level values.

Run: python -m visualizations.mme_vs_overdose_2012_2016
"""
import os
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
import sys; sys.path.insert(0, BASE)
from visualizations.theme import DARK_BLUE, MID_BLUE, GOLD_BROWN, TEAL

# Average MME (mean of Medicaid and Non-Medicaid Avg MME)
avg_mme = [
    (12.47 + 13.55) / 2,  # 2012
    (12.50 + 13.35) / 2,  # 2013
    (12.40 + 13.35) / 2,  # 2014
    (12.63 + 13.47) / 2,  # 2015
    (12.68 + 13.33) / 2,  # 2016
]

# Overdose deaths
deaths = [33735, 35799, 38416, 42665, 51555]

fig, ax = plt.subplots()
fig.patch.set_facecolor(DARK_BLUE)
ax.set_facecolor(DARK_BLUE)
ax.scatter(avg_mme, deaths, color=TEAL, s=80, alpha=0.8, edgecolor=GOLD_BROWN)
ax.set_xlabel("Average MME", color="white")
ax.set_ylabel("Overdose Deaths", color="white")
ax.set_title("Average MME vs Overdose Deaths (2012–2016)", color="white")
ax.tick_params(colors="white")
for spine in ax.spines.values():
    spine.set_color("white")

out_path = os.path.join(BASE, "output", "plots", "mme_vs_overdose_2012_2016.png")
os.makedirs(os.path.dirname(out_path), exist_ok=True)
plt.savefig(out_path, dpi=150)
print(f"Saved: {out_path}")
plt.show()
