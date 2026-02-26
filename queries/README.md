# Queries

SQL modules that run against the IQVIA PostgreSQL database.
Each module handles connection pooling, chunked execution, and CSV export.

## Modules

| Module | Purpose | main.py Command |
|--------|---------|-----------------|
| `explore_payors.py` | Discover Medicaid plan IDs and payor categories | `explore` |
| `medicaid_vs_general.py` | Q1--Q5: Medicaid vs Non-Medicaid comparisons | `medicaid`, `q3`, `q4`, `q5` |
| `geographic.py` | Zip-code and state-level geographic queries | `geo`, `geo-light` |
| `extended.py` | Q6--Q9: State x year, sales channel, monthly, 2018 sample | `extended`, `q6`--`q9` |
| `county_panel.py` | County-level IQVIA panel via zip-to-county aggregation | `county` |
| `mme_spread.py` | MME 5-number summary and spread data for mapping | `map-mme` |

## Outputs

| Directory | Contents |
|-----------|----------|
| `output/lookups/` | Payor plan IDs, Medicaid plan list |
| `output/iqvia_core/` | Q1--Q5 Medicaid vs Non-Medicaid results |
| `output/extended/` | Q6--Q9 state x year and sales channel results |
| `output/county/` | County-level panel, merged data, MME summary |

## Database

The IQVIA database contains four tables:

- **`main`** -- Prescription transaction records (2.1B rows)
- **`drug`** -- Drug product reference (name, USP class, MME per unit)
- **`prescriber_limited`** -- Prescriber zip, state, specialty
- **`payor_plan`** -- Insurance plan categories

Opioids are filtered by `drug.usc LIKE '022%'` (3,959 product groups).
Medicaid is identified via 71 payor plan IDs containing "medicaid".
