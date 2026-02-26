# Statistics vs. Stigma: How Opioid Prescriptions Relate to Overdose Deaths

**Comparing Lucy's IQVIA to CDC Wonder**  
*Lucy Institute Health Challenge — 2.27.2026*

---

## Research Question

> **What can Opioid Prescription Data tell us about Opioid Overdose Death?**

We combined **2.1 billion prescription records** (IQVIA, 1997–2018) with **CDC WONDER overdose mortality data** (1999–2020) to explore correlations between prescribing patterns and overdose deaths across geography and time.

---

## Causality Disclaimer

Our analysis examined variable effects on overdose rates from CDC Wonder data to establish **correlation** between variables. There is **no implication of causality** within our findings. We have identified coincidence and correlation only.

---

## Key Findings

### Prescription Patterns

- **Geographic ties to national prescription rates** — Opioid prescriptions peaked around 2012 and steadily declined. Even where some counties increased, total prescriptions decreased.
- **Low prescribing for Medicaid** — T-tests (95% CI) show Medicaid prescription rate is **lower** than US Medicaid enrollment rate. Americans on Medicaid were not prescribed opioids at the same rate as the general population.
- **Normal MME distribution** — Average Morphine Milligram Equivalence (MME) per prescription follows a bell curve centered around 10–15 MME. Median: 11.75 mg/dose; range: 1.63–120 mg/dose; IQR: 9.70–13.77 mg/dose.

### Overdose Death Patterns

- **Geography correlates with overdose** — County overdose death rates generally increased from 2008–2017, with geographic clustering.
- **Dosage strength correlates with overdose** — Evidence suggests a positive correlation between Average MME and total overdose deaths (Pearson r). Higher-dose counties tend to have higher overdose rates.
- **No correlation between Medicaid and overdose** — Mann-Whitney U test failed to reject the null hypothesis. Overdose rate does not differ significantly by below vs. above average Medicaid Rx rate.

### Fentanyl Spread

- **Fentanyl deaths were nearly nonexistent before 2013**, then exploded outward from the Northeast, visually showing how illicit fentanyl replaced prescription opioids as the dominant killer.

---

## Team

- **Otto Drake** — Freshman, ACMS  
- **Thomas Bui** — Freshman, Electrical Engineering  
- **Matus Vecera** — Freshman, Computer Science  
- **Mark Chambers** — Junior, Business Analytics, ACMS  

---

## Project Structure

```
lucyInstituteChallenge/
|
|-- main.py                  # CLI entry point for queries, maps, and analysis
|-- requirements.txt         # Python dependencies
|-- README.md                # This file
|
|-- visualizations/          # Animated map scripts (Plotly HTML)
|-- queries/                 # IQVIA database query modules (PostgreSQL)
|-- cdc/                     # CDC WONDER data loading and merging
|-- census/                  # Census ACS data loading
|-- utils/                   # Database connection and helpers
|-- tests/                   # Automated data verification
|
|-- archive/                 # Archived chart scripts (Matplotlib)
|-- Datasets/                # Raw data (CDC, Census, geo)
|-- output/                  # Generated CSVs, HTML maps, PNGs
+-- docs/                    # Documentation and deliverables
```

Full layout: [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)

---

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

Create a `.env` file with database credentials (see `utils/db_connect.py`). Place raw data in `Datasets/` (CDC CSVs, Census ACS, geo files).

---

## Running Maps & Visualizations

### Animated Maps (no database required for CDC-only maps)

```bash
python main.py map-county       # Drug overdose deaths per 100K by county (2008–2017)
python main.py map-fentanyl     # Fentanyl/synthetic opioid deaths per 100K by county
python main.py map-illicit      # Illicit overdose trends by state (1999–2018)
python main.py map-dashboard    # Multi-metric county dashboard (Rx, MME, Medicaid %, deaths)
python main.py map-mme          # MME spread by county + 5-number summary
```

### Maps from the Presentation

| Slide | Map | Command | Output |
|-------|-----|---------|--------|
| Total Rx per 1K population | Prescriptions per capita by county | `map-dashboard` (Rx/1K tab) | `output/county/county_dashboard_map.html` |
| Drug overdose deaths per 100K | Overdose death rate by county | `map-county` | `output/cdc/county_overdose_spread_map.html` |
| Fentanyl deaths per 100K | Fentanyl/synthetic opioid deaths by county | `map-fentanyl` | `output/cdc/fentanyl_spread_map.html` |
| Medicaid % | Medicaid share of prescriptions by county | `map-dashboard` (Medicaid % tab) | `output/county/county_dashboard_map.html` |
| Avg MME | MME distribution by county | `map-mme` | `output/plots/mme_spread_map.html` |

### Charts (archived)

```bash
python -m archive.visualizations.prescriptionsVsOverdose   # Total Rx v. Overdose (binscatter)
python -m archive.visualizations.Medicaid_boxplot          # Medicaid v. Overdose (boxplot)
python -m archive.visualizations.mme_vs_deaths_scatterplot # MME v. Overdose (scatter)
python -m archive.visualizations.heroinVsFentanyl          # Heroin vs fentanyl death trends
```

---

## How Code Maps to Presentation

| Slide / Finding | Code | Output |
|-----------------|------|--------|
| Total Rx per capita map | `visualizations/county_dashboard_map.py` (Rx/1K tab) | `output/county/county_dashboard_map.html` |
| Drug overdose deaths per 100K map | `visualizations/county_overdose_spread.py` | `output/cdc/county_overdose_spread_map.html` |
| Fentanyl deaths per 100K map | `visualizations/fentanyl_spread.py` | `output/cdc/fentanyl_spread_map.html` |
| Total Rx v. Overdose (binscatter) | `archive/visualizations/prescriptionsVsOverdose.py` | `output/plots/binscatter_rx_per_capita_vs_overdose.png` |
| Medicaid v. Overdose (boxplot) | `archive/visualizations/Medicaid_boxplot.py` | `output/plots/boxplot_medicaid_group_overdose.png` |
| MME v. Overdose (scatter) | `archive/visualizations/mme_vs_deaths_scatterplot.py` | `output/plots/mme_vs_deaths_by_county.png` |
| MME histogram / 5-number summary | `visualizations/mme_spread_map.py`, `queries/mme_spread.py` | `output/plots/mme_spread_map.html`, console output |
| Medicaid % map | `visualizations/county_dashboard_map.py` (Medicaid % tab) | `output/county/county_dashboard_map.html` |

---

## Limitations

- **Time series analysis** — Within the scope of our project, a time series analysis.
- **No causality** — There is no link to causality in our data; we have only found correlation.
- **Confounding variables** — Other variables may play into our data that we do not have access to.
- **County-level only** — Data segmented to county, not personal level; counties weighted by population.
- **Linear analysis** — Other relationships (quadratic, exponential) could show similar correlation.

---

## Call to Action

These findings provide insight into the relationship between strength of dosage and geographical location in correlation to opioid overdose death, aligning with existing research.

We advise **longitudinal examination** of counties with these variables to examine the case for causal relationships that could help prevent the next opioid crisis. We also advise **continuing this research to the modern day** with data beyond 2017.

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/PRESENTATION_FINDINGS.md](docs/PRESENTATION_FINDINGS.md) | Findings aligned with presentation slides |
| [docs/VISUALIZATION_GUIDE.md](docs/VISUALIZATION_GUIDE.md) | Map and chart descriptions |
| [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) | Full directory layout |
| [docs/DATA_FLOW.md](docs/DATA_FLOW.md) | Data pipeline |
| [docs/FINDINGS.md](docs/FINDINGS.md) | Detailed research findings |

---

## Testing

```bash
python -m pytest tests/ -v
```

Tests verify that visualization data matches source formulas.
