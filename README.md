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
├── main.py                     ← CLI orchestrator — runs all queries against the DB
│
├── queries/                    ← SQL query modules (hit the IQVIA PostgreSQL DB)
│   ├── explore_payors.py       │  Discover Medicaid plan IDs & payor categories
│   ├── medicaid_vs_general.py  │  Q1–Q5: core Medicaid vs Non-Medicaid comparisons
│   ├── geographic.py           │  Zip-code & state-level geographic queries
│   ├── extended.py             │  Q6–Q9: state×year, sales channel, monthly, 2018 sample
│   └── pill_mill.py            │  Prescriber concentration / pill mill analysis
│
├── analysis/                   ← Post-query statistical analysis (runs on CSV outputs)
│   ├── analyze.py              │  Generic CSV analyzer with auto-detect stat tests
│   ├── deep_analysis.py        │  Cross-analysis of Q1–Q5 + CDC (10 sections)
│   ├── extended_analysis.py    │  Analysis of Q6 (state×year) + Q7 (sales channel)
│   ├── bridge_analysis.py      │  Integrates Q6/Q7 with Q1–Q5 + CDC
│   ├── what_happened_2012.py   │  Forensic investigation of the 2012 inflection
│   └── check_2018.py           │  Proves 2018 data is truncated (~3.6 months)
│
├── visualizations/             ← Charts and figures
│   └── prescriptionsVsOverdose.py  │  Bar chart: Rx index vs OD death index (2012=100)
│
├── utils/                      ← Database connection & helper functions
│   ├── db_connect.py           │  DB connection config (host, credentials)
│   └── db_utils.py             │  Connection pooling, query runner, CSV export, lookup caches
│
├── cdc/                        ← CDC WONDER data loading & merging
│   ├── load_wonder.py          │  Parse CDC Multiple Cause of Death CSV
│   └── merge_iqvia_cdc.py      │  Merge IQVIA state data with CDC overdose rates
│
├── census/                     ← US Census ACS data loading & merging
│   ├── load_census.py          │  Parse Census ACS tables (population, income, etc.)
│   └── merge_iqvia_census.py   │  Merge IQVIA zip data with Census demographics
│
├── output/                     ← All generated CSV files (organized by source)
│   ├── lookups/                │  Payor plan tables, Medicaid plan IDs
│   ├── iqvia_core/             │  Q1–Q5 results (by year, state, drug, specialty)
│   ├── extended/               │  Q6–Q7 results (state×year, sales channel)
│   ├── cdc/                    │  CDC overdose data + merged IQVIA-CDC files
│   └── pillmill/               │  Prescriber concentration results
│
├── Datasets/                   ← Raw data files (not in git — too large)
│   ├── Multiple Cause of Death, 1999-2020.csv
│   ├── ACSDT5Y2018.B01003*/   │  Census: total population
│   ├── ACSDT5Y2018.B02001*/   │  Census: race/ethnicity
│   ├── ACSDT5Y2018.B19013*/   │  Census: median household income
│   ├── ACSST5Y2018.S1701*/    │  Census: poverty status
│   ├── ACSST5Y2018.S2704*/    │  Census: insurance coverage
│   └── IQVIA/                  │  IQVIA reference files
│
├── instructions/               ← Challenge instructions & rubric
│   ├── summary.md              │  Challenge overview
│   ├── IQVIA.md                │  IQVIA database documentation
│   ├── otherData.md            │  Supplementary data sources
│   └── rubric.md               │  Grading rubric
│
├── FINDINGS.md                 ← 📊 Full research findings (the deliverable)
├── DATA_STRATEGY.md            ← Database schema & query strategy documentation
├── leadingQuestion.md          ← Original research question
└── requirements.txt            ← Python dependencies
```

---

## Setup

### 1. Python Environment

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file (already gitignored) if needed for DB overrides. The default connection config is in `utils/db_connect.py`.

### 3. Datasets

The `Datasets/` folder is not in git (too large). Place it in the project root:
- **CDC WONDER:** `Datasets/Multiple Cause of Death, 1999-2020.csv`
- **Census ACS:** Five `ACSDT5Y*` / `ACSST5Y*` folders
- **IQVIA reference:** `Datasets/IQVIA/`

---

## Running Queries

All queries are run through `main.py`:

```bash
# Core Medicaid vs Non-Medicaid (Q1–Q5)
python main.py medicaid

# Individual queries
python main.py q3              # State-level comparison
python main.py q4              # Drug-level comparison
python main.py q5              # Specialty-level comparison

# Extended queries (Q6–Q9)
python main.py extended        # All extended queries
python main.py q6              # State × Year panel
python main.py q7              # Retail vs Mail Order

# Other modules
python main.py explore         # Discover payor plan categories
python main.py pillmill        # Prescriber concentration analysis
python main.py cdc             # Merge IQVIA + CDC overdose data
python main.py census          # Load Census ACS tables
python main.py merge           # Merge IQVIA zip + Census demographics
```

## Running Analysis

After queries produce CSVs in `output/`, run the analysis scripts:

```bash
python -m analysis.deep_analysis          # Cross-analysis of Q1–Q5 + CDC
python -m analysis.extended_analysis      # Q6/Q7 analysis
python -m analysis.bridge_analysis        # Integrated findings
python -m analysis.what_happened_2012     # 2012 inflection forensics
python -m analysis.check_2018             # Confirm 2018 truncation
```

---

## Key Dependencies

| Package | Purpose |
|---------|---------|
| pandas | Data manipulation |
| numpy | Numerical computation |
| scipy | Statistical tests |
| matplotlib | Visualization |
| psycopg2-binary | PostgreSQL connection |
| python-dotenv | Environment variable loading |

---

## Data Notes

- **IQVIA database:** 2.1B rows on AWS RDS PostgreSQL (read-only access)
- **Medicaid identification:** 71 payor plan IDs containing "medicaid" keyword
- **Opioid identification:** 3,959 product groups with `drug.usc LIKE '022%'`
- **2018 data is truncated:** Only ~3.6 months exist — use 1997–2017 for trends
- **IQVIA raw values:** `new_rx`, `total_rx`, `new_qty`, `total_qty` must be divided by 1000
