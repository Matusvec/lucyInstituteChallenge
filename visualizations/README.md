# Visualizations

Active animated map scripts for the Lucy Institute Health Challenge.
Each script produces an interactive HTML choropleth map via Plotly.

## Maps

| Script | Command | Output | Description |
|--------|---------|--------|-------------|
| `county_overdose_spread.py` | `python main.py map-county` | `output/cdc/county_overdose_spread_map.html` | County-level overdose death rate per 100K (2008--2017) |
| `fentanyl_spread.py` | `python main.py map-fentanyl` | `output/cdc/fentanyl_spread_map.html` | Fentanyl/synthetic opioid deaths by county (2008--2017) |
| `illicit_overdose_spread.py` | `python main.py map-illicit` | `output/cdc/illicit_overdose_spread_map.html` | Illicit drug overdose trends by state (1999--2018) |
| `county_dashboard_map.py` | `python main.py map-dashboard` | `output/county/county_dashboard_map.html` | Multi-metric dashboard with 4 switchable layers |
| `mme_spread_map.py` | `python main.py map-mme` | `output/plots/mme_spread_map.html` | Average MME per prescription unit by county (2008--2017) |

## Shared Module

- `theme.py` -- Color scales, background colors, and Plotly colorscale
  definitions shared across all maps.

## Data Sources

- **CDC data:** `Datasets/cdc/` (overdose CSVs by state, county, drug type)
- **GeoJSON:** `Datasets/geo/us_counties_geojson.json` (county boundaries)
- **IQVIA panel:** `output/county/iqvia_cdc_county_merged.csv` (merged data)

## Archived Charts

Non-map visualizations (Matplotlib scatter plots, bar charts, timelines)
are in `archive/visualizations/`. They remain runnable:

```bash
python -m archive.visualizations.heroinVsFentanyl
python -m archive.visualizations.divergence_plot
python -m archive.visualizations.mme_vs_overdose_2012_2016
```
