# Data Catalog

Raw/source data files used in the Lucy Institute Opioid Challenge.
Processed outputs go in `output/`; raw inputs live here in `Datasets/`.

---

## Datasets/cdc/ - CDC WONDER Overdose Data

Source: https://wonder.cdc.gov -> Multiple Cause of Death, 1999-2020

| File | Granularity | Years | Key Columns |
|------|-------------|-------|--------------|
| `overdose_by_state_year_1999-2020.csv` | State x Year | 1999-2020 | State, Year, Deaths, Population, Crude Rate |
| `overdose_by_county_year_2008-2017.csv` | County x Year | 2008-2017 | County, County Code (FIPS), Year, Deaths, Population, Crude Rate |
| `overdose_by_county_drugtype_2008-2012.csv` | County x Year x Drug | 2008-2012 | + Multiple Cause of death Code (T40.1-T40.5, T43.6) |
| `overdose_by_county_drugtype_2013-2017.csv` | County x Year x Drug | 2013-2017 | Same as above |
| `illicit_overdose_by_state_1999-2018.csv` | State x Year x Cause | 1999-2018 | Illicit drug overdose deaths |
| `rx_overdose_by_state_1999-2018.csv` | State x Year x Cause | 1999-2018 | Prescription drug overdose deaths |

### ICD-10 Drug Codes

| Code | Drug Category |
|------|---------------|
| T40.1 | Heroin |
| T40.2 | Natural/semi-synthetic opioids |
| T40.3 | Methadone |
| T40.4 | Synthetic opioids (fentanyl) |
| T40.5 | Cocaine |
| T43.6 | Psychostimulants (methamphetamine) |

---

## Datasets/geo/ - Geographic Reference Files

| File | Description |
|------|-------------|
| `us_counties_geojson.json` | US county boundaries for choropleth maps (~3,200 counties, 5-digit FIPS) |
| `zcta_county_rel_10.csv` | Census 2010 ZCTA-to-County crosswalk (used by county_panel.py for zip-to-county aggregation) |

---

## Datasets/census/ - Census & USAFacts

| File | Description |
|------|-------------|
| `USAFacts_health_data.csv` | Medicaid enrollment and population by county |
| `USAFacts_health_data (Populations).csv` | Population estimates |

---

## Datasets/ACSDT* and ACSST* - Census ACS 5-Year Estimates

American Community Survey 5-year estimates (2018 release). Each folder contains:

- `*-Data.csv` - Main data table
- `*-Column-Metadata.csv` - Column definitions
- `*-Table-Notes.txt` - Census Bureau notes

| Folder Pattern | Table | Content |
|----------------|-------|---------|
| ACSDT5Y2018.B01003* | B01003 | Total Population by zip |
| ACSDT5Y2018.B02001* | B02001 | Race & Ethnicity by zip |
| ACSDT5Y2018.B19013* | B19013 | Median Household Income by zip |
| ACSST5Y2018.S1701* | S1701 | Poverty Status by zip |
| ACSST5Y2018.S2704* | S2704 | Health Insurance Coverage by zip |

Used by `census/load_census.py` to enrich IQVIA zip-level data with demographics.
