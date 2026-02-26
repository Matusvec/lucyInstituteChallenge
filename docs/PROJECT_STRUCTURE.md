# Project Structure

Complete directory layout for the Lucy Institute Health Challenge.

---

## Root Directory

```
lucyInstituteChallenge/
|-- main.py                     # CLI entry point -- runs queries, maps, analysis
|-- requirements.txt            # Python dependencies
|-- README.md                   # Project overview and setup instructions
|-- .gitignore                  # Git ignore rules
|-- .env                        # Database credentials (gitignored)
|
|-- visualizations/             # Active map scripts (Plotly HTML maps)
|   |-- county_overdose_spread.py    # County overdose deaths per 100K
|   |-- fentanyl_spread.py           # Fentanyl/synthetic opioid county map
|   |-- illicit_overdose_spread.py   # Illicit overdose state-level map
|   |-- county_dashboard_map.py      # Multi-metric dashboard (4 layers)
|   |-- mme_spread_map.py            # MME distribution county map
|   +-- theme.py                     # Shared color scales and styling
|
|-- queries/                    # IQVIA PostgreSQL query modules
|   |-- medicaid_vs_general.py       # Q1-Q5: Medicaid vs Non-Medicaid
|   |-- geographic.py                # Zip and state-level queries
|   |-- extended.py                  # Q6-Q9: State x year, sales channel
|   |-- county_panel.py              # County-level panel (zip-to-county)
|   |-- mme_spread.py                # MME 5-number summary and data
|   +-- explore_payors.py            # Payor plan category discovery
|
|-- cdc/                        # CDC WONDER data loading and merging
|   |-- load_wonder.py               # State-level overdose (1999-2020)
|   |-- load_wonder_county.py        # County-level overdose (2008-2017)
|   |-- load_wonder_county_drugtype.py # County by drug type (fentanyl, etc.)
|   |-- load_wonder_drug_types.py    # State by drug type + illicit panel
|   |-- merge_iqvia_cdc.py           # IQVIA + CDC state-level merge
|   |-- merge_iqvia_cdc_county.py    # IQVIA + CDC county-level merge
|   +-- merge_iqvia_cdc_drugtype.py  # IQVIA + CDC drug-type merge
|
|-- census/                     # Census ACS data loading
|   |-- load_census.py               # Load ACS tables (population, income, etc.)
|   +-- merge_iqvia_census.py        # Merge IQVIA zip data with Census
|
|-- utils/                      # Database connection and helpers
|   |-- db_connect.py                # PostgreSQL connection config
|   +-- db_utils.py                  # Connection pool, CSV export, lookups
|
|-- tests/                      # Automated verification
|   +-- test_visualization_data.py   # Data formula checks for all maps
|
|-- archive/                    # Archived scripts (still runnable)
|   |-- visualizations/              # Non-map chart scripts (Matplotlib)
|   |   |-- heroinVsFentanyl.py           # Heroin vs fentanyl death trends
|   |   |-- divergence_plot.py            # Rx decline vs overdose rise
|   |   |-- Medicaid_Timeline.py          # Medicaid Rx vs enrollment timeline
|   |   |-- Medicaid_boxplot.py           # Overdose by Medicaid Rx group
|   |   |-- prescriptionsVsOverdose.py    # Binscatter: Rx vs overdose
|   |   |-- mme_vs_overdose_2012_2016.py  # MME vs overdose scatter
|   |   |-- mme_vs_deaths_scatterplot.py  # MME vs deaths by county
|   |   +-- (more chart scripts)
|   |-- analysis/                    # Statistical analysis scripts
|   |   |-- deep_analysis.py              # Q1-Q5 + CDC cross-analysis
|   |   |-- extended_analysis.py          # Q6/Q7 analysis
|   |   |-- bridge_analysis.py            # Integrated findings
|   |   |-- what_happened_2012.py         # 2012 inflection forensics
|   |   |-- analyze.py                    # Generic CSV analyzer
|   |   +-- check_2018.py                 # 2018 data truncation check
|   +-- scripts/                     # Legacy scripts
|       |-- python/                       # Early Python prototypes
|       +-- r/                            # R map scripts (optional)
|
|-- Datasets/                   # Raw data files
|   |-- cdc/                         # CDC WONDER overdose CSVs
|   |-- census/                      # USAFacts Medicaid enrollment
|   |-- geo/                         # GeoJSON + ZCTA-county crosswalk
|   |-- shapefiles/                  # US state boundary shapefiles
|   |-- IQVIA/                       # IQVIA reference files
|   |-- archive/                     # Legacy/unused data files
|   |-- ACSDT5Y2018.B01003*/         # Census: Total Population
|   |-- ACSDT5Y2018.B02001*/         # Census: Race & Ethnicity
|   |-- ACSDT5Y2018.B19013*/         # Census: Median Household Income
|   |-- ACSST5Y2018.S1701*/          # Census: Poverty Status
|   |-- ACSST5Y2018.S2704*/          # Census: Health Insurance Coverage
|   +-- DATA_CATALOG.md              # Data file descriptions
|
|-- output/                     # Generated outputs
|   |-- cdc/                         # CDC-related CSVs + HTML maps
|   |-- county/                      # County panel CSVs + dashboard map
|   |-- iqvia_core/                  # Q1-Q5 result CSVs
|   |-- extended/                    # Q6-Q9 result CSVs
|   |-- lookups/                     # Payor plan and Medicaid ID lookups
|   +-- plots/                       # Generated charts and PNGs
|
+-- docs/                      # Documentation
    |-- FINDINGS.md                  # Complete research findings
    |-- VISUALIZATION_GUIDE.md       # Map descriptions and usage
    |-- PROJECT_STRUCTURE.md         # This file
    |-- DATA_FLOW.md                 # Data pipeline documentation
    |-- DATA_GUIDE.md                # Dataset source descriptions
    |-- DATA_STRATEGY.md             # Database schema and query strategy
    |-- deliverables/                # Presentation materials
    +-- instructions/                # Challenge instructions and rubric
```

---

## Module Descriptions

### `main.py`

CLI orchestrator. Run `python main.py <mode>` where mode is one of:

| Mode | Description |
|------|-------------|
| `explore` | Discover Medicaid payor plan IDs |
| `medicaid` | Q1--Q5: Medicaid vs Non-Medicaid comparisons |
| `q3`, `q4`, `q5` | Individual query modules |
| `geo`, `geo-light` | Zip and state-level geographic data |
| `extended` | Q6--Q9: State x year, sales channel, etc. |
| `county` | County-level IQVIA panel (zip-to-county) |
| `census` | Load Census ACS tables |
| `merge` | Merge IQVIA + Census |
| `cdc` | Merge IQVIA + CDC overdose |
| `cdc-drug` | CDC drug-type panel + illicit spread |
| `map-illicit` | Illicit overdose state map |
| `map-county` | County overdose spread map |
| `map-fentanyl` | Fentanyl county spread map |
| `map-dashboard` | Multi-metric county dashboard |
| `map-mme` | MME spread map + 5-number summary |

### `visualizations/`

Active animated map scripts that produce the HTML map outputs used in
the presentation. Each script loads data, builds Plotly choropleth
frames, and writes an interactive HTML file.

### `queries/`

SQL query modules that connect to the IQVIA PostgreSQL database.
Each module handles connection pooling, chunked queries, caching
lookups, and CSV export via utilities in `utils/`.

### `cdc/`

Loaders for CDC WONDER Multiple Cause of Death data. Each loader
reads CSVs from `Datasets/cdc/`, cleans and filters them, and
provides DataFrames to the merge and visualization modules.

### `census/`

Loaders for Census ACS 5-year estimates. `load_census.py` reads
the five ACS table folders (population, race, income, poverty,
insurance) and combines them into a single zip-level DataFrame.

### `archive/`

Scripts that were used during development and are preserved for
reference. All paths have been updated so they remain runnable
via `python -m archive.visualizations.<script_name>`.
