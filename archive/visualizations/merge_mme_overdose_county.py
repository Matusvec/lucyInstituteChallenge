"""
Merge IQVIA county panel (MME) with CDC county overdose data.
Output used by mme_vs_deaths_scatterplot.py.

Run: python -m visualizations.merge_mme_overdose_county
"""
import os
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

df1 = pd.read_csv(os.path.join(BASE, "output", "county", "iqvia_county_year_panel.csv"))
df2 = pd.read_csv(os.path.join(BASE, "Datasets", "cdc", "overdose_by_county_year_2008-2017.csv"))

df1 = df1.rename(columns={"county_fips": "county_code", "avg_mme_per_unit": "Average MME"})
df2 = df2.rename(columns={"County Code": "county_code", "Year": "year"})

iqcy_subset = df1[["county_code", "year", "Average MME"]].copy()
iqcy_subset["county_code"] = iqcy_subset["county_code"].astype(str).str.zfill(5)
odcy_subset = df2[["county_code", "year", "Deaths"]].copy()
odcy_subset["county_code"] = odcy_subset["county_code"].astype(str).str.zfill(5)

final_df = pd.merge(iqcy_subset, odcy_subset, on=["county_code", "year"], how="inner")

out_path = os.path.join(BASE, "output", "county", "avg_mme_vs_overdose.csv")
os.makedirs(os.path.dirname(out_path), exist_ok=True)
final_df.to_csv(out_path, index=False)
print(f"Merged shape: {final_df.shape}")
print(f"Saved: {out_path}")
