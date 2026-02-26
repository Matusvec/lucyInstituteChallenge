# Visualizations

Maps and charts for the Lucy Institute Health Challenge.

## Maps (Plotly → HTML)

Run via `main.py`:

| Script | Command | Output |
|--------|---------|--------|
| `illicit_overdose_spread.py` | `python main.py map-illicit` | `output/cdc/illicit_overdose_spread_map.html` |
| `county_overdose_spread.py` | `python main.py map-county` | `output/cdc/county_overdose_spread_map.html` |
| `fentanyl_spread.py` | `python main.py map-fentanyl` | `output/cdc/fentanyl_spread_map.html` |
| `county_dashboard_map.py` | `python main.py map-dashboard` | `output/county/county_dashboard_map.html` |

## Charts (Matplotlib)

| Script | Run | Output |
|--------|-----|--------|
| `heroinVsFentanyl.py` | `python -m visualizations.heroinVsFentanyl` | Window |
| `prescriptionsVsOverdose.py` | `python -m visualizations.prescriptionsVsOverdose` or `scripts/python/_test_chart.py` | PNG via `_test_chart.py` |
| `Medicaid_Timeline.py` | `python -m visualizations.Medicaid_Timeline` | `medicaid_rx_vs_enrollment_timeline.png` |
| `merge_mme_overdose_county.py` | `python -m visualizations.merge_mme_overdose_county` | Merged CSV |
| `mme_vs_deaths_scatterplot.py` | `python -m visualizations.mme_vs_deaths_scatterplot` | `output/plots/mme_vs_deaths_by_county.png` |
| `mme_vs_overdose_2012_2016.py` | `python -m visualizations.mme_vs_overdose_2012_2016` | `output/plots/mme_vs_overdose_2012_2016.png` |

## Data Dependencies

- **Maps:** `Datasets/cdc/`, `Datasets/geo/us_counties_geojson.json`, `output/cdc/`, `output/county/`
- **Charts:** `output/iqvia_core/`, `output/cdc/`, `output/county/`, `Datasets/census/`

See [docs/VISUALIZATIONS.md](../docs/VISUALIZATIONS.md) for full instructions.
