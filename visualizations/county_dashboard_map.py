"""
Comprehensive county dashboard map: IQVIA prescriptions + CDC overdose deaths.

Animated by year (2008-2017) with dropdown to switch between metrics:
  - Overdose death rate per 100K
  - Prescriptions per 1,000 population
  - Average MME per unit
  - Medicaid % of prescriptions
  - Fentanyl death rate per 100K

Hovering over any county shows ALL available data at once.

Input:
  Merged IQVIA + CDC county panel (built inline from source data)

Output:
  output/county/county_dashboard_map.html

Run:
  python -m visualizations.county_dashboard_map
"""

import json
import os
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from cdc.merge_iqvia_cdc_county import merge_county_panel

BASE = os.path.dirname(os.path.dirname(__file__))
OUT_HTML = os.path.join(BASE, "output", "county", "county_dashboard_map.html")

GEOJSON_LOCAL = os.path.join(BASE, "Datasets", "geo", "us_counties_geojson.json")
_GEOJSON_FALLBACK = os.path.join(BASE, "Datasets", "us_counties_geojson.json")
GEOJSON_URL = (
    "https://raw.githubusercontent.com/plotly/datasets/master/"
    "geojson-counties-fips.json"
)

BG_COLOR = "rgb(15, 15, 35)"

METRICS = {
    "overdose_rate_per_100k": {
        "label": "Overdose Death Rate (per 100K)",
        "short": "Deaths/100K",
        "scale": [
            [0.00, "rgb(15,15,35)"], [0.05, "rgb(50,10,60)"],
            [0.15, "rgb(100,15,55)"], [0.30, "rgb(160,25,40)"],
            [0.50, "rgb(210,55,25)"], [0.70, "rgb(240,120,10)"],
            [0.85, "rgb(255,200,30)"], [1.00, "rgb(255,255,110)"],
        ],
        "pctile": 0.98,
    },
    "rx_per_capita": {
        "label": "Opioid Rx per 1,000 Population",
        "short": "Rx/1K pop",
        "scale": [
            [0.00, "rgb(15,15,35)"], [0.05, "rgb(10,30,60)"],
            [0.15, "rgb(20,60,100)"], [0.30, "rgb(30,100,140)"],
            [0.50, "rgb(40,150,160)"], [0.70, "rgb(80,200,170)"],
            [0.85, "rgb(160,240,180)"], [1.00, "rgb(240,255,220)"],
        ],
        "pctile": 0.98,
    },
    "avg_mme_per_unit": {
        "label": "Average MME per Prescription Unit",
        "short": "Avg MME",
        "scale": [
            [0.00, "rgb(15,15,35)"], [0.05, "rgb(40,10,50)"],
            [0.15, "rgb(80,20,80)"], [0.30, "rgb(130,30,100)"],
            [0.50, "rgb(180,40,100)"], [0.70, "rgb(220,70,80)"],
            [0.85, "rgb(250,130,60)"], [1.00, "rgb(255,220,100)"],
        ],
        "pctile": 0.98,
    },
    "pct_medicaid": {
        "label": "Medicaid % of Opioid Prescriptions",
        "short": "Medicaid %",
        "scale": [
            [0.00, "rgb(15,15,35)"], [0.05, "rgb(10,25,55)"],
            [0.15, "rgb(20,50,100)"], [0.30, "rgb(30,80,160)"],
            [0.50, "rgb(50,120,200)"], [0.70, "rgb(90,170,230)"],
            [0.85, "rgb(150,210,250)"], [1.00, "rgb(230,245,255)"],
        ],
        "pctile": 0.98,
    },
}


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


def _build_hover_text(df: pd.DataFrame) -> pd.Series:
    """Rich hover text showing all key metrics for each county-year."""
    lines = []
    for _, r in df.iterrows():
        parts = [f"<b>{r.get('county', '?')}</b>"]
        parts.append(f"Year: {int(r['year'])}")
        parts.append("─── Overdose Deaths ───")

        deaths = r.get("overdose_deaths")
        if pd.notna(deaths):
            parts.append(f"Deaths: {int(deaths):,}")
            parts.append(f"Rate: {r.get('overdose_rate_per_100k', 0):.1f} / 100K")
        else:
            parts.append("Deaths: suppressed (<10)")

        pop = r.get("population")
        if pd.notna(pop):
            parts.append(f"Population: {int(pop):,}")

        fent = r.get("fentanyl_deaths")
        heroin = r.get("heroin_deaths")
        if pd.notna(fent) or pd.notna(heroin):
            parts.append("─── By Drug Type ───")
            if pd.notna(fent):
                parts.append(f"Fentanyl: {int(fent):,}")
            if pd.notna(heroin):
                parts.append(f"Heroin: {int(heroin):,}")
            rx_d = r.get("rx_opioid_deaths")
            if pd.notna(rx_d):
                parts.append(f"Rx Opioids: {int(rx_d):,}")

        rx = r.get("total_rx")
        if pd.notna(rx) and rx > 0:
            parts.append("─── IQVIA Prescriptions ───")
            parts.append(f"Total Rx: {rx:,.0f}")
            rpc = r.get("rx_per_capita")
            if pd.notna(rpc):
                parts.append(f"Rx per 1K pop: {rpc:.1f}")
            mme = r.get("avg_mme_per_unit")
            if pd.notna(mme):
                parts.append(f"Avg MME: {mme:.1f}")
            pct = r.get("pct_medicaid")
            if pd.notna(pct):
                parts.append(f"Medicaid: {pct:.1f}%")
            nrr = r.get("new_rx_ratio")
            if pd.notna(nrr):
                parts.append(f"New Rx ratio: {nrr:.1f}%")

        lines.append("<br>".join(parts))
    return pd.Series(lines, index=df.index)


def build_dashboard_map() -> str:
    """Build the multi-metric animated county map."""

    panel = merge_county_panel()

    # Compute fentanyl rate where data exists
    if "fentanyl_deaths" in panel.columns:
        panel["fentanyl_rate_per_100k"] = np.where(
            panel["population"].notna() & (panel["population"] > 0)
            & panel["fentanyl_deaths"].notna(),
            panel["fentanyl_deaths"] / panel["population"] * 100_000,
            np.nan,
        )

    counties_geojson = _load_geojson()
    years = sorted(panel["year"].dropna().unique())

    # Default metric
    default_metric = "overdose_rate_per_100k"
    mcfg = METRICS[default_metric]
    cap = float(panel[default_metric].quantile(mcfg["pctile"]))

    print(f"  Building map for {len(years)} years, {panel['county_fips'].nunique():,} counties...")
    print(f"  Default metric: {mcfg['label']} (cap={cap:.1f})")

    # ── Build frames ──
    frames = []
    for yr in years:
        yr_df = panel[panel["year"] == yr].copy()
        yr_df = yr_df[yr_df["county_fips"].notna()].copy()
        yr_df["hover_text"] = _build_hover_text(yr_df)

        frames.append(go.Frame(
            data=[go.Choropleth(
                geojson=counties_geojson,
                locations=yr_df["county_fips"],
                z=yr_df[default_metric].fillna(0),
                customdata=yr_df["hover_text"],
                colorscale=mcfg["scale"],
                zmin=0, zmax=cap,
                marker_line_width=0,
                hovertemplate="%{customdata}<extra></extra>",
                colorbar=dict(
                    title=mcfg["short"],
                    tickfont=dict(color="white"),
                    titlefont=dict(color="white"),
                    len=0.6,
                ),
            )],
            name=str(int(yr)),
        ))

    # ── Initial trace (first year) ──
    init = frames[0].data[0]

    fig = go.Figure(data=[init], frames=frames)

    # ── Geo styling ──
    fig.update_geos(
        scope="usa",
        bgcolor=BG_COLOR,
        lakecolor=BG_COLOR,
        landcolor="rgb(25,25,45)",
        showlakes=True, showland=True,
        subunitcolor="rgba(100,110,140,0.25)",
        countrycolor="rgba(100,110,140,0.4)",
    )

    # ── Metric-switch buttons ──
    metric_buttons = []
    for key, cfg in METRICS.items():
        metric_cap = float(panel[key].quantile(cfg["pctile"]))
        metric_buttons.append(dict(
            label=cfg["short"],
            method="restyle",
            args=[{
                "colorscale": [cfg["scale"]],
                "zmin": 0,
                "zmax": metric_cap,
                "colorbar.title.text": cfg["short"],
            }],
        ))

    # ── Layout ──
    fig.update_layout(
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        font=dict(color="white", family="Arial, sans-serif"),
        title=dict(
            text=(
                "County Opioid Dashboard: Prescriptions + Overdose Deaths<br>"
                "<span style='font-size:13px; color:#aaa'>"
                "2008-2017 | IQVIA + CDC WONDER | "
                "Hover for full detail | Use buttons to switch metric"
                "</span>"
            ),
            font=dict(size=18, color="white"),
            x=0.5, xanchor="center",
        ),
        margin=dict(l=0, r=0, t=90, b=0),
        updatemenus=[
            # Play / Pause button
            dict(
                type="buttons",
                showactive=False,
                x=0.05, y=0.05,
                xanchor="right", yanchor="top",
                buttons=[
                    dict(label="Play",
                         method="animate",
                         args=[None, {
                             "frame": {"duration": 1500, "redraw": True},
                             "transition": {"duration": 700, "easing": "cubic-in-out"},
                             "fromcurrent": True,
                         }]),
                    dict(label="Pause",
                         method="animate",
                         args=[[None], {
                             "frame": {"duration": 0, "redraw": False},
                             "mode": "immediate",
                         }]),
                ],
                font=dict(color="white"),
                bgcolor="rgba(40,40,60,0.8)",
                bordercolor="rgba(100,110,140,0.4)",
            ),
            # Metric switcher
            dict(
                type="buttons",
                direction="right",
                showactive=True,
                x=0.5, y=1.06,
                xanchor="center", yanchor="bottom",
                buttons=metric_buttons,
                font=dict(color="white", size=11),
                bgcolor="rgba(40,40,60,0.8)",
                bordercolor="rgba(100,110,140,0.4)",
                active=0,
            ),
        ],
        sliders=[dict(
            active=0,
            steps=[
                dict(args=[[str(int(yr))],
                           {"frame": {"duration": 300, "redraw": True},
                            "mode": "immediate"}],
                     label=str(int(yr)),
                     method="animate")
                for yr in years
            ],
            x=0.1, len=0.8,
            xanchor="left",
            y=0, yanchor="top",
            currentvalue=dict(
                prefix="Year: ",
                visible=True,
                font=dict(color="white", size=14),
                xanchor="center",
            ),
            font=dict(color="white"),
            activebgcolor="rgb(200,80,30)",
            bgcolor="rgb(40,40,60)",
            bordercolor="rgba(0,0,0,0)",
            tickcolor="white",
        )],
    )

    os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
    fig.write_html(OUT_HTML, include_plotlyjs="cdn")
    print(f"  Dashboard map saved -> {OUT_HTML}")
    return OUT_HTML


if __name__ == "__main__":
    out = build_dashboard_map()
    if out:
        print(f"\nDone! Open in browser:\n  {out}")
