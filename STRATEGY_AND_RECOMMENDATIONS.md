# 🏆 Lucy Institute Health Challenge: Strategy & Dataset Recommendations

## Executive Summary

After analyzing all three datasets and the rubric criteria, **both IQVIA and Environmental Health are excellent choices** for a technically advanced team at Notre Dame with SQL experience. 

**Updated Recommendation: IQVIA (Opioid Prescription Data)** is actually your strongest option because:
1. The opioid epidemic IS a health equity crisis
2. Zipcode data lets you merge with Census demographics, CDC mortality, income data, etc.
3. 21 years of longitudinal data (1997-2018) = powerful trend analysis
4. Less likely other teams will tackle this (competitive advantage)
5. Shows technical sophistication to judges

---

## 📊 Dataset Comparison

### 1. Environmental Health Dataset (EJSCREEN 2023) ⭐ **RECOMMENDED**

| Attribute | Details |
|-----------|---------|
| **Size** | 86,081 rows × 126 columns |
| **Coverage** | All 56 US states & territories (Census tract level) |
| **Data Type** | GIS/Geographic, Demographic, Environmental, Health |
| **Complexity** | High - rich for analysis |
| **Accessibility** | Local CSV - easy to work with |

**Key Variable Categories:**
- **Demographics**: Population, % people of color, low income %, unemployment %, education levels, age groups
- **Environmental Hazards**: PM2.5, Ozone, Diesel particulate matter, Air toxics, Traffic proximity
- **Health Outcomes**: Cancer risk, Respiratory hazard index, Life expectancy
- **Infrastructure Risks**: Lead paint %, Superfund proximity, Hazardous waste, Underground storage tanks, Wastewater discharge
- **Environmental Justice Indices**: Pre-calculated EJ indices combining environmental + demographic factors

**Pros:**
- ✅ **Directly addresses health equity** (the core rubric requirement!)
- ✅ Pre-calculated Environmental Justice indices ready for analysis
- ✅ Massive geographic coverage enables powerful comparative analysis
- ✅ 126 variables = rich for correlation, regression, clustering analysis
- ✅ Data is LOCAL - no database connection issues
- ✅ Clear variables with provided codebook
- ✅ Easy to supplement with Census/CDC data
- ✅ Compelling visualizations possible (maps, choropleth, scatter plots)

**Cons:**
- ❌ Cross-sectional (one time point) - no temporal trends
- ❌ Large file requires careful handling

---

### 2. Malaria Dataset (Kenya Spatial Repellent Trial)

| Attribute | Details |
|-----------|---------|
| **Size** | ~13,000-28,000 rows across 8 files |
| **Coverage** | 58 clusters in Western Kenya |
| **Data Type** | Clinical trial, Longitudinal |
| **Complexity** | Medium |
| **Accessibility** | Local CSVs - easy to work with |

**Key Variables:**
- Treatment allocation (Placebo vs Spatial Repellent)
- Demographics (age, gender)
- Living conditions (wall type, roof type, eaves, windows)
- Infection outcomes (first-time vs overall, diagnosis results)
- Cluster information
- Precipitation data (in supplementary files)

**Pros:**
- ✅ True experimental data (randomized controlled trial)
- ✅ Longitudinal - can show changes over time
- ✅ Clear treatment vs control comparison
- ✅ Good for causal inference questions

**Cons:**
- ❌ **Less directly about "health equity"** - more about treatment efficacy
- ❌ Narrow geographic scope (one region in Kenya)
- ❌ Limited to malaria - narrower health topic
- ❌ Requires careful handling of multiple related files
- ❌ Some variables marked "Ignore" - less documentation clarity

---

### 3. IQVIA Dataset (National Prescription Opioids) ⭐ **TOP RECOMMENDATION FOR ADVANCED TEAMS**

| Attribute | Details |
|-----------|---------|
| **Size** | 2.1 BILLION+ rows in main table |
| **Coverage** | US National, 1997-2018 (21 years!) |
| **Data Type** | Pharmaceutical, Prescription, Geographic |
| **Complexity** | Very High (but you can handle it) |
| **Accessibility** | PostgreSQL server on ND WiFi ✅ |

**Key Variables:**
- Drug information (dosage, type, opioid classification - USC codes starting with 022)
- Prescriber details (specialty, state, **ZIPCODE**)
- Payment types (retail vs mail order, payor plans)
- Temporal data (monthly granularity, 1997-2018)
- MME (Morphine Milligram Equivalents) - standardized potency measure

**🔥 The Zipcode Advantage:**
With prescriber zipcodes, you can JOIN with:
- **Census Data**: Income, race, education, poverty rates by zipcode
- **CDC Wonder**: Overdose death rates by county/state
- **EJSCREEN**: Environmental justice indices
- **USDA**: Rural vs urban classification
- **BLS**: Unemployment rates

**Pros:**
- ✅ Opioid epidemic = **MAJOR health equity issue** (rural communities, low-income areas devastated)
- ✅ 21 years of data = powerful longitudinal analysis
- ✅ Zipcode enables rich demographic joins
- ✅ Can analyze prescriber specialty disparities
- ✅ Shows technical sophistication (SQL, big data handling)
- ✅ Likely **fewer teams will attempt this** = competitive advantage
- ✅ MME allows standardized dosage comparisons
- ✅ Payment type analysis (insurance equity)

**Cons:**
- ❌ Requires strategic SQL queries (don't SELECT * from main!)
- ❌ Need to aggregate intelligently (by year, state, zipcode)
- ❌ Will need supplemental Census/CDC data for demographics

---

## 🎯 Winning Strategy: IQVIA Opioid Dataset

### Recommended Research Question

> **"How do opioid prescribing patterns vary by socioeconomic status and geographic region, and did these disparities change during the opioid epidemic (1997-2018)?"**

**Alternative powerful questions:**

1. **"Are low-income communities prescribed higher MME (morphine-equivalent) dosages? A 21-year analysis of prescribing inequality."**

2. **"The Geography of Opioid Prescribing: How prescriber specialty and location predict prescription volume and potency."**

3. **"Did the opioid epidemic hit rural America harder? Analyzing prescribing rates by urban/rural classification over time."**

4. **"Insurance and Opioids: Do payment types correlate with prescribing patterns and potential over-prescribing?"**

---

## 🔧 Technical Strategy for IQVIA

### Smart SQL Query Approach

**DO NOT try to download the entire main table (2.1B rows)!**

Instead, aggregate strategically:

```sql
-- Example: Annual prescriptions by state and drug type
SELECT 
    p.state,
    d.usc,
    m.year,
    SUM(m.total_rx) / 1000.0 as total_prescriptions,
    SUM(m.total_qty) / 1000.0 as total_quantity,
    AVG(d.mme_per_unit) as avg_mme
FROM main m
JOIN prescriber_limited p ON m.prescriber_key = p.prescriber_key
JOIN drug d ON m.pg = d.pg
WHERE d.usc LIKE '022%'  -- Opioids only
GROUP BY p.state, d.usc, m.year
ORDER BY m.year, p.state;
```

```sql
-- Example: Prescriptions by zipcode (for Census joining)
SELECT 
    p.zip_code,
    p.state,
    m.year,
    COUNT(DISTINCT m.prescriber_key) as num_prescribers,
    SUM(m.total_rx) / 1000.0 as total_prescriptions,
    SUM(m.new_rx) / 1000.0 as new_prescriptions
FROM main m
JOIN prescriber_limited p ON m.prescriber_key = p.prescriber_key
JOIN drug d ON m.pg = d.pg
WHERE d.usc LIKE '022%'
GROUP BY p.zip_code, p.state, m.year;
```

```sql
-- Example: By prescriber specialty
SELECT 
    p.specialty,
    m.year,
    SUM(m.total_rx) / 1000.0 as total_prescriptions,
    AVG(d.mme_per_unit) as avg_potency
FROM main m
JOIN prescriber_limited p ON m.prescriber_key = p.prescriber_key
JOIN drug d ON m.pg = d.pg
WHERE d.usc LIKE '022%'
GROUP BY p.specialty, m.year
ORDER BY total_prescriptions DESC;
```

### Data Pipeline Plan

```
1. IQVIA Database (PostgreSQL)
   ├── Query aggregated opioid data by zipcode/year
   └── Export to CSV (~manageable size)
   
2. Census Data (data.census.gov)
   ├── Download demographics by zipcode/ZCTA
   └── Income, race, education, poverty rates
   
3. CDC Wonder (optional)
   ├── Overdose mortality rates by county/year
   └── Drug-related deaths
   
4. Python/R Analysis
   ├── Join datasets on zipcode/FIPS
   ├── Regression: demographics → prescribing rates
   ├── Time series: track inequality over time
   └── Visualizations
```

---

## 📋 Rubric-Aligned Execution Plan (IQVIA Focus)

### 1. Question Design and Dataset Utilization ✅
- **Health Equity Focus**: Opioid epidemic disproportionately affects low-income, rural, and certain racial communities
- **Novel Angle**: 21-year longitudinal analysis of prescribing inequality by socioeconomic factors
- **Datasets Used**: IQVIA (primary) + Census (demographics) + optional CDC (outcomes)

### 2. Methodology and Result Generation ✅
**Recommended Methods:**
```
- Strategic SQL aggregation (by zipcode, year, specialty)
- Join with Census demographics on zipcode/ZCTA
- Correlation analysis: income/education vs prescribing rates
- Time series analysis: how did disparities change 1997-2018?
- Regression: demographic predictors of high-MME prescribing
- Geographic visualization (state/regional heatmaps)
```

### 3. Discussion of Results and Conclusions ✅
- Frame in context of opioid epidemic timeline
- Discuss which communities were most affected
- Analyze role of prescriber specialty
- Connect to policy implications (prescription monitoring programs)
- Suggest interventions for high-risk areas

### 4. Evaluation of Error, Bias, and Statistics ✅
**Include:**
- Confidence intervals on trend estimates
- R² values for regression models
- p-values for group comparisons
- Discussion of limitations:
  - Prescriptions ≠ actual use (diversion exists)
  - Zipcode aggregation (ecological fallacy)
  - Missing demographics in IQVIA itself
  - Selection: only filled prescriptions captured

### 5. Presentation Organization and Quality ✅
**Suggested Structure (8 min):**
| Section | Time | Content |
|---------|------|---------|
| Hook | 0.5 min | Opioid epidemic impact, health equity framing |
| Data Overview | 1 min | IQVIA + Census joining strategy |
| Methods | 1.5 min | SQL aggregation, statistical approach |
| Results | 3 min | Key findings, maps, trends over time |
| Discussion | 1.5 min | Implications, limitations, policy |
| Conclusion | 0.5 min | Summary, call to action |

### 6. Code Organization and Quality ✅
**Recommended Structure:**
```
project/
├── data/
│   ├── raw/
│   │   ├── iqvia_aggregated.csv (from SQL queries)
│   │   └── census_demographics.csv
│   └── processed/
│       └── merged_analysis.csv
├── sql/
│   ├── opioid_by_zipcode.sql
│   ├── opioid_by_specialty.sql
│   └── temporal_trends.sql
├── notebooks/
│   └── analysis.ipynb
├── scripts/
│   ├── data_merge.py
│   ├── analysis.py
│   └── visualization.py
├── figures/
├── README.md
└── requirements.txt
```

---

## 🔥 High-Impact Visualization Ideas (IQVIA)

1. **Animated Choropleth Map**: Prescriptions per capita by state, animated 1997→2018
2. **Line Chart**: Opioid prescriptions over time, split by income quartile (from Census join)
3. **Heatmap**: Prescribing rates by specialty × year
4. **Scatter Plot**: Zipcode poverty rate vs prescriptions per capita
5. **Bar Chart**: Top 10 states by MME per capita (potency analysis)
6. **Dual-Axis Chart**: Prescriptions vs overdose deaths over time (if using CDC)
7. **Box Plot**: Prescription distribution by urban/rural classification

---

## 📊 Census Data You'll Want to Join

Download from data.census.gov for ZCTA (ZIP Code Tabulation Areas):

| Variable | Why It Matters |
|----------|---------------|
| Median household income | Income-based health equity |
| % below poverty line | Vulnerability indicator |
| % with bachelor's degree | Education disparities |
| % uninsured | Healthcare access |
| % white/Black/Hispanic | Racial equity analysis |
| % rural population | Urban vs rural disparities |
| Unemployment rate | Economic stress |

---

## ⚠️ Dataset Comparison (Updated View)

### IQVIA (Recommended for Your Team) ⭐
- **Best for**: Technical teams who want to stand out
- **Health Equity Angle**: Opioid epidemic disparities, geographic inequality, insurance equity
- **Competitive Edge**: Most teams will avoid this due to complexity - you won't

### Environmental Health (Strong Backup)
- **Best for**: Teams wanting simpler analysis path
- **Health Equity Angle**: Pre-built EJ indices make this obvious
- **Trade-off**: Easier = more teams likely to choose it

### Malaria (Niche Option)
- **Best for**: Teams interested in global health, experimental design
- **Health Equity Angle**: Living conditions → infection (weaker equity framing)
- **Trade-off**: Narrower scope, less familiar context for judges

---

## 📈 Supplemental Data Sources

| Source | Data Available | Join Key |
|--------|---------------|----------|
| **Census (data.census.gov)** | Demographics, income, education, race | Zipcode/ZCTA |
| **CDC Wonder** | Overdose deaths, mortality rates | County/State FIPS |
| **USDA ERS** | Rural-Urban Continuum Codes | County FIPS |
| **BLS** | Unemployment rates | County/State |
| **EJSCREEN** | Environmental justice indices | Census tract (can aggregate to county) |

---

## 🚀 Quick Start Action Items (IQVIA Path)

1. [ ] Connect to IQVIA PostgreSQL server
2. [ ] Run test query on `drug` table (small, safe)
3. [ ] Write aggregation query for opioids by zipcode/year
4. [ ] Download Census demographics by ZCTA
5. [ ] Join datasets in Python on zipcode
6. [ ] Run correlation/regression analysis
7. [ ] Create timeline visualizations
8. [ ] Build geographic heatmaps
9. [ ] Write up findings with limitations
10. [ ] Practice 8-minute presentation

---

## 🔗 Database Connection Info (IQVIA)

```
Host: lucy-iqvia-db.c61zpvuf4ib1.us-east-1.rds.amazonaws.com
Port: 5432 
Database: postgres
User: student_read_only_limited
Password: studentuseriqvialogin
```

**Python connection:**
```python
import psycopg2
import pandas as pd

conn = psycopg2.connect(
    host="lucy-iqvia-db.c61zpvuf4ib1.us-east-1.rds.amazonaws.com",
    port=5432,
    database="postgres",
    user="student_read_only_limited",
    password="studentuseriqvialogin"
)

# Always aggregate - never SELECT * FROM main!
query = """
SELECT p.state, m.year, SUM(m.total_rx)/1000.0 as total_rx
FROM main m
JOIN prescriber_limited p ON m.prescriber_key = p.prescriber_key
JOIN drug d ON m.pg = d.pg
WHERE d.usc LIKE '022%'
GROUP BY p.state, m.year
"""

df = pd.read_sql(query, conn)
```

---

## Final Recommendation

**Go with IQVIA.** For a technically advanced team at ND:
- You have the SQL skills to handle it
- Network access is reliable
- Zipcode joins unlock powerful health equity analysis
- 21-year longitudinal data is unmatched
- **You'll differentiate yourself from teams taking the "easy" path**
- The opioid epidemic is one of the most pressing health equity crises of our time

The combination of IQVIA prescribing data + Census demographics by zipcode = a winning formula.

Good luck! 🎯
