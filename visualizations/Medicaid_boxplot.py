
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd
import scipy.stats as stats
import statsmodels.api as sm
import os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

pd.set_option('display.max_rows', 20)
pd.set_option('display.max_columns', 10)

# ── 1. Load Data ──────────────────────────────────────────────────────────────

med_rx = pd.read_csv(os.path.join(BASE, 'output', 'county', 'iqvia_county_year_panel.csv'))
med_rx = med_rx[['county_fips', 'year', 'total_rx','medicaid_rx', 'nonmedicaid_rx']]
med_rx = med_rx[(med_rx['year'] >= 2008) & (med_rx['year'] <= 2017)]

med_rx['medicaid_rx_rate'] = med_rx['medicaid_rx'] / med_rx['total_rx']


county_overdose = pd.read_csv(os.path.join(BASE, 'Datasets', 'cdc', 'overdose_by_county_year_2008-2017.csv'))
county_overdose = county_overdose[['County', 'County Code', 'Year', 'Deaths', 'Population', 'Crude Rate']]


# Merge and drop right-side columns to avoid duplicate names
med_rx = med_rx.merge(county_overdose, 
                      left_on=['county_fips', 'year'], 
                      right_on=['County Code', 'Year'], 
                      how='left', 
                      suffixes=('', '_right'))

# --- Timeline plot: Percent of US population on Medicaid and County Average Medicaid Prescription Rate ---


# Drop the right-side columns before renaming
med_rx = med_rx.drop(columns=['County Code', 'Year'])

med_rx = med_rx.rename(columns={'County': 'county_name',
                                'Deaths': 'overdose_deaths',
                                'Population': 'population',
                                'Crude Rate': 'overdose_rate'})

# ── 2. Aggregate to County Level (2008–2017) ──────────────────────────────────

# Drop rows where overdose_deaths is suppressed / missing
med_rx['overdose_deaths'] = pd.to_numeric(med_rx['overdose_deaths'], errors='coerce')
med_rx['population']      = pd.to_numeric(med_rx['population'],      errors='coerce')


# Aggregate columns
agg_df = med_rx.groupby('county_fips').agg({
    'county_name': lambda x: x.dropna().iloc[0] if x.dropna().size else 'Unknown',
    'overdose_deaths': 'sum',
    'population': 'mean',
    'medicaid_rx_rate': 'sum',  # placeholder, will fix below
    'total_rx': 'sum'           # needed for weighted avg
}).reset_index()

# Compute weighted average Medicaid Rx rate per county
def weighted_avg_rate(subdf):
    if subdf['total_rx'].sum() > 0:
        return np.average(subdf['medicaid_rx_rate'], weights=subdf['total_rx'])
    else:
        return np.nan

medicaid_rx_rate_wtd = med_rx.groupby('county_fips').apply(weighted_avg_rate)
agg_df['wtd_medicaid_rate'] = medicaid_rx_rate_wtd.values

# Rename columns for compatibility
agg_df = agg_df.rename(columns={
    'overdose_deaths': 'total_overdose_deaths',
    'population': 'avg_population'
})

# Drop rows with missing values in key columns
county_agg = agg_df.dropna(subset=['total_overdose_deaths', 'wtd_medicaid_rate'])

# Per-100k overdose death rate over the decade
county_agg['overdose_rate_decade'] = (
    county_agg['total_overdose_deaths'] / county_agg['avg_population'] * 100_000
)

# ── 3. Global Weighted Average Medicaid Rx Rate ───────────────────────────────

global_wtd_avg = np.average(
    county_agg['wtd_medicaid_rate'],
    weights=county_agg['avg_population'].fillna(1)
)
print(f"Global weighted avg Medicaid Rx rate: {global_wtd_avg:.4f}  ({global_wtd_avg*100:.2f}%)")

county_agg['medicaid_group'] = np.where(
    county_agg['wtd_medicaid_rate'] >= global_wtd_avg,
    f'Above avg  (≥ {global_wtd_avg*100:.1f}%)',
    f'Below avg  (< {global_wtd_avg*100:.1f}%)'
)




# ── 5. Plot 2 – Boxplots: Below vs Above Global Avg Medicaid Rx Rate ─────────

DARK_BLUE = "#0C2340"
TEAL      = "#4EAE81"
GOLD      = "#BFA15D"
LIGHT_BG  = "#E1E8F2"
FADED_BG  = "#EEF3F9"

county_agg_nonzero = county_agg[county_agg['overdose_rate_decade'] > 0]

print(county_agg_nonzero['medicaid_group'].unique())

below_label = [g for g in county_agg_nonzero['medicaid_group'].unique() if g.startswith('Below')][0]
above_label = [g for g in county_agg_nonzero['medicaid_group'].unique() if g.startswith('Above')][0]
group_order = [below_label, above_label]

data_groups = [
    county_agg_nonzero.loc[county_agg_nonzero['medicaid_group'] == g, 'overdose_rate_decade'].values
    for g in group_order
]

print(county_agg_nonzero['medicaid_group'].unique())

fig, ax = plt.subplots(figsize=(8, 6))

bp = ax.boxplot(
    data_groups,
    tick_labels=group_order,
    patch_artist=True,
    notch=True,
    widths=0.45,
    medianprops=dict(color='black', linewidth=2),
    flierprops=dict(marker='o', markersize=3, alpha=0.4, markeredgewidth=0.5),
)

colors = [TEAL, GOLD]
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.75)

for i, d in enumerate(data_groups, start=1):
    med = np.median(d)
    ax.text(i, med + 0.5, f'{med:.1f}', ha='center', va='bottom',
            fontsize=9, fontweight='bold', color="black")

stat, pval = stats.mannwhitneyu(data_groups[0], data_groups[1], alternative='two-sided')
ax.set_title(
    f'Overdose Death Rate by Medicaid Rx Group (2008–2017)\n'
    f'Mann-Whitney U p = {pval:.4f}',
    fontsize=12, fontweight='bold', color="black"
)
ax.set_ylabel('Cumulative Overdose Deaths per 100k (2008–2017)', fontsize=11, color="black")
ax.set_xlabel('Medicaid Prescription Rate Group', fontsize=11, color="black")
ax.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.0f'))
ax.grid(True, axis='y', linestyle=':', linewidth=0.6, alpha=0.7)
plt.tight_layout()
plt.savefig('boxplot_medicaid_group_overdose.png', dpi=150)
plt.show()