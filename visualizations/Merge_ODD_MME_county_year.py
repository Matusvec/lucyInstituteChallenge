import pandas as pd

# Load your datasets
df1 = pd.read_csv("C:\\Users\\tmnfn\\OneDrive\\Desktop\\python shit\\iqvia_county_year_panel.csv")
df2 = pd.read_csv("C:\\Users\\tmnfn\\OneDrive\\Desktop\\python shit\\overdose_by_county_year_2008-2017.csv")

# Check column names before renaming to avoid errors
print("df1 columns:", df1.columns.tolist())
print("df2 columns:", df2.columns.tolist())

# Rename to standardize
df1.rename(columns={'county_fips': 'county_code', 'avg_mme_per_unit': 'Average MME'}, inplace=True)
df2.rename(columns={'County Code': 'county_code', 'Year':'year'}, inplace=True)

# Keep county_code AND year in both subsets
iqcy_subset = df1[['county_code', 'year', 'Average MME']]
odcy_subset = df2[['county_code', 'year', 'Deaths']]

# Merge on both county AND year
final_df = pd.merge(iqcy_subset, odcy_subset, on=['county_code', 'year'], how='inner')

# Sanity check
print(f"\nMerged shape: {final_df.shape}")
print(final_df.head(10))

final_df.to_csv("C:\\Users\\tmnfn\\OneDrive\\Desktop\\python shit\\hdac\\AvgMME_v_ODD.csv", index=False)

