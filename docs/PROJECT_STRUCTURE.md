# Project Structure

Complete directory layout and file purposes for the Lucy Institute Health Challenge.

---

## Root Directory

```
lucyInstituteChallenge/
├── main.py                 # CLI entry point — run queries, maps, charts
├── requirements.txt        # Python dependencies
├── README.md               # Project overview
├── .gitignore
├── .env                    # Database credentials (gitignored)
│
├── scripts/
│   ├── python/             # Standalone Python scripts
│   │   ├── _test_chart.py  # Saves prescriptionsVsOverdose as PNG
│   │   └── seg_bar_graph_rough.py  # Stacked bar: prescriptions by year
│   └── r/                  # R maps (optional)
│
├── DATA_STRATEGY.md        # Database schema & query strategy
├── FINDINGS.md             # Research findings (main deliverable)
├── leadingQuestion.md      # Original research question
├── suggestions.md          # Project suggestions
│
├── instructions/           # Challenge instructions
├── docs/                   # Additional documentation
│   ├── deliverables/       # Story2Lucy.pdf, story_sources, Gameplan.jpg
│   └── misc/               # Miscellaneous notes
├── analysis/               # Statistical analysis scripts
├── cdc/                    # CDC WONDER data loading
├── census/                 # Census ACS loading
├── queries/                # SQL query modules
├── utils/                  # DB connection & helpers
├── visualizations/         # Maps, charts, figures
├── Datasets/               # Raw data files
├── output/                 # Generated outputs
├── Shape Files/            # US state boundaries (for R maps)
└── (misc: .zip, .xls, etc.)
```

---

## Python Modules

### `main.py`
CLI orchestrator. Run `python main.py <mode>` for:
- **explore** — Discover Medicaid payor IDs
- **medicaid** — Q1–Q5 Medicaid vs Non-Medicaid
- **geo** / **geo-light** — Zip/state geographic data
- **extended** — Q6–Q9 (state×year, sales channel, etc.)
- **county** — County-level IQVIA panel
- **census** — Load Census ACS
- **merge** — Merge IQVIA + Census
- **cdc** — Merge IQVIA + CDC overdose
- **cdc-drug** — CDC drug-type panel
- **map-illicit** | **map-county** | **map-fentanyl** | **map-dashboard** — Animated maps
- **pillmill** — Prescriber concentration

### `queries/`
SQL modules that hit the IQVIA PostgreSQL database:
- `explore_payors.py` — Payor plan discovery
- `medicaid_vs_general.py` — Q1–Q5
- `geographic.py` — Zip/state queries
- `extended.py` — Q6–Q9
- `county_panel.py` — County aggregation
- `pill_mill.py` — Prescriber concentration

### `cdc/`
CDC WONDER data loading and merging:
- `load_wonder.py` — State-level overdose
- `load_wonder_county.py` — County overdose
- `load_wonder_county_drugtype.py` — County by drug type
- `load_wonder_drug_types.py` — State by drug type
- `merge_iqvia_cdc.py` — IQVIA + CDC state
- `merge_iqvia_cdc_county.py` — IQVIA + CDC county
- `merge_iqvia_cdc_drugtype.py` — IQVIA + CDC drug-type

### `census/`
- `load_census.py` — Load Census ACS tables
- `merge_iqvia_census.py` — Merge IQVIA zip + Census
- `USAFacts_health_data.csv` — Medicaid enrollment (for Medicaid_Timeline)

### `analysis/`
Post-query analysis (runs on output CSVs):
- `analyze.py` — Generic CSV analyzer
- `deep_analysis.py` — Q1–Q5 + CDC cross-analysis
- `extended_analysis.py` — Q6/Q7 analysis
- `bridge_analysis.py` — Integrated findings
- `what_happened_2012.py` — 2012 inflection
- `check_2018.py` — 2018 truncation check

### `utils/`
- `db_connect.py` — DB connection config
- `db_utils.py` — Connection pool, export, lookups

### `visualizations/`
**Maps (Plotly → HTML):**
- `illicit_overdose_spread.py`
- `county_overdose_spread.py`
- `fentanyl_spread.py`
- `county_dashboard_map.py`

**Charts (Matplotlib):**
- `heroinVsFentanyl.py`
- `prescriptionsVsOverdose.py`
- `Medicaid_Timeline.py`
- `merge_mme_overdose_county.py`
- `mme_vs_deaths_scatterplot.py`
- `mme_vs_overdose_2012_2016.py`
- `Merge_ODD_MME_county_year.py`, `!Script_MME_ODD_Scatterplot.py`
- `MMEvsOverdosedeath (2012-2016)` — Simple scatter (no extension)

---

## Data Directories

### `Datasets/`
Raw data (CDC, Census, shapefiles, etc.):
- `cdc/` — CDC WONDER CSVs
- `geo/` — GeoJSON (counties)
- `shapefiles/` — US state boundaries
- `census/` — USAFacts copies
- `IQVIA/` — IQVIA reference files
- `archive/` — Zips, sample files
- `archive/from_root/` — Former root-level zips (cb_2018_*.zip, zip_to_county.zip, sample_-_superstore.xls)
- `DATA_CATALOG.md` — Data catalog

### `output/`
Generated outputs:
- `output/cdc/` — CDC CSVs + HTML maps
- `output/county/` — County panel + dashboard map
- `output/extended/` — Q6–Q9 results
- `output/iqvia_core/` — Q1–Q5 results
- `output/lookups/` — Payor plans, Medicaid IDs
- `output/pillmill/` — Prescriber concentration
- `output/plots/` — Generated charts/images

---

## `docs/`
- `VISUALIZATIONS.md` — How to run visualizations
- `DATA_FLOW.md` — Data dependencies
- `PROJECT_STRUCTURE.md` — This file

---

## `scripts/r/`
Optional R scripts:
- `mapView.Rmd` — Medicaid vs Non-Medicaid state map
- `State_Map.Rmd` — Same, alternate version
- `IQVIA_hookup.R` — DB connection from R
- `README.md` — R usage instructions
