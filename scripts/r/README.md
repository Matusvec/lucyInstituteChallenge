# R Scripts (Optional)

These R scripts are **optional** and not part of the main Python pipeline.

| File | Purpose |
|------|---------|
| `mapView.Rmd` | Interactive map: Medicaid vs Non-Medicaid opioid Rx by state |
| `mapView.R` | R script version (legacy paths) |
| `State_Map.Rmd` | Same map, alternate version (uses `Datasets/shapefiles/`) |
| `State_Map_legacy.Rmd` | Legacy version (uses `Shape Files/`) |
| `IQVIA_hookup.R` | Connect to IQVIA PostgreSQL database from R |
| `IQVIA_hookup_legacy.R` | Legacy copy (same content) |

**Requirements:** R with `pacman`, `DBI`, `RPostgres`, `sf`, `mapview`, `leaflet`, `leafsync`

**Run from project root** (shapefiles: `Datasets/shapefiles/cb_2018_us_state_20m/`):

```r
# Render R Markdown
rmarkdown::render("scripts/r/mapView.Rmd")

# Or source the DB connection script
source("scripts/r/IQVIA_hookup.R")
```

**Data dependency:** `python main.py extended` (or `python main.py q6`) must be run first to generate `output/extended/medicaid_vs_nonmedicaid_by_state_year.csv`.
