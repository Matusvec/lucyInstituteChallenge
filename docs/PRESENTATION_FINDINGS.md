# Presentation Findings

**Statistics vs. Stigma: How Opioid Prescriptions Relate to Overdose Deaths**  
*Comparing Lucy's IQVIA to CDC Wonder — 2.27.2026*

This document summarizes the findings from our presentation slides and maps them to the code and outputs in this repository.

---

## Research Question

> **What can Opioid Prescription Data tell us about Opioid Overdose Death?**

---

## Causality Disclaimer

Our analysis of the IQVIA dataset examined variable effects on overdose rates from CDC Wonder data to establish **mere correlation** between variables. There is **no implication of causality** within our findings. We have identified coincidence and correlation only.

---

## About the Datasets

### IQVIA — Opioid Prescription Data

- Nationwide database of opioid prescriptions filled from 1997–2018
- Each record: who prescribed, what drug, how much, when filled, how paid
- Includes doctor (specialty + location), drug (type and dosage), payment source (insurance type)
- **2.1B prescription records** (1997–2018): Monthly opioid prescription data at individual fill level
- **4 linked tables:** Prescriptions (main), drug details (including MME), payment types, prescriber info (specialty + location)
- Built for opioid trend analysis: prescribing behavior, dosage changes, time trends, payment patterns

### CDC Wonder — Overdose Death Metrics

- CDC's public database of death certificate data, including drug overdose deaths across the US
- **State-level overdose deaths** — Total drug overdose deaths and rates per 100,000 people by state and year (1999–2020)
- **County-level overdose deaths** — Same metrics at county level (2008–2017), used for county maps and dashboards
- **Deaths by drug type** — Overdose deaths by drug (heroin, fentanyl, prescription opioids, cocaine, meth) at state and county level
- **Purpose** — Compare overdose deaths with IQVIA prescription data to study links between prescribing and overdose trends over time and geography

---

## Slide-by-Slide Findings

### Slide 5: Initial Findings — Opioid Prescriptions v. Overdose Deaths

- **Total opioid prescriptions (2008–2017):** Decline after 2012 peak, encouraged by ACA implementation
- **Overdose deaths (CDC Wonder):** Fentanyl deaths climb past prescription opioid deaths over the same period

### Slide 7: Total Prescriptions per Capita — A Geological Lens

| | |
|---|---|
| **Overview** | Queried IQVIA by prescriber zip, mapped zips to counties (Census crosswalk), divided total Rx by county population (CDC) × 1,000 |
| **Methods** | Animated map showing prescriptions per 1,000 people in each county across the US (2008–2017) |
| **Findings** | Prescriptions peaked around 2012 and steadily declined. Even though some counties increased, total prescriptions decreased. |

**Code:** `visualizations/county_dashboard_map.py` (Rx/1K tab)  
**Output:** `output/county/county_dashboard_map.html`

### Slide 8: US Medicaid Rate vs Medicaid Opioid Prescription Rate

| | |
|---|---|
| **Overview** | Compared % of US population enrolled in Medicaid to average share of opioid prescriptions to people on Medicaid |
| **Methods** | T-test isolated by year |
| **Findings** | Medicaid prescription rate is **lower** than US Medicaid rate. Americans on Medicaid were not prescribed opioids at the same rate as the general population. 95% confidence interval concludes Medicaid prescriptions is lower than enrollment. |

### Slide 9: Average MME Findings — What is a "normal" dose?

| | |
|---|---|
| **Overview** | Morphine Milligram Equivalence (MME) = standardization of dose-strength in opioids. Calculated by product of Daily Dose (mg) and conversion factor. |
| **Methods** | Histogram of Average MME by county; bell curve |
| **Findings** | High frequency of doses ~10–15 MME. Common prescriptions: low doses of Oxycodone, Tramadol, Codeine (CDC). Median: 11.75 mg/dose. Range: 1.63–120 mg/dose. IQR: 9.70–13.77 mg/dose. |

**Code:** `visualizations/mme_spread_map.py`, `queries/mme_spread.py`  
**Output:** `output/plots/mme_spread_map.html`, console 5-number summary

### Slide 11: Drug Overdose Deaths per 100K Population

| | |
|---|---|
| **Overview** | Built from CDC WONDER death certificate data grouped by county and year; deaths and population used to calculate rates per 100K |
| **Methods** | Animated county-level map of drug overdose death rates per 100K population (2008–2017) |
| **Findings** | County overdose rate generally increasing over time, with larger increases in certain regions. |

**Code:** `visualizations/county_overdose_spread.py`  
**Output:** `output/cdc/county_overdose_spread_map.html`

### Slide 12: Fentanyl (Synthetic Opioids) Deaths per 100K

| | |
|---|---|
| **Overview** | CDC WONDER death certificates filtered to synthetic opioid deaths by county and year (2008–2017) |
| **Methods** | Animated county-level map of fentanyl/synthetic opioid overdose death rates per 100K |
| **Findings** | Fentanyl deaths nearly nonexistent before 2013, then exploded outward from the Northeast. Illicit fentanyl replaced prescription opioids as the dominant killer. |

**Code:** `visualizations/fentanyl_spread.py`  
**Output:** `output/cdc/fentanyl_spread_map.html`

### Slide 13: Total Rx v. Overdose Deaths

| | |
|---|---|
| **Overview** | Plotted Overdose Death Rate (averaged per bin) vs. Aggregated Prescription Rate |
| **Methods** | Binscatter; bin-level OLS trend |
| **Findings** | Evidence of positive linear relationship linking Total Prescription Rate and Total Overdose Death Rate. For every 1-pill increase in per capita pill volume (PCPV) at county level, associated 0.20 increase in opioid-related deaths (Griffith et al.). |

**Code:** `archive/visualizations/prescriptionsVsOverdose.py`  
**Output:** `output/plots/binscatter_rx_per_capita_vs_overdose.png`

### Slide 14: Medicaid v. Total Overdose Deaths

| | |
|---|---|
| **Overview** | Boxplot distributions of Overdose Rates for county observations with below vs. above avg Medicaid Rx rate |
| **Methods** | Mann-Whitney U test |
| **Findings** | **Failed to reject null hypothesis** — OD rate does not differ by below vs. above avg Medicaid Rx rate. (Reference: Cerdá et al. — ACA expansion states saw 6% reduction in total opioid overdose deaths.) |

**Code:** `archive/visualizations/Medicaid_boxplot.py`  
**Output:** `output/plots/boxplot_medicaid_group_overdose.png`

### Slide 15: Average MME v. Total Overdose Deaths

| | |
|---|---|
| **Overview** | Combined CDC overdose death data with IQVIA MME statistics by county code and year |
| **Methods** | Binned scatterplot; Pearson r |
| **Findings** | Evidence suggesting correlation between Average MME and Total Overdose Deaths. "The risk for opioid overdose increases markedly with dose among patients receiving long-term opioid therapy." (Von Korff et al.) |

**Code:** `archive/visualizations/mme_vs_deaths_scatterplot.py`, `archive/visualizations/Binned_Scatter.py`  
**Output:** `output/plots/mme_vs_deaths_by_county.png`, `output/plots/mme_vs_deaths_binned.png`

---

## Summary of Findings (Slide 16)

**Generally:**
- Found geographic ties to national prescription rates
- Established low prescribing pattern for people on Medicaid
- Displayed roughly normal distribution for Average MME

**With respect to overdose:**
- Found coincidence between geography and overdose death rate
- Substantiated correlation between strength of dosage and overdose death rate
- Demonstrated **no correlation** between Medicaid and overdose death rate

---

## Limitations (Slide 17)

- **Time series analysis** — Within the scope of our project
- **Linking data to causality** — No link to causality; only correlation found
- **Confounding variables** — Other variables may play into our data that we do not have access to
- **Data segmented to county** — Not personal level; weighted counties by population (each county considered equal)
- **Linear analysis** — Other relationships (quadratic, exponential) could show similar correlation

---

## Call to Action (Slide 18)

These findings provide insight into the relationship between strength of dosage and geographical location in correlation to opioid overdose death, aligning with existing research.

We advise:
1. **Longitudinal examination** of counties with these variables to examine the case for causal relationships that could prevent the next opioid crisis
2. **Continuing this research to the modern day** with data beyond 2017

---

## Works Cited (from slides)

- Cerdá, Magdalena, et al. "Association of Medicaid Expansion With Opioid Overdose Mortality in the United States." *JAMA Network Open*, 2020.
- CDC. "CDC Clinical Practice Guideline for Prescribing Opioids for Pain — United States, 2022."
- Griffith, Kevin N., et al. "Implications of County-Level Variation in U.S. Opioid Distribution." *Drug and Alcohol Dependence*, 2021.
- Von Korff, M., et al. "Long-Term Opioid Therapy Reconsidered." *Annals of Internal Medicine*, 2011.
