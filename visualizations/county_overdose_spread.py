"""
Animated US county choropleth: drug-overdose death rate spreading over time.

Dark-themed heat map that shows overdose hotspots emerging and intensifying
across ~3,100 US counties from 2008 to 2017.

Input:
  CDC WONDER county-level overdose CSV (loaded via cdc.load_wonder_county)

Output:
  output/cdc/county_overdose_spread_map.html

Run:
  python -m visualizations.county_overdose_spread
"""

import json
import os
import sys

import pandas as pd
import plotly.express as px

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from cdc.load_wonder_county import load_county_overdose_2008_2017

BASE = os.path.dirname(os.path.dirname(__file__))
OUT_HTML = os.path.join(BASE, "output", "cdc", "county_overdose_spread_map.html")

GEOJSON_URL = (
    "https://raw.githubusercontent.com/plotly/datasets/master/"
    "geojson-counties-fips.json"
)
GEOJSON_LOCAL = os.path.join(BASE, "Datasets", "us_counties_geojson.json")

# Dark-to-hot color scale: low rates blend into the dark background,
# high rates glow bright orange/yellow.
HEAT_SCALE = [
    [0.00, "rgb(15, 15, 35)"],
    [0.04, "rgb(50, 10, 60)"],
    [0.12, "rgb(100, 15, 55)"],
    [0.25, "rgb(160, 25, 40)"],
    [0.40, "rgb(200, 55, 25)"],
    [0.55, "rgb(225, 95, 15)"],
    [0.70, "rgb(245, 145, 10)"],
    [0.85, "rgb(255, 200, 30)"],
    [1.00, "rgb(255, 255, 110)"],
]

BG_COLOR = "rgb(15, 15, 35)"


def _load_geojson() -> dict:
    """Download the simplified US county GeoJSON (or load from cache)."""
    if os.path.exists(GEOJSON_LOCAL):
        print(f"  Loading cached county GeoJSON: {GEOJSON_LOCAL}")
        with open(GEOJSON_LOCAL, encoding="utf-8") as f:
            return json.load(f)

    print("  Downloading US county GeoJSON from GitHub ...")
    from urllib.request import urlopen

    with urlopen(GEOJSON_URL) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    os.makedirs(os.path.dirname(GEOJSON_LOCAL), exist_ok=True)
    with open(GEOJSON_LOCAL, "w", encoding="utf-8") as f:
        json.dump(data, f)
    print(f"  Cached -> {GEOJSON_LOCAL}")
    return data


def build_county_map() -> str:
    """Build the animated county-level overdose choropleth and save as HTML."""

    # ── Load data ──
    df = load_county_overdose_2008_2017()

    # Only keep rows where we have a rate to display
    df = df[df["overdose_rate_per_100k"].notna()].copy()
    df["year_str"] = df["year"].astype(str)

    # Cap the color range at the 98th percentile to prevent outliers
    # from washing out the rest of the map
    rate_cap = float(df["overdose_rate_per_100k"].quantile(0.98))
    print(f"  Color range: 0 - {rate_cap:.1f} deaths per 100K (98th pctile)")

    counties_geojson = _load_geojson()

    # ── Build figure ──
    fig = px.choropleth(
        df,
        geojson=counties_geojson,
        locations="county_fips",
        color="overdose_rate_per_100k",
        animation_frame="year_str",
        scope="usa",
        color_continuous_scale=HEAT_SCALE,
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

    # ── Dark theme styling ──
    fig.update_geos(
        bgcolor=BG_COLOR,
        lakecolor=BG_COLOR,
        landcolor="rgb(25, 25, 45)",
        showlakes=True,
        showland=True,
        subunitcolor="rgba(100, 110, 140, 0.25)",
        countrycolor="rgba(100, 110, 140, 0.4)",
    )

    fig.update_layout(
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        font=dict(color="white", family="Arial, sans-serif"),
        title=dict(
            text=(
                "Drug Overdose Deaths per 100K Population<br>"
                "<span style='font-size:14px; color:#aaa'>"
                "US Counties, 2008-2017  |  CDC WONDER  |  "
                "Grey = suppressed (&lt;10 deaths)"
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

    # ── Smooth animation: 1.5s per frame, 0.7s crossfade ──
    for button in fig.layout.updatemenus:
        if button.type == "buttons":
            for b in button.buttons:
                if b.args and len(b.args) > 1 and isinstance(b.args[1], dict):
                    b.args[1]["frame"] = {"duration": 1500, "redraw": True}
                    b.args[1]["transition"] = {"duration": 700, "easing": "cubic-in-out"}

    # Style the slider
    if fig.layout.sliders and len(fig.layout.sliders) > 0:
        fig.layout.sliders[0].update(
            font=dict(color="white"),
            activebgcolor="rgb(200, 80, 30)",
            bgcolor="rgb(40, 40, 60)",
            bordercolor="rgba(0,0,0,0)",
            tickcolor="white",
        )

    os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
    fig.write_html(OUT_HTML, include_plotlyjs="cdn")
    print(f"  Map saved -> {OUT_HTML}")
    return OUT_HTML


if __name__ == "__main__":
    out = build_county_map()
    print(f"\nDone! Open in browser:\n  {out}")
