# CDC WONDER Data Loading

Loads and merges CDC Multiple Cause of Death data with IQVIA outputs.

| Module | Purpose |
|--------|---------|
| `load_wonder.py` | State-level overdose (1999–2020) |
| `load_wonder_county.py` | County overdose (2008–2017) |
| `load_wonder_county_drugtype.py` | County by drug type (fentanyl, heroin, etc.) |
| `load_wonder_drug_types.py` | State by drug type, illicit spread panel |
| `merge_iqvia_cdc.py` | IQVIA state + CDC overdose |
| `merge_iqvia_cdc_county.py` | IQVIA county + CDC county |
| `merge_iqvia_cdc_drugtype.py` | IQVIA state×year + CDC drug-type |

**Data:** `Datasets/cdc/` — overdose CSVs from CDC WONDER.

**Outputs:** `output/cdc/` — merged CSVs used by maps and charts.
