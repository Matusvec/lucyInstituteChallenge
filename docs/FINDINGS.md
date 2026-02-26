# The Medicaid Myth: Are Medicaid Patients Really Over-Prescribed Opioids?

## Research Findings — Lucy Institute Health Challenge

---

## Table of Contents

1. [Research Question](#research-question)
2. [Data Sources](#data-sources)
3. [Methodology](#methodology)
4. [Executive Summary](#executive-summary)
5. [Part I — Core Prescribing Comparisons (Q1–Q5)](#part-i--core-prescribing-comparisons-q1q5)
   - [Q1 — Prescriptions Over Time](#q1--opioid-prescriptions-by-medicaid-status-over-time)
   - [Q2 — Medicaid Share Over Time](#q2--medicaid-share-of-opioid-prescriptions-over-time)
   - [Q3 — State-Level Comparison](#q3--state-level-medicaid-vs-non-medicaid-prescribing)
   - [Q4 — Drug-Level Comparison](#q4--drug-level-medicaid-vs-non-medicaid-prescribing)
   - [Q5 — Specialty-Level Comparison](#q5--specialty-level-medicaid-vs-non-medicaid-prescribing)
6. [Part II — Extended Analysis (Q6–Q7)](#part-ii--extended-analysis-q6q7)
   - [Q6 — State × Year Panel](#q6--state--year-panel-data)
   - [Q7 — Sales Channel (Retail vs Mail Order)](#q7--sales-channel-retail-vs-mail-order)
7. [Part III — CDC Overdose Mortality Integration](#part-iii--cdc-overdose-mortality-integration)
   - [State-Level Correlation](#state-level-correlation-medicaid-prescribing-vs-overdose-deaths)
   - [ACA Expansion Analysis](#aca-medicaid-expansion-and-overdose-rates)
8. [Part IV — The Three Major Discoveries](#part-iv--the-three-major-discoveries)
   - [Discovery 1: The Prescription–Overdose Divorce](#discovery-1-the-prescriptionoverdose-divorce-post-2012)
   - [Discovery 2: The 2012 Inflection Point](#discovery-2-the-2012-inflection-point--what-caused-it)
   - [Discovery 3: Three Distinct Prescribing Populations](#discovery-3-three-distinct-prescribing-populations)
9. [Part V — Supporting Evidence](#part-v--supporting-evidence)
   - [The Methadone Paradox](#the-methadone-paradox)
   - [Buprenorphine as Treatment Marker](#buprenorphine-as-treatment-marker)
   - [ACA Had ~Zero Effect on Opioid Prescribing](#aca-had-zero-effect-on-opioid-prescribing-did)
   - [Drug Portfolio Inequity](#drug-portfolio-inequity--formulary-restrictions)
   - [2018 Data Truncation](#2018-data-truncation)
10. [Conclusions](#conclusions)
11. [Policy Implications](#policy-implications)
12. [Limitations & Bias Evaluation](#limitations--bias-evaluation)

---

## Research Question

> **Is there a significant difference between the way people on Medicaid are prescribed opioids versus the general population?**

The prevailing narrative suggests that Medicaid patients are over-prescribed opioids, contributing disproportionately to the opioid crisis. This research tests that assumption using **2.1 billion prescription records** from the IQVIA pharmaceutical database (1997–2018), supplemented with **CDC WONDER overdose mortality data** (1999–2018).

**Short answer:** Yes, there is a significant difference — but it's the *opposite* of what most people assume. Medicaid patients are prescribed opioids at **lower doses**, in **fewer drug categories**, with **more acute (new) prescriptions** rather than chronic refills, and with **zero access to mail-order opioids**. Most strikingly, Medicaid's share of opioid prescriptions has been in **freefall since 2010** — two full years before the national prescribing peak — and there is **zero correlation** between a state's Medicaid opioid prescribing rate and its overdose death rate.

---

## Data Sources

| Source | Description | Size | Time Period |
|--------|-------------|------|-------------|
| **IQVIA Pharmaceutical Database** | National prescription-level data (prescriber, drug, quantity, payor) | 2.1 billion rows | 1997–2018 |
| **CDC WONDER** | Multiple Cause of Death — drug-induced causes (ICD-10 X40–X44, X60–X64, X85, Y10–Y14) | 1,020 rows (51 states × 20 years) | 1999–2018 |
| **US Census ACS (2018)** | Population, race/ethnicity, median income, poverty rate, insurance coverage by county | 5 tables | 2018 (5-year estimates) |

- **IQVIA** is hosted on a shared PostgreSQL database on AWS RDS
- Medicaid payor plans identified by filtering `payor_plan` table for "medicaid" keyword → **71 unique Medicaid plan IDs**
- Opioid drugs identified by filtering `drug` table for known opioid active ingredients → **3,959 product groups**
- Morphine Milligram Equivalents (MME) calculated using standard CDC conversion factors mapped in Python
- **2018 data is truncated** (~3.6 months / Q1 only) — all trend analyses use 1997–2017

---

## Methodology

### Database Optimization
- Pre-fetched all 71 Medicaid plan IDs and 3,959 opioid product groups into literal SQL `IN (...)` tuples
- Eliminated expensive JOINs by mapping drug metadata (MME, ingredient) in Python from cached lookups
- All queries executed year-by-year (1997–2018) to manage memory and provide progress tracking
- Single persistent connection with connection pooling

### Statistical Methods
- **Welch's t-test** — comparison of means between Medicaid and Non-Medicaid groups
- **Paired t-test** — year-over-year paired comparisons
- **Mann-Whitney U test** — non-parametric alternative for non-normal distributions
- **Cohen's d** — effect size measurement
- **Pearson correlation (r)** — linear relationship between variables
- **Spearman rank correlation (ρ)** — monotonic relationships
- **Linear regression** — trend analysis over time
- **Difference-in-Differences (DiD)** — ACA Medicaid expansion natural experiment
- **Herfindahl-Hirschman Index (HHI)** — market concentration
- **Gini coefficient** — inequality in prescribing concentration

---

## Executive Summary

| Finding | Result | Significance |
|---------|--------|-------------|
| Medicaid MME vs Non-Medicaid MME | Medicaid **lower** every year (2008–2018) | p = 0.000016, Cohen's d = −0.74 |
| Medicaid share of opioid Rx | Declining −0.54%/yr (9.3% → 3.6%) | p = 0.000146 |
| Medicaid peaked 2 years before national | Medicaid peak: 2010 vs National: 2012 | Medicaid was the canary in the coal mine |
| Per-drug MME differences | Not significant | p = 0.75, Cohen's d = 0.10 |
| Quantity per Rx (across 20 drugs) | No significant difference | p = 0.87 |
| Medicaid % vs overdose death rate | **Zero correlation** | ρ = +0.001, p = 0.99 |
| Rx ↔ Overdose divergence | Pre-2012: r = +0.975 → Post-2012: r = −0.656 | Structural break — illicit opioids driving deaths |
| ACA expansion effect on opioid prescribing | Null effect (DiD = +0.04 pp) | Adding millions to Medicaid didn't change prescribing |
| Mail order opioids for Medicaid | **0%** — completely blocked | Medicaid patients cannot receive opioids by mail |
| Medicaid new Rx % vs Non-Medicaid | 90.2% vs 84.6% (less chronic) | Consistent across all 50 states |

**Bottom line:** Medicaid patients are prescribed opioids at lower doses, in fewer drug categories, with more acute (new) rather than chronic prescriptions, and with zero access to mail-order opioids. Restricting Medicaid prescribing has not reduced overdose deaths — the crisis has shifted to illicit opioids.

---

## Part I — Core Prescribing Comparisons (Q1–Q5)

### Q1 — Opioid Prescriptions by Medicaid Status Over Time

**Query:** Total Rx count, new Rx count, total quantity, and average MME per year, split by Medicaid vs Non-Medicaid.

**Output:** 29,485 rows → aggregated to 33 year × group rows | Runtime: 59.6 minutes

#### Results

| Year | Medicaid Rx | Medicaid Avg MME | Non-Medicaid Rx | Non-Medicaid Avg MME | MME Gap |
|------|------------|------------------|-----------------|---------------------|---------|
| 2008 | 18,583,366 | 13.48 | 227,572,350 | 14.46 | −0.98 |
| 2009 | 20,129,095 | 13.23 | 231,322,650 | 14.50 | −1.28 |
| **2010** | **24,023,363** | 13.05 | 234,363,814 | 14.75 | **−1.70** |
| 2011 | 22,875,956 | 12.71 | 236,307,005 | 14.10 | −1.39 |
| **2012** | 16,931,903 | 12.47 | **244,685,098** | 13.55 | −1.08 |
| 2013 | 13,761,303 | 12.50 | 239,137,138 | 13.35 | −0.85 |
| 2014 | 13,525,447 | 12.40 | 231,894,089 | 13.35 | −0.95 |
| 2015 | 11,271,444 | 12.63 | 217,247,540 | 13.47 | −0.84 |
| 2016 | 9,563,449 | 12.68 | 207,287,492 | 13.33 | −0.65 |
| 2017 | 7,805,454 | 12.57 | 189,011,464 | 13.00 | −0.43 |

> **Key observation:** Medicaid Rx peaked in **2010** (24M) then collapsed. Non-Medicaid didn't peak until **2012** (245M). Medicaid was the *first* population to see prescribing decline — two years ahead of the national trend.

#### Statistical Analysis

| Test | Statistic | p-value | Interpretation |
|------|-----------|---------|----------------|
| Paired t-test (MME) | t = −6.33 | **p = 0.000016** | Medicaid MME significantly lower |
| Cohen's d | −0.74 | — | Medium-to-large effect size |
| Mann-Whitney U | U = 0.0 | **p = 0.000098** | Non-parametric confirms result |
| Linear trend (Med MME) | slope = −0.060/yr | p = 0.095 | Slight downward trend |
| Linear trend (NonMed MME) | slope = −0.241/yr | p = 0.0002 | Strong downward trend |

**Interpretation:** Medicaid average MME was lower than Non-Medicaid in **every single year** from 2008–2018. The gap narrowed over time as both groups reduced prescribing intensity, but Medicaid was consistently prescribed lower-potency opioids.

---

### Q2 — Medicaid Share of Opioid Prescriptions Over Time

**Query:** Medicaid's percentage share of total opioid prescriptions by year.

| Year | Medicaid Rx | Total Rx | Medicaid % |
|------|------------|----------|-----------|
| 2008 | 18,583,366 | 246,155,715 | 7.55% |
| 2009 | 20,129,095 | 251,451,746 | 8.01% |
| **2010** | **24,023,363** | 258,387,176 | **9.30% (peak)** |
| 2011 | 22,875,956 | 259,182,961 | 8.83% |
| 2012 | 16,931,903 | 261,617,001 | 6.47% |
| 2013 | 13,761,303 | 252,898,441 | 5.44% |
| 2014 | 13,525,447 | 245,419,537 | 5.51% |
| 2015 | 11,271,444 | 228,518,984 | 4.93% |
| 2016 | 9,563,449 | 216,850,941 | 4.41% |
| 2017 | 7,805,454 | 196,816,918 | 3.97% |

| Test | Statistic | p-value |
|------|-----------|---------|
| Linear trend | slope = **−0.54%/yr** | **p = 0.000146** |

**Interpretation:** Medicaid's share of opioid prescriptions has been in steep, statistically significant decline — dropping from a peak of 9.3% (2010) to under 4% (2017). This represents a **61% reduction** in Medicaid's proportional contribution to opioid prescribing. Medicaid enrollment actually *increased* during this period (especially post-ACA 2014), making the per-enrollee decline even steeper.

---

### Q3 — State-Level Medicaid vs Non-Medicaid Prescribing

**Query:** Total Rx, new Rx, and total quantity by state, split by Medicaid vs Non-Medicaid (all years aggregated).

**Output:** 115 rows (58 states/territories × 2 groups) | Runtime: 135.5 minutes

#### Key National Metrics

| Metric | Medicaid | Non-Medicaid |
|--------|----------|-------------|
| New Rx as % of Total (national avg) | **90.2%** | 84.6% |
| Avg Quantity per Rx | 61.7 | 59.5 |

Medicaid patients have a **higher new Rx ratio** (90.2% vs 84.6%), meaning their opioid prescriptions are more likely to be first-time/acute prescriptions rather than chronic refills. This pattern holds in **every state** — even in the states with the most chronic Medicaid prescribing, Medicaid still has a higher new Rx % than Non-Medicaid.

#### Top States by Medicaid Opioid Volume Share

| State | Medicaid % | State | Medicaid % |
|-------|-----------|-------|-----------|
| Vermont | 11.47% | Tennessee | 6.43% |
| Wisconsin | 9.87% | North Carolina | 6.53% |
| Maine | 9.59% | Alaska | 6.26% |
| Connecticut | 8.94% | — | — |
| Delaware | 7.66% | — | — |

#### States with Most Acute Prescribing (Highest New Rx %)

| State | Medicaid New Rx % | Non-Medicaid New Rx % | Diff |
|-------|-------------------|----------------------|------|
| OK | 94.4% | 86.7% | +7.6 |
| AK | 94.1% | 90.8% | +3.3 |
| MD | 94.0% | 90.3% | +3.7 |
| CO | 94.0% | 86.3% | +7.7 |
| NH | 94.0% | 89.6% | +4.4 |

---

### Q4 — Drug-Level Medicaid vs Non-Medicaid Prescribing

**Query:** Total Rx, total quantity, and average MME by active ingredient, split by Medicaid vs Non-Medicaid.

**Output:** 40 rows (20 drugs × 2 groups) | Runtime: 97.5 minutes

#### Top 10 Drugs by Rx Volume

| Drug | Medicaid Rx | Medicaid % | Med MME | NonMed MME |
|------|------------|-----------|---------|-----------|
| Hydrocodone | 73,314,288 | 3.5% | 8.48 | 7.52 |
| Oxycodone | 37,169,052 | 4.5% | 23.82 | 22.72 |
| Tramadol | 21,089,503 | 4.0% | 11.73 | 9.54 |
| Codeine | 13,254,898 | 3.3% | 4.19 | 4.50 |
| Morphine | 5,024,969 | 4.4% | **49.73** | 33.77 |
| Propoxyphene | 2,939,493 | 0.9% | 19.52 | 17.80 |
| Methadone | 2,290,631 | 4.2% | 29.79 | 39.53 |
| Fentanyl | 2,260,891 | 2.7% | 246.38 | 195.71 |
| Hydromorphone | 1,689,981 | 4.4% | 26.15 | 33.97 |
| Oxymorphone | 570,769 | 5.3% | 42.84 | 39.01 |

#### Statistical Tests

| Test | Statistic | p-value | Interpretation |
|------|-----------|---------|----------------|
| Welch's t-test (MME) | t = 0.324 | **p = 0.75** | ❌ NOT significant |
| Cohen's d | 0.10 | — | Negligible effect size |
| Paired t-test (qty/Rx) | — | **p = 0.87** | ❌ NOT significant |

**Interpretation:** On a per-drug basis, the MME differences between Medicaid and Non-Medicaid are **not statistically significant**. The overall lower MME for Medicaid (from Q1) is driven by **drug mix** — Medicaid patients are prescribed more hydrocodone (low MME) and less fentanyl/methadone (high MME) — not by lower doses of individual drugs.

#### Drug Portfolio Differences

**Over-represented in Medicaid:** Oxymorphone (1.53×), Oxycodone (1.30×), Hydromorphone (1.27×)

**Under-represented in Medicaid:** Propoxyphene (0.24×), Dextropropoxyphene (0.21×), Fentanyl (0.74×)

**Market Concentration (HHI):** Medicaid **2,879** vs Non-Medicaid **2,714** — Medicaid prescribing is more concentrated in fewer drugs. Top 3 drugs = 81.9% of Medicaid vs 75.4% of Non-Medicaid. This suggests **formulary restrictions** limit the range of drugs available to Medicaid patients.

---

### Q5 — Specialty-Level Medicaid vs Non-Medicaid Prescribing

**Query:** Total Rx by prescriber specialty, split by Medicaid vs Non-Medicaid.

**Output:** 860 rows (441 specialties × 2 groups) | Runtime: 170.7 minutes

#### Specialties with Highest Medicaid Share

| Specialty | Medicaid % | Total Rx |
|-----------|-----------|----------|
| Pediatric Hematology/Oncology | 17.6% | 916,561 |
| Pediatric Anesthesiology | 12.2% | 107,611 |
| Urology-Pediatric | 12.1% | 687,145 |
| Pediatric Surgery | 11.2% | 1,008,452 |
| Pediatrics | 10.8% | 246,564 |
| OB/GYN | 9.4% | 7,964,029 |

#### Specialties with Lowest Medicaid Share

| Specialty | Medicaid % | Total Rx |
|-----------|-----------|----------|
| Veterinary | 0.5% | 6,028,160 |
| Dermatology | 1.0% | 6,856,668 |
| Sports Medicine Ortho | 1.1% | 14,700,139 |
| Plastic Surgery | 1.4% | 30,880,753 |

#### Prescribing Concentration

| Metric | Medicaid | Non-Medicaid |
|--------|----------|-------------|
| Gini coefficient | **0.947** | 0.944 |
| Top 5 specialties share | **49.9%** | 48.6% |

**Interpretation:** Pediatric specialties and OB/GYN have the highest Medicaid share — reflecting **who Medicaid covers** (children and pregnant women), not prescribing behavior. Elective/cosmetic specialties have the lowest share.

---

## Part II — Extended Analysis (Q6–Q7)

### Q6 — State × Year Panel Data

**Query:** Total Rx, new Rx, and total quantity by state × year × Medicaid status (2008–2018). This is the workhorse dataset — it enables difference-in-differences analysis, state trajectory analysis, and state-level overdose correlations.

**Output:** ~1,200 rows | Runtime: 62.3 minutes

#### State Trajectories — Who Declined Fastest?

Using linear regression on Medicaid opioid share (2009–2017) per state:

| Falling Fastest (pp/yr) | | Rising — Anomalies (pp/yr) | |
|---|---|---|---|
| Delaware | −2.545 pp/yr | Colorado | +1.344 pp/yr |
| New York | −1.891 pp/yr | Montana | +0.520 pp/yr |
| Louisiana | −1.677 pp/yr | | |
| West Virginia | −1.634 pp/yr | | |

> **47/50 states show declining Medicaid opioid share.** Colorado and Montana are the only states where Medicaid's share is *rising* — likely reflecting different state-level Medicaid program policies.

#### Biggest Drops in Medicaid Share (Early vs Late Period)

| State | Change |
|-------|--------|
| Virgin Islands | −88.7% |
| West Virginia | −84.2% |
| Maine | −81.8% |
| Delaware | −80.1% |

#### Consistency Check
Q6 state-level sums match Q1 national totals with **0.00% average difference**, and Q6 state rollups match Q3 all-time totals — data is internally consistent across all query modules.

---

### Q7 — Sales Channel (Retail vs Mail Order)

**Query:** Opioid prescriptions by sales channel (Retail vs Mail Order) × Medicaid status × year.

**Output:** ~90 rows | Runtime: 58.1 minutes

#### The Key Finding: Medicaid Has ZERO Mail-Order Opioids

| Channel | Group | Qty/Rx | New Rx % | Profile |
|---------|-------|--------|----------|---------|
| Mail Order | Non-Medicaid | **185.8** | **63.4%** | 90-day chronic fills |
| Retail | Non-Medicaid | 58.6 | 84.8% | Standard community pharmacy |
| Retail | Medicaid | 61.5 | 90.2% | Most acute, smallest fills |

- **0%** of Medicaid opioid prescriptions go through mail order
- Mail order opioids are declining: from 0.84% to 0.38% of all opioid Rx over the study period (slope = −0.0214 pp/yr, p < 0.05)
- Mail order patients get **3× more pills per prescription** (185.8 vs 58.6 units) with far fewer new Rx (63% vs 85%)

**Interpretation:** This reveals a **structural access barrier** — Medicaid patients cannot receive opioids by mail. This likely reflects state Medicaid pharmacy mandates requiring in-person dispensing. Medicaid patients must physically visit a pharmacy for every refill, which creates greater monitoring/oversight but also places disproportionate burden on chronically ill patients.

---

## Part III — CDC Overdose Mortality Integration

### State-Level Correlation: Medicaid Prescribing vs Overdose Deaths

**Data:** CDC WONDER drug-induced deaths (ICD-10 X40–X44, X60–X64, X85, Y10–Y14) merged with IQVIA state-level prescribing data.

| Correlation | ρ | p-value | Interpretation |
|-------------|---|---------|----------------|
| Medicaid % of Rx ↔ Overdose Rate | **+0.001** | **p = 0.99** | ❌ No relationship whatsoever |
| Qty ratio (Med/NonMed) ↔ Overdose Rate | **−0.335** | **p = 0.016** | ✅ Under-treatment associated with higher deaths |
| Medicaid new Rx % ↔ OD rate | +0.306 | p = 0.029 | ✅ More restriction → worse outcomes |
| Non-Medicaid new Rx % ↔ OD rate | +0.371 | p = 0.007 | ✅ Same pattern in Non-Medicaid |

**The quantity ratio finding:** States where Medicaid patients get *relatively smaller* fills compared to Non-Medicaid have **higher** overdose rates. This suggests that **under-treatment** of Medicaid patients (restricting their access) may paradoxically be associated with worse outcomes.

**The new Rx finding:** States with more acute (new) prescriptions and fewer chronic refills have *higher* overdose rates — for both Medicaid and Non-Medicaid populations. This counterintuitive result suggests that aggressively restricting chronic prescribing may push patients toward illicit opioid sources.

### ACA Medicaid Expansion and Overdose Rates

| Group | Avg Overdose Rate (per 100K) | n |
|-------|------------------------------|---|
| ACA Expansion States | **18.7** | 28 |
| Non-Expansion States | **15.0** | 23 |
| Welch's t-test | **p = 0.01** | ✅ Significant |

All top 10 overdose states (WV, KY, OH, NM, PA, RI, DE, DC, NH, MA) are ACA expansion states — but this is almost certainly a **selection effect**: states with the worst opioid crises were more motivated to expand Medicaid as a public health response. The causality runs **crisis → expansion**, not the reverse.

#### State-Year Panel: Rx–Overdose Correlation by State

Using Q6 state×year data merged with CDC annual overdose rates:

- **47/50 states** show positive Rx–Overdose correlation (more prescriptions, more deaths)
- **21 states** are statistically significant (p < 0.05)
- **Oklahoma** has the strongest correlation (ρ = +0.708)
- **No state** shows a significant *negative* correlation

---

## Part IV — The Three Major Discoveries

### Discovery 1: The Prescription–Overdose Divorce (Post-2012)

> **This is the single most important finding in the entire analysis.**

| Year | Total Opioid Rx | Overdose Rate (per 100K) |
|------|----------------|-------------------------|
| 2000 | 169,433,693 | 7.0 |
| 2004 | 208,032,513 | 10.5 |
| 2008 | 246,155,715 | 12.7 |
| 2010 | 258,387,176 | 13.1 |
| **2012** | **261,617,001** | **14.0** |
| 2013 | 252,898,441 | 14.7 |
| 2015 | 228,518,984 | 17.2 |
| 2017 | 196,816,918 | **22.7** |

| Period | Pearson r (Rx vs OD rate) | Interpretation |
|--------|--------------------------|----------------|
| **Pre-2012** | **r = +0.975** | Near-perfect positive correlation |
| **Post-2012** | **r = −0.656** | Strong *negative* correlation |

Before 2012, prescriptions and overdose deaths moved in lockstep (r = +0.975). After 2012, prescriptions dropped by 25% while overdose deaths **increased by 62%** — the correlation flipped to r = −0.656.

**What this means:** Post-2012 overdose deaths are driven primarily by **illicit opioids** (heroin, illicit fentanyl), not prescription opioids. Policies restricting Medicaid prescribing are targeting the wrong source of the crisis. The prescription pipeline was effectively shut down, but demand didn't disappear — it shifted to the street.

**CDC overdose death trajectory around the break:**

| Year | Deaths | Year-over-Year Change |
|------|--------|-----------------------|
| 2012 | 33,735 | +0.6% |
| 2013 | 35,799 | +6.1% |
| 2014 | 38,416 | +7.3% |
| 2015 | 42,665 | +11.1% |
| 2016 | 51,555 | +20.8% |

The acceleration in deaths *after* prescriptions started falling is the clearest evidence that illicit supply, not prescription opioids, became the dominant killer.

---

### Discovery 2: The 2012 Inflection Point — What Caused It?

The year 2012 is not a random turning point. It represents the **convergence of at least five simultaneous policy and market interventions**:

| Year | Event | Impact |
|------|-------|--------|
| 2010 | FDA pulls propoxyphene (Darvon/Darvocet) | ~8% of Non-Medicaid Rx volume removed overnight |
| 2010 | Purdue reformulates OxyContin to abuse-deterrent | Abuse-prone users shift to heroin/other drugs |
| 2011 | DEA pill mill crackdowns begin (esp. Florida) | Major supply source eliminated |
| 2012 | State PDMP mandates spread rapidly | Doctors can see patient history across prescribers |
| 2012 | Florida "pill mill" law takes full effect | The #1 source state for diverted opioids is shut down |

#### Why Medicaid Peaked 2 Years Earlier (2010 vs 2012)

Medicaid opioid Rx peaked at **24,023,363** in 2010, then collapsed to **16,931,903** by 2012 (−30%). Non-Medicaid was *still growing* through 2012.

Why the gap? Medicaid programs responded **faster** due to:
- Stronger formulary controls and prior authorization requirements
- State Medicaid agencies implemented restrictions before federal guidelines
- Propoxyphene removal had less impact on Medicaid (only 1.87% of Medicaid Rx vs 7.82% of Non-Medicaid)

**State-level peak year distribution:**
- 18 states peaked **before** 2012
- 28 states peaked **in** 2012
- 5 states peaked **after** 2012

#### The Unintended Consequence

Patients lost access to prescription opioids → illicit market (heroin, then fentanyl) filled the demand → overdose deaths **accelerated** despite fewer prescriptions. The 2012 inflection is where the opioid crisis stopped being a *prescribing* crisis and became a *supply* crisis.

---

### Discovery 3: Three Distinct Prescribing Populations

The Q7 sales channel data reveals that "Non-Medicaid opioid patients" is not a monolithic group. There are actually **three distinct populations** with very different prescribing profiles:

| Population | Qty/Rx | New Rx % | Channel | Profile |
|-----------|--------|----------|---------|---------|
| **Mail Order Non-Medicaid** | 185.8 | 63.4% | Mail | CHRONIC pain patients on 90-day refills |
| **Retail Non-Medicaid** | 58.6 | 84.8% | Retail | Mixed acute/chronic at community pharmacies |
| **Retail Medicaid** | 61.5 | 90.2% | Retail only | MOST acute, highest turnover, smallest fills |

This is invisible when you just compare "Medicaid vs Non-Medicaid" — the mail-order chronic pain population is pooled in with retail acute patients, distorting the comparison.

**Implications:**
- The mail-order population (90-day supplies, low new Rx %) represents the **chronic pain cohort** most at risk for dependency
- This population is **100% non-Medicaid** — Medicaid patients are structurally excluded
- Medicaid patients cycle in and out of opioid treatment more rapidly (90% new Rx)
- Comparing "Medicaid vs everyone else" unfairly pools vastly different prescribing patterns

---

## Part V — Supporting Evidence

### The Methadone Paradox

| Metric | Medicaid | Non-Medicaid |
|--------|----------|-------------|
| Methadone avg MME | **29.8** | 39.5 |
| Methadone Rx count | 2,290,631 | 52,809,214 |
| Medicaid share | 4.2% | — |

Medicaid methadone prescriptions have a **25% lower average MME** than Non-Medicaid. Lower-dose methadone is characteristic of **opioid addiction treatment** (maintenance therapy at 20–40 mg/day) versus higher-dose methadone for pain management (40–120 mg/day). This reframes Medicaid not as an over-prescriber but as a **treatment provider** — Medicaid is partially funding addiction treatment through methadone maintenance.

### Buprenorphine as Treatment Marker

| Metric | Value |
|--------|-------|
| Buprenorphine Medicaid Rx | 196,976 |
| Buprenorphine Non-Medicaid Rx | 4,333,052 |
| Medicaid share of buprenorphine | **4.3%** |
| Overall Medicaid opioid share | ~3.5% |

Buprenorphine (Suboxone) is primarily used for opioid addiction treatment. Medicaid's share of buprenorphine prescriptions (4.3%) is **higher** than its overall opioid share (3.5%), further supporting Medicaid's role in treatment, not over-prescribing.

### ACA Had ~Zero Effect on Opioid Prescribing (DiD)

Using Q6 state×year panel data as a natural experiment:

| Group | Pre-ACA (2009–2013) | Post-ACA (2014–2018) | Change |
|-------|--------------------|--------------------|--------|
| Expansion states | Higher Medicaid % | Lower Medicaid % | Declining |
| Non-expansion states | Lower Medicaid % | Lower Medicaid % | Declining |
| **DiD estimate** | — | — | **+0.04 pp (null)** |

ACA expansion vs non-expansion slope difference: **p = 0.8191** (not significant). Adding millions of new beneficiaries to Medicaid through ACA expansion had essentially **zero effect** on opioid prescribing patterns. Formulary rules were already so tight that expanding coverage didn't expand opioid access.

### Drug Portfolio Inequity / Formulary Restrictions

| Metric | Medicaid | Non-Medicaid |
|--------|----------|-------------|
| HHI (drug concentration) | 2,879 | 2,714 |
| Top 3 drugs share | 81.9% | 75.4% |
| Drugs available (>1% share) | ~6 | ~8 |

Medicaid patients are prescribed from a **narrower formulary** — 81.9% of their prescriptions come from just three drugs (hydrocodone, oxycodone, tramadol) vs 75.4% for Non-Medicaid.

### Quantity per Rx Trends (Pill Burden)

| Trend | Slope | p-value |
|-------|-------|---------|
| Medicaid qty/Rx over time | −0.10 units/yr | Not significant |
| Non-Medicaid qty/Rx over time | **+0.40 units/yr** | **p = 0.019** |

Non-Medicaid fill sizes are **growing** over time while Medicaid fills remain flat — the average Non-Medicaid patient is getting progressively larger fills while Medicaid patients stay at the same acute-level fill size.

### 2018 Data Truncation

**2018 data contains only ~3.6 months (approximately Q1)**. Evidence:

- 2018/2017 total Rx ratio: **0.301** across all states
- All 57 state/territory codes present in both years
- Ratio is uniform (0.266–0.334) across all states, channels, and payer types
- Medicaid ratio: 0.275 (~3.3 months)

The ~70% drop is **not** a real prescribing collapse — it is incomplete data. All trend analyses in this report use **1997–2017** for valid conclusions.

---

## Conclusions

### The Medicaid Myth — Debunked

The data consistently shows that **Medicaid patients are NOT over-prescribed opioids**:

1. **Lower doses:** Medicaid average MME is lower than Non-Medicaid in every year (p = 0.000016)
2. **Fewer chronic prescriptions:** 90.2% of Medicaid opioid Rx are new vs 84.6% for Non-Medicaid
3. **Shrinking share:** Medicaid's proportion of opioid Rx dropped 61% from 2010 to 2017
4. **Same per-drug doses:** When prescribed the same drug, doses are equivalent (p = 0.75)
5. **Same fill sizes:** Quantity per Rx shows no significant difference (p = 0.87)
6. **Concentrated formulary:** Medicaid patients are limited to fewer drug options (HHI 2,879 vs 2,714)
7. **Treatment role:** Medicaid over-indexes on addiction treatment drugs (buprenorphine 4.3% vs 3.5% overall; methadone at lower/treatment doses)
8. **No mail order:** 0% of Medicaid opioids go through mail order — most restrictive access
9. **Collapsed first:** Medicaid peaked in 2010, two years before the national peak
10. **Zero overdose correlation:** Medicaid prescribing rate has zero relationship to overdose rate (ρ = 0.001, p = 0.99)

### The Real Driver of Overdose Deaths

The post-2012 divergence (r = +0.975 → r = −0.656) demonstrates that overdose deaths are now driven by **illicit opioids**, not prescriptions. Total prescriptions declined 25%+ since 2012, yet overdose deaths increased 62%. The prescription pipeline was shut down — the street supply was not.

---

## Policy Implications

1. **Restricting Medicaid opioid access may be counterproductive** — the negative correlation between quantity ratio and overdose rate (ρ = −0.335, p = 0.016) suggests under-treatment is associated with worse outcomes

2. **Prescription restrictions didn't reduce deaths** — the prescription–overdose divorce proves that cutting Rx volume post-2012 coincided with *accelerating* deaths

3. **Medicaid plays a treatment role that should be protected** — methadone maintenance and buprenorphine access represent addiction treatment, not over-prescribing

4. **ACA expansion did not worsen prescribing** — the DiD null result (+0.04 pp) means expanding health coverage did not expand opioid access

5. **Mail-order blocking creates patient burden** — Medicaid patients must visit a pharmacy monthly for medications that Non-Medicaid patients receive in 90-day mail supplies

6. **Policy should target illicit supply** — post-2012 deaths are driven by heroin and illicit fentanyl, not prescriptions

---

## Limitations & Bias Evaluation

### Data Limitations
- **IQVIA Medicaid coding:** Only available 2008–2018 (11 years vs 22 years for Non-Medicaid)
- **2018 truncation:** Only ~3.6 months present — all trends use 2017 as endpoint
- **Aggregate data:** Prescription-level aggregates, not patient-level — cannot track individuals
- **No demographics:** Cannot adjust for age, sex, race, or comorbidity differences
- **No enrollment counts:** Cannot compute per-enrollee rates, only aggregate shares

### Potential Biases
- **Ecological fallacy:** State-level correlations do not prove individual-level causation
- **Selection bias:** Medicaid patients are systematically different (lower income, higher disability)
- **ACA confound:** States with severe crises were more likely to expand Medicaid (endogeneity)
- **Formulary effects:** Lower prescribing may reflect access restrictions, not lower clinical need

### What Additional Data Would Help
- **Patient-level data** for demographics, comorbidities, individual trajectories
- **Medicaid enrollment counts** by state/year for per-enrollee rates
- **DEA seizure data** to quantify illicit supply
- **ED visit data** to capture morbidity, not just mortality
- **Prescriber-level panels** to see if providers treat groups differently

---

*Analysis conducted using Python (pandas, numpy, scipy, matplotlib) against the IQVIA PostgreSQL database on AWS RDS.*
*Total query runtime: ~8 hours for Q1–Q7.*
*All code available at [github.com/Matusvec/lucyInstituteChallenge](https://github.com/Matusvec/lucyInstituteChallenge).*
