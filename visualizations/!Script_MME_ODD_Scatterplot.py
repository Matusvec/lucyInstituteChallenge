import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

final_df = pd.read_csv("C:\\Users\\tmnfn\\OneDrive\\Desktop\\python shit\\hdac\\AvgMME_v_ODD.csv")

final_df['Average MME'] = pd.to_numeric(final_df['Average MME'], errors='coerce')
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

final_df = pd.read_csv("C:\\Users\\tmnfn\\OneDrive\\Desktop\\python shit\\hdac\\AvgMME_v_ODD.csv")

# Force numeric and drop suppressed/missing deaths before aggregating
final_df['Average MME'] = pd.to_numeric(final_df['Average MME'], errors='coerce')
final_df['Deaths'] = pd.to_numeric(final_df['Deaths'], errors='coerce')
final_df.dropna(subset=['Deaths', 'Average MME'], inplace=True)

print(f"Rows after dropping suppressed/missing: {len(final_df)}")

county_df = final_df.groupby('county_code').agg(
    Avg_MME=('Average MME', 'mean'),
    Total_Deaths=('Deaths', 'sum')
).reset_index()

# Flag the county of interest
county_df['Highlight'] = county_df['county_code'].apply(
    lambda x: 'County 18141' if x == 18141 else 'Other Counties'
)

r, p = stats.pearsonr(county_df['Avg_MME'], county_df['Total_Deaths'])
print(f"Pearson r: {r:.3f}, p-value: {p:.4f}")
print(f"Total counties after cleaning: {len(county_df)}")

sns.set_theme(style="whitegrid")
plt.figure(figsize=(11, 7))

sns.scatterplot(
    data=county_df, x='Avg_MME', y='Total_Deaths',
    hue='Highlight',
    palette={'Other Counties': 'steelblue', 'County 18141': 'red'},
    size='Highlight',
    sizes={'Other Counties': 40, 'County 18141': 120},
    alpha=0.6, edgecolor='white', linewidth=0.3
)

sns.regplot(data=county_df, x='Avg_MME', y='Total_Deaths', scatter=False, color='black', line_kws={'linewidth': 1.5})

# Label the highlighted county
target = county_df[county_df['county_code'] == 18141].iloc[0]
plt.annotate('County 18141', xy=(target['Avg_MME'], target['Total_Deaths']),
             xytext=(10, 10), textcoords='offset points', fontsize=10,
             color='red', fontweight='bold')

plt.title(f'Average MME vs. Total Overdose Deaths by County (2008–2017)\nPearson r = {r:.3f},  p = {p:.4f}', fontsize=14)
plt.xlabel('Average MME per County (mean across years)', fontsize=12)
plt.ylabel('Total Overdose Deaths per County (summed across years)', fontsize=12)
plt.legend(title='County')

plt.tight_layout()
plt.savefig("C:\\Users\\tmnfn\\OneDrive\\Desktop\\python shit\\hdac\\visualizations\\mme_vs_deaths_by_county.png", dpi=300)
plt.show()