import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

final_df = pd.read_csv("C:\\Users\\tmnfn\\OneDrive\\Desktop\\python shit\\hdac\\AvgMME_v_ODD.csv")

# Check dtypes
print(final_df.dtypes)
print(final_df.head())

# Force numeric conversion (anything that can't convert becomes NaN)
final_df['Average MME'] = pd.to_numeric(final_df['Average MME'], errors='coerce')
final_df['Deaths'] = pd.to_numeric(final_df['Deaths'], errors='coerce')

# Aggregate to one row per county
county_df = final_df.groupby('county_code').agg(
    Avg_MME=('Average MME', 'mean'),
    Total_Deaths=('Deaths', 'sum')
).reset_index()

# Drop any NaN rows that resulted from bad conversions
county_df.dropna(subset=['Avg_MME', 'Total_Deaths'], inplace=True)

print(f"\nTotal counties after cleaning: {len(county_df)}")
print(county_df.dtypes)

# Pearson correlation
r, p = stats.pearsonr(county_df['Avg_MME'], county_df['Total_Deaths'])
print(f"\nPearson r: {r:.3f}, p-value: {p:.4f}")

# Plot
sns.set_theme(style="whitegrid")
plt.figure(figsize=(11, 7))

sns.scatterplot(data=county_df, x='Avg_MME', y='Total_Deaths', alpha=0.5, edgecolor='white', linewidth=0.3)
sns.regplot(data=county_df, x='Avg_MME', y='Total_Deaths', scatter=False, color='red', line_kws={'linewidth': 1.5})

plt.title(f'Average MME vs. Total Overdose Deaths by County (2008–2017)\nPearson r = {r:.3f},  p = {p:.4f}', fontsize=14)
plt.xlabel('Average MME per County (mean across years)', fontsize=12)
plt.ylabel('Total Overdose Deaths per County (summed across years)', fontsize=12)

plt.tight_layout()
plt.savefig("C:\\Users\\tmnfn\\OneDrive\\Desktop\\python shit\\hdac\\mme_vs_deaths_by_county.png", dpi=300)
plt.show()