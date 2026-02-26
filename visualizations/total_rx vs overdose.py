import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd
import scipy.stats as stats
import statsmodels.api as sm

pd.set_option('display.max_rows', 20)
pd.set_option('display.max_columns', 10)

# ── 1. Load Data ──────────────────────────────────────────────────────────────

med_rx = pd.read_csv(
    'C:/Users/M16Mc/Documents/2026/lucyInstituteChallenge/output/county/iqvia_county_year_panel.csv'
)
med_rx = med_rx[['county_fips', 'year', 'total_rx', 'medicaid_rx', 'nonmedicaid_rx']]
med_rx = med_rx[(med_rx['year'] >= 2008) & (med_rx['year'] <= 2017)]

med_rx['medicaid_rx_rate'] = med_rx['medicaid_rx'] / med_rx['total_rx']

county_overdose = pd.read_csv(
    'C:/Users/M16Mc/Documents/2026/lucyInstituteChallenge/Datasets/cdc/overdose_by_county_year_2008-2017.csv'
)
county_overdose = county_overdose[['County', 'County Code', 'Year', 'Deaths', 'Population', 'Crude Rate']]

med_rx = med_rx.merge(
    county_overdose,
    left_on=['county_fips', 'year'],
    right_on=['County Code', 'Year'],
    how='left',
    suffixes=('', '_right')
)

med_rx['overdose_deaths'] = pd.to_numeric(med_rx['Deaths'],     errors='coerce')
med_rx['population']      = pd.to_numeric(med_rx['Population'], errors='coerce')

# ── 2. Aggregate to County Level ──────────────────────────────────────────────

county_agg = (
    med_rx
    .groupby('county_fips')
    .agg(
        county_name     = ('County',          lambda x: x.dropna().iloc[0] if x.dropna().size else 'Unknown'),
        total_rx        = ('total_rx',        'sum'),
        overdose_deaths = ('overdose_deaths', 'sum'),
        avg_population  = ('population',      'mean'),
    )
    .reset_index()
    .dropna(subset=['overdose_deaths', 'avg_population', 'total_rx'])
)

county_agg = county_agg[county_agg['avg_population'] > 0].copy()

county_agg['rx_per_capita']       = county_agg['total_rx']        / county_agg['avg_population'] * 100_000
county_agg['overdose_per_capita'] = county_agg['overdose_deaths'] / county_agg['avg_population'] * 100_000

county_agg = county_agg[
    (county_agg['rx_per_capita']       > 0) &
    (county_agg['overdose_per_capita'] > 0)
]

# ── 3. Statistical Analysis ───────────────────────────────────────────────────

x_raw = county_agg['rx_per_capita']
y_raw = county_agg['overdose_per_capita']

slope, intercept, r, p_ols, se = stats.linregress(x_raw, y_raw)
rho, p_spearman = stats.spearmanr(x_raw, y_raw)

print(f"Pearson  r  = {r:.3f}  (p = {p_ols:.4f})")
print(f"Spearman ρ  = {rho:.3f}  (p = {p_spearman:.4f})")

# ── 4. Bin into equal-count deciles ───────────────────────────────────────────

N_BINS = 10

county_agg['rx_bin'] = pd.qcut(county_agg['rx_per_capita'], q=N_BINS, labels=False)

bin_stats = (
    county_agg
    .groupby('rx_bin')
    .agg(
        bin_mid         = ('rx_per_capita',      'median'),
        mean_overdose   = ('overdose_per_capita', 'mean'),
        se_overdose     = ('overdose_per_capita', lambda v: v.std() / np.sqrt(len(v))),
        n_counties      = ('overdose_per_capita', 'count'),
    )
    .reset_index()
)

# OLS trendline through bin medians
bx = bin_stats['bin_mid']
by = bin_stats['mean_overdose']
b_slope, b_intercept, b_r, b_p, _ = stats.linregress(bx, by)
trend_x = np.linspace(bx.min(), bx.max(), 300)
trend_y = b_slope * trend_x + b_intercept

# ── 5. ND Brand Colors ────────────────────────────────────────────────────────

DARK_BLUE = "#0C2340"
TEAL      = "#4EAE81"
GOLD      = "#BFA15D"
LIGHT_BG  = "#E1E8F2"
FADED_BG  = "#EEF3F9"

# ── 6. Plot ───────────────────────────────────────────────────────────────────

fig, ax = plt.subplots(figsize=(10, 6.5))
fig.patch.set_facecolor(FADED_BG)
ax.set_facecolor(LIGHT_BG)

# Left accent bar
fig.add_axes([0.0, 0.0, 0.018, 1.0]).set_facecolor(DARK_BLUE)
fig.axes[-1].set_axis_off()

# ±1 SE error bars
ax.errorbar(
    bin_stats['bin_mid'],
    bin_stats['mean_overdose'],
    yerr=bin_stats['se_overdose'],
    fmt='none',
    color=GOLD,
    capsize=5,
    linewidth=1.3,
    zorder=2
)

# Bin scatter dots — sized by county count
dot_sizes = bin_stats['n_counties'] * 4
ax.scatter(
    bin_stats['bin_mid'],
    bin_stats['mean_overdose'],
    s=dot_sizes,
    color=TEAL,
    edgecolors=DARK_BLUE,
    linewidths=0.8,
    zorder=3,
    label='Bin mean overdose rate (dot size ∝ n counties)'
)

# Trendline through bin means
ax.plot(
    trend_x, trend_y,
    color=DARK_BLUE,
    linewidth=2.2,
    linestyle='--',
    zorder=4,
    label=f'Bin-level OLS trend  (r = {b_r:.2f}, p = {b_p:.3f})'
)

# Annotate each dot with n= and decile label
for _, row in bin_stats.iterrows():
    ax.text(
        row['bin_mid'],
        row['mean_overdose'] + row['se_overdose'] + 0.4,
        f"D{int(row['rx_bin']) + 1}\nn={int(row['n_counties'])}",
        ha='center', va='bottom', fontsize=7, color=DARK_BLUE, linespacing=1.4
    )

# Grid and spines
ax.yaxis.grid(True, linestyle=':', linewidth=0.7, color=DARK_BLUE, alpha=0.25)
ax.xaxis.grid(True, linestyle=':', linewidth=0.7, color=DARK_BLUE, alpha=0.25)
ax.set_axisbelow(True)
for spine in ax.spines.values():
    spine.set_edgecolor(DARK_BLUE)
    spine.set_linewidth(0.8)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.tick_params(colors=DARK_BLUE, labelsize=9)

# Correlation annotation
ax.text(
    0.02, 0.95,
    f'County-level Spearman ρ = {rho:.2f}  (p = {p_spearman:.3f})\n'
    f'County-level Pearson  r = {r:.2f}  (p = {p_ols:.3f})',
    transform=ax.transAxes, fontsize=8.5,
    color=DARK_BLUE, fontstyle='italic', va='top', linespacing=1.6
)

# Labels and title
ax.set_xlabel(
    'Median Opioid Prescriptions per 100k within Decile Bin (2008–2017 cumulative)',
    fontsize=10, color=DARK_BLUE
)
ax.set_ylabel('Mean Overdose Deaths per 100k (2008–2017 cumulative)', fontsize=10, color=DARK_BLUE)
ax.set_title(
    'County Prescription Volume vs. Overdose Death Rate (2008–2017)',
    fontsize=13, fontweight='bold', color=DARK_BLUE, pad=14, loc='left'
)
ax.text(
    0.0, 1.03,
    'Equal-count decile bins (D1=lowest Rx, D10=highest)  |  '
    'Error bars = ±1 SE  |  Counties with suppressed CDC data excluded',
    transform=ax.transAxes, fontsize=7.5, color=DARK_BLUE, fontstyle='italic'
)

ax.legend(fontsize=9, framealpha=0.6, edgecolor=DARK_BLUE,
          facecolor=LIGHT_BG, labelcolor=DARK_BLUE, loc='lower right')

# Teal title underline
fig.add_axes([0.09, 0.895, 0.65, 0.008]).set_facecolor(TEAL)
fig.axes[-1].set_axis_off()

plt.tight_layout(rect=[0.02, 0, 1, 1])
plt.savefig('binscatter_rx_per_capita_vs_overdose.png', dpi=150, facecolor=FADED_BG)
plt.show()