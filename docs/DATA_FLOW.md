# Data Flow

Query-to-output mapping and data dependencies.

---

## Pipeline Overview

```
IQVIA DB --> queries/*.py --> output/iqvia_core/, output/extended/, output/county/
CDC CSVs --> cdc/load_*.py --> cdc/merge_*.py --> output/cdc/
Census ACS --> census/load_census.py --> census/merge_*.py
output/county/ + output/cdc/ --> visualizations/*.py --> output/cdc/*.html, output/plots/*.html
```

---

## Query to Output

| Command | Outputs |
|---------|---------|
| `main.py explore` | `output/lookups/medicaid_plan_ids.csv`, `payor_plan_*.csv` |
| `main.py medicaid` | `output/iqvia_core/medicaid_vs_nonmedicaid_by_*.csv` |
| `main.py geo` | `output/extended/` (state/zip geographic data) |
| `main.py extended` | `output/extended/medicaid_vs_nonmedicaid_by_state_year.csv`, `by_sales_channel.csv` |
| `main.py county` | `output/county/iqvia_county_year_panel.csv`, `iqvia_zip_year_panel.csv` |
| `main.py cdc` | `output/cdc/iqvia_cdc_merged_by_state.csv` |
| `main.py cdc-drug` | `output/cdc/cdc_illicit_overdose_by_state_year.csv`, `heroin_vs_fentanyl_1999-2018.csv` |
| `main.py census` | Merged Census + IQVIA (in-memory / downstream) |
| `main.py merge` | IQVIA zip + Census merge |

---

## Map Data Dependencies

| Map | Data Source |
|-----|-------------|
| map-county | `Datasets/cdc/overdose_by_county_year_2008-2017.csv`, `Datasets/geo/us_counties_geojson.json` |
| map-fentanyl | `Datasets/cdc/overdose_by_county_drugtype_*.csv`, `Datasets/geo/us_counties_geojson.json` |
| map-illicit | `output/cdc/cdc_illicit_overdose_by_state_year.csv` (run `cdc-drug` first) |
| map-dashboard | `output/county/iqvia_cdc_county_merged.csv` (run `county` + merge) |
| map-mme | `output/county/iqvia_cdc_county_merged.csv` or `iqvia_county_year_panel.csv` |
