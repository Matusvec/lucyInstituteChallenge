# CDC WONDER Data Loading

Loads and merges CDC Multiple Cause of Death data with IQVIA outputs.
Data source: [CDC WONDER](https://wonder.cdc.gov) -- Multiple Cause of Death.

## Modules

| Module | Purpose | Data Source |
|--------|---------|-------------|
| `load_wonder.py` | State-level overdose deaths (1999--2020) | `Datasets/cdc/overdose_by_state_year_1999-2020.csv` |
| `load_wonder_county.py` | County-level overdose deaths (2008--2017) | `Datasets/cdc/overdose_by_county_year_2008-2017.csv` |
| `load_wonder_county_drugtype.py` | County by drug type (fentanyl, heroin, etc.) | `Datasets/cdc/overdose_by_county_drugtype_*.csv` |
| `load_wonder_drug_types.py` | State by drug type, illicit spread panel | `Datasets/cdc/illicit_overdose_by_state_1999-2018.csv` |
| `merge_iqvia_cdc.py` | Merge IQVIA state data with CDC overdose rates | Outputs `output/cdc/iqvia_cdc_merged_by_state.csv` |
| `merge_iqvia_cdc_county.py` | Merge IQVIA county panel with CDC county data | Outputs `output/county/iqvia_cdc_county_merged.csv` |
| `merge_iqvia_cdc_drugtype.py` | Merge IQVIA state x year with CDC drug-type | Outputs `output/cdc/` |

## Data Notes

- Death counts < 10 are **suppressed** by CDC for privacy (appear as grey on maps).
- Drug-type deaths can list multiple ICD-10 codes per death (e.g., heroin + fentanyl),
  so summing across drug types may overcount.
- County data covers 2008--2017; state data covers 1999--2020.
