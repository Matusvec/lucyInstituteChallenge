# Visualization Guide — What Each Map & Tab Does

**Presentation:** *Statistics vs. Stigma: How Opioid Prescriptions Relate to Overdose Deaths* (2.27.2026)

## Presentation Slide Mapping

| Slide | Visualization | Map/Chart |
|-------|---------------|-----------|
| 7 | Total Rx per 1K population | County Dashboard (Rx/1K tab) |
| 11 | Drug overdose deaths per 100K | County Overdose Spread Map |
| 12 | Fentanyl deaths per 100K | Fentanyl Spread Map |
| 13 | Total Rx v. Overdose Deaths | Binscatter (prescriptionsVsOverdose) |
| 14 | Medicaid v. Overdose Deaths | Boxplot (Medicaid_boxplot) |
| 15 | MME v. Overdose Deaths | Scatter (mme_vs_deaths_scatterplot, Binned_Scatter) |
| 21 | Medicaid % by county | County Dashboard (Medicaid % tab) |
| 22 | Avg MME by county | MME Spread Map |

---

## Animated Maps (HTML)

### 1. Illicit Overdose Spread Map
**File:** `output/cdc/illicit_overdose_spread_map.html`

**What it shows:** State-level death rate from **illicit-proxy** drug overdoses (heroin, synthetic opioids/fentanyl, cocaine, psychostimulants) per 100,000 population, 1999–2018.

**Data source:** CDC WONDER Multiple Cause of Death, drug-type breakout. Built by `python main.py cdc-drug` → `output/cdc/cdc_illicit_overdose_by_state_year.csv`.

**Note:** Deaths can list multiple drug types (e.g., heroin + fentanyl). Summing across categories may overcount; this is a **proxy** for illicit spread intensity.

---

### 2. County Overdose Spread Map
**File:** `output/cdc/county_overdose_spread_map.html`

**What it shows:** County-level **all drug overdose** death rate per 100,000 population, 2008–2017.

**Data source:** CDC WONDER `overdose_by_county_year_2008-2017.csv` (all drug-induced causes).

**Note:** Grey/suppressed = CDC suppresses counts &lt;10 for privacy.

---

### 3. Fentanyl Spread Map
**File:** `output/cdc/fentanyl_spread_map.html`

**What it shows:** County-level death rate from **fentanyl/synthetic opioids** (ICD-10 T40.4) per 100,000 population, 2008–2017.

**Data source:** CDC WONDER county × drug-type files (`overdose_by_county_drugtype_2008-2012.csv`, `_2013-2017.csv`), filtered to T40.4.

**Note:** Fentanyl was rare before ~2013; the map shows its geographic spread.

---

### 4. County Dashboard Map
**File:** `output/county/county_dashboard_map.html`

**What it shows:** County-level map with a **metric switcher** (left side). You can switch between four metrics:

| Tab / Option | What it shows |
|--------------|---------------|
| **Deaths/100K** | Overdose death rate per 100,000 population (CDC). Same concept as County Overdose Spread but in a multi-metric view. |
| **Rx/1K pop** | Opioid prescriptions per 1,000 population. From IQVIA `total_rx` ÷ population × 1000. |
| **Avg MME** | Average morphine milligram equivalent (MME) per prescription unit. From IQVIA county panel (qty-weighted). |
| **Medicaid %** | Share of opioid prescriptions paid by Medicaid. From IQVIA (medicaid_rx ÷ total_rx × 100). |

**Data source:** Merged panel from IQVIA county panel + CDC county overdose + CDC drug-type pivot. Cached at `output/county/iqvia_cdc_county_merged.csv`.

**Hover:** Shows all metrics for that county-year (deaths, population, Rx, MME, Medicaid %, etc.).

---

### 5. MME Spread Map
**File:** `output/plots/mme_spread_map.html`

**What it shows:** Geographic spread of **average MME per prescription unit** across IQVIA counties, 2008–2017. A choropleth map with year slider and play/pause.

**5-number summary** (printed when building):
- Min, Q1, Median, Q3, Max
- Range (max − min)

**Data source:** IQVIA county panel (`avg_mme_per_unit` = qty-weighted MME per unit). Loads from merged cache or `iqvia_county_year_panel.csv`.

**Run:** `python main.py map-mme` or `python -m visualizations.mme_spread_map`

---

## Data Accuracy Summary

| Visualization | Data | Accuracy |
|---------------|------|----------|
| Illicit Overdose | CDC drug-type, illicit categories summed | Proxy (possible overlap/double-count across drug types) |
| County Overdose | CDC all drug overdose by county | Direct CDC counts and rates |
| Fentanyl | CDC T40.4 only | Direct CDC counts and rates |
| Dashboard | IQVIA + CDC merge on (county_fips, year) | IQVIA from DB; CDC from CSVs; merge is outer so some counties have Rx-only or CDC-only |
| MME Spread | IQVIA county panel avg_mme_per_unit | Same as Dashboard MME metric; qty-weighted MME per unit |

---

## Regenerating Maps

```bash
.venv\Scripts\Activate.ps1
python main.py map-illicit
python main.py map-county
python main.py map-fentanyl
python main.py map-dashboard
python main.py map-mme
```

Dashboard uses cached merge; add `--force-merge` when running the module directly to re-merge after updating source data.

---

## Data Verification

Run comprehensive tests to verify visualization data matches source formulas:

```bash
python -m tests.test_visualization_data
```

**Verified:**
- **Illicit Overdose:** rate = deaths/pop × 100,000
- **County Overdose:** rate = deaths/pop × 100,000
- **Fentanyl:** rate = deaths/pop × 100,000 (T40.4 only)
- **Dashboard:** overdose_rate, rx_per_capita, pct_medicaid, avg_mme_per_unit formulas
