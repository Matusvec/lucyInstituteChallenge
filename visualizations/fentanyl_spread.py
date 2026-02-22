"""
Animated US county choropleth: fentanyl (synthetic opioid) death spread over time.

Shows the explosive geographic spread of fentanyl-involved deaths (ICD-10 T40.4)
across US counties from 2008 to 2017.  Fentanyl was negligible before ~2013;
the map shows it emerge in the Northeast and spread rapidly.

Input:
  CDC WONDER county x drug-type files (loaded via cdc.load_wonder_county_drugtype)

Output:
  output/cdc/fentanyl_spread_map.html

Run:
  python -m visualizations.fentanyl_spread
"""

import json
import os
import sys

import pandas as pd
import plotly.express as px

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from cdc.load_wonder_county_drugtype import load_fentanyl_county

BASE = os.path.dirname(os.path.dirname(__file__))
OUT_HTML = os.path.join(BASE, "output", "cdc", "fentanyl_spread_map.html")

GEOJSON_URL = (
    "https://raw.githubusercontent.com/plotly/datasets/master/"
    "geojson-counties-fips.json"
)
GEOJSON_LOCAL = os.path.join(BASE, "Datasets", "geo", "us_counties_geojson.json")
_GEOJSON_FALLBACK = os.path.join(BASE, "Datasets", "us_counties_geojson.json")

# Blue-to-cyan-to-white "cold fire" palette — distinct from the red/orange
# total-overdose map so the two can be compared side by side.
FENTANYL_SCALE = [
    [0.00, "rgb(10, 10, 25)"],
    [0.05, "rgb(15, 20, 70)"],
    [0.12, "rgb(30, 40, 130)"],
    [0.25, "rgb(50, 70, 180)"],
    [0.40, "rgb(20, 120, 200)"],
    [0.55, "rgb(10, 170, 210)"],
    [0.70, "rgb(40, 220, 210)"],
    [0.85, "rgb(140, 250, 230)"],
    [1.00, "rgb(240, 255, 255)"],
]

BG_COLOR = "rgb(10, 10, 25)"


def _load_geojson() -> dict:
    for path in [GEOJSON_LOCAL, _GEOJSON_FALLBACK]:
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)

    from urllib.request import urlopen

    print("  Downloading US county GeoJSON ...")
    with urlopen(GEOJSON_URL) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    os.makedirs(os.path.dirname(GEOJSON_LOCAL), exist_ok=True)
    with open(GEOJSON_LOCAL, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return data


def build_fentanyl_map() -> str:
    """Build the animated fentanyl-spread county choropleth."""

    df = load_fentanyl_county(min_year=2008, max_year=2017)
    df = df[df["overdose_rate_per_100k"].notna()].copy()
    df["year_str"] = df["year"].astype(str)

    if df.empty:
        print("  WARNING: No fentanyl data with rates available.")
        return ""

    rate_cap = float(df["overdose_rate_per_100k"].quantile(0.95))
    print(f"  Color range: 0 - {rate_cap:.1f} deaths per 100K (95th pctile)")

    counties_geojson = _load_geojson()

    fig = px.choropleth(
        df,
        geojson=counties_geojson,
        locations="county_fips",
        color="overdose_rate_per_100k",
        animation_frame="year_str",
        scope="usa",
        color_continuous_scale=FENTANYL_SCALE,
        range_color=(0, rate_cap),
        hover_name="county",
        hover_data={
            "overdose_deaths": ":,.0f",
            "population": ":,.0f",
            "overdose_rate_per_100k": ":.1f",
            "state": True,
            "county_fips": True,
            "year_str": False,
        },
        labels={
            "overdose_rate_per_100k": "Deaths / 100K",
            "overdose_deaths": "Deaths",
            "population": "Population",
            "state": "State",
            "county_fips": "FIPS",
        },
    )

    fig.update_geos(
        bgcolor=BG_COLOR,
        lakecolor=BG_COLOR,
        landcolor="rgb(18, 18, 35)",
        showlakes=True,
        showland=True,
        subunitcolor="rgba(60, 80, 120, 0.25)",
        countrycolor="rgba(60, 80, 120, 0.4)",
    )

    fig.update_layout(
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        font=dict(color="white", family="Arial, sans-serif"),
        title=dict(
            text=(
                "Fentanyl (Synthetic Opioid) Deaths per 100K<br>"
                "<span style='font-size:14px; color:#8af'>"
                "US Counties, 2008-2017  |  ICD-10 T40.4  |  CDC WONDER"
                "</span>"
            ),
            font=dict(size=20, color="white"),
            x=0.5,
            xanchor="center",
        ),
        margin=dict(l=0, r=0, t=80, b=0),
        coloraxis_colorbar=dict(
            title=dict(text="Deaths / 100K", font=dict(color="white")),
            tickfont=dict(color="white"),
            bgcolor="rgba(0,0,0,0)",
            len=0.6,
            x=1.0,
        ),
    )

    for button in fig.layout.updatemenus:
        if button.type == "buttons":
            for b in button.buttons:
                if b.args and len(b.args) > 1 and isinstance(b.args[1], dict):
                    b.args[1]["frame"] = {"duration": 1500, "redraw": True}
                    b.args[1]["transition"] = {"duration": 700, "easing": "cubic-in-out"}

    if fig.layout.sliders and len(fig.layout.sliders) > 0:
        fig.layout.sliders[0].update(
            font=dict(color="white"),
            activebgcolor="rgb(40, 140, 220)",
            bgcolor="rgb(30, 30, 55)",
            bordercolor="rgba(0,0,0,0)",
            tickcolor="white",
        )

    os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
    fig.write_html(OUT_HTML, include_plotlyjs="cdn")
    print(f"  Fentanyl map saved -> {OUT_HTML}")
    return OUT_HTML


if __name__ == "__main__":
    out = build_fentanyl_map()
    if out:
        print(f"\nDone! Open in browser:\n  {out}")
