# Lucy Institute Health Challenge

## Medicaid & Opioid Prescribing Analysis

> **Research Question:** Is there a significant difference between the way
> people on Medicaid are prescribed opioids versus the general population?

---

### Summary

We analyzed **2.1 billion prescription records** (IQVIA, 1997--2018) combined
with **CDC overdose mortality data** (1999--2018) and **Census demographic
data** to investigate whether Medicaid patients are over-prescribed opioids.

### Key Findings

1. **Medicaid patients are NOT over-prescribed.** They receive lower average
   MME (morphine milligram equivalents), fewer chronic prescriptions, and a
   narrower drug formulary than non-Medicaid patients.
2. **Medicaid has zero mail-order opioids.** Non-Medicaid patients can access
   90-day mail-order refills; Medicaid patients cannot.
3. **The prescription--overdose link broke after 2012.** Prescriptions fell
   ~25% nationally while overdose deaths rose ~62%, proving illicit opioids
   (heroin, fentanyl) now drive the crisis.
4. **Fentanyl spread geographically from the Northeast.** County-level mapping
   shows synthetic opioid deaths concentrated in Appalachia and the Eastern
   seaboard before spreading west.

Full findings: [docs/FINDINGS.md](docs/FINDINGS.md)

---

## Project Structure

```
lucyInstituteChallenge/
|
|-- main.py                  # CLI entry point for queries, maps, and analysis
|-- requirements.txt         # Python dependencies
|-- README.md                # This file
|
|-- visualizations/          # Active map scripts (Plotly animated HTML maps)
|-- queries/                 # IQVIA database query modules (PostgreSQL)
|-- cdc/                     # CDC WONDER data loading and merging
|-- census/                  # Census ACS data loading and merging
|-- utils/                   # Database connection and helper utilities
|-- tests/                   # Automated data verification tests
|
|-- archive/                 # Archived scripts kept for reference
|   |-- visualizations/      # Non-map chart scripts (Matplotlib)
|   |-- analysis/            # Statistical analysis scripts
|   +-- scripts/             # Legacy R and Python scripts
|
|-- Datasets/                # Raw data files (CDC, Census, geo, shapefiles)
|-- output/                  # Generated outputs (CSVs, HTML maps, PNGs)
+-- docs/                    # Documentation, deliverables, and instructions
```

Full layout: [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)

---

## Setup

### 1. Python Environment

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file (gitignored) with database credentials.
Default config is in `utils/db_connect.py`.

### 3. Datasets

Place raw data in `Datasets/`:

| Subfolder | Contents |
|-----------|----------|
| `cdc/` | CDC WONDER overdose CSVs (state, county, drug-type) |
| `census/` | USAFacts Medicaid enrollment data |
| `geo/` | County GeoJSON boundaries, ZCTA-to-county crosswalk |
| `IQVIA/` | IQVIA reference documentation |
| `ACSDT*` / `ACSST*` | Census ACS 5-year estimates (population, income, poverty, insurance, race) |

---

## Running the Project

All commands go through `main.py`:

### Animated Maps (no database required)

```bash
python main.py map-county       # County overdose deaths per 100K (2008-2017)
python main.py map-fentanyl     # Fentanyl/synthetic opioid spread by county
python main.py map-illicit      # State-level illicit overdose trends (1999-2018)
python main.py map-dashboard    # Multi-metric county dashboard (4 layers)
python main.py map-mme          # MME spread across counties + 5-number summary
```

Maps output to `output/cdc/` and `output/plots/` as interactive HTML files.

### Database Queries (requires IQVIA PostgreSQL access)

```bash
python main.py medicaid         # Q1-Q5: Medicaid vs Non-Medicaid comparisons
python main.py geo              # State and zip-level geographic analysis
python main.py extended         # Q6-Q9: State x year, sales channel, monthly
python main.py county           # County-level panel (zip-to-county aggregation)
```

### Data Merging

```bash
python main.py cdc              # Merge IQVIA state data with CDC overdose rates
python main.py cdc-drug         # CDC drug-type breakdown + illicit spread panel
python main.py census           # Load Census ACS tables
python main.py merge            # Merge IQVIA zip-level data with Census demographics
```

### Archived Charts (Matplotlib)

```bash
python -m archive.visualizations.heroinVsFentanyl
python -m archive.visualizations.divergence_plot
python -m archive.visualizations.mme_vs_overdose_2012_2016
python -m archive.visualizations.Medicaid_Timeline
```

---

## How the Code Maps to Findings

| Finding | Code | Output |
|---------|------|--------|
| Overdose deaths rising despite Rx decline | `archive/visualizations/divergence_plot.py` | `output/plots/divergence_plot.png` |
| County overdose death rates (2008--2017) | `visualizations/county_overdose_spread.py` | `output/cdc/county_overdose_spread_map.html` |
| Fentanyl geographic spread | `visualizations/fentanyl_spread.py` | `output/cdc/fentanyl_spread_map.html` |
| Heroin vs fentanyl crossover | `archive/visualizations/heroinVsFentanyl.py` | `output/plots/heroin_vs_fentanyl.png` |
| MME distribution across counties | `visualizations/mme_spread_map.py` | `output/plots/mme_spread_map.html` |
| Multi-metric county dashboard | `visualizations/county_dashboard_map.py` | `output/county/county_dashboard_map.html` |
| Medicaid vs Non-Medicaid Rx volume | `queries/medicaid_vs_general.py` | `output/iqvia_core/` CSVs |
| State-level Rx vs overdose correlation | `cdc/merge_iqvia_cdc.py` | `output/cdc/iqvia_cdc_merged_by_state.csv` |
| Medicaid Rx timeline vs enrollment | `archive/visualizations/Medicaid_Timeline.py` | `output/plots/medicaid_rx_vs_enrollment_timeline.png` |
| Illicit overdose state spread | `visualizations/illicit_overdose_spread.py` | `output/cdc/illicit_overdose_spread_map.html` |

---

## Testing

```bash
python -m pytest tests/ -v
```

Automated tests verify that visualization data matches source formulas:
overdose rates, Rx per capita, Medicaid percentages, and MME calculations.

---

## Key Dependencies

| Package | Purpose |
|---------|---------|
| `pandas` | Data manipulation and aggregation |
| `numpy` | Numerical computation |
| `scipy` | Statistical tests (t-tests, correlations) |
| `matplotlib` | Static charts and figures |
| `plotly` | Interactive animated choropleth maps |
| `psycopg2-binary` | PostgreSQL database connection |
| `python-dotenv` | Environment variable loading |

---

## Data Notes

- **IQVIA:** 2.1B prescription rows on AWS RDS PostgreSQL (read-only access)
- **Medicaid identification:** 71 payor plan IDs containing "medicaid"
- **Opioid filter:** 3,959 product groups where `drug.usc LIKE '022%'`
- **2018 data:** Truncated at ~3.6 months -- all trend analyses use 1997--2017
- **IQVIA scaling:** Raw columns (`new_rx`, `total_rx`, `new_qty`, `total_qty`) are divided by 1,000
- **CDC suppression:** County death counts < 10 are suppressed for privacy

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/FINDINGS.md](docs/FINDINGS.md) | Complete research findings and statistical results |
| [docs/VISUALIZATION_GUIDE.md](docs/VISUALIZATION_GUIDE.md) | What each map shows and how to regenerate |
| [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) | Full directory and file reference |
| [docs/DATA_FLOW.md](docs/DATA_FLOW.md) | Data pipeline and query-to-output mapping |
| [docs/DATA_GUIDE.md](docs/DATA_GUIDE.md) | Dataset descriptions and sources |
| [docs/DATA_STRATEGY.md](docs/DATA_STRATEGY.md) | Database schema and query optimization |
| [Datasets/DATA_CATALOG.md](Datasets/DATA_CATALOG.md) | Raw data file catalog |
