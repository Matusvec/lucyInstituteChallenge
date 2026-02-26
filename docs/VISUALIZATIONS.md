# How to Run Visualizations

This guide covers every visualization, map, and chart in the codebase.

---

## Quick Reference

| Type | Command / Script | Output |
|------|------------------|--------|
| **Animated maps** | `python main.py map-*` | HTML files (open in browser) |
| **Charts** | `python main.py chart-*` or run scripts directly | PNG or matplotlib window |
| **R maps** | `rmarkdown::render("scripts/r/...")` | Interactive viewer |

---

## 1. Animated Maps (Plotly → HTML)

These produce interactive HTML files. Open them in any web browser and use the **Play** button or slider to animate through years.

### Map: Illicit Overdose Spread (State-Level)

**Command:**
```bash
python main.py map-illicit
```

**Output:** `output/cdc/illicit_overdose_spread_map.html`

**Data needed:** `output/cdc/cdc_illicit_overdose_by_state_year.csv`  
→ Run `python main.py cdc-drug` first if missing.

**Years:** 1999–2018

---

### Map: County Overdose Spread

**Command:**
```bash
python main.py map-county
```

**Output:** `output/cdc/county_overdose_spread_map.html`

**Data needed:** `Datasets/cdc/overdose_by_county_year_2008-2017.csv` (in repo)

**Years:** 2008–2017 | **No database required**

---

### Map: Fentanyl Spread (County-Level)

**Command:**
```bash
python main.py map-fentanyl
```

**Output:** `output/cdc/fentanyl_spread_map.html`

**Data needed:**  
- `Datasets/cdc/overdose_by_county_drugtype_2008-2012.csv`  
- `Datasets/cdc/overdose_by_county_drugtype_2013-2017.csv`  

**Years:** 2008–2017 | **No database required**

---

### Map: County Dashboard (Multi-Metric)

**Command:**
```bash
python main.py map-dashboard
```

**Output:** `output/county/county_dashboard_map.html`

**Data needed:**  
- `output/county/iqvia_county_year_panel.csv` → Run `python main.py county` first  
- CDC county CSVs (in `Datasets/cdc/`)

**Features:** Dropdown to switch between Overdose Rate, Rx per Capita, MME, Medicaid %

---

## 2. Charts (Matplotlib / Python)

### Heroin vs Fentanyl Bar Chart

**Command:**
```bash
python main.py chart-heroin-fentanyl
```

**Output:** Opens matplotlib window (no save by default)

**Data:** `output/cdc/heroin_vs_fentanyl_1999-2018.csv` | **No database required**

**Or run directly:**
```bash
python -m visualizations.heroinVsFentanyl
```

---

### Rx vs Overdose Indexed Chart

**Command:**
```bash
python scripts/python/_test_chart.py
```

**Output:** `output/plots/rx_vs_overdose_by_type.png` (or `output/cdc/` depending on `_test_chart` config)

**Data:** `output/iqvia_core/medicaid_pct_by_year.csv`, `output/cdc/cdc_overdose_by_state_year.csv`, `output/cdc/heroin_vs_fentanyl_1999-2018.csv`

**Or run directly:**
```bash
python -m visualizations.prescriptionsVsOverdose
```
(Shows window; use `python scripts/python/_test_chart.py` to save as PNG)

---

### Stacked Bar: Prescriptions by Year

**Script:** `scripts/python/seg_bar_graph_rough.py`

**Run:**
```bash
python scripts/python/seg_bar_graph_rough.py
```

**Data:** `output/iqvia_core/medicaid_vs_nonmedicaid_by_year.csv`

**Output:** Displays window; add `plt.savefig(...)` to save.

---

### Medicaid Timeline (Population Share vs Rx Share)

**Script:** `visualizations/Medicaid_Timeline.py`

**Run:**
```bash
python visualizations/Medicaid_Timeline.py
```

**Data:**  
- `census/USAFacts_health_data.csv`  
- `output/county/iqvia_county_year_panel.csv`  
- `Datasets/cdc/overdose_by_county_year_2008-2017.csv`

**Output:** `medicaid_rx_vs_enrollment_timeline.png` (in cwd) or configured path

---

### MME vs Overdose Deaths Scatter (by County)

**Scripts:**  
1. `visualizations/merge_mme_overdose_county.py` — merges data  
2. `visualizations/mme_vs_deaths_scatterplot.py` — creates scatter plot

**Run:**
```bash
python -m visualizations.merge_mme_overdose_county
python -m visualizations.mme_vs_deaths_scatterplot
```

**Data:** `output/county/iqvia_county_year_panel.csv`, CDC county overdose CSV

**Output:** `output/plots/mme_vs_deaths_by_county.png`

---

### MME vs Overdose (2012–2016) — Simple Scatter

**Script:** `visualizations/mme_vs_overdose_2012_2016.py`

**Run:**
```bash
python -m visualizations.mme_vs_overdose_2012_2016
```

**Data:** Hardcoded values (no external data)

**Output:** `output/plots/mme_vs_overdose_2012_2016.png`

---

## 3. R Visualizations (Optional)

**Location:** `scripts/r/`

**Requirements:** R with `pacman`, `DBI`, `RPostgres`, `sf`, `mapview`, `leaflet`, `leafsync`

### Medicaid vs Non-Medicaid State Maps

**Run from project root:**
```r
rmarkdown::render("scripts/r/mapView.Rmd")
# or
rmarkdown::render("scripts/r/State_Map.Rmd")
```

**Data:** `output/extended/medicaid_vs_nonmedicaid_by_state_year.csv`  
→ Run `python main.py extended` (or `q6`) first.

**Shapefiles:** `Datasets/shapefiles/cb_2018_us_state_20m/` or `Shape Files/`

---

## 4. Pre-Generated Images in `output/plots/`

These files exist in the repo. Their generators are listed above or in the scripts:

| Image | Generator |
|-------|-----------|
| `rx_vs_overdose_by_type.png` | `scripts/python/_test_chart.py` + `prescriptionsVsOverdose.py` |
| `medicaid_rx_vs_enrollment_timeline.png` | `Medicaid_Timeline.py` |
| `mme_vs_deaths_by_county.png` | `mme_vs_deaths_scatterplot.py` |
| `seg_bar_prescriptions_by_year.png` | `scripts/python/seg_bar_graph_rough.py` (if configured to save) |
| `mme_vs_overdose_2012_2016.png` | `mme_vs_overdose_2012_2016.py` |
| `Figure_1.png`, `divergenceGraph.png`, etc. | Various analysis/exploration scripts |

---

## 5. No Database Required

These run without a database connection (read from CSV only):

- `map-county`
- `map-fentanyl`
- `map-illicit` (if `cdc-drug` was run previously)
- `map-dashboard` (if `county` was run previously)
- `chart-heroin-fentanyl`

---

## 6. Dependencies

```bash
pip install -r requirements.txt
```

Key packages: `pandas`, `numpy`, `matplotlib`, `plotly`, `scipy`, `psycopg2-binary`, `python-dotenv`
