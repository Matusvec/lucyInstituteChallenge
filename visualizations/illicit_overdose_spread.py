"""
Animated US choropleth: illicit-overdose spread over time.

Input:
  output/cdc/cdc_illicit_overdose_by_state_year.csv

Output:
  output/cdc/illicit_overdose_spread_map.html

Run:
  python -m visualizations.illicit_overdose_spread
"""

import os
import sys
import pandas as pd
import plotly.express as px

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from visualizations.theme import SCALE_OVERDOSE

BASE = os.path.dirname(os.path.dirname(__file__))
IN_CSV = os.path.join(BASE, "output", "cdc", "cdc_illicit_overdose_by_state_year.csv")
OUT_HTML = os.path.join(BASE, "output", "cdc", "illicit_overdose_spread_map.html")

STATE_FIPS_TO_ABBR = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT", "10": "DE",
    "11": "DC", "12": "FL", "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN", "19": "IA",
    "20": "KS", "21": "KY", "22": "LA", "23": "ME", "24": "MD", "25": "MA", "26": "MI", "27": "MN",
    "28": "MS", "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH", "34": "NJ", "35": "NM",
    "36": "NY", "37": "NC", "38": "ND", "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI",
    "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA",
    "54": "WV", "55": "WI", "56": "WY",
}


def build_map() -> str:
    if not os.path.exists(IN_CSV):
        raise FileNotFoundError(
            f"Missing input CSV: {IN_CSV}\n"
            "Run CDC drug-type pipeline first (python main.py cdc-drug)."
        )

    df = pd.read_csv(IN_CSV)
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["year", "state_code", "illicit_overdose_rate_per_100k"]).copy()
    df = df.sort_values("year").reset_index(drop=True)

    df["state_code"] = df["state_code"].astype(str).str.zfill(2)
    df["state_abbr"] = df["state_code"].map(STATE_FIPS_TO_ABBR)
    df = df[df["state_abbr"].notna()].copy()
    df["year_str"] = df["year"].astype(str)

    year_order = [str(y) for y in sorted(df["year"].unique())]
    fig = px.choropleth(
        df,
        locations="state_abbr",
        locationmode="USA-states",
        color="illicit_overdose_rate_per_100k",
        animation_frame="year_str",
        scope="usa",
        color_continuous_scale=SCALE_OVERDOSE,
        range_color=(0, float(df["illicit_overdose_rate_per_100k"].quantile(0.98))),
        hover_data={
            "state": True,
            "illicit_overdose_deaths": ":,.0f",
            "illicit_overdose_rate_per_100k": ":.2f",
            "illicit_category_count": True,
            "state_abbr": False,
            "year_str": False,
        },
        title="Illicit-Proxy Overdose Death Rate by State Over Time",
        labels={"illicit_overdose_rate_per_100k": "Deaths per 100K"},
        category_orders={"year_str": year_order},
    )

    fig.update_layout(
        paper_bgcolor="rgb(12, 35, 64)",
        plot_bgcolor="rgb(12, 35, 64)",
        font=dict(color="white", family="Arial, sans-serif"),
        margin=dict(l=5, r=5, t=60, b=5),
        coloraxis_colorbar=dict(
            title="Deaths / 100K",
            tickfont=dict(color="white"),
        ),
    )
    fig.update_geos(
        bgcolor="rgb(12, 35, 64)",
        lakecolor="rgb(12, 35, 64)",
        landcolor="rgb(20, 45, 70)",
        subunitcolor="rgba(59, 94, 140, 0.25)",
        countrycolor="rgba(59, 94, 140, 0.4)",
    )

    fig.write_html(OUT_HTML, include_plotlyjs="cdn")
    return OUT_HTML


if __name__ == "__main__":
    out = build_map()
    print(f"✅ Wrote animated map: {out}")