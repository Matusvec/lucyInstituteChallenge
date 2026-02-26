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
  output/county/iqvia_cdc_county_merged.csv (cached; created on first run or when missing)

Output:
  output/county/county_dashboard_map.html

Run:
  python -m visualizations.county_dashboard_map

  Add --force-merge to re-merge data (e.g. after updating source CSVs).
"""

import json
import os
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from cdc.merge_iqvia_cdc_county import load_county_panel
from visualizations.theme import (
    BG_COLOR,
    SCALE_OVERDOSE,
    SCALE_RX,
    SCALE_MME,
    SCALE_MEDICAID,
)

BASE = os.path.dirname(os.path.dirname(__file__))
OUT_HTML = os.path.join(BASE, "output", "county", "county_dashboard_map.html")

GEOJSON_LOCAL = os.path.join(BASE, "Datasets", "geo", "us_counties_geojson.json")
_GEOJSON_FALLBACK = os.path.join(BASE, "Datasets", "us_counties_geojson.json")
GEOJSON_URL = (
    "https://raw.githubusercontent.com/plotly/datasets/master/"
    "geojson-counties-fips.json"
)

METRICS = {
    "overdose_rate_per_100k": {
        "label": "Overdose Death Rate (per 100K)",
        "short": "Deaths/100K",
        "scale": SCALE_OVERDOSE,
        "pctile": 0.98,
    },
    "rx_per_capita": {
        "label": "Opioid Rx per 1,000 Population",
        "short": "Rx/1K pop",
        "scale": SCALE_RX,
        "pctile": 0.98,
    },
    "avg_mme_per_unit": {
        "label": "Average MME per Prescription Unit",
        "short": "Avg MME",
        "scale": SCALE_MME,
        "pctile": 0.98,
    },
    "pct_medicaid": {
        "label": "Medicaid % of Opioid Prescriptions",
        "short": "Medicaid %",
        "scale": SCALE_MEDICAID,
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


def build_dashboard_map(force_merge: bool = False) -> str:
    """Build the multi-metric animated county map."""

    panel = load_county_panel(force_merge=force_merge)

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
        landcolor="rgb(20,45,70)",
        showlakes=True, showland=True,
        subunitcolor="rgba(59,94,140,0.25)",
        countrycolor="rgba(59,94,140,0.4)",
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
        margin=dict(l=120, r=0, t=90, b=0),
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
                bgcolor="rgba(27,59,44,0.9)",
                bordercolor="rgba(78,174,129,0.5)",
            ),
            # Metric switcher (left side to avoid covering title and legend)
            dict(
                type="buttons",
                direction="down",
                showactive=True,
                x=-0.02, y=0.5,
                xanchor="right", yanchor="middle",
                buttons=metric_buttons,
                font=dict(color="black", size=11),
                bgcolor="rgba(255,255,255,0.95)",
                bordercolor="rgba(100,100,100,0.5)",
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
            activebgcolor="rgb(191,161,93)",
            bgcolor="rgb(59,94,140)",
            bordercolor="rgba(0,0,0,0)",
            tickcolor="white",
        )],
    )

    os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
    fig.write_html(OUT_HTML, include_plotlyjs="cdn")
    print(f"  Dashboard map saved -> {OUT_HTML}")
    return OUT_HTML


if __name__ == "__main__":
    import sys
    force = "--force-merge" in sys.argv
    out = build_dashboard_map(force_merge=force)
    if out:
        print(f"\nDone! Open in browser:\n  {out}")
