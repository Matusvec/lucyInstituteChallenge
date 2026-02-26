# Visualization Guide

Descriptions of each map and chart, what data they use, and how to regenerate them.

---

## Animated Maps (Plotly HTML)

### 1. County Overdose Spread Map

**File:** `output/cdc/county_overdose_spread_map.html`
**Run:** `python main.py map-county`

Shows county-level **all drug overdose death rate** per 100,000 population,
animated from 2008 to 2017. Grey counties have suppressed data (< 10 deaths).

**Data:** CDC WONDER `Datasets/cdc/overdose_by_county_year_2008-2017.csv`.

---

### 2. Fentanyl Spread Map

**File:** `output/cdc/fentanyl_spread_map.html`
**Run:** `python main.py map-fentanyl`

Shows county-level death rate from **fentanyl and synthetic opioids**
(ICD-10 T40.4) per 100,000 population, 2008--2017. Fentanyl was rare
before 2013; this map reveals its geographic spread from the Northeast.

**Data:** CDC WONDER county x drug-type files
(`Datasets/cdc/overdose_by_county_drugtype_2008-2012.csv`,
`Datasets/cdc/overdose_by_county_drugtype_2013-2017.csv`),
filtered to T40.4 (synthetic opioids).

---

### 3. Illicit Overdose Spread Map

**File:** `output/cdc/illicit_overdose_spread_map.html`
**Run:** `python main.py map-illicit`

Shows state-level death rate from **illicit-proxy drug overdoses** (heroin,
synthetic opioids/fentanyl, cocaine, psychostimulants) per 100,000
population, 1999--2018.

**Data:** CDC WONDER state-level drug-type breakout.
Built by `python main.py cdc-drug`.

**Note:** Deaths can list multiple drug types (e.g., heroin + fentanyl),
so this is a proxy for illicit spread intensity.

---

### 4. County Dashboard Map

**File:** `output/county/county_dashboard_map.html`
**Run:** `python main.py map-dashboard`

Multi-metric county map with a **metric switcher** offering four views:

| Metric | Description |
|--------|-------------|
| **Deaths/100K** | Overdose death rate per 100,000 population (CDC) |
| **Rx/1K pop** | Opioid prescriptions per 1,000 population (IQVIA) |
| **Avg MME** | Average morphine milligram equivalent per prescription unit |
| **Medicaid %** | Share of opioid prescriptions paid by Medicaid |

**Data:** Merged panel from IQVIA county panel + CDC county overdose.
Cached at `output/county/iqvia_cdc_county_merged.csv`.

---

### 5. MME Spread Map

**File:** `output/plots/mme_spread_map.html`
**Run:** `python main.py map-mme`

Shows the geographic spread of **average MME per prescription unit** across
IQVIA counties, 2008--2017. Includes a year slider and play/pause controls.
Running this also prints the 5-number summary (min, Q1, median, Q3, max).

**Data:** IQVIA county panel (`avg_mme_per_unit`).

---

## Archived Charts (Matplotlib)

Located in `archive/visualizations/`. Run with:

```bash
python -m archive.visualizations.<script_name>
```

| Chart | Script | What It Shows |
|-------|--------|---------------|
| Heroin vs Fentanyl Deaths | `heroinVsFentanyl.py` | National death trends showing fentanyl surpassing heroin |
| Rx vs Overdose Divergence | `divergence_plot.py` | Prescriptions declining while overdose deaths rise |
| Medicaid Timeline | `Medicaid_Timeline.py` | Medicaid Rx volume vs enrollment over time |
| Binscatter Rx vs Overdose | `prescriptionsVsOverdose.py` | County Rx per capita vs overdose rate |
| MME vs Overdose 2012--2016 | `mme_vs_overdose_2012_2016.py` | National average MME vs overdose deaths |

---

## Regenerating All Maps

```bash
python main.py map-county
python main.py map-fentanyl
python main.py map-illicit
python main.py map-dashboard
python main.py map-mme
```

---

## Data Verification

Run automated tests to verify visualization data matches source formulas:

```bash
python -m pytest tests/ -v
```

Verified calculations:
- Overdose rate = deaths / population x 100,000
- Rx per capita = total_rx / population x 1,000
- Medicaid % = medicaid_rx / total_rx x 100
- Avg MME = quantity-weighted MME per prescription unit

---

## Accuracy Summary

| Visualization | Data Source | Notes |
|---------------|------------|-------|
| County Overdose | CDC WONDER county-level | Direct CDC counts and rates |
| Fentanyl Spread | CDC WONDER T40.4 only | Direct CDC counts, filtered to synthetic opioids |
| Illicit Overdose | CDC drug-type, categories summed | Proxy (possible overlap across drug types) |
| Dashboard | IQVIA + CDC merged on (county_fips, year) | Outer merge; some counties Rx-only or CDC-only |
| MME Spread | IQVIA county panel | Quantity-weighted MME per prescription unit |
