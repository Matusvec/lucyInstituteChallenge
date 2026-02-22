# Data Catalog

All raw/source data files used in the Lucy Institute Opioid Challenge.
Processed outputs go in `output/`; raw inputs live here in `Datasets/`.

---

## Datasets/cdc/ — CDC WONDER Overdose Data

Source: https://wonder.cdc.gov -> Multiple Cause of Death, 1999-2020

| File | Granularity | Years | Rows | Key Columns |
|------|------------|-------|------|-------------|
| `overdose_by_state_year_1999-2020.csv` | State x Year | 1999-2020 | ~1,100 | State, Year, Deaths, Population, Crude Rate |
| `overdose_by_county_year_2008-2017.csv` | County x Year | 2008-2017 | ~31,500 | County, County Code (FIPS), Year, Deaths, Population, Crude Rate |
| `overdose_by_county_drugtype_2008-2012.csv` | County x Year x Drug | 2008-2012 | ~3,400 | + Multiple Cause of death Code (T40.1-T40.5, T43.6) |
| `overdose_by_county_drugtype_2013-2017.csv` | County x Year x Drug | 2013-2017 | ~6,400 | + Multiple Cause of death Code (T40.1-T40.5, T43.6) |
| `illicit_overdose_by_state_1999-2018.csv` | State x Year x Cause | 1999-2018 | ~2,400 | Illicit drug overdose deaths (X40-X44 unintentional) |
| `rx_overdose_by_state_1999-2018.csv` | State x Year x Cause | 1999-2018 | ~2,400 | Prescription drug overdose deaths |

### ICD-10 Drug Codes (Multiple Cause of Death)

| Code | Drug Category |
|------|--------------|
| T40.1 | Heroin |
| T40.2 | Natural/semi-synthetic opioids (oxycodone, hydrocodone) |
| T40.3 | Methadone |
| T40.4 | Synthetic opioids other than methadone (**fentanyl**) |
| T40.5 | Cocaine |
| T43.6 | Psychostimulants with abuse potential (methamphetamine) |

### Underlying Cause of Death Codes (drug-induced deaths)

| Code | Meaning |
|------|---------|
| X40-X44 | Accidental drug poisoning |
| X60-X64 | Intentional self-poisoning (suicide) |
| X85 | Assault by drug poisoning (homicide) |
| Y10-Y14 | Drug poisoning, undetermined intent |

### Notes on CDC Suppression

- Death counts under 10 are marked "Suppressed" for privacy.
- Rates based on 20 or fewer deaths are flagged "Unreliable".
- At county level, ~50% of rows are suppressed (small/rural counties).
- County-level drug-type data has more suppression (fewer deaths per type).

---

## Datasets/geo/ — Geographic Reference Files

| File | Description |
|------|-------------|
| `us_counties_geojson.json` | Simplified US county boundaries (from Plotly datasets). Used for county-level choropleth maps. ~3,200 counties with 5-digit FIPS as feature ID. |

---

## Datasets/ (root) — Other Source Data

| File | Description |
|------|-------------|
| `Multiple Cause of Death, 1999-2020.csv` | Legacy copy of state-level CDC data (same as `cdc/overdose_by_state_year_1999-2020.csv`) |
| `TitalMedicaidData.csv` | Indiana county-level Medicaid coverage rates (93 rows) |
| `zcta_county_rel_10.csv` | Census 2010 ZCTA-to-County crosswalk (auto-downloaded by `county_panel.py`) |
| `us_counties_geojson.json` | Legacy copy of county GeoJSON |

---

## Naming Convention for New Files

When adding new CDC WONDER downloads, use this pattern:

```
Datasets/cdc/{metric}_by_{geography}_{optional_detail}_{year_range}.csv
```

Examples:
- `overdose_by_county_year_2018-2022.csv` — total overdose deaths, county x year
- `overdose_by_county_drugtype_2018-2022.csv` — by drug type, county x year
- `overdose_by_county_occurrence_2008-2017.csv` — occurrence-based (not residence)
- `fentanyl_by_county_year_2012-2022.csv` — fentanyl-only (T40.4)

---

## output/ — Processed Results

| Directory | Contents |
|-----------|----------|
| `output/iqvia_core/` | Q1-Q5: Medicaid vs non-Medicaid by year, state, drug, specialty |
| `output/extended/` | Q6-Q9: state x year, sales channel, monthly, 2018 sample |
| `output/lookups/` | Payor plan tables, Medicaid plan IDs |
| `output/county/` | County-level IQVIA panel (zip -> county aggregation) |
| `output/county/_incremental/` | Per-year cache for county panel (auto-generated, safe to delete for re-run) |
| `output/cdc/` | Processed CDC outputs, merged panels, and HTML map visualizations |
