# Lucy Institute Health Challenge — Medicaid & Opioid Prescribing Analysis

> **Research Question:** Is there a significant difference between the way people on Medicaid are prescribed opioids versus the general population?

## TL;DR

We analyzed **2.1 billion prescription records** (IQVIA, 1997–2018) combined with **CDC overdose mortality data** (1999–2018) and found that the "Medicaid over-prescribing" narrative is a myth. Medicaid patients receive lower doses, fewer chronic prescriptions, a narrower drug formulary, and zero access to mail-order opioids. Most critically, after 2012 the link between prescriptions and overdose deaths **broke completely** — prescriptions fell 25% while deaths rose 62% — proving that illicit opioids (heroin, fentanyl), not prescriptions, now drive the crisis.

**Full findings →** [FINDINGS.md](FINDINGS.md)

---

## Project Structure

```
lucyInstituteChallenge/
│
├── main.py                     ← CLI orchestrator — runs queries, maps, analysis
│
├── queries/                   ← SQL query modules (IQVIA PostgreSQL)
├── analysis/                  ← Post-query statistical analysis
├── visualizations/            ← Maps (Plotly) + charts (Matplotlib)
├── cdc/                       ← CDC WONDER data loading & merging
├── census/                    ← Census ACS loading & merging
├── utils/                     ← DB connection & helpers
│
├── scripts/r/                 ← Optional R maps (Medicaid vs Non-Medicaid)
├── Datasets/                  ← Raw data (CDC, Census, shapefiles)
├── output/                    ← Generated CSVs, maps, plots
├── docs/                      ← Documentation
├── instructions/              ← Challenge instructions
│
├── FINDINGS.md                ← Main research deliverable
├── DATA_STRATEGY.md           ← Database schema & query strategy
└── requirements.txt
```

**Full layout →** [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)

---

## Setup

### 1. Python Environment

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file (gitignored) for DB overrides. Default config is in `utils/db_connect.py`.

### 3. Datasets

Place `Datasets/` in the project root (not in git if large):

- **CDC WONDER:** `Datasets/cdc/` — overdose CSVs (county, state, drug type)
- **Census ACS:** `Datasets/census/` — USAFacts, ACS tables
- **Geo:** `Datasets/geo/us_counties_geojson.json` — county boundaries
- **IQVIA reference:** `Datasets/IQVIA/`

---

## Running Queries

All queries run through `main.py`:

```bash
# Core Medicaid vs Non-Medicaid (Q1–Q5)
python main.py medicaid

# Individual queries
python main.py q3              # State-level
python main.py q4              # Drug-level
python main.py q5              # Specialty-level

# Extended (Q6–Q9)
python main.py extended
python main.py q6              # State × Year panel
python main.py q7              # Retail vs Mail Order

# Other
python main.py explore         # Discover payor plan categories
python main.py pillmill        # Prescriber concentration
python main.py county         # County-level IQVIA panel
python main.py cdc            # Merge IQVIA + CDC overdose
python main.py cdc-drug       # CDC drug-type panel + illicit spread
python main.py census         # Load Census ACS
python main.py merge          # Merge IQVIA zip + Census
```

---

## Running Maps & Visualizations

### Animated Maps (Plotly → HTML)

```bash
python main.py map-illicit     # State illicit overdose (1999–2018)
python main.py map-county      # County overdose (2008–2017)
python main.py map-fentanyl   # County fentanyl spread
python main.py map-dashboard  # Multi-metric county map
```

Outputs: `output/cdc/*.html`, `output/county/*.html` — open in browser.

### Charts (Matplotlib)

```bash
python scripts/python/_test_chart.py     # Rx vs Overdose indexed chart → PNG
python scripts/python/seg_bar_graph_rough.py  # Stacked bar: prescriptions by year
python -m visualizations.heroinVsFentanyl
python -m visualizations.prescriptionsVsOverdose
python -m visualizations.Medicaid_Timeline
python -m visualizations.mme_vs_deaths_scatterplot
python -m visualizations.mme_vs_overdose_2012_2016
```

**Full guide →** [docs/VISUALIZATIONS.md](docs/VISUALIZATIONS.md)

---

## Running Analysis

After queries produce CSVs in `output/`:

```bash
python -m analysis.deep_analysis          # Q1–Q5 + CDC cross-analysis
python -m analysis.extended_analysis     # Q6/Q7 analysis
python -m analysis.bridge_analysis       # Integrated findings
python -m analysis.what_happened_2012    # 2012 inflection forensics
python -m analysis.check_2018            # 2018 truncation check
```

---

## No Database Required

These run from CSV only (no IQVIA connection):

- `map-county`, `map-fentanyl` (CDC data in repo)
- `map-illicit`, `map-dashboard` (if `cdc-drug` / `county` run previously)
- All chart scripts (if input CSVs exist)

---

## Key Dependencies

| Package | Purpose |
|---------|---------|
| pandas | Data manipulation |
| numpy | Numerical computation |
| scipy | Statistical tests |
| matplotlib | Charts |
| plotly | Interactive maps |
| psycopg2-binary | PostgreSQL |
| python-dotenv | Environment variables |

---

## Data Notes

- **IQVIA:** 2.1B rows on AWS RDS PostgreSQL (read-only)
- **Medicaid:** 71 payor plan IDs containing "medicaid"
- **Opioids:** 3,959 product groups with `drug.usc LIKE '022%'`
- **2018:** Truncated (~3.6 months) — use 1997–2017 for trends
- **IQVIA raw:** `new_rx`, `total_rx`, `new_qty`, `total_qty` ÷ 1000

---

## Documentation

| Doc | Description |
|-----|-------------|
| [docs/VISUALIZATIONS.md](docs/VISUALIZATIONS.md) | How to run every map and chart |
| [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) | Full directory layout |
| [docs/DATA_FLOW.md](docs/DATA_FLOW.md) | Data dependencies & query→output mapping |
| [DATA_STRATEGY.md](DATA_STRATEGY.md) | Database schema & query strategy |
| [Datasets/DATA_CATALOG.md](Datasets/DATA_CATALOG.md) | Data catalog |
