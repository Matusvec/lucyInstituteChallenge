"""
Stacked bar chart: prescriptions by year (Medicaid vs Non-Medicaid).

Run from project root: python scripts/python/seg_bar_graph_rough.py
"""
import pandas as pd
import matplotlib.pyplot as plt
import os
import sys

# Project root is parent of scripts/
_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(_script_dir))
sys.path.insert(0, project_root)
from visualizations.theme import DARK_BLUE, MID_BLUE, GOLD_BROWN, TEAL

data_path = os.path.join(project_root, "output", "iqvia_core", "medicaid_vs_nonmedicaid_by_year.csv")

df = pd.read_csv(data_path, usecols=['year', 'is_medicaid', 'total_rx', 'new_rx', 'total_qty'])
subset = df.iloc[11:32]
df_pivoted = subset.pivot(index='year', columns='is_medicaid', values=['new_rx', 'total_rx'])
df_pivoted.columns = [f'{col[0]} ({col[1]})' for col in df_pivoted.columns]

fig, ax = plt.subplots(figsize=(12, 7))
fig.patch.set_facecolor(DARK_BLUE)
ax.set_facecolor(DARK_BLUE)
colors = [MID_BLUE, GOLD_BROWN, TEAL, "#7AB89A"]  # light teal
df_pivoted.plot(kind='bar', stacked=True, ax=ax, color=colors[:len(df_pivoted.columns)])

ax.set_title('Number of Prescriptions by Year', color='white')
ax.set_xlabel('Year', color='white')
ax.set_ylabel('Number of Perscriptions', color='white')
ax.tick_params(colors='white')
for spine in ax.spines.values():
    spine.set_color('white')
ax.legend(title='Metrics', bbox_to_anchor=(1.05, 1), loc='upper left',
          facecolor=DARK_BLUE, edgecolor='white', labelcolor='white')
plt.xticks(rotation=45)
plt.tight_layout()

plt.show()
