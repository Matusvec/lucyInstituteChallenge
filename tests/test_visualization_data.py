"""
Comprehensive data verification for all visualizations.

Verifies that map/chart data matches source data and formulas are correct.
Run: python -m tests.test_visualization_data
"""
import os
import sys

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)


def test_illicit_overdose():
    """Verify illicit overdose map data."""
    print("\n" + "=" * 60)
    print("TEST: Illicit Overdose Spread Map")
    print("=" * 60)

    path = os.path.join(BASE, "output", "cdc", "cdc_illicit_overdose_by_state_year.csv")
    if not os.path.exists(path):
        print("  SKIP: CSV not found (run python main.py cdc-drug)")
        return

    df = pd.read_csv(path)
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["illicit_overdose_deaths"] = pd.to_numeric(df["illicit_overdose_deaths"], errors="coerce")
    df["population"] = pd.to_numeric(df["population"], errors="coerce")

    # Verify rate formula: deaths / population * 100000
    df["rate_check"] = (df["illicit_overdose_deaths"] / df["population"] * 100_000).round(3)
    df["rate_match"] = np.isclose(
        df["illicit_overdose_rate_per_100k"].fillna(0),
        df["rate_check"].fillna(0),
        rtol=1e-3,
    )
    mismatches = df[~df["rate_match"] & df["illicit_overdose_rate_per_100k"].notna()]
    if len(mismatches) > 0:
        print(f"  FAIL: {len(mismatches)} rows have rate mismatch")
        print(mismatches.head(5).to_string())
    else:
        print("  PASS: illicit_overdose_rate_per_100k = deaths/pop*100000")

    # Spot check: CA 2017
    ca17 = df[(df["state"] == "California") & (df["year"] == 2017)]
    if not ca17.empty:
        r = ca17.iloc[0]
        expected = r["illicit_overdose_deaths"] / r["population"] * 100_000
        print(f"  Spot check CA 2017: rate={r['illicit_overdose_rate_per_100k']:.2f}, "
              f"expected={expected:.2f}, match={np.isclose(r['illicit_overdose_rate_per_100k'], expected)}")


def test_county_overdose():
    """Verify county overdose map data."""
    print("\n" + "=" * 60)
    print("TEST: County Overdose Spread Map")
    print("=" * 60)

    import io
    import contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        from cdc.load_wonder_county import load_county_overdose_2008_2017
        df = load_county_overdose_2008_2017()
    df = df[df["overdose_rate_per_100k"].notna()].copy()

    # Verify rate: deaths / population * 100000
    df["rate_check"] = (df["overdose_deaths"] / df["population"] * 100_000).round(3)
    checkable = df[df["rate_check"].notna() & df["overdose_rate_per_100k"].notna()]
    checkable = checkable.copy()
    checkable["rate_match"] = np.isclose(
        checkable["overdose_rate_per_100k"].astype(float),
        checkable["rate_check"],
        rtol=1e-2,
    )
    mismatches = checkable[~checkable["rate_match"]]
    if len(mismatches) > 0:
        print(f"  FAIL: {len(mismatches)} rows have rate mismatch")
        print(mismatches.head(5)[["county", "year", "overdose_deaths", "population", "overdose_rate_per_100k", "rate_check"]].to_string())
    else:
        print("  PASS: overdose_rate_per_100k = deaths/pop*100000")

    # Spot check: Los Angeles 2015
    la = df[(df["county"].str.contains("Los Angeles")) & (df["year"] == 2015)]
    if not la.empty:
        r = la.iloc[0]
        expected = r["overdose_deaths"] / r["population"] * 100_000
        print(f"  Spot check LA 2015: rate={r['overdose_rate_per_100k']:.1f}, expected={expected:.1f}")


def test_fentanyl():
    """Verify fentanyl map data."""
    print("\n" + "=" * 60)
    print("TEST: Fentanyl Spread Map")
    print("=" * 60)

    import io
    import contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        from cdc.load_wonder_county_drugtype import load_fentanyl_county
        df = load_fentanyl_county(min_year=2008, max_year=2017)
    df = df[df["overdose_rate_per_100k"].notna()].copy()

    # Verify rate
    df["rate_check"] = (df["overdose_deaths"] / df["population"] * 100_000).round(3)
    checkable = df[df["rate_check"].notna() & df["overdose_rate_per_100k"].notna()].copy()
    checkable["rate_match"] = np.isclose(
        checkable["overdose_rate_per_100k"].astype(float),
        checkable["rate_check"],
        rtol=1e-2,
    )
    mismatches = checkable[~checkable["rate_match"]]
    if len(mismatches) > 0:
        print(f"  FAIL: {len(mismatches)} rows have rate mismatch")
    else:
        print("  PASS: overdose_rate_per_100k = deaths/pop*100000 (T40.4 only)")

    # Verify T40.4 filter
    assert (df["drug_code"] == "T40.4").all(), "Should only have T40.4"
    print("  PASS: All rows are T40.4 (fentanyl/synthetic)")


def test_dashboard_metrics():
    """Verify dashboard metric formulas against merged panel."""
    print("\n" + "=" * 60)
    print("TEST: County Dashboard Metrics")
    print("=" * 60)

    path = os.path.join(BASE, "output", "county", "iqvia_cdc_county_merged.csv")
    if not os.path.exists(path):
        print("  SKIP: Merged panel not found (run python main.py map-dashboard)")
        return

    df = pd.read_csv(path, dtype={"county_fips": str})
    df["county_fips"] = df["county_fips"].astype(str).str.zfill(5)

    # Filter to rows with both IQVIA and CDC data
    valid = df[df["total_rx"].notna() & df["overdose_deaths"].notna() & (df["population"] > 0)].copy()

    # 1. overdose_rate_per_100k = deaths / population * 100000
    valid["od_rate_check"] = valid["overdose_deaths"] / valid["population"] * 100_000
    valid["od_match"] = np.isclose(
        valid["overdose_rate_per_100k"].fillna(0),
        valid["od_rate_check"],
        rtol=1e-2,
    )
    od_mismatch = valid[~valid["od_match"]]
    if len(od_mismatch) > 0:
        print(f"  FAIL overdose_rate: {len(od_mismatch)} mismatches")
    else:
        print("  PASS: overdose_rate_per_100k = deaths/pop*100000")

    # 2. rx_per_capita = total_rx / population * 1000
    valid["rx_cap_check"] = valid["total_rx"] / valid["population"] * 1000
    valid["rx_match"] = np.isclose(
        valid["rx_per_capita"].fillna(0),
        valid["rx_cap_check"],
        rtol=1e-2,
    )
    rx_mismatch = valid[~valid["rx_match"]]
    if len(rx_mismatch) > 0:
        print(f"  FAIL rx_per_capita: {len(rx_mismatch)} mismatches")
        print(rx_mismatch[["county", "year", "total_rx", "population", "rx_per_capita", "rx_cap_check"]].head(3).to_string())
    else:
        print("  PASS: rx_per_capita = total_rx/pop*1000")

    # 3. pct_medicaid = medicaid_rx / total_rx * 100
    has_med = valid[valid["total_rx"] > 0]
    if "medicaid_rx" in has_med.columns:
        has_med = has_med.copy()
        has_med["pct_check"] = has_med["medicaid_rx"] / has_med["total_rx"] * 100
        has_med["pct_match"] = np.isclose(
            has_med["pct_medicaid"].fillna(0),
            has_med["pct_check"],
            rtol=1e-2,
            atol=0.01,
        )
        pct_mismatch = has_med[~has_med["pct_match"]]
        if len(pct_mismatch) > 0:
            print(f"  FAIL pct_medicaid: {len(pct_mismatch)} mismatches (sample below)")
            print(pct_mismatch[["county", "year", "medicaid_rx", "total_rx", "pct_medicaid", "pct_check"]].head(3).to_string())
        else:
            print("  PASS: pct_medicaid = medicaid_rx/total_rx*100")
    else:
        print("  SKIP pct_medicaid: medicaid_rx not in merged (may come from IQVIA county panel)")

    # 4. avg_mme_per_unit - from IQVIA, no simple cross-check without DB
    if "avg_mme_per_unit" in valid.columns:
        sane = valid["avg_mme_per_unit"].between(0, 500).sum()
        total = valid["avg_mme_per_unit"].notna().sum()
        print(f"  INFO: avg_mme_per_unit in [0,500] for {sane}/{total} rows (typical MME range)")

    # Spot check one county-year
    sample = valid.iloc[0]
    print(f"\n  Spot check: {sample['county']} {int(sample['year'])}")
    print(f"    overdose_deaths={sample['overdose_deaths']:.0f}, pop={sample['population']:.0f}")
    print(f"    rate={sample['overdose_rate_per_100k']:.1f} (expected {sample['overdose_deaths']/sample['population']*100000:.1f})")
    print(f"    total_rx={sample['total_rx']:.1f}, rx_per_capita={sample['rx_per_capita']:.1f} (expected {sample['total_rx']/sample['population']*1000:.1f})")


def test_dashboard_uses_correct_columns():
    """Verify dashboard map reads the right columns from panel."""
    print("\n" + "=" * 60)
    print("TEST: Dashboard Column Mapping")
    print("=" * 60)

    path = os.path.join(BASE, "output", "county", "iqvia_cdc_county_merged.csv")
    if not os.path.exists(path):
        print("  SKIP: Merged panel not found")
        return

    df = pd.read_csv(path, nrows=5)
    required = ["overdose_rate_per_100k", "rx_per_capita", "avg_mme_per_unit", "pct_medicaid"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"  FAIL: Missing columns: {missing}")
    else:
        print("  PASS: All 4 metric columns present in merged panel")


def test_dashboard_map_data_flow():
    """Verify dashboard map receives correct data from load_county_panel."""
    print("\n" + "=" * 60)
    print("TEST: Dashboard Map Data Flow")
    print("=" * 60)

    import io
    import contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        from cdc.merge_iqvia_cdc_county import load_county_panel
        panel = load_county_panel(force_merge=False)

    # Dashboard uses these columns for each metric
    metrics = ["overdose_rate_per_100k", "rx_per_capita", "avg_mme_per_unit", "pct_medicaid"]
    for m in metrics:
        if m not in panel.columns:
            print(f"  FAIL: Dashboard metric '{m}' missing from panel")
        elif panel[m].isna().all():
            print(f"  WARN: '{m}' is all NaN")
        else:
            n_valid = panel[m].notna().sum()
            print(f"  PASS: '{m}' has {n_valid:,} non-null values")


def run_all():
    """Run all verification tests."""
    print("\n" + "#" * 60)
    print("# VISUALIZATION DATA VERIFICATION")
    print("#" * 60)

    test_illicit_overdose()
    test_county_overdose()
    test_fentanyl()
    test_dashboard_metrics()
    test_dashboard_uses_correct_columns()
    test_dashboard_map_data_flow()

    print("\n" + "=" * 60)
    print("Verification complete.")
    print("=" * 60)


if __name__ == "__main__":
    run_all()
