# Queries

SQL modules that run against the IQVIA PostgreSQL database.

| Module | Purpose | main.py Command |
|--------|---------|-----------------|
| `explore_payors.py` | Discover Medicaid plan IDs & payor categories | `explore` |
| `medicaid_vs_general.py` | Q1–Q5: Medicaid vs Non-Medicaid comparisons | `medicaid`, `q3`, `q4`, `q5` |
| `geographic.py` | Zip-code & state-level geographic data | `geo`, `geo-light` |
| `extended.py` | Q6–Q9: state×year, sales channel, monthly, 2018 sample | `extended`, `q6`–`q9` |
| `county_panel.py` | County-level IQVIA panel (zip→county) | `county` |
| `pill_mill.py` | Prescriber concentration / pill mill analysis | `pillmill` |

Outputs go to `output/lookups/`, `output/iqvia_core/`, `output/extended/`, `output/county/`, `output/pillmill/`.
