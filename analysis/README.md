# Analysis

Post-query statistical analysis. Runs on CSV outputs from `main.py` (no database required).

| Script | Purpose |
|--------|---------|
| `analyze.py` | Generic CSV analyzer with auto-detect stat tests |
| `deep_analysis.py` | Cross-analysis of Q1–Q5 + CDC (10 sections) |
| `extended_analysis.py` | Q6 (state×year) + Q7 (sales channel) analysis |
| `bridge_analysis.py` | Integrates Q6/Q7 with Q1–Q5 + CDC |
| `what_happened_2012.py` | Forensic investigation of the 2012 inflection |
| `check_2018.py` | Proves 2018 data is truncated (~3.6 months) |

**Run:**
```bash
python -m analysis.deep_analysis
python -m analysis.extended_analysis
python -m analysis.bridge_analysis
python -m analysis.what_happened_2012
python -m analysis.check_2018
```
