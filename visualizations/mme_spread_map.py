"""
MME Spread Map — Geographic distribution of opioid MME across IQVIA counties.

Shows avg_mme_per_unit (qty-weighted morphine milligram equivalents per prescription unit)
as a choropleth map. Animated by year (2008-2017).

Input:
  output/county/iqvia_cdc_county_merged.csv (or iqvia_county_year_panel.csv)

Output:
  output/plots/mme_spread_map.html

Run:
  python -m visualizations.mme_spread_map
"""

import json
import os
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from cdc.merge_iqvia_cdc_county import load_county_panel
from queries.mme_spread import load_mme_data, mme_spread_summary, print_mme_summary
from visualizations.theme import BG_COLOR, SCALE_MME

BASE = os.path.dirname(os.path.dirname(__file__))
OUT_HTML = os.path.join(BASE, "output", "plots", "mme_spread_map.html")
GEOJSON_LOCAL = os.path.join(BASE, "Datasets", "geo", "us_counties_geojson.json")
_GEOJSON_FALLBACK = os.path.join(BASE, "Datasets", "us_counties_geojson.json")
GEOJSON_URL = (
    "https://raw.githubusercontent.com/plotly/datasets/master/"
    "geojson-counties-fips.json"
)


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


def build_mme_spread_map(force_merge: bool = False) -> str:
    """Build animated MME spread choropleth map by county."""

    # Load county panel (merged or IQVIA-only)
    try:
        panel = load_county_panel(force_merge=force_merge)
    except FileNotFoundError:
        panel = load_mme_data()

    if "avg_mme_per_unit" not in panel.columns:
        raise ValueError("Panel missing avg_mme_per_unit column")

    # Print 5-number summary and range
    summary = mme_spread_summary(panel)
    print_mme_summary(summary)

    counties_geojson = _load_geojson()
    years = sorted(panel["year"].dropna().unique())
    mme = panel["avg_mme_per_unit"]
    cap = float(mme.quantile(0.98))

    print(f"  Building MME spread map: {len(years)} years, "
          f"{panel['county_fips'].nunique():,} counties (cap={cap:.1f})")

    # Build frames
    frames = []
    for yr in years:
        yr_df = panel[panel["year"] == yr].copy()
        yr_df = yr_df[yr_df["county_fips"].notna()].copy()
        county_label = yr_df["county"] if "county" in yr_df.columns else yr_df["county_fips"]
        yr_df["hover_text"] = (
            "<b>" + county_label.astype(str) + "</b><br>"
            "Year: " + yr_df["year"].astype(int).astype(str) + "<br>"
            "Avg MME: " + yr_df["avg_mme_per_unit"].round(1).astype(str) + "<br>"
            "Total Rx: " + yr_df["total_rx"].fillna(0).apply(lambda x: f"{x:,.0f}")
        )

        frames.append(go.Frame(
            data=[go.Choropleth(
                geojson=counties_geojson,
                locations=yr_df["county_fips"],
                z=yr_df["avg_mme_per_unit"].fillna(0),
                customdata=yr_df["hover_text"],
                colorscale=SCALE_MME,
                zmin=0,
                zmax=cap,
                marker_line_width=0,
                hovertemplate="%{customdata}<extra></extra>",
                colorbar=dict(
                    title="Avg MME",
                    tickfont=dict(color="white"),
                    len=0.6,
                ),
            )],
            name=str(int(yr)),
        ))

    fig = go.Figure(data=[frames[0].data[0]], frames=frames)

    fig.update_geos(
        scope="usa",
        bgcolor=BG_COLOR,
        lakecolor=BG_COLOR,
        landcolor="rgb(20,45,70)",
        showlakes=True,
        showland=True,
        subunitcolor="rgba(59,94,140,0.25)",
        countrycolor="rgba(59,94,140,0.4)",
    )

    fn = summary["five_number"]
    fig.update_layout(
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        font=dict(color="white", family="Arial, sans-serif"),
        title=dict(
            text=(
                "MME Spread Across IQVIA Counties<br>"
                "<span style='font-size:13px; color:#aaa'>"
                f"5-number summary: min={fn['min']:.1f} | Q1={fn['q1']:.1f} | "
                f"median={fn['median']:.1f} | Q3={fn['q3']:.1f} | max={fn['max']:.1f} | "
                f"range={summary['range']:.1f}"
                "</span>"
            ),
            font=dict(size=18, color="white"),
            x=0.5,
            xanchor="center",
        ),
        margin=dict(l=0, r=0, t=100, b=0),
        sliders=[dict(
            active=0,
            steps=[
                dict(
                    args=[[str(int(yr))], {"frame": {"duration": 300, "redraw": True}, "mode": "immediate"}],
                    label=str(int(yr)),
                    method="animate",
                )
                for yr in years
            ],
            x=0.1,
            len=0.8,
            xanchor="left",
            y=0,
            yanchor="top",
            currentvalue=dict(
                prefix="Year: ",
                visible=True,
                font=dict(color="white", size=14),
                xanchor="center",
            ),
            font=dict(color="white"),
            activebgcolor="rgb(191,161,93)",
            bgcolor="rgb(59,94,140)",
            bordercolor="rgba(0,0,0,0)",
            tickcolor="white",
        )],
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
                        args=[None, {
                            "frame": {"duration": 1500, "redraw": True},
                            "transition": {"duration": 700, "easing": "cubic-in-out"},
                            "fromcurrent": True,
                        }],
                    ),
                    dict(
                        label="Pause",
                        method="animate",
                        args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}],
                    ),
                ],
                font=dict(color="white"),
                bgcolor="rgba(27,59,44,0.9)",
                bordercolor="rgba(78,174,129,0.5)",
            ),
        ],
    )

    os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
    fig.write_html(OUT_HTML, include_plotlyjs="cdn")
    print(f"  MME spread map saved -> {OUT_HTML}")
    return OUT_HTML


if __name__ == "__main__":
    force = "--force-merge" in sys.argv
    out = build_mme_spread_map(force_merge=force)
    if out:
        print(f"\nDone! Open in browser:\n  {out}")
