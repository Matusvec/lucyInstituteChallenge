"""
Analyze IQVIA opioid query output CSVs.

Usage:
    python analyze.py output/test_indiana_2018.csv
    python analyze.py output/test_indiana_2018.csv --plot
"""

import argparse
import sys
import pandas as pd
import numpy as np
from scipy import stats


# ── helpers ──────────────────────────────────────────────────────────
def section(title):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")


def pct(num, denom):
    return num / denom * 100 if denom else float("nan")


# ── core analyses ────────────────────────────────────────────────────
def overview(df, med, non):
    section("OVERVIEW")
    print(f"  File rows:                 {len(df):,}")
    print(f"  Unique zip codes:          {df['zip_code'].nunique():,}")
    states = df["state"].nunique() if "state" in df.columns else "N/A"
    print(f"  Unique states:             {states}")
    print(f"  Medicaid zip-groups:       {len(med):,}")
    print(f"  Non-Medicaid zip-groups:   {len(non):,}")


def rx_summary(med, non, total_rx_sum):
    section("TOTAL PRESCRIPTIONS (Rx)")
    fmt = "  {:<14s} — Sum: {:>12,.1f}   Mean/zip: {:>10,.1f}   Median: {:>10,.1f}"
    print(fmt.format("Medicaid",     med["total_rx"].sum(),  med["total_rx"].mean(),  med["total_rx"].median()))
    print(fmt.format("Non-Medicaid", non["total_rx"].sum(),  non["total_rx"].mean(),  non["total_rx"].median()))
    print(f"  Medicaid share of total Rx: {pct(med['total_rx'].sum(), total_rx_sum):.2f}%")


def mme_summary(med, non):
    section("AVERAGE MME PER ZIP")
    fmt = "  {:<14s} — Mean: {:>8.2f}   Median: {:>8.2f}   Std: {:>8.2f}   Min: {:>6.1f}   Max: {:>8.1f}"
    print(fmt.format("Medicaid",     med["avg_mme"].mean(), med["avg_mme"].median(), med["avg_mme"].std(), med["avg_mme"].min(), med["avg_mme"].max()))
    print(fmt.format("Non-Medicaid", non["avg_mme"].mean(), non["avg_mme"].median(), non["avg_mme"].std(), non["avg_mme"].min(), non["avg_mme"].max()))
    diff = med["avg_mme"].mean() - non["avg_mme"].mean()
    print(f"\n  Raw mean difference (Med − NonMed): {diff:+.2f} MME")


def volume_weighted_mme(med, non):
    section("Rx-VOLUME WEIGHTED MME")
    med_w = np.average(med["avg_mme"], weights=med["total_rx"]) if len(med) else float("nan")
    non_w = np.average(non["avg_mme"], weights=non["total_rx"]) if len(non) else float("nan")
    print(f"  Medicaid:     {med_w:.2f}")
    print(f"  Non-Medicaid: {non_w:.2f}")
    print(f"  Difference:   {med_w - non_w:+.2f}")
    print("  (Weights each zip's MME by how many Rx it contributed)")


def paired_comparison(med, non):
    both = pd.merge(
        med[["zip_code", "total_rx", "avg_mme"]].rename(columns={"total_rx": "med_rx", "avg_mme": "med_mme"}),
        non[["zip_code", "total_rx", "avg_mme"]].rename(columns={"total_rx": "nonmed_rx", "avg_mme": "nonmed_mme"}),
        on="zip_code",
    )
    if len(both) == 0:
        print("\n  ⚠ No zips have both Medicaid and Non-Medicaid data — skipping paired analysis.")
        return both

    both["mme_diff"] = both["med_mme"] - both["nonmed_mme"]
    both["rx_ratio"] = both["med_rx"] / both["nonmed_rx"]

    section(f"PAIRED ZIP COMPARISON  (n = {len(both)} zips with both groups)")
    print(f"  Mean MME diff  (Med − NonMed): {both['mme_diff'].mean():+.2f}")
    print(f"  Median MME diff:               {both['mme_diff'].median():+.2f}")
    print(f"  Std of MME diff:               {both['mme_diff'].std():.2f}")
    higher = pct((both["mme_diff"] > 0).sum(), len(both))
    lower  = pct((both["mme_diff"] < 0).sum(), len(both))
    equal  = pct((both["mme_diff"] == 0).sum(), len(both))
    print(f"  Medicaid MME higher: {higher:.1f}%   lower: {lower:.1f}%   equal: {equal:.1f}%")
    print(f"  Avg Medicaid Rx as % of Non-Medicaid Rx: {both['rx_ratio'].mean()*100:.1f}%")
    return both


def stat_tests(med, non, both):
    section("STATISTICAL TESTS")

    # Welch's t-test (unpaired)
    t, p = stats.ttest_ind(med["avg_mme"].dropna(), non["avg_mme"].dropna(), equal_var=False)
    sig = "YES ✅" if p < 0.05 else "NO ❌"
    print(f"  Welch's t-test (unpaired)")
    print(f"    t = {t:.3f},  p = {p:.6f}  →  Significant at α=0.05? {sig}")

    # Paired t-test (same-zip)
    if len(both) > 1:
        t2, p2 = stats.ttest_rel(both["med_mme"], both["nonmed_mme"])
        sig2 = "YES ✅" if p2 < 0.05 else "NO ❌"
        print(f"\n  Paired t-test (same-zip, n={len(both)})")
        print(f"    t = {t2:.3f},  p = {p2:.6f}  →  Significant at α=0.05? {sig2}")

    # Mann-Whitney U
    u, pu = stats.mannwhitneyu(med["avg_mme"].dropna(), non["avg_mme"].dropna(), alternative="two-sided")
    sigu = "YES ✅" if pu < 0.05 else "NO ❌"
    print(f"\n  Mann-Whitney U (non-parametric)")
    print(f"    U = {u:.1f},  p = {pu:.6f}  →  Significant at α=0.05? {sigu}")

    # Effect size — Cohen's d
    pooled_std = np.sqrt((med["avg_mme"].std()**2 + non["avg_mme"].std()**2) / 2)
    d = (med["avg_mme"].mean() - non["avg_mme"].mean()) / pooled_std if pooled_std else float("nan")
    label = "negligible" if abs(d) < 0.2 else "small" if abs(d) < 0.5 else "medium" if abs(d) < 0.8 else "large"
    print(f"\n  Cohen's d (effect size): {d:+.3f}  ({label})")


def top_bottom_zips(both, n=10):
    if len(both) == 0:
        return
    section(f"TOP {n} ZIPS — Medicaid MME HIGHER than Non-Medicaid")
    top = both.nlargest(n, "mme_diff")[["zip_code", "med_mme", "nonmed_mme", "mme_diff", "med_rx", "nonmed_rx"]]
    print(top.to_string(index=False))

    section(f"TOP {n} ZIPS — Medicaid MME LOWER than Non-Medicaid")
    bot = both.nsmallest(n, "mme_diff")[["zip_code", "med_mme", "nonmed_mme", "mme_diff", "med_rx", "nonmed_rx"]]
    print(bot.to_string(index=False))


def distribution_check(med, non):
    section("DISTRIBUTION CHECKS (Shapiro-Wilk, max n=5000)")
    for label, series in [("Medicaid", med["avg_mme"]), ("Non-Medicaid", non["avg_mme"])]:
        s = series.dropna()
        if len(s) > 5000:
            s = s.sample(5000, random_state=42)
        if len(s) >= 3:
            w, p = stats.shapiro(s)
            normal = "YES" if p > 0.05 else "NO"
            print(f"  {label:<14s}  W={w:.4f}  p={p:.6f}  Normal? {normal}")


def make_plots(df, med, non, both):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("\n  ⚠ matplotlib not installed — skipping plots. Run: pip install matplotlib")
        return

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Opioid Prescribing: Medicaid vs Non-Medicaid", fontsize=14, fontweight="bold")

    # 1 — MME distributions
    ax = axes[0, 0]
    bins = np.linspace(0, min(80, df["avg_mme"].quantile(0.99)), 40)
    ax.hist(non["avg_mme"], bins=bins, alpha=0.6, label="Non-Medicaid", color="#4C72B0")
    ax.hist(med["avg_mme"], bins=bins, alpha=0.6, label="Medicaid", color="#DD8452")
    ax.set_xlabel("Avg MME")
    ax.set_ylabel("# of Zips")
    ax.set_title("Distribution of Avg MME per Zip")
    ax.legend()

    # 2 — Rx volume comparison (log scale)
    ax = axes[0, 1]
    ax.hist(np.log10(non["total_rx"].clip(lower=0.1)), bins=40, alpha=0.6, label="Non-Medicaid", color="#4C72B0")
    ax.hist(np.log10(med["total_rx"].clip(lower=0.1)), bins=40, alpha=0.6, label="Medicaid", color="#DD8452")
    ax.set_xlabel("log₁₀(Total Rx)")
    ax.set_ylabel("# of Zips")
    ax.set_title("Distribution of Total Rx per Zip (log scale)")
    ax.legend()

    # 3 — Paired MME scatter
    ax = axes[1, 0]
    if len(both) > 0:
        ax.scatter(both["nonmed_mme"], both["med_mme"], alpha=0.4, s=15, color="#55A868")
        lim = max(both["nonmed_mme"].max(), both["med_mme"].max()) * 1.05
        ax.plot([0, lim], [0, lim], "k--", lw=1, label="Equal MME line")
        ax.set_xlabel("Non-Medicaid Avg MME")
        ax.set_ylabel("Medicaid Avg MME")
        ax.set_title("Same-Zip MME Comparison")
        ax.legend()
    else:
        ax.text(0.5, 0.5, "No paired data", ha="center", va="center", transform=ax.transAxes)

    # 4 — Box plot
    ax = axes[1, 1]
    data_to_plot = [non["avg_mme"].dropna(), med["avg_mme"].dropna()]
    bp = ax.boxplot(data_to_plot, labels=["Non-Medicaid", "Medicaid"], patch_artist=True)
    bp["boxes"][0].set_facecolor("#4C72B0")
    bp["boxes"][1].set_facecolor("#DD8452")
    ax.set_ylabel("Avg MME")
    ax.set_title("MME Box Plot")

    plt.tight_layout()
    out_path = "output/analysis_plots.png"
    plt.savefig(out_path, dpi=150)
    print(f"\n  📊 Plots saved → {out_path}")
    plt.close()


# ── main ─────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Analyze IQVIA opioid query CSV output")
    parser.add_argument("csv", help="Path to CSV file")
    parser.add_argument("--plot", action="store_true", help="Generate plots (requires matplotlib)")
    args = parser.parse_args()

    df = pd.read_csv(args.csv)
    cols = set(df.columns)

    print("=" * 60)
    print(f"  OPIOID PRESCRIBING ANALYSIS — {args.csv}")
    print(f"  Columns: {list(df.columns)}")
    print("=" * 60)

    # ── Auto-detect format ──
    # Format A: year-level (Q1 output) — has 'year', 'is_medicaid', 'avg_mme'
    # Format B: zip-level (test_indiana) — has 'zip_code', 'is_medicaid', 'avg_mme'
    # Format C: pct summary (Q2 output) — has 'pct_medicaid'

    if "pct_medicaid" in cols:
        # ── Format C: Q2 percentage summary ──
        analyze_pct_summary(df, args)
    elif "year" in cols and "is_medicaid" in cols:
        # ── Format A: year-level ──
        unit = "year"
        analyze_grouped(df, unit, args)
    elif "zip_code" in cols and "is_medicaid" in cols:
        # ── Format B: zip-level (original) ──
        unit = "zip_code"
        analyze_grouped(df, unit, args)
    else:
        print(f"\n❌ Unrecognized format. Columns: {list(df.columns)}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("  Done.")
    print(f"{'='*60}\n")


def analyze_pct_summary(df, args):
    """Analyze Q2-style percentage summary."""
    section("MEDICAID SHARE OF OPIOID Rx OVER TIME")
    # Only years with Medicaid data
    has_med = df[df["pct_medicaid"].notna()].copy()
    no_med  = df[df["pct_medicaid"].isna()].copy()
    print(f"  Years with Medicaid data:    {len(has_med)} ({int(has_med['year'].min())}–{int(has_med['year'].max())})")
    print(f"  Years without Medicaid data: {len(no_med)} ({int(no_med['year'].min())}–{int(no_med['year'].max())})")

    section("MEDICAID % BY YEAR")
    for _, r in has_med.iterrows():
        bar = "█" * int(r["pct_medicaid"] * 2)
        print(f"  {int(r['year'])}  {r['pct_medicaid']:5.2f}%  {bar}")

    section("TREND STATISTICS")
    peak_yr = has_med.loc[has_med["pct_medicaid"].idxmax()]
    low_yr  = has_med.loc[has_med["pct_medicaid"].idxmin()]
    print(f"  Peak Medicaid share:  {peak_yr['pct_medicaid']:.2f}% in {int(peak_yr['year'])}")
    print(f"  Low Medicaid share:   {low_yr['pct_medicaid']:.2f}% in {int(low_yr['year'])}")

    # Linear trend
    from scipy.stats import linregress
    slope, intercept, r, p, se = linregress(has_med["year"], has_med["pct_medicaid"])
    sig = "YES ✅" if p < 0.05 else "NO ❌"
    print(f"\n  Linear trend (pct_medicaid ~ year):")
    print(f"    Slope: {slope:+.3f}%/year   R²: {r**2:.3f}   p={p:.6f}   Significant? {sig}")
    if slope < 0:
        print(f"    → Medicaid share is declining by ~{abs(slope):.2f} percentage points per year")
    else:
        print(f"    → Medicaid share is increasing by ~{slope:.2f} percentage points per year")

    section("TOTAL Rx VOLUME TREND")
    # Show overall Rx volume trend (all years)
    peak_rx = df.loc[df["total_rx"].idxmax()]
    print(f"  Peak total opioid Rx: {peak_rx['total_rx']:,.0f} in {int(peak_rx['year'])}")
    latest = df.iloc[-1]
    print(f"  Latest year ({int(latest['year'])}):    {latest['total_rx']:,.0f}")
    if len(df) > 1:
        first_full = df.iloc[0]
        change = (latest["total_rx"] - first_full["total_rx"]) / first_full["total_rx"] * 100
        print(f"  Change {int(first_full['year'])}→{int(latest['year'])}: {change:+.1f}%")
    print(f"\n  ⚠  2018 appears partial (only {latest['total_rx']:,.0f} vs ~250M in peak years)")


def analyze_grouped(df, unit, args):
    """Analyze data grouped by a unit (year or zip_code)."""
    med = df[df["is_medicaid"] == "Medicaid"].copy()
    non = df[df["is_medicaid"] == "Non-Medicaid"].copy()

    # ── Overview ──
    section("OVERVIEW")
    print(f"  File rows:                   {len(df):,}")
    print(f"  Grouping unit:               {unit}")
    print(f"  Unique {unit}s:          {df[unit].nunique():,}")
    print(f"  Medicaid groups:             {len(med):,}")
    print(f"  Non-Medicaid groups:         {len(non):,}")
    if unit == "year":
        print(f"  Year range:                  {int(df['year'].min())}–{int(df['year'].max())}")
        print(f"  Medicaid years:              {sorted(med['year'].unique().astype(int).tolist())}")

    # ── Rx summary ──
    total_rx_sum = df["total_rx"].sum()
    rx_summary(med, non, total_rx_sum)

    # ── MME summary (if available) ──
    if "avg_mme" in df.columns:
        mme_summary(med, non)
        volume_weighted_mme(med, non)

    # ── Qty & New Rx (if available) ──
    if "total_qty" in df.columns:
        section("TOTAL QUANTITY DISPENSED")
        print(f"  Medicaid total qty:     {med['total_qty'].sum():>18,.1f}")
        print(f"  Non-Medicaid total qty: {non['total_qty'].sum():>18,.1f}")
        if med['total_qty'].sum() > 0:
            med_qty_per_rx = med['total_qty'].sum() / med['total_rx'].sum()
            non_qty_per_rx = non['total_qty'].sum() / non['total_rx'].sum()
            print(f"  Avg units per Rx (Medicaid):     {med_qty_per_rx:.1f}")
            print(f"  Avg units per Rx (Non-Medicaid): {non_qty_per_rx:.1f}")

    if "new_rx" in df.columns:
        section("NEW vs REFILL PRESCRIPTIONS")
        med_new_pct = pct(med["new_rx"].sum(), med["total_rx"].sum()) if med["total_rx"].sum() else float("nan")
        non_new_pct = pct(non["new_rx"].sum(), non["total_rx"].sum())
        print(f"  Medicaid new Rx %:     {med_new_pct:.1f}%")
        print(f"  Non-Medicaid new Rx %: {non_new_pct:.1f}%")
        print(f"  → {'Medicaid has MORE new Rx (vs refills)' if med_new_pct > non_new_pct else 'Non-Medicaid has MORE new Rx'}")

    # ── Paired comparison ──
    both = pd.merge(
        med[[unit, "total_rx"]].rename(columns={"total_rx": "med_rx"}),
        non[[unit, "total_rx"]].rename(columns={"total_rx": "nonmed_rx"}),
        on=unit,
    )
    if "avg_mme" in med.columns:
        both = pd.merge(
            both,
            med[[unit, "avg_mme"]].rename(columns={"avg_mme": "med_mme"}),
            on=unit,
        )
        both = pd.merge(
            both,
            non[[unit, "avg_mme"]].rename(columns={"avg_mme": "nonmed_mme"}),
            on=unit,
        )
        both["mme_diff"] = both["med_mme"] - both["nonmed_mme"]

    both["rx_ratio"] = both["med_rx"] / both["nonmed_rx"]

    section(f"PAIRED COMPARISON  (n = {len(both)} {unit}s with both groups)")
    if len(both) > 0:
        print(f"  Avg Medicaid Rx as % of Non-Medicaid: {both['rx_ratio'].mean()*100:.2f}%")
        if "mme_diff" in both.columns:
            print(f"  Mean MME diff  (Med − NonMed): {both['mme_diff'].mean():+.4f}")
            print(f"  Median MME diff:               {both['mme_diff'].median():+.4f}")
            higher = pct((both["mme_diff"] > 0).sum(), len(both))
            lower  = pct((both["mme_diff"] < 0).sum(), len(both))
            print(f"  Years Medicaid MME higher: {higher:.0f}%   lower: {lower:.0f}%")
    else:
        print("  ⚠ No paired data available.")

    # ── Statistical tests ──
    if "avg_mme" in df.columns and len(med) > 1 and len(non) > 1:
        section("STATISTICAL TESTS")
        # Welch's t-test
        t, p = stats.ttest_ind(med["avg_mme"].dropna(), non["avg_mme"].dropna(), equal_var=False)
        sig = "YES ✅" if p < 0.05 else "NO ❌"
        print(f"  Welch's t-test (unpaired, n_med={len(med)}, n_non={len(non)})")
        print(f"    t = {t:.4f},  p = {p:.6f}  →  Significant? {sig}")

        # Paired t-test
        if "mme_diff" in both.columns and len(both) > 1:
            t2, p2 = stats.ttest_rel(both["med_mme"], both["nonmed_mme"])
            sig2 = "YES ✅" if p2 < 0.05 else "NO ❌"
            print(f"\n  Paired t-test (same-{unit}, n={len(both)})")
            print(f"    t = {t2:.4f},  p = {p2:.6f}  →  Significant? {sig2}")

        # Mann-Whitney U
        u, pu = stats.mannwhitneyu(med["avg_mme"].dropna(), non["avg_mme"].dropna(), alternative="two-sided")
        sigu = "YES ✅" if pu < 0.05 else "NO ❌"
        print(f"\n  Mann-Whitney U (non-parametric)")
        print(f"    U = {u:.1f},  p = {pu:.6f}  →  Significant? {sigu}")

        # Cohen's d
        pooled_std = np.sqrt((med["avg_mme"].std()**2 + non["avg_mme"].std()**2) / 2)
        d = (med["avg_mme"].mean() - non["avg_mme"].mean()) / pooled_std if pooled_std else float("nan")
        label = "negligible" if abs(d) < 0.2 else "small" if abs(d) < 0.5 else "medium" if abs(d) < 0.8 else "large"
        print(f"\n  Cohen's d (effect size): {d:+.4f}  ({label})")

        # Trend test (year-level only)
        if unit == "year" and "mme_diff" in both.columns and len(both) >= 3:
            section("MME GAP TREND OVER TIME")
            from scipy.stats import linregress
            slope, intercept, r, p_trend, se = linregress(both[unit], both["mme_diff"])
            sig_t = "YES ✅" if p_trend < 0.05 else "NO ❌"
            print(f"  Linear trend (mme_diff ~ year):")
            print(f"    Slope: {slope:+.4f} MME/year   R²: {r**2:.3f}   p={p_trend:.6f}   Significant? {sig_t}")
            for _, row in both.sort_values(unit).iterrows():
                bar = "█" * max(1, int(abs(row['mme_diff']) * 5))
                sign = "+" if row['mme_diff'] > 0 else "-"
                print(f"    {int(row[unit])}  {row['mme_diff']:+.4f}  {sign}{bar}")

    if unit == "zip_code" and args.plot:
        make_plots(df, med, non, both)


if __name__ == "__main__":
    main()
