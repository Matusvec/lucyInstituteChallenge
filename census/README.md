# Census Data Loading

Loads Census ACS 5-year estimates and USAFacts data for merging with IQVIA prescription data.

## Modules

| Module | Purpose |
|--------|---------|
| `load_census.py` | Load ACS tables (B01003, B02001, B19013, S1701, S2704) from `Datasets/ACSDT*` and `Datasets/ACSST*` folders. Extracts 5-digit zip from GEO_ID, merges into single zip-level DataFrame. |
| `merge_iqvia_census.py` | Merge IQVIA zip-level prescription data with Census demographics. |

## Data Locations

- **ACS tables:** `Datasets/ACSDT5Y2018.B01003_*/`, `Datasets/ACSDT5Y2018.B02001_*/`, etc.
- **USAFacts:** `Datasets/census/USAFacts_health_data.csv`
