import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import numpy as np
final_df = pd.read_csv("C:\\Users\\tmnfn\\OneDrive\\Desktop\\python shit\\hdac\\AvgMME_v_ODD.csv")
final_df['Average MME'] = pd.to_numeric(final_df['Average MME'], errors='coerce')
final_df['Deaths'] = pd.to_numeric(final_df['Deaths'], errors='coerce')
final_df.dropna(subset=['Deaths', 'Average MME'], inplace=True)
print(f"Rows after dropping suppressed/missing: {len(final_df)}")
county_df = final_df.groupby('county_code').agg(
    Avg_MME=('Average MME', 'mean'),
    Total_Deaths=('Deaths', 'sum')
).reset_index()
print(f"Total counties after cleaning: {len(county_df)}")
# --- Equal-count decile bins with jitter to handle tied MME values ---
county_df['Avg_MME_jittered'] = county_df['Avg_MME'] + np.random.uniform(-1e-6, 1e-6, size=len(county_df))
county_df['MME_bin'] = pd.qcut(county_df['Avg_MME_jittered'], q=10, duplicates='drop')
binned_df = county_df.groupby('MME_bin', observed=True).agg(
    Bin_Mid=('Avg_MME', 'mean'),
    Mean_Deaths=('Total_Deaths', 'mean'),
    Std_Deaths=('Total_Deaths', 'std'),
    Count=('Total_Deaths', 'count')
).reset_index()
# 95% CI = 1.96 * (std / sqrt(n))
binned_df['CI_95'] = 1.96 * (binned_df['Std_Deaths'] / binned_df['Count'].pow(0.5))
# Pearson r on full county-level data
r, p = stats.pearsonr(county_df['Avg_MME'], county_df['Total_Deaths'])
print(f"Pearson r: {r:.3f}, p-value: {p:.4f}")
# Bin-level OLS
slope, intercept, r_bin, p_bin, se = stats.linregress(binned_df['Bin_Mid'], binned_df['Mean_Deaths'])
print(f"Bin-level OLS — slope: {slope:.4f}, intercept: {intercept:.4f}, r: {r_bin:.3f}, p: {p_bin:.4f}")
sns.set_theme(style="whitegrid")
fig, ax = plt.subplots(figsize=(11, 7))
# Error bars
ax.errorbar(
    binned_df['Bin_Mid'],
    binned_df['Mean_Deaths'],
    yerr=binned_df['CI_95'],
    fmt='none',
    ecolor='#BFA15D',
    elinewidth=1.2,
    capsize=5,
    capthick=1.2,
    alpha=0.6,
    zorder=2
)
scatter = ax.scatter(
    binned_df['Bin_Mid'],
    binned_df['Mean_Deaths'],
    s=binned_df['Count'] * 3,
    color='#0C2340',
    alpha=0.75,
    edgecolors='white',
    linewidths=0.5,
    zorder=3
)
ols_line, = ax.plot([], [], color='black', linewidth=1.5,
                    label=f'Bin-level OLS (r={r_bin:.3f}, p={p_bin:.4f})')
sns.regplot(
    data=binned_df,
    x='Bin_Mid',
    y='Mean_Deaths',
    scatter=False,
    ax=ax,
    color='black',
    line_kws={'linewidth': 1.5}
)
for count_val in [5, 20, 50]:
    ax.scatter([], [], s=count_val * 3, color='#0C2340', alpha=0.75,
               edgecolors='white', label=f'n = {count_val}')
ax.legend(title='Counties per Bin', frameon=True)
ax.set_title(
    f'Average MME vs. Mean Overdose Deaths by MME Bin (2008–2017)\nPearson r = {r:.3f}, p = {p:.4f}',
    fontsize=14
)
ax.set_xlabel('Average MME (binned, mean within bin)', fontsize=12)
ax.set_ylabel('Mean Total Overdose Deaths per County', fontsize=12)
plt.tight_layout()
plt.savefig(
    "C:\\Users\\tmnfn\\OneDrive\\Desktop\\python shit\\hdac\\visualizations\\mme_vs_deaths_binned.png",
    dpi=300
)
plt.show()

