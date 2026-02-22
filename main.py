"""
main.py — Orchestrates all data pulls for the Lucy Institute Health Challenge.

Leading question
================
"Is there a significant difference between the way people on Medicaid
 are prescribed opioids versus the general population?"

Usage
-----
    python main.py                  # run everything (explore + analysis + geo)
    python main.py explore          # only explore payor plans
    python main.py medicaid         # only Medicaid vs Non-Medicaid queries (Q1-Q5)
    python main.py q3               # only Q3 (by state)
    python main.py q4               # only Q4 (by drug)
    python main.py q5               # only Q5 (by specialty)
    python main.py q4q5             # Q4 + Q5 together
    python main.py q3q4q5           # Q3 + Q4 + Q5 together
    python main.py extended         # all 4 extended queries (Q6-Q9)
    python main.py q6               # only Q6 (state × year)
    python main.py q7               # only Q7 (retail vs mail order)
    python main.py q8               # only Q8 (monthly seasonality)
    python main.py q9               # only Q9 (stratified 2018 sample)
    python main.py pillmill          # prescriber concentration / pill mill analysis
    python main.py county           # county-level panel (zip→county), 2008-2017
    python main.py geo              # only geographic / zip-code queries
    python main.py geo-light        # only state-level + zip % (faster)
    python main.py census           # load & combine Census ACS tables
    python main.py merge            # merge IQVIA zip output + Census demographics
    python main.py cdc              # merge IQVIA state data + CDC WONDER overdose data
    python main.py cdc-drug         # build CDC drug-type panel + merge with IQVIA state×year
    python main.py map-illicit      # build animated map of illicit-overdose spread
    python main.py map-county       # build animated county-level overdose spread map
    python main.py map-fentanyl     # build animated fentanyl spread map by county
    python main.py map-dashboard    # comprehensive county map (IQVIA + CDC merged)
"""

import sys
import time

# ── importable query modules ────────────────────────────────────────────────
from queries import explore_payors
from queries import medicaid_vs_general
from queries import geographic
from queries import extended
from queries import pill_mill
from queries import county_panel
from census import load_census
from census import merge_iqvia_census
from cdc import load_wonder
from cdc import merge_iqvia_cdc
from cdc import load_wonder_drug_types
from cdc import merge_iqvia_cdc_drugtype
from utils.db_utils import get_connection, export_to_csv


def verify_connection() -> bool:
    """Quick connectivity check before running heavy queries."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.close()
        # Do NOT close conn — it's the shared pool connection
        print(" Database connection verified.\n")
        return True
    except Exception as e:
        print(f" Cannot reach database: {e}")
        return False


def run_explore():
    """Step 1 – Discover payor plan categories (find Medicaid IDs)."""
    print("=" * 60)
    print("STEP 1: EXPLORE PAYOR PLANS")
    print("=" * 60)
    explore_payors.run_all(save=True)


def run_medicaid():
    """Step 2 – Medicaid vs Non-Medicaid comparisons."""
    print("\n" + "=" * 60)
    print("STEP 2: MEDICAID vs NON-MEDICAID ANALYSIS")
    print("=" * 60)
    medicaid_vs_general.run_all(save=True)


def run_geo(light: bool = False):
    """Step 3 – Geographic / zip-code level data for mapping."""
    print("\n" + "=" * 60)
    print("STEP 3: GEOGRAPHIC DATA (zip-code level)")
    print("=" * 60)

    if light:
        # Only run the two lighter queries
        from utils.db_utils import export_to_csv

        print("\n  Zip-level Medicaid vs Non-Medicaid …")
        df_zip = geographic.opioid_rx_by_zip_medicaid()
        print(df_zip.head(20).to_string(index=False))
        export_to_csv(df_zip, "geo_zip_medicaid.csv", subdir="iqvia_core")

        print("\n  Medicaid % by zip code (derived from above — no DB call) …")
        df_pct = geographic.medicaid_pct_by_zipcode(df_zip)
        print(df_pct.head(20).to_string(index=False))
        export_to_csv(df_pct, "geo_zip_medicaid_pct.csv", subdir="iqvia_core")
    else:
        geographic.run_all(save=True)


def run_census():
    """Step 4 – Load & combine all Census ACS tables."""
    print("\n" + "=" * 60)
    print("STEP 4: LOAD CENSUS DATA")
    print("=" * 60)
    load_census.run_all(save=True)


def run_q3():
    """Run only Q3 (Medicaid vs Non-Medicaid by state)."""
    print("\n" + "=" * 60)
    print("Q3: MEDICAID vs NON-MEDICAID BY STATE")
    print("=" * 60)
    import time
    t0 = time.time()
    df = medicaid_vs_general.opioid_rx_medicaid_by_state()
    print(df.head(20).to_string(index=False))
    export_to_csv(df, "medicaid_vs_nonmedicaid_by_state.csv", subdir="iqvia_core")
    print(f"  Q3 done in {(time.time()-t0)/60:.1f} min")


def run_q4():
    """Run only Q4 (Medicaid vs Non-Medicaid by drug)."""
    print("\n" + "=" * 60)
    print("Q4: MEDICAID vs NON-MEDICAID BY DRUG")
    print("=" * 60)
    import time
    t0 = time.time()
    df = medicaid_vs_general.opioid_rx_medicaid_by_drug()
    print(df.head(20).to_string(index=False))
    export_to_csv(df, "medicaid_vs_nonmedicaid_by_drug.csv", subdir="iqvia_core")
    print(f"  Q4 done in {(time.time()-t0)/60:.1f} min")


def run_q5():
    """Run only Q5 (Medicaid vs Non-Medicaid by prescriber specialty)."""
    print("\n" + "=" * 60)
    print("Q5: MEDICAID vs NON-MEDICAID BY SPECIALTY")
    print("=" * 60)
    import time
    t0 = time.time()
    df = medicaid_vs_general.opioid_rx_medicaid_by_specialty()
    print(df.head(20).to_string(index=False))
    export_to_csv(df, "medicaid_vs_nonmedicaid_by_specialty.csv", subdir="iqvia_core")
    print(f"  Q5 done in {(time.time()-t0)/60:.1f} min")


def run_extended():
    """Step 6 – Extended queries: state×year, retail/mail, monthly, 2018 sample."""
    print("\n" + "=" * 60)
    print("STEP 6: EXTENDED QUERIES (Q6–Q9)")
    print("=" * 60)
    extended.run_all(save=True)


def run_q6():
    """Run only Q6 (State × Year × Medicaid)."""
    print("\n" + "=" * 60)
    print("Q6: MEDICAID vs NON-MEDICAID BY STATE × YEAR")
    print("=" * 60)
    t0 = time.time()
    df = extended.opioid_rx_by_state_year_medicaid()
    print(df.head(20).to_string(index=False))
    export_to_csv(df, "medicaid_vs_nonmedicaid_by_state_year.csv", subdir="extended")
    print(f"  Q6 done in {(time.time()-t0)/60:.1f} min")


def run_q7():
    """Run only Q7 (Retail vs Mail Order)."""
    print("\n" + "=" * 60)
    print("Q7: RETAIL vs MAIL ORDER BY MEDICAID STATUS")
    print("=" * 60)
    t0 = time.time()
    df = extended.opioid_rx_by_sales_channel_year()
    print(df.head(20).to_string(index=False))
    export_to_csv(df, "medicaid_vs_nonmedicaid_by_sales_channel.csv", subdir="extended")
    print(f"  Q7 done in {(time.time()-t0)/60:.1f} min")


def run_q8():
    """Run only Q8 (Monthly Seasonality)."""
    print("\n" + "=" * 60)
    print("Q8: MONTHLY SEASONALITY BY MEDICAID STATUS")
    print("=" * 60)
    t0 = time.time()
    df = extended.opioid_rx_by_month_medicaid()
    print(df.head(20).to_string(index=False))
    export_to_csv(df, "medicaid_vs_nonmedicaid_by_month.csv", subdir="extended")
    print(f"  Q8 done in {(time.time()-t0)/60:.1f} min")


def run_q9():
    """Run only Q9 (Stratified 2018 Sample for logistic regression)."""
    print("\n" + "=" * 60)
    print("Q9: STRATIFIED 2018 SAMPLE (~2M ROWS)")
    print("=" * 60)
    t0 = time.time()
    df = extended.stratified_sample_2018(target_rows=2_000_000)
    print(f"     Shape: {df.shape}")
    print(f"     Medicaid %: {df['is_medicaid'].mean()*100:.2f}%")
    export_to_csv(df, "sample_2018_for_regression.csv", subdir="extended")
    print(f"  Q9 done in {(time.time()-t0)/60:.1f} min")

def run_pillmill():
    """Prescriber concentration / pill mill analysis."""
    print("\n" + "=" * 60)
    print("PILL MILL ANALYSIS — PRESCRIBER CONCENTRATION")
    print("=" * 60)
    pill_mill.run_all(save=True)

def run_cdc():
    """Step 7 – Merge IQVIA state data with CDC WONDER overdose deaths."""
    print("\n" + "=" * 60)
    print("STEP 7: MERGE IQVIA + CDC WONDER OVERDOSE DATA")
    print("=" * 60)
    df = merge_iqvia_cdc.merge_iqvia_cdc()
    if not df.empty:
        export_to_csv(df, "iqvia_cdc_merged_by_state.csv", subdir="cdc")
        merge_iqvia_cdc.analyze_merged(df)


def run_cdc_drug():
    """Step 8 – Build CDC drug-type outputs and merge with IQVIA state×year panel."""
    print("\n" + "=" * 60)
    print("STEP 8: CDC DRUG-TYPE PANEL + IQVIA STATE×YEAR MERGE")
    print("=" * 60)

    cdc_types = load_wonder_drug_types.load_overdose_deaths_by_drug_type()
    export_to_csv(cdc_types, "cdc_overdose_by_state_year_drug_type.csv", subdir="cdc")

    illicit_panel = load_wonder_drug_types.build_illicit_spread_panel(cdc_types, start_year=1999, end_year=2018)
    export_to_csv(illicit_panel, "cdc_illicit_overdose_by_state_year.csv", subdir="cdc")

    merged = merge_iqvia_cdc_drugtype.merge_iqvia_cdc_drugtype()
    export_to_csv(merged, "iqvia_cdc_state_year_illicit_panel.csv", subdir="cdc")


def run_county():
    """County-level panel: zip→county aggregation with full Medicaid/MME detail."""
    print("\n" + "=" * 60)
    print("COUNTY PANEL: ZIP→COUNTY OPIOID DATA (2008–2017)")
    print("=" * 60)
    county_panel.run_all(save=True)


def run_map_illicit():
    """Step 9 – Build animated US map of illicit-overdose spread by year."""
    print("\n" + "=" * 60)
    print("STEP 9: ILLICIT OVERDOSE SPREAD MAP")
    print("=" * 60)
    from visualizations.illicit_overdose_spread import build_map

    out = build_map()
    print(f"  ✅ Map saved to: {out}")


def run_map_county():
    """Build animated county-level overdose spread map (2008-2017)."""
    print("\n" + "=" * 60)
    print("COUNTY OVERDOSE SPREAD MAP (2008-2017)")
    print("=" * 60)
    from visualizations.county_overdose_spread import build_county_map

    out = build_county_map()
    print(f"  ✅ Map saved to: {out}")


def run_map_fentanyl():
    """Build animated county-level fentanyl spread map (2008-2017)."""
    print("\n" + "=" * 60)
    print("FENTANYL SPREAD MAP (2008-2017)")
    print("=" * 60)
    from visualizations.fentanyl_spread import build_fentanyl_map

    out = build_fentanyl_map()
    print(f"  ✅ Map saved to: {out}")


def run_map_dashboard():
    """Build comprehensive county dashboard map (IQVIA + CDC merged)."""
    print("\n" + "=" * 60)
    print("COUNTY DASHBOARD MAP (IQVIA + CDC MERGED)")
    print("=" * 60)
    from visualizations.county_dashboard_map import build_dashboard_map

    out = build_dashboard_map()
    print(f"  ✅ Map saved to: {out}")


def run_merge():
    """Step 5 – Merge IQVIA zip data with Census demographics."""
    print("\n" + "=" * 60)
    print("STEP 5: MERGE IQVIA + CENSUS")
    print("=" * 60)
    merge_iqvia_census.run_all(save=True)


# ── CLI entry-point ─────────────────────────────────────────────────────────
def main():
    start = time.time()

    if not verify_connection():
        sys.exit(1)

    # Parse CLI argument (default = run everything)
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "all"

    if mode == "explore":
        run_explore()
    elif mode == "medicaid":
        run_medicaid()
    elif mode == "q3":
        run_q3()
    elif mode == "q4":
        run_q4()
    elif mode == "q5":
        run_q5()
    elif mode == "q3q4q5":
        run_q3()
        run_q4()
        run_q5()
    elif mode == "q4q5":
        run_q4()
        run_q5()
    elif mode == "extended":
        run_extended()
    elif mode == "q6":
        run_q6()
    elif mode == "q7":
        run_q7()
    elif mode == "q8":
        run_q8()
    elif mode == "q9":
        run_q9()
    elif mode == "q6q7q8":
        run_q6()
        run_q7()
        run_q8()
    elif mode == "pillmill":
        run_pillmill()
    elif mode == "geo":
        run_geo(light=False)
    elif mode == "geo-light":
        run_geo(light=True)
    elif mode == "census":
        run_census()
    elif mode == "merge":
        run_merge()
    elif mode == "cdc":
        run_cdc()
    elif mode == "cdc-drug":
        run_cdc_drug()
    elif mode == "county":
        run_county()
    elif mode == "map-illicit":
        run_map_illicit()
    elif mode == "map-county":
        run_map_county()
    elif mode == "map-fentanyl":
        run_map_fentanyl()
    elif mode == "map-dashboard":
        run_map_dashboard()
    elif mode == "all":
        run_explore()
        run_medicaid()
        run_geo(light=False)
        run_census()
        run_merge()
    else:
        print(f"Unknown mode '{mode}'. Use: explore | medicaid | q3 | q4 | q5 | q3q4q5 | q4q5 | "
              f"extended | q6 | q7 | q8 | q9 | q6q7q8 | pillmill | geo | geo-light | "
              f"county | census | merge | cdc | cdc-drug | map-illicit | map-county | map-fentanyl | map-dashboard | all")
        sys.exit(1)

    elapsed = time.time() - start
    print(f"\n Done in {elapsed / 60:.1f} minutes.")


if __name__ == "__main__":
    main()
