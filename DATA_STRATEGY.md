# 📊 Data Strategy: Medicaid vs Non-Medicaid Opioid Prescribing

## Research Question

> **Is there a significant difference between the way people on Medicaid are prescribed opioids versus the way the general (non-Medicaid) population is prescribed opioids in the United States?**

---

## 1. Database Schema

### Tables

| Table | Rows | Purpose |
|---|---|---|
| **main** | **2.13 billion** | One row per prescription (1997–2018). Cannot download whole table. |
| **drug** | 4,067 | Drug details — active ingredient, dosage, MME, drug class (`usc`). |
| **payor_plan** | 15,088 | Payment plan names and variants. |
| **prescriber_limited** | 1,958,685 | Prescriber specialty, state, and zip code. |

### Key Relationships (JOINs)

```
main.pg  ──────────────►  drug.pg            (what drug was prescribed)
main.payor_plan_id  ───►  payor_plan.payor_plan_id  (who paid)
main.prescriber_key ───►  prescriber_limited.prescriber_key  (who wrote it / where)
```

### Important Data Notes

- `new_rx`, `total_rx`, `new_qty`, `total_qty` must all be **divided by 1000** to get real values.
- All opioid drugs have `drug.usc LIKE '022%'`.
- MME (Morphine Milligram Equivalents) via `drug.mme_per_unit` standardises potency across drugs.
- **2018 data is truncated** (~3.6 months / Q1 only).

---

## 2. Medicaid Identification

**71 payor plans** whose name contains "Medicaid":

| Category | Count | Examples |
|---|---|---|
| State Medicaid programs | 53 | `MEDICAID ALABAMA (AL)`, `MEDICAID CALIFORNIA (CA)`, … |
| Medicaid managed-care / HMO | 17 | `PRIORITY HEALTH MEDICAID (MI)`, `SIMPLY HEALTHCARE MEDICAID (FL)` |
| Generic / unspecified | 1 | `MEDICAID UNSPECIFIED` |

**SQL classification:**
```sql
CASE
    WHEN pp.payor_plan ILIKE '%medicaid%'
      OR pp.payor_plan_var ILIKE '%medicaid%'
    THEN 'Medicaid'
    ELSE 'Non-Medicaid'
END
```

---

## 3. Query Modules

### Module 1 — `queries/medicaid_vs_general.py` (Q1–Q5)

| # | Query | What It Answers | Runtime |
|---|---|---|---|
| Q1 | **By Year** | Total Rx, MME by Medicaid status per year | ~60 min |
| Q2 | **% Share by Year** | Medicaid's % of all opioid Rx each year | derived |
| Q3 | **By State** | State-level Medicaid vs Non-Medicaid totals (all years) | ~136 min |
| Q4 | **By Drug** | Per-drug Medicaid vs Non-Medicaid MME and volume | ~98 min |
| Q5 | **By Specialty** | Per-specialty Medicaid vs Non-Medicaid volume | ~171 min |

### Module 2 — `queries/extended.py` (Q6–Q9)

| # | Query | What It Answers | Runtime |
|---|---|---|---|
| Q6 | **State × Year** | Panel data for DiD analysis, state trajectories | ~62 min |
| Q7 | **Sales Channel** | Retail vs Mail Order by Medicaid status | ~58 min |
| Q8 | **Monthly** | Seasonal patterns by Medicaid status | not run |
| Q9 | **2018 Sample** | Stratified 2M-row sample for logistic regression | not run |

### Module 3 — `queries/geographic.py`

| # | Query | What It Answers |
|---|---|---|
| 1 | **Zip Code** | Per-zip Medicaid vs Non-Medicaid totals |
| 2 | **Zip × Year** | Zip-level time series |
| 3 | **State Level** | Lighter-weight state summary |
| 4 | **Medicaid % per Zip** | Single metric per zip for choropleth maps |

### Module 4 — `queries/pill_mill.py`

5-layer prescriber concentration analysis to identify potential "pill mill" prescribers.

---

## 4. Analysis Modules

Located in `analysis/`:

| Script | Purpose | Input |
|---|---|---|
| `deep_analysis.py` | 10-section cross-analysis of Q1–Q5 + CDC | iqvia_core/ + cdc/ CSVs |
| `extended_analysis.py` | 6-section analysis of Q6 + Q7 (ACA DiD, trajectories, channels) | extended/ CSVs |
| `bridge_analysis.py` | 7-section integration of Q6/Q7 with Q1–Q5 + CDC | All CSVs |
| `what_happened_2012.py` | Forensic investigation of the 2012 inflection point | iqvia_core/ + extended/ + cdc/ |
| `check_2018.py` | Proves 2018 data is truncated (~3.6 months) | extended/ + iqvia_core/ |
| `analyze.py` | Generic CSV analyzer (auto-detect stat tests, plotting) | Any CSV |

---

## 5. External Data Sources

| Source | Purpose | Location |
|---|---|---|
| **CDC WONDER** | Overdose death rates by state × year (1999–2018) | `Datasets/Multiple Cause of Death, 1999-2020.csv` |
| **Census ACS B01003** | Total population by county | `Datasets/ACSDT5Y2018.B01003*/` |
| **Census ACS B02001** | Race/ethnicity by county | `Datasets/ACSDT5Y2018.B02001*/` |
| **Census ACS B19013** | Median household income by county | `Datasets/ACSDT5Y2018.B19013*/` |
| **Census ACS S1701** | Poverty status by county | `Datasets/ACSST5Y2018.S1701*/` |
| **Census ACS S2704** | Insurance coverage by county | `Datasets/ACSST5Y2018.S2704*/` |

---

## 6. Output Organization

```
output/
├── lookups/        → payor_plan_full.csv, payor_plan_summary.csv, medicaid_plan_ids.csv
├── iqvia_core/     → Q1–Q5 results (medicaid_vs_nonmedicaid_by_*.csv, medicaid_pct_by_year.csv)
├── extended/       → Q6–Q7 results (by_state_year.csv, by_sales_channel.csv)
├── cdc/            → CDC data + merged IQVIA-CDC files
└── pillmill/       → Prescriber concentration output
```

---

## 7. Query Optimization Strategy

Because the `main` table has 2.1B rows:

1. **No full table scans** — every query uses `WHERE pg IN (...)` + `GROUP BY`
2. **Literal IN tuples** — pre-fetched 71 Medicaid IDs and 3,959 opioid PGs, embedded as literal SQL
3. **Year-by-year execution** — queries loop 1997–2018, aggregating one year at a time
4. **Python-side enrichment** — drug metadata (MME, ingredient) mapped from cached lookups, not JOINs
5. **Single persistent connection** — connection pooling via `utils/db_utils.py`

---

## 8. Statistical Tests Applied

| Test | Purpose |
|---|---|
| Welch's t-test / Mann-Whitney U | Mean MME differences between groups |
| Paired t-test | Year-over-year paired comparisons |
| Cohen's d | Effect size measurement |
| Pearson r / Spearman ρ | Correlation (Rx trends vs overdose trends) |
| Linear regression | Time trend analysis |
| Difference-in-Differences | ACA expansion natural experiment |
| HHI | Drug market concentration |
| Gini coefficient | Prescribing inequality across specialties |

---

## 9. File Structure

```
lucyInstituteChallenge/
├── main.py                          ← CLI orchestrator
├── queries/                         ← DB query modules
│   ├── explore_payors.py
│   ├── medicaid_vs_general.py       ← Q1–Q5
│   ├── geographic.py
│   ├── extended.py                  ← Q6–Q9
│   └── pill_mill.py
├── analysis/                        ← Post-query analysis
│   ├── deep_analysis.py
│   ├── extended_analysis.py
│   ├── bridge_analysis.py
│   ├── what_happened_2012.py
│   ├── check_2018.py
│   └── analyze.py
├── visualizations/                  ← Charts & figures
│   └── prescriptionsVsOverdose.py
├── utils/                           ← DB connection & helpers
│   ├── db_connect.py
│   └── db_utils.py
├── cdc/                             ← CDC WONDER loading/merging
├── census/                          ← Census ACS loading/merging
├── output/                          ← Generated CSVs
├── Datasets/                        ← Raw data (not in git)
├── instructions/                    ← Challenge docs
├── FINDINGS.md                      ← Research findings
├── DATA_STRATEGY.md                 ← This file
└── requirements.txt
```
