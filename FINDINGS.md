# The Medicaid Myth: Are Medicaid Patients Really Over-Prescribed Opioids?

## Research Findings — Lucy Institute Health Challenge

---

## Table of Contents

1. [Research Question](#research-question)
2. [Data Sources](#data-sources)
3. [Methodology](#methodology)
4. [Key Findings Summary](#key-findings-summary)
5. [Q1 — Opioid Prescriptions by Medicaid Status Over Time](#q1--opioid-prescriptions-by-medicaid-status-over-time)
6. [Q2 — Medicaid Share of Opioid Prescriptions Over Time](#q2--medicaid-share-of-opioid-prescriptions-over-time)
7. [Q3 — State-Level Medicaid vs Non-Medicaid Prescribing](#q3--state-level-medicaid-vs-non-medicaid-prescribing)
8. [Q4 — Drug-Level Medicaid vs Non-Medicaid Prescribing](#q4--drug-level-medicaid-vs-non-medicaid-prescribing)
9. [Q5 — Specialty-Level Medicaid vs Non-Medicaid Prescribing](#q5--specialty-level-medicaid-vs-non-medicaid-prescribing)
10. [CDC WONDER — Overdose Deaths vs Medicaid Prescribing](#cdc-wonder--overdose-deaths-vs-medicaid-prescribing)
11. [Deep Cross-Analysis — Unexpected Findings](#deep-cross-analysis--unexpected-findings)
12. [Conclusions](#conclusions)
13. [Limitations & Bias Evaluation](#limitations--bias-evaluation)

---

## Research Question

> **Is there a significant difference between the way people on Medicaid are prescribed opioids versus the general population?**

The prevailing narrative suggests that Medicaid patients are over-prescribed opioids, contributing disproportionately to the opioid crisis. This research tests that assumption using 2.1 billion prescription records from the IQVIA pharmaceutical database (1997–2018), supplemented with CDC WONDER overdose mortality data.

---

## Data Sources

| Source | Description | Size | Time Period |
|--------|-------------|------|-------------|
| **IQVIA Pharmaceutical Database** | National prescription-level data (prescriber, drug, quantity, payor) | 2.1 billion rows | 1997–2018 |
| **CDC WONDER** | Multiple Cause of Death — drug-induced causes (X40–X44, X60–X64, X85, Y10–Y14) | 1,020 rows (51 states × 20 years) | 1999–2018 |

- **IQVIA** is hosted on a shared PostgreSQL database on AWS RDS
- Medicaid payor plans identified by filtering `payor_plan` table for "medicaid" keyword → **71 unique Medicaid plan IDs**
- Opioid drugs identified by filtering `drug` table for known opioid active ingredients → **3,959 product groups**
- Morphine Milligram Equivalents (MME) calculated using standard CDC conversion factors mapped in Python

---

## Methodology

### Database Optimization
- Pre-fetched all 71 Medicaid plan IDs and 3,959 opioid product groups into literal SQL `IN (...)` tuples
- Eliminated expensive JOINs by mapping drug metadata (MME, ingredient) in Python from cached lookups
- All queries executed year-by-year (1997–2018) to manage memory and provide progress tracking
- Single persistent connection with connection pooling

### Statistical Methods Used
- **Welch's t-test** — comparison of means between Medicaid and Non-Medicaid groups
- **Paired t-test** — year-over-year paired comparisons
- **Mann-Whitney U test** — non-parametric alternative for non-normal distributions
- **Cohen's d** — effect size measurement
- **Pearson correlation (r)** — linear relationship between variables
- **Spearman rank correlation (ρ)** — monotonic relationships
- **Linear regression** — trend analysis over time
- **Herfindahl-Hirschman Index (HHI)** — market concentration
- **Gini coefficient** — inequality in prescribing concentration

---

## Key Findings Summary

| Finding | Result | Significance |
|---------|--------|-------------|
| Medicaid MME vs Non-Medicaid MME | Medicaid **lower** every year (2008–2018) | p = 0.000016, Cohen's d = −0.74 |
| Medicaid share of opioid Rx | Declining −0.54%/yr (9.3% → 3.6%) | p = 0.000146 |
| Quantity per Rx (across 20 drugs) | No significant difference | p = 0.87 |
| Per-drug MME differences | Not significant | p = 0.75, Cohen's d = 0.10 |
| Medicaid % vs overdose death rate | **Zero correlation** | r = 0.001, p = 0.99 |
| Prescribing ↔ overdose divergence | Pre-2012: r = +0.975; Post-2012: r = −0.656 | Structural break detected |
| Medicaid new Rx % vs Non-Medicaid | 90.2% vs 84.6% (less chronic prescribing) | Consistent across states |

**Bottom line: Medicaid patients are prescribed opioids at lower doses, in fewer drug categories, with more acute (new) rather than chronic prescriptions. Restricting Medicaid prescribing has not reduced overdose deaths.**

---

## Q1 — Opioid Prescriptions by Medicaid Status Over Time

**Query:** Total Rx count, new Rx count, total quantity, and average MME per year, split by Medicaid vs Non-Medicaid.

**Output:** 29,485 rows → aggregated to 33 year × group rows | Runtime: 59.6 minutes

### Results

| Year | Medicaid Rx | Medicaid Avg MME | Non-Medicaid Rx | Non-Medicaid Avg MME | MME Gap |
|------|------------|------------------|-----------------|---------------------|---------|
| 2008 | 18,583,366 | 13.48 | 227,572,350 | 14.46 | −0.98 |
| 2009 | 20,129,095 | 13.23 | 231,322,650 | 14.50 | −1.28 |
| 2010 | 24,023,363 | 13.05 | 234,363,814 | 14.75 | −1.70 |
| 2011 | 22,875,956 | 12.71 | 236,307,005 | 14.10 | −1.39 |
| 2012 | 16,931,903 | 12.47 | 244,685,098 | 13.55 | −1.08 |
| 2013 | 13,761,303 | 12.50 | 239,137,138 | 13.35 | −0.85 |
| 2014 | 13,525,447 | 12.40 | 231,894,089 | 13.35 | −0.95 |
| 2015 | 11,271,444 | 12.63 | 217,247,540 | 13.47 | −0.84 |
| 2016 | 9,563,449 | 12.68 | 207,287,492 | 13.33 | −0.65 |
| 2017 | 7,805,454 | 12.57 | 189,011,464 | 13.00 | −0.43 |
| 2018 | 2,146,930 | 12.45 | 56,949,863 | 12.77 | −0.32 |

### Statistical Analysis

| Test | Statistic | p-value | Interpretation |
|------|-----------|---------|----------------|
| Paired t-test (MME) | t = −6.33 | **p = 0.000016** | Medicaid MME significantly lower |
| Cohen's d | −0.74 | — | Medium-to-large effect size |
| Mann-Whitney U | U = 0.0 | **p = 0.000098** | Non-parametric confirms result |
| Linear trend (Med MME) | slope = −0.060/yr | p = 0.095 | Slight downward trend |
| Linear trend (NonMed MME) | slope = −0.241/yr | p = 0.0002 | Strong downward trend |

**Interpretation:** Medicaid average MME was lower than Non-Medicaid in **every single year** from 2008–2018. The gap narrowed over time as both groups reduced prescribing intensity, but Medicaid was consistently prescribed lower-potency opioids. This directly contradicts the "Medicaid over-prescribing" narrative.

---

## Q2 — Medicaid Share of Opioid Prescriptions Over Time

**Query:** Medicaid's percentage share of total opioid prescriptions by year.

**Output:** 22 rows | Runtime: instant (derived from Q1)

### Results

| Year | Medicaid Rx | Total Rx | Medicaid % |
|------|------------|----------|-----------|
| 2008 | 18,583,366 | 246,155,715 | 7.55% |
| 2009 | 20,129,095 | 251,451,746 | 8.01% |
| 2010 | 24,023,363 | 258,387,176 | **9.30%** (peak) |
| 2011 | 22,875,956 | 259,182,961 | 8.83% |
| 2012 | 16,931,903 | 261,617,001 | 6.47% |
| 2013 | 13,761,303 | 252,898,441 | 5.44% |
| 2014 | 13,525,447 | 245,419,537 | 5.51% |
| 2015 | 11,271,444 | 228,518,984 | 4.93% |
| 2016 | 9,563,449 | 216,850,941 | 4.41% |
| 2017 | 7,805,454 | 196,816,918 | 3.97% |
| 2018 | 2,146,930 | 59,096,793 | **3.63%** (lowest) |

### Statistical Analysis

| Test | Statistic | p-value |
|------|-----------|---------|
| Linear trend | slope = **−0.54%/yr** | **p = 0.000146** |

**Interpretation:** Medicaid's share of opioid prescriptions has been in steep, statistically significant decline — dropping from a peak of 9.3% (2010) to 3.6% (2018). This represents a **61% reduction** in Medicaid's proportional contribution to opioid prescribing. Note: Medicaid enrollment actually *increased* during this period (especially post-ACA 2014), making the per-enrollee decline even steeper.

---

## Q3 — State-Level Medicaid vs Non-Medicaid Prescribing

**Query:** Total Rx, new Rx, and total quantity by state, split by Medicaid vs Non-Medicaid (all years aggregated). Uses prescriber table JOIN for state mapping.

**Output:** 115 rows (58 states/territories × 2 groups) | Runtime: 135.5 minutes

### Key State Metrics

| Metric | Medicaid | Non-Medicaid |
|--------|----------|-------------|
| New Rx as % of Total (national avg) | **90.2%** | 84.6% |
| Avg Quantity per Rx | 61.7 | 59.5 |

**Interpretation:** Medicaid patients have a **higher new Rx ratio** (90.2% vs 84.6%), meaning their opioid prescriptions are more likely to be first-time/acute prescriptions rather than chronic refills. This is the opposite of what would be expected if Medicaid patients were being over-prescribed for chronic use.

### Top 10 States by Medicaid Opioid Volume Share

| State | Medicaid % of Opioid Rx |
|-------|------------------------|
| Vermont | 11.47% |
| Wisconsin | 9.87% |
| Maine | 9.59% |
| Connecticut | 8.94% |
| Delaware | 7.66% |
| Colorado | 7.35% |
| West Virginia | 7.26% |
| Tennessee | 6.43% |
| North Carolina | 6.53% |
| Alaska | 6.26% |

### States Where Medicaid Has Most Acute Prescribing (Highest New Rx %)

| State | Medicaid New Rx % | Non-Medicaid New Rx % | Difference |
|-------|-------------------|----------------------|-----------|
| OK | 94.4% | 86.7% | +7.6 |
| AK | 94.1% | 90.8% | +3.3 |
| MD | 94.0% | 90.3% | +3.7 |
| CO | 94.0% | 86.3% | +7.7 |
| NH | 94.0% | 89.6% | +4.4 |

### States Where Medicaid Has Most Chronic Prescribing (Lowest New Rx %)

| State | Medicaid New Rx % | Non-Medicaid New Rx % | Difference |
|-------|-------------------|----------------------|-----------|
| CA | 84.0% | 79.0% | +5.0 |
| WV | 85.3% | 80.7% | +4.6 |
| AL | 86.2% | 81.0% | +5.2 |
| UT | 86.3% | 84.5% | +1.8 |
| KY | 86.5% | 81.7% | +4.9 |

**Key insight:** Even in the states with the *most* chronic Medicaid prescribing, Medicaid still has a higher new Rx % than Non-Medicaid — the difference is consistent across all states.

---

## Q4 — Drug-Level Medicaid vs Non-Medicaid Prescribing

**Query:** Total Rx, total quantity, and average MME by active ingredient, split by Medicaid vs Non-Medicaid (all years aggregated).

**Output:** 40 rows (20 drugs × 2 groups) | Runtime: 97.5 minutes

### Top 10 Drugs by Rx Volume

| Drug | Medicaid Rx | Medicaid % | Med MME | NonMed MME |
|------|------------|-----------|---------|-----------|
| Hydrocodone | 73,314,288 | 3.5% | 8.48 | 7.52 |
| Oxycodone | 37,169,052 | 4.5% | 23.82 | 22.72 |
| Tramadol | 21,089,503 | 4.0% | 11.73 | 9.54 |
| Codeine | 13,254,898 | 3.3% | 4.19 | 4.50 |
| Morphine | 5,024,969 | 4.4% | **49.73** | 33.77 |
| Propoxyphene | 2,939,493 | 0.9% | 19.52 | 17.80 |
| Methadone | 2,290,631 | 4.2% | 29.79 | 39.53 |
| Fentanyl | 2,260,891 | 2.7% | **246.38** | 195.71 |
| Hydromorphone | 1,689,981 | 4.4% | 26.15 | 33.97 |
| Oxymorphone | 570,769 | 5.3% | 42.84 | 39.01 |

### Statistical Analysis

| Test | Statistic | p-value | Interpretation |
|------|-----------|---------|----------------|
| Welch's t-test (MME) | t = 0.324 | **p = 0.75** | ❌ NOT significant |
| Cohen's d | 0.10 | — | Negligible effect size |
| Raw mean MME diff | +4.88 | — | Higher for Medicaid on average |
| Volume-weighted MME diff | +1.67 | — | Minimal when weighted by Rx volume |

**Interpretation:** On a per-drug basis, the MME differences between Medicaid and Non-Medicaid are **not statistically significant**. Medicaid patients prescribed the *same drug* receive a similar dose. The overall lower MME for Medicaid (from Q1) is driven by **drug mix** — Medicaid patients are prescribed more hydrocodone (low MME) and less fentanyl/methadone (high MME) — not by lower doses of individual drugs.

### Drug Portfolio Differences

Drugs **over-represented** in Medicaid prescribing:
- **Oxymorphone**: 1.53× over-representation
- **Oxycodone**: 1.30× over-representation
- **Hydromorphone**: 1.27× over-representation

Drugs **under-represented** in Medicaid prescribing:
- **Propoxyphene**: 0.24× (Medicaid share is ¼ of expected)
- **Dextropropoxyphene**: 0.21×
- **Pentazocine**: 0.28×
- **Butorphanol**: 0.26×
- **Fentanyl**: 0.74×

**Market Concentration (HHI):**
- Medicaid HHI: **2,879** (more concentrated)
- Non-Medicaid HHI: **2,714**
- Top 3 drugs share — Medicaid: **81.9%** vs Non-Medicaid: **75.4%**

This suggests **formulary restrictions** limit the range of drugs available to Medicaid patients, concentrating their prescriptions into fewer drug categories.

---

## Q5 — Specialty-Level Medicaid vs Non-Medicaid Prescribing

**Query:** Total Rx by prescriber specialty, split by Medicaid vs Non-Medicaid.

**Output:** 860 rows (441 specialties × 2 groups) | Runtime: 170.7 minutes

### Top Prescribing Specialties (Non-Medicaid)

| Specialty | Non-Medicaid Rx | Rank |
|-----------|----------------|------|
| 01FM (Family Medicine) | 747,291,110 | 1 |
| 01IM (Internal Medicine) | 584,736,160 | 2 |
| 04DGP (Dentist-General) | 303,509,441 | 3 |
| 01ORS (Orthopedic Surgery) | 281,230,577 | 4 |
| 02FM (Family Medicine-2) | 212,629,068 | 5 |

### Specialties with Highest Medicaid Opioid Share

| Specialty | Medicaid % | Total Rx |
|-----------|-----------|----------|
| 01PHO (Pediatric Hematology/Oncology) | 17.6% | 916,561 |
| 01PAN (Pediatric Anesthesiology) | 12.2% | 107,611 |
| 01UP (Urology-Pediatric) | 12.1% | 687,145 |
| 01PDS (Pediatric Surgery) | 11.2% | 1,008,452 |
| 01PE (Pediatrics) | 10.8% | 246,564 |
| 02OBG (OB/GYN) | 9.4% | 7,964,029 |

### Specialties with Lowest Medicaid Opioid Share

| Specialty | Medicaid % | Total Rx |
|-----------|-----------|----------|
| 05VET (Veterinary) | 0.5% | 6,028,160 |
| 01REN (Renal/Nephrology) | 0.8% | 1,376,705 |
| 01D (Dermatology) | 1.0% | 6,856,668 |
| 01OSS (Orthopedic Surgery-Sports) | 1.1% | 14,700,139 |
| 01PS (Plastic Surgery) | 1.4% | 30,880,753 |

### Prescribing Concentration

| Metric | Medicaid | Non-Medicaid |
|--------|----------|-------------|
| Gini coefficient | **0.947** | 0.944 |
| Top 5 specialties share | **49.9%** | 48.6% |

**Interpretation:** Pediatric specialties and OB/GYN have the highest Medicaid opioid share, which is expected — children and pregnant women are disproportionately covered by Medicaid. Elective/cosmetic specialties (dermatology, plastic surgery, sports medicine) have the lowest Medicaid share. This pattern reflects **the demographics of who Medicaid covers**, not prescribing behavior.

---

## CDC WONDER — Overdose Deaths vs Medicaid Prescribing

**Data:** Drug-induced deaths (ICD-10 codes X40–X44, X60–X64, X85, Y10–Y14) grouped by state and year, 1999–2018.

**Merged dataset:** 51 states with IQVIA state-level data, CDC overdose rates, and ACA Medicaid expansion flags.

### Core Finding: Zero Correlation

| Correlation | ρ | p-value | Interpretation |
|-------------|---|---------|----------------|
| Medicaid % of Rx ↔ Overdose Rate | **+0.001** | **p = 0.99** | ❌ No relationship whatsoever |
| Medicaid qty/Rx ↔ Overdose Rate | −0.180 | p = 0.21 | ❌ Not significant |
| Non-Medicaid qty/Rx ↔ Overdose Rate | +0.182 | p = 0.20 | ❌ Not significant |
| Qty ratio (Med/NonMed) ↔ Overdose Rate | **−0.335** | **p = 0.016** | ✅ Significant — see below |

**The quantity ratio finding:** States where Medicaid patients get *relatively smaller* fills compared to Non-Medicaid have **higher** overdose rates. This suggests that **under-treatment** of Medicaid patients (restricting their access) may paradoxically be associated with worse outcomes.

### ACA Medicaid Expansion and Overdose Rates

| Group | Avg Overdose Rate (per 100K) | n |
|-------|------------------------------|---|
| ACA Expansion States | **18.7** | 28 |
| Non-Expansion States | **15.0** | 23 |
| **Welch's t-test** | **p = 0.01** | ✅ Significant |

**Interpretation:** States that expanded Medicaid under the ACA have significantly *higher* overdose rates. However, this is likely a **selection effect** — states with the worst opioid crises were more motivated to expand Medicaid as a public health response, not the other way around. This is an important bias to acknowledge.

### Top 10 States by Overdose Rate

| Rank | State | OD Rate (per 100K) | ACA Expansion |
|------|-------|--------------------|----|
| 1 | West Virginia | 35.96 | ✅ Yes |
| 2 | Kentucky | 26.77 | ✅ Yes |
| 3 | Ohio | 25.14 | ✅ Yes |
| 4 | New Mexico | 24.81 | ✅ Yes |
| 5 | Pennsylvania | 24.37 | ✅ Yes |
| 6 | Rhode Island | 23.57 | ✅ Yes |
| 7 | Delaware | 23.05 | ✅ Yes |
| 8 | DC | 22.84 | ✅ Yes |
| 9 | New Hampshire | 22.59 | ✅ Yes |
| 10 | Massachusetts | 21.99 | ✅ Yes |

All top 10 overdose states are ACA expansion states — again likely reflecting that the crisis drove the policy, not vice versa.

---

## Deep Cross-Analysis — Unexpected Findings

### Finding 1: The Post-2012 Prescribing ↔ Overdose Divergence

**This is the most important finding in the entire analysis.**

| Year | Total Opioid Rx | Overdose Rate (per 100K) |
|------|----------------|-------------------------|
| 2000 | 169,433,693 | 7.0 |
| 2004 | 208,032,513 | 10.5 |
| 2008 | 246,155,715 | 12.7 |
| 2010 | 258,387,176 | 13.1 |
| **2012** | **261,617,001** | **14.0** |
| 2013 | 252,898,441 | 14.7 |
| 2015 | 228,518,984 | 17.2 |
| 2017 | 196,816,918 | 22.7 |

| Period | Pearson r (Rx vs OD rate) | Interpretation |
|--------|--------------------------|----------------|
| Pre-2012 | **r = +0.975** | Near-perfect positive correlation |
| Post-2012 | **r = −0.656** | Strong *negative* correlation |

Before 2012, prescriptions and overdose deaths moved in lockstep. After 2012, prescriptions dropped sharply while overdose deaths **accelerated upward**. This structural break proves that **post-2012 overdose deaths are driven primarily by illicit opioids** (heroin, illicit fentanyl), not prescription opioids. Policies restricting Medicaid prescribing may have been targeting the wrong source of the crisis.

### Finding 2: The Methadone Paradox

| Metric | Medicaid | Non-Medicaid |
|--------|----------|-------------|
| Methadone avg MME | **29.8** | 39.5 |
| Methadone Rx count | 2,290,631 | 52,809,214 |
| Medicaid share | 4.2% | — |

Medicaid methadone prescriptions have a **25% lower average MME** than Non-Medicaid. Lower-dose methadone is characteristic of **opioid addiction treatment** (maintenance therapy) versus higher-dose methadone for pain management. This reframes Medicaid not as an over-prescriber but as a **treatment provider** — Medicaid is partially funding addiction treatment through methadone maintenance.

### Finding 3: Buprenorphine as Treatment Marker

| Metric | Value |
|--------|-------|
| Buprenorphine Medicaid Rx | 196,976 |
| Buprenorphine Non-Medicaid Rx | 4,333,052 |
| Medicaid share of buprenorphine | **4.3%** |
| Overall Medicaid opioid share | ~3.5% |

Buprenorphine (Suboxone) is primarily used for opioid addiction treatment. Medicaid's share of buprenorphine prescriptions (4.3%) is **higher** than its overall opioid share (3.5%), further indicating Medicaid's role in treatment, not over-prescribing.

### Finding 4: Propoxyphene Ban Effect (Nov 2010)

| Year | Medicaid Rx | Non-Medicaid Rx |
|------|------------|-----------------|
| 2009 | 20,129,095 | 231,322,650 |
| 2010 | 24,023,363 | 234,363,814 |
| 2011 | 22,875,956 | 236,307,005 |
| 2012 | 16,931,903 | 244,685,098 |

Medicaid opioid prescriptions dropped **26%** from 2010 to 2012 while Non-Medicaid prescriptions actually **increased 4.4%**. Medicaid responded more aggressively to the propoxyphene market withdrawal and broader opioid prescribing reforms, suggesting stronger formulary controls and utilization management.

### Finding 5: New Rx Ratio Correlates with Overdose (Counterintuitively)

| Correlation | ρ | p-value |
|-------------|---|---------|
| Medicaid new Rx % ↔ OD rate | **+0.306** | **p = 0.029** |
| Non-Medicaid new Rx % ↔ OD rate | **+0.371** | **p = 0.007** |

States with **more new (acute) prescriptions** and fewer chronic refills have **higher** overdose rates. This counterintuitive finding suggests that states aggressively restricting chronic prescribing may push patients toward illicit opioid sources, worsening the crisis.

### Finding 6: Year-Over-Year Prescribing Collapse

| Period | Medicaid Rx Trend | Non-Medicaid Rx Trend |
|--------|-------------------|-----------------------|
| 2008–2010 | Growing (+8–19%/yr) | Stable (+1%/yr) |
| 2011–2018 | **Declining** (−5 to −73%/yr) | Declining (−3 to −70%/yr) |
| 2012 | **−26%** (sharpest single-year drop) | +3.5% (still growing) |

Medicaid prescribing collapsed years before Non-Medicaid, and at a much faster rate. The 2012 Medicaid cliff (−26%) predates the general prescribing decline by 1–2 years, likely reflecting state Medicaid program reforms and prior authorization requirements.

---

## Conclusions

### The Medicaid Myth — Debunked

The data consistently shows that **Medicaid patients are NOT over-prescribed opioids**:

1. **Lower doses:** Medicaid average MME is lower than Non-Medicaid in every year measured (p = 0.000016)
2. **Fewer chronic prescriptions:** 90.2% of Medicaid opioid Rx are new vs 84.6% for Non-Medicaid
3. **Shrinking share:** Medicaid's proportion of opioid Rx dropped 61% from 2010 to 2018
4. **Same per-drug doses:** When prescribed the same drug, Medicaid patients receive equivalent doses (p = 0.75)
5. **Same fill sizes:** Quantity per Rx shows no significant difference across drug categories (p = 0.87)
6. **Concentrated formulary:** Medicaid patients are limited to fewer drug options (HHI 2,879 vs 2,714)
7. **Treatment role:** Medicaid over-indexes on addiction treatment drugs (buprenorphine 4.3% share vs 3.5% overall; methadone at lower/treatment doses)

### The Real Driver of Overdose Deaths

The post-2012 divergence (r = +0.975 → r = −0.656) demonstrates that overdose deaths are now driven by **illicit opioids**, not prescriptions. Total prescriptions have declined by 25%+ since 2012, yet overdose deaths have increased 55%. Policies targeting Medicaid prescription restrictions are addressing a problem that no longer drives the crisis.

### Policy Implications

- **Restricting Medicaid opioid access may be counterproductive** — the negative correlation between quantity ratio and overdose rate (ρ = −0.335, p = 0.016) suggests under-treatment is associated with worse outcomes
- **ACA expansion states have higher OD rates** — but this reflects crisis severity driving policy, not policy causing crisis (selection bias)
- **Medicaid plays a treatment role** — through methadone maintenance and buprenorphine access that should be protected, not restricted

---

## Limitations & Bias Evaluation

### Data Limitations
- **IQVIA coverage:** Medicaid-specific payor coding only available 2008–2018 (11 years vs 22 years for Non-Medicaid)
- **2018 data truncation:** Both groups show ~70% Rx drops in 2018, suggesting incomplete year or reporting change — 2018 comparisons should be treated cautiously
- **Aggregate data:** IQVIA provides prescription-level aggregates, not patient-level data — we cannot track individual patients across prescriptions
- **No demographic controls:** We cannot adjust for age, sex, race, or comorbidity differences between Medicaid and Non-Medicaid populations

### Potential Biases
- **Ecological fallacy:** State-level correlations (CDC merge) do not prove individual-level causation
- **Selection bias:** Medicaid patients are systematically different from the general population (lower income, higher disability rates, different age/sex distributions) — observed prescribing differences may reflect population health needs rather than prescribing behavior
- **ACA expansion confound:** States with severe opioid crises were more likely to expand Medicaid, creating an endogeneity problem in the expansion ↔ overdose analysis
- **Formulary effects:** Lower Medicaid prescribing may reflect formulary restrictions (prior authorization, step therapy) rather than lower clinical need — this is a restriction of access, not evidence of appropriate prescribing
- **Survivor bias in 2018:** The sharp drop in 2018 data may reflect reporting changes or IQVIA data collection artifacts rather than true prescribing changes

### What Additional Data Would Help
- **Patient-level data:** To control for demographics, comorbidities, and track individual prescribing trajectories
- **Medicaid enrollment counts by state/year:** To calculate per-enrollee prescribing rates rather than aggregate shares
- **Illicit drug seizure data (DEA):** To directly quantify the illicit opioid supply driving post-2012 deaths
- **Emergency department visit data:** To capture opioid-related morbidity, not just mortality
- **Prescriber-level panel data:** To identify whether specific prescribers treat Medicaid and Non-Medicaid patients differently

---

*Analysis conducted using Python (pandas, numpy, scipy) against the IQVIA PostgreSQL database on AWS RDS. All code available at [github.com/Matusvec/lucyInstituteChallenge](https://github.com/Matusvec/lucyInstituteChallenge).*

*Total query runtime: ~6.7 hours for Q3–Q5 (overnight batch), ~1 hour for Q1–Q2.*
