import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd
import scipy.stats as stats
import statsmodels.api as sm
import os
import sys

BASE = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, BASE)
from visualizations.theme import DARK_BLUE, MID_BLUE, GOLD_BROWN, TEAL, DARK_TEAL

pd.set_option('display.max_rows', 20)
pd.set_option('display.max_columns', 10)

# ── 1. Load Data ──────────────────────────────────────────────────────────────

US_medicaid = pd.read_csv('C:/Users/M16Mc/Documents/2026/lucyInstituteChallenge/census/USAFacts_health_data.csv')
US_medicaid = US_medicaid.rename(columns={"Percent of US population on Medicaid": "percent_on_medicaid"})

med_rx = pd.read_csv('C:/Users/M16Mc/Documents/2026/lucyInstituteChallenge/output/county/iqvia_county_year_panel.csv')
med_rx = med_rx[['county_fips', 'year', 'total_rx','medicaid_rx', 'nonmedicaid_rx']]
med_rx = med_rx[(med_rx['year'] >= 2008) & (med_rx['year'] <= 2017)]

med_rx['medicaid_rx_rate'] = med_rx['medicaid_rx'] / med_rx['total_rx']


county_overdose = pd.read_csv('C:/Users/M16Mc/Documents/2026/lucyInstituteChallenge/Datasets/cdc/overdose_by_county_year_2008-2017.csv')
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



# --- Weighted average medicaid_rx_rate by year (pivot table) ---

# Remove rows with missing population or medicaid_rx_rate
med_rx_clean = med_rx.dropna(subset=['population', 'medicaid_rx_rate'])

# ── 2. Clean and Compute Weighted Average by Year ────────────────────────────

# Convert population to numeric (coerce errors to NaN, then drop)
med_rx_clean['population'] = pd.to_numeric(med_rx_clean['population'], errors='coerce')
med_rx_clean = med_rx_clean.dropna(subset=['population'])

# If 'year' is both a column and index, drop from index
if med_rx_clean.index.names and 'year' in med_rx_clean.index.names:
    med_rx_clean = med_rx_clean.reset_index()

# Ensure 'year' is a 1D column
if 'year' in med_rx_clean.columns and med_rx_clean['year'].ndim > 1:
    med_rx_clean['year'] = med_rx_clean['year'].iloc[:,0]

# Compute weighted average by year
weighted_avg_by_year = med_rx_clean.groupby('year').apply(
    lambda x: np.average(x['medicaid_rx_rate'], weights=x['population'])
).reset_index(name='weighted_avg_medicaid_rx_rate')


# ── 3. Build Timeline DataFrame ───────────────────────────────────────────────

US_medicaid = US_medicaid.rename(columns={'fiscal year': 'year'})

US_medicaid = US_medicaid.merge(weighted_avg_by_year, 
                                left_on='year', 
                                right_on='year', 
                                how='inner')

timeline_df = pd.merge(
    US_medicaid.rename(columns={"Percent of US population on Medicaid": "percent_on_medicaid"}),
    weighted_avg_by_year.rename(columns={"weighted_avg_medicaid_rx_rate": "county_avg_medicaid_rx_rate"}),
    on="year"
)


timeline_df['delta'] = (
    timeline_df['weighted_avg_medicaid_rx_rate'] - timeline_df['percent_on_medicaid']
)

print("=" * 55)
print("DESCRIPTIVE STATISTICS: Delta (Rx Share − Pop Share)")
print("=" * 55)
print(timeline_df[['year', 'percent_on_medicaid',
                    'weighted_avg_medicaid_rx_rate', 'delta']].to_string(index=False))
print(f"\nMean delta:          {timeline_df['delta'].mean():.4f}")
print(f"Min delta:           {timeline_df['delta'].min():.4f}")
print(f"Max delta:           {timeline_df['delta'].max():.4f}")
print(f"Years delta < 0:     {(timeline_df['delta'] < 0).sum()} / {len(timeline_df)}")

# ── 4. Statistical Tests ──────────────────────────────────────────────────────

DARK_BLUE = "#0C2340"   # Dark Blue
MID_BLUE  = "#3B5E8C"   # midpoint between #0C2340 and #E1E8F2
GOLD_BROWN = "#BFA15D"   # Golden Brown
TEAL     = "#4EAE81"   # Teal
DARK_TEAL = "#1B3B2C"   # Dark Teal

# ── Test 1: One-sample t-test on 10 annual deltas ────────────────────────────

t_stat, p_two = stats.ttest_1samp(timeline_df['delta'], popmean=0)
p_one = p_two / 2 if t_stat < 0 else 1 - p_two / 2

print("\n" + "=" * 55)
print("TEST 1: One-sample t-test on annual delta series (n=10)")
print("  H0: mean delta = 0")
print("  H1: mean delta < 0  [Medicaid under-prescribed]")
print("=" * 55)
print(f"  t-statistic:      {t_stat:.4f}")
print(f"  p-value (two):    {p_two:.4f}")
print(f"  p-value (one):    {p_one:.4f}")
print(f"  Mean delta:       {timeline_df['delta'].mean()*100:.2f} percentage points")

# ── Test 2: County-level WLS with year fixed effects ─────────────────────────
# Delta is computed at county-year level by merging national enrollment share.
# The year fixed effects then absorb national trends, and we test whether the
# intercept (constant) is significantly below zero — i.e., whether counties
# are systematically under-prescribed relative to enrollment after year shocks
# are removed.

panel = med_rx_clean.merge(
    US_medicaid[['year', 'percent_on_medicaid']], on='year', how='left'
)

# County-level delta: local Rx rate minus national enrollment share for that year
panel['county_delta'] = panel['medicaid_rx_rate'] - panel['percent_on_medicaid']

# Year dummies absorb any year-level shock common to all counties
year_dummies = pd.get_dummies(panel['year'], prefix='yr', drop_first=True).astype(float)

# X is just year fixed effects — we're asking whether the residual (intercept)
# after absorbing year trends is negative
X = sm.add_constant(year_dummies)
y = panel['county_delta']
w = panel['population']

ols_model = sm.WLS(y, X, weights=w).fit(cov_type='HC3')

print("\n" + "=" * 55)
print("TEST 2: County-level WLS, outcome = county_delta")
print("  Year FE absorb national trends")
print("  Intercept < 0 → counties systematically under-prescribed")
print("  HC3 robust SEs correct for county size heteroskedasticity")
print("=" * 55)
print(ols_model.summary(
    xname=['intercept'] + [str(y) for y in sorted(panel['year'].unique())[1:]]
))

# ── Test 3: Wilcoxon signed-rank on annual deltas (non-parametric) ────────────

wilcox = stats.wilcoxon(timeline_df['delta'], alternative='less')

print("\n" + "=" * 55)
print("TEST 3: Wilcoxon signed-rank test on annual delta (n=10)")
print("  No normality assumption — uses ranks only")
print("  H1: delta systematically < 0")
print("=" * 55)
print(f"  Statistic:  {wilcox.statistic:.4f}")
print(f"  p-value:    {wilcox.pvalue:.4f}")

# ── 5. Compute county-level weighted CI for bottom panel ─────────────────────
# For each year: population-weighted mean and SE of county_delta,
# then 95% CI = mean ± 1.96 * SE

def weighted_mean_se(group):
    w   = group['population']
    d   = group['county_delta']
    w   = w / w.sum()                          # normalise weights
    mu  = (w * d).sum()                        # weighted mean
    var = (w * (d - mu) ** 2).sum()            # weighted variance
    n   = group['population'].count()
    se  = np.sqrt(var / n)                     # weighted SE
    return pd.Series({'delta_mean': mu, 'delta_se': se})

ci_df = (
    panel.groupby('year')
    .apply(weighted_mean_se)
    .reset_index()
)
ci_df['ci95'] = 1.96 * ci_df['delta_se']

# Merge CIs into timeline_df for plotting
timeline_df = timeline_df.merge(ci_df[['year', 'delta_mean', 'ci95']], on='year', how='left')


# ── 5. Timeline Plot ──────────────────────────────────────────────────────────

fig, axes = plt.subplots(2, 1, figsize=(11, 9), sharex=True,
                         gridspec_kw={'height_ratios': [2, 1]})

fig.patch.set_facecolor(DARK_BLUE)
ax1 = axes[0]
ax1.set_facecolor(DARK_BLUE)
ax1.plot(timeline_df['year'], timeline_df['percent_on_medicaid'] * 100,
         color=MID_BLUE, marker='o', linewidth=2.2,
         label='Medicaid Enrollment Share (% US Pop)')
ax1.plot(timeline_df['year'], timeline_df['weighted_avg_medicaid_rx_rate'] * 100,
         color=GOLD_BROWN, marker='s', linewidth=2.2,
         label='Medicaid Share of Opioid Rx (Pop-Weighted County Avg)')
ax1.fill_between(timeline_df['year'],
                 timeline_df['percent_on_medicaid'] * 100,
                 timeline_df['weighted_avg_medicaid_rx_rate'] * 100,
                 alpha=0.2, color=TEAL,
                 label='Gap (enrollment − Rx share)')
ax1.set_ylabel('Percent (%)', fontsize=12, color='white')
ax1.set_title('Medicaid Population Share vs. Opioid Prescription Share\n2008–2017, US Counties (Population-Weighted)',
              fontsize=13, fontweight='bold', color='white')
ax1.legend(fontsize=10, facecolor=DARK_BLUE, edgecolor='white', labelcolor='white')
ax1.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.1f%%'))
ax1.tick_params(colors='white')
ax1.xaxis.label.set_color('white')
ax1.spines['bottom'].set_color('white')
ax1.spines['top'].set_color('white')
ax1.spines['left'].set_color('white')
ax1.spines['right'].set_color('white')
ax1.grid(axis='y', linestyle='--', alpha=0.3, color='white')

ax1.set_ylim(bottom=0)

ax2 = axes[1]
ax2.set_facecolor(DARK_BLUE)
bar_colors = [GOLD_BROWN if d >= 0 else TEAL for d in timeline_df['delta']]
ax2.bar(timeline_df['year'], timeline_df['delta'] * 100,
        color=bar_colors, edgecolor='white', linewidth=0.6)

ax2.errorbar(
    timeline_df['year'],
    timeline_df['delta'] * 100,
    yerr=timeline_df['ci95'] * 100,
    fmt='none',
    color=GOLD_BROWN,
    capsize=5,
    capthick=1.8,
    elinewidth=1.8,
    zorder=5,
)

ax2.axhline(0, color='white', linewidth=1.0)
ax2.set_ylabel('Delta (pp)', fontsize=11, color='white')
ax2.set_xlabel('Year', fontsize=12, color='white')
ax2.set_title('Annual Delta: Rx Share \u2212 Enrollment Share\n'
              '(Teal = Medicaid received less than population share) '
              '\u00b1 95% CI (county-level, pop-weighted)',
              fontsize=11, color='white')
ax2.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.1f%%'))
ax2.set_xticks(timeline_df['year'])
ax2.tick_params(colors='white')
ax2.spines['bottom'].set_color('white')
ax2.spines['top'].set_color('white')
ax2.spines['left'].set_color('white')
ax2.spines['right'].set_color('white')
ax2.grid(axis='y', linestyle='--', alpha=0.3, color='white')

plt.tight_layout()
plt.savefig('medicaid_rx_vs_enrollment_timeline.png', dpi=150, bbox_inches='tight')
plt.show()