# Archive

Scripts preserved from development. All paths have been updated to use
relative references, so they remain runnable from the project root.

## Archived Visualizations (`archive/visualizations/`)

Non-map chart scripts (Matplotlib). Run via:

```bash
python -m archive.visualizations.<script_name>
```

| Script | Description | Output |
|--------|-------------|--------|
| `heroinVsFentanyl.py` | Heroin vs fentanyl death trends (1999--2018) | `output/plots/heroin_vs_fentanyl.png` |
| `divergence_plot.py` | Rx decline vs overdose death rise | `output/divergence_plot.png` |
| `Medicaid_Timeline.py` | Medicaid Rx volume vs enrollment timeline | `output/plots/medicaid_rx_vs_enrollment_timeline.png` |
| `Medicaid_boxplot.py` | Overdose rates by Medicaid Rx group | `output/plots/boxplot_medicaid_group_overdose.png` |
| `prescriptionsVsOverdose.py` | Binscatter: Rx per capita vs overdose rate | `output/plots/binscatter_rx_per_capita_vs_overdose.png` |
| `mme_vs_overdose_2012_2016.py` | MME vs overdose scatter (national) | `output/plots/mme_vs_overdose_2012_2016.png` |
| `mme_vs_deaths_scatterplot.py` | MME vs deaths by county | `output/plots/mme_vs_deaths_by_county.png` |
| `Binned_Scatter.py` | Binned scatter: MME vs deaths with CI | `output/plots/mme_vs_deaths_binned.png` |

## Archived Analysis (`archive/analysis/`)

Statistical analysis scripts that run on output CSVs:

| Script | Description |
|--------|-------------|
| `deep_analysis.py` | Q1--Q5 + CDC cross-analysis |
| `extended_analysis.py` | Q6/Q7 state x year and channel analysis |
| `bridge_analysis.py` | Integrated findings across all queries |
| `what_happened_2012.py` | 2012 prescribing inflection forensics |
| `analyze.py` | Generic CSV statistical analyzer |
| `check_2018.py` | 2018 data truncation verification |

## Archived Scripts (`archive/scripts/`)

Legacy R and Python prototypes from early development:

- `r/mapView.Rmd`, `r/State_Map.Rmd` -- R choropleth maps
- `r/IQVIA_hookup.R` -- R database connection
- `python/seg_bar_graph_rough.py` -- Stacked bar chart prototype
