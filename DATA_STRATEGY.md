# 📊 Data Strategy: Medicaid vs Non-Medicaid Opioid Prescribing

## Research Question

> **Is there a significant difference between the way people on Medicaid are prescribed opioids versus the way the general (non-Medicaid) population is prescribed opioids in the United States?**

---

## 1. What We're Working With

### Database at a Glance

| Table | Rows | Purpose |
|---|---|---|
| **main** | **2.13 billion** | One row per prescription (1997–2018). Cannot download whole table. |
| **drug** | 4,067 | Drug details — active ingredient, dosage, MME, drug class (`usc`). |
| **payor_plan** | 15,088 | Payment plan names and variants. |
| **prescriber_limited** | 1,958,685 | Prescriber specialty, state, and **zip code**. |

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

---

## 2. How We Identify Medicaid

We ran an exploration query on `payor_plan` and found **71 plans** whose name contains the word "Medicaid":

| Category | Count | Examples |
|---|---|---|
| **State Medicaid programs** | 53 | `MEDICAID ALABAMA (AL)`, `MEDICAID CALIFORNIA (CA)`, … every US state + DC + PR |
| **Medicaid managed-care / HMO** | 17 | `PRIORITY HEALTH MEDICAID (MI)`, `SIMPLY HEALTHCARE MEDICAID (FL)`, `HIP MEDICAID (NY)`, etc. |
| **Generic / unspecified** | 1 | `MEDICAID UNSPECIFIED` |

**Classification rule used in all queries:**

```sql
CASE
    WHEN pp.payor_plan ILIKE '%medicaid%'
      OR pp.payor_plan_var ILIKE '%medicaid%'
    THEN 'Medicaid'
    ELSE 'Non-Medicaid'
END
```

The remaining ~15,017 plans fall into "Non-Medicaid" — these include commercial insurance, Medicare, employer plans, cash pay, workers' comp, discount cards, etc.  This gives us the **Medicaid vs everybody else** comparison the research question asks for.

---

## 3. Query Strategy (Built & Ready to Run)

Every query filters to **opioids only** (`usc LIKE '022%'`) and splits results by Medicaid vs Non-Medicaid.  Because the `main` table has 2.1 B rows, we **never** `SELECT *` — every query aggregates with `GROUP BY` so the database does the heavy lifting and returns a manageable result set.

### Module 1 — `queries/medicaid_vs_general.py` (5 queries)

| # | Query | What It Answers | Key Columns |
|---|---|---|---|
| 1 | **By Year** | How do total opioid Rx volumes compare Medicaid vs Non-Medicaid, year over year (1997–2018)? | `year`, `is_medicaid`, `total_rx`, `new_rx`, `total_qty`, `avg_mme` |
| 2 | **% Share by Year** | What *percentage* of all opioid Rx are Medicaid each year? Is it growing or shrinking? | `year`, `pct_medicaid`, `pct_non_medicaid` |
| 3 | **By State** | Which states have the biggest Medicaid vs Non-Medicaid opioid gap? | `state`, `is_medicaid`, `total_rx`, `avg_mme` |
| 4 | **By Drug (Active Ingredient)** | Do Medicaid patients get prescribed *different* opioids than non-Medicaid patients? (e.g. more generic vs brand-name, higher MME drugs?) | `active_ingredient`, `is_medicaid`, `total_rx`, `avg_mme` |
| 5 | **By Prescriber Specialty** | Which doctor specialties write the most Medicaid opioid Rx? Do pain clinics or primary care dominate? | `specialty`, `is_medicaid`, `total_rx`, `avg_mme` |

### Module 2 — `queries/geographic.py` (4 queries)

| # | Query | What It Answers | Key Columns |
|---|---|---|---|
| 1 | **Zip Code — Medicaid vs Non-Medicaid** | Per-zip totals for joining with a US shapefile → choropleth map | `zip_code`, `state`, `is_medicaid`, `total_rx`, `avg_mme`, `prescriber_count` |
| 2 | **Zip Code × Year** | Same but year-by-year — enables animated/time-lapse maps or pre/post policy comparisons | `zip_code`, `state`, `year`, `is_medicaid`, `total_rx` |
| 3 | **State Level** | Lighter-weight state-level summary — quick US map | `state`, `is_medicaid`, `total_rx`, `avg_mme` |
| 4 | **Medicaid % per Zip** | Single metric per zip: *"What % of opioid Rx in this zip were Medicaid?"* Best for a one-layer choropleth | `zip_code`, `state`, `pct_medicaid` |

---

## 4. Analysis Plan — What These Data Will Show

### 4A. National Trend (Time Series)

With Query 1 & 2 we can plot:
- **Total Medicaid opioid Rx vs Non-Medicaid opioid Rx** over 21 years.
- **Medicaid's share** of all opioid prescriptions over time.
- Whether the opioid epidemic "peaked" differently for Medicaid patients (e.g. did prescribing drop faster/slower after CDC guidelines in 2016?).

### 4B. Potency / Drug Type Comparison

With Query 4 we can answer:
- Are Medicaid patients prescribed **higher-MME (more potent)** opioids on average?
- Do Medicaid patients receive more **generic** opioids vs brand-name?
- Are certain high-risk drugs (e.g. fentanyl, oxycodone) disproportionately prescribed to one group?

### 4C. Prescriber Behavior

With Query 5 we can see:
- Do **pain management specialists** write a larger share of Medicaid opioid Rx?
- Are **primary care / family medicine** doctors the main prescribers for both groups, or does the specialty mix differ?
- Could certain specialty patterns suggest "pill mill" dynamics in one insurance category?

### 4D. Geographic Disparities (The Map Story)

With the geographic queries + a US zip-code shapefile:
- Build a **choropleth map** of Medicaid opioid Rx rates across the country.
- Overlay or side-by-side compare with Non-Medicaid rates.
- Identify **hot-spot zip codes** where Medicaid opioid prescribing is disproportionately high.
- Cross-reference with known opioid-crisis regions (Appalachia, rural South, etc.).

### 4E. State Policy Impact

With Query 3 (by state):
- Compare states that expanded Medicaid (ACA expansion) vs those that didn't.
- Look for changes in Medicaid opioid Rx around **2014** (ACA Medicaid expansion year).
- Identify states where Medicaid opioid prescribing is highest per capita.

---

## 5. GIS / Mapping Plan

The leading question specifically calls for geographic visualization using zip-code shapefiles.

### Data Flow

```
┌─────────────────────────────┐
│  geo_zip_medicaid_pct.csv   │  ← Query 4 output (pct_medicaid per zip)
│  zip_code | state | pct_med │
└──────────────┬──────────────┘
               │  JOIN on zip_code
               ▼
┌─────────────────────────────┐
│  US Zip-Code Shapefile      │  ← Census ZCTA shapefile (free download)
│  ZCTA5CE20 | geometry       │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  Choropleth Map             │  ← Python (geopandas + matplotlib/folium)
│  Color = % Medicaid opioid  │     or R (sf + ggplot2)
└─────────────────────────────┘
```

### Shapefile Source
- **US Census ZCTA (Zip Code Tabulation Areas):** https://www.census.gov/cgi-bin/geo/shapefiles/index.php → select "Zip Code Tabulation Areas"
- These provide polygon geometries for every US zip code.

---

## 6. Potential Supplementary Data (Enrichment)

To strengthen the health-equity angle, the zip-code data can be joined with:

| Source | What It Adds | Join Key |
|---|---|---|
| **US Census ACS** | Income, poverty rate, race/ethnicity, education, uninsured % by zip/ZCTA | zip / ZCTA |
| **CDC WONDER** | Overdose death rates by county/state | state / FIPS |
| **USDA Rural-Urban Codes** | Rural vs urban classification | FIPS / zip |
| **CMS Medicaid Enrollment** | Actual Medicaid enrollee counts by state/year | state + year |

This would let you normalise: *"Medicaid opioid Rx per 1,000 Medicaid enrollees"* instead of raw counts — a much fairer comparison.

---

## 7. Run Order & Time Estimates

| Step | Command | Expected Time | Output |
|---|---|---|---|
| ✅ Done | `python main.py explore` | ~10 sec | `output/payor_plan_summary.csv`, `medicaid_plan_ids.csv` |
| **Next** | `python main.py medicaid` | 10–30 min (5 heavy JOINs on 2.1B rows) | 5 CSVs in `output/` |
| Then | `python main.py geo-light` | 10–20 min | State-level + zip % CSVs |
| Optional | `python main.py geo` | 30–60+ min | Full zip × year breakdown |

> **Recommendation:** Run `python main.py medicaid` first. Those 5 CSVs give you enough to build all the charts and statistical tests for the research question. Run the geographic queries after, since they're mainly for the map visualisation.

---

## 8. Statistical Tests to Apply (Post-Query)

Once CSVs are in hand, use Python/R to run:

| Test | Purpose |
|---|---|
| **Two-sample t-test / Mann-Whitney U** | Is the average MME significantly different between Medicaid and Non-Medicaid? |
| **Chi-squared test** | Are certain drugs prescribed at significantly different rates between groups? |
| **Linear regression** | Does Medicaid status predict higher Rx volume after controlling for state/year? |
| **Difference-in-differences** | Did the Medicaid opioid gap change after specific policy interventions (2010 CDC, 2016 guidelines)? |
| **Spatial autocorrelation (Moran's I)** | Are high-Medicaid-opioid zip codes clustered geographically? |

---

## 9. File Structure

```
lucyInstituteChallenge/
├── main.py                          ← Run everything or pick a module
├── db_connect.py                    ← Connection config (already existed)
├── utils/
│   └── db_utils.py                  ← get_connection(), run_query(), export_to_csv()
├── queries/
│   ├── explore_payors.py            ← Step 1: discover Medicaid plan IDs
│   ├── medicaid_vs_general.py       ← Step 2: 5 comparison queries
│   └── geographic.py                ← Step 3: 4 zip/state-level queries
├── output/                          ← All CSVs land here
│   ├── payor_plan_summary.csv       ✅
│   ├── medicaid_plan_ids.csv        ✅
│   └── payor_plan_full.csv          ✅
├── DATA_STRATEGY.md                 ← This file
└── leadingQuestion.md               ← Original research question
```
