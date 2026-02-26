import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.family'] = 'serif'

def main():
    csv_path = os.path.join('output', 'county', 'iqvia_county_year_panel.csv')
    df = pd.read_csv(csv_path, usecols=['state', 'county_fips', 'year', 'avg_mme_per_unit', 'total_rx'])
    df['avg_mme_per_unit'] = pd.to_numeric(df['avg_mme_per_unit'], errors='coerce')
    df['total_rx'] = pd.to_numeric(df['total_rx'], errors='coerce')
    df = df.dropna()

    # Compute weighted average MME per county
    df['weighted_mme'] = df['avg_mme_per_unit'] * df['total_rx']
    county_agg = df.groupby('county_fips').agg(
        weighted_avg_mme=('weighted_mme', 'sum'),
        total_weight=('total_rx', 'sum')
    )
    county_agg['avg_mme_per_unit'] = county_agg['weighted_avg_mme'] / county_agg['total_weight']
    county_agg = county_agg.dropna()

    out_dir = os.path.join('output', 'plots')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'avg_mme_per_unit_hist_weighted.png')

    # Compute simple median for the aggregated data
    median_val = county_agg['avg_mme_per_unit'].median()
    mean_val = county_agg['avg_mme_per_unit'].mean()
    std_val = county_agg['avg_mme_per_unit'].std()
    bin_width = (46 - 0) / 50

    plt.figure(figsize=(8, 6), facecolor='#EEF3F9')
    plt.hist(county_agg['avg_mme_per_unit'], bins=50, range=(0, 46), color='#4A6B8A', edgecolor='black')
    plt.axvline(median_val, color='#BFA15D', linestyle='--', linewidth=2, label=f'Median: {median_val:.2f}')
    plt.plot([], [], ' ', label=f'Mean: {mean_val:.2f}')
    plt.plot([], [], ' ', label=f'Std: {std_val:.2f}')
    plt.plot([], [], ' ', label=f'Bin size: {bin_width:.2f}')
    plt.xlabel('Average Morphine Milligram Equivalence per Prescription')
    plt.ylabel('Frequency')
    plt.title('Frequency of average Morphine Milligram Equivalence by county from 2008-2017')
    plt.xlim(0, 40)
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.legend()
    plt.ticklabel_format(style='plain', axis='y')
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    print(f"Saved histogram to {out_path}")
    print(f"n={len(county_agg)}, median={median_val:.4f}, mean={mean_val:.4f}, std={std_val:.4f}, bin_width={bin_width:.4f}")


if __name__ == '__main__':
    main()
