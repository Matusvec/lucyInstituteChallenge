"""
Animated US county choropleth: fentanyl (synthetic opioid) death spread over time.

Shows the explosive geographic spread of fentanyl-involved deaths (ICD-10 T40.4)
across US counties from 2008 to 2017.  Fentanyl was negligible before ~2013;
the map shows it emerge in the Northeast and spread rapidly.

Years are sequential; later years (exponential growth) get longer frame duration.

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
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from cdc.load_wonder_county_drugtype import load_fentanyl_county
from visualizations.theme import BG_COLOR, SCALE_FENTANYL

BASE = os.path.dirname(os.path.dirname(__file__))
OUT_HTML = os.path.join(BASE, "output", "cdc", "fentanyl_spread_map.html")

GEOJSON_URL = (
    "https://raw.githubusercontent.com/plotly/datasets/master/"
    "geojson-counties-fips.json"
)
GEOJSON_LOCAL = os.path.join(BASE, "Datasets", "geo", "us_counties_geojson.json")
_GEOJSON_FALLBACK = os.path.join(BASE, "Datasets", "us_counties_geojson.json")


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
    df = df.sort_values("year").reset_index(drop=True)

    if df.empty:
        print("  WARNING: No fentanyl data with rates available.")
        return ""

    rate_cap = float(df["overdose_rate_per_100k"].quantile(0.95))
    print(f"  Color range: 0 - {rate_cap:.1f} deaths per 100K (95th pctile)")

    counties_geojson = _load_geojson()
    years = sorted(df["year"].dropna().unique().tolist())

    years_extended = years

    frames = []
    for yr in years_extended:
        yr_df = df[df["year"] == yr].copy()
        if yr_df.empty:
            continue
        yr_df = yr_df[yr_df["county_fips"].notna()].copy()
        hover_lines = []
        for _, r in yr_df.iterrows():
            parts = [f"<b>{r['county']}</b>", f"Year: {int(yr)}"]
            if pd.notna(r.get("overdose_deaths")):
                parts.append(f"Deaths: {int(r['overdose_deaths']):,}")
            if pd.notna(r.get("population")):
                parts.append(f"Population: {int(r['population']):,}")
            parts.append(f"Rate: {r['overdose_rate_per_100k']:.1f} / 100K")
            hover_lines.append("<br>".join(parts))
        frames.append(go.Frame(
            data=[go.Choropleth(
                geojson=counties_geojson,
                locations=yr_df["county_fips"],
                z=yr_df["overdose_rate_per_100k"].fillna(0),
                customdata=hover_lines,
                hovertemplate="%{customdata}<extra></extra>",
                colorscale=SCALE_FENTANYL,
                zmin=0,
                zmax=rate_cap,
                marker_line_width=0,
                colorbar=dict(title="Deaths / 100K", tickfont=dict(color="white"), len=0.6),
            )],
            name=str(int(yr)),
        ))

    init = frames[0].data[0]
    fig = go.Figure(data=[init], frames=frames)

    fig.update_geos(
        scope="usa",
        bgcolor=BG_COLOR,
        lakecolor=BG_COLOR,
        landcolor="rgb(20, 45, 70)",
        showlakes=True,
        showland=True,
        subunitcolor="rgba(59, 94, 140, 0.25)",
        countrycolor="rgba(59, 94, 140, 0.4)",
    )

    # Slider steps: one per frame, sequential years 2008-2017
    all_steps = []
    for i, yr in enumerate(years_extended):
        all_steps.append(dict(
            args=[[frames[i].name], {"frame": {"duration": 300, "redraw": True}, "mode": "immediate"}],
            label=str(int(yr)),
            method="animate",
        ))

    fig.update_layout(
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        font=dict(color="white", family="Arial, sans-serif"),
        title=dict(
            text=(
                "Fentanyl (Synthetic Opioid) Deaths per 100K<br>"
                "<span style='font-size:14px; color:#4EAE81'>"
                "US Counties, 2008-2017  |  ICD-10 T40.4  |  CDC WONDER"
                "</span>"
            ),
            font=dict(size=20, color="white"),
            x=0.5,
            xanchor="center",
        ),
        margin=dict(l=0, r=0, t=80, b=0),
        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                x=0.05,
                y=0.05,
                xanchor="right",
                yanchor="top",
                buttons=[
                    dict(
                        label="Play",
                        method="animate",
                        args=[None, {"frame": {"duration": 1000, "redraw": True}, "transition": {"duration": 600, "easing": "cubic-in-out"}, "fromcurrent": True}],
                    ),
                    dict(label="Pause", method="animate", args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}]),
                ],
                font=dict(color="white"),
                bgcolor="rgba(27,59,44,0.9)",
                bordercolor="rgba(78,174,129,0.5)",
            ),
        ],
        sliders=[dict(
            active=0,
            steps=all_steps,
            x=0.1,
            len=0.8,
            xanchor="left",
            y=0,
            yanchor="top",
            currentvalue=dict(prefix="Year: ", visible=True, font=dict(color="white", size=14), xanchor="center"),
            font=dict(color="white"),
            activebgcolor="rgb(191, 161, 93)",
            bgcolor="rgb(59, 94, 140)",
            bordercolor="rgba(0,0,0,0)",
            tickcolor="white",
        )],
    )

    os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
    fig.write_html(OUT_HTML, include_plotlyjs="cdn")
    print(f"  Fentanyl map saved -> {OUT_HTML}")
    return OUT_HTML


if __name__ == "__main__":
    out = build_fentanyl_map()
    if out:
        print(f"\nDone! Open in browser:\n  {out}")
