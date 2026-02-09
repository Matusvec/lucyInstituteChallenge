"""
Analysis scripts for post-query statistical analysis.

Scripts in this directory analyze the CSV outputs from queries/
and produce cross-dataset insights.

Modules:
  analyze.py              — Generic CSV analyzer (auto-detects format, runs stat tests)
  deep_analysis.py        — Cross-analysis of Q1–Q5 + CDC (10 sections)
  extended_analysis.py    — Analysis of Q6 (state×year) + Q7 (sales channel)
  bridge_analysis.py      — Bridges Q6/Q7 with Q1–Q5 + CDC for integrated findings
  what_happened_2012.py   — Forensic investigation of the 2012 inflection point
  check_2018.py           — Confirms 2018 data is truncated (~3.6 months)
"""
