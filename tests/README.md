# Tests

Automated verification that visualization data matches source formulas.

## Run Tests

```bash
python -m pytest tests/ -v
```

## What Is Verified

- **Illicit Overdose:** rate = deaths / population x 100,000
- **County Overdose:** rate = deaths / population x 100,000
- **Fentanyl:** rate = deaths / population x 100,000 (T40.4 only)
- **Dashboard:** overdose_rate, rx_per_capita, pct_medicaid, avg_mme_per_unit formulas
- **Data flow:** Correct columns from merge pipeline to map inputs
