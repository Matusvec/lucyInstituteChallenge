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
    python main.py geo              # only geographic / zip-code queries
    python main.py geo-light        # only state-level + zip % (faster)
    python main.py census           # load & combine Census ACS tables
    python main.py merge            # merge IQVIA zip output + Census demographics
    python main.py cdc              # merge IQVIA state data + CDC WONDER overdose data
"""

import sys
import time

# ── importable query modules ────────────────────────────────────────────────
from queries import explore_payors
from queries import medicaid_vs_general
from queries import geographic
from census import load_census
from census import merge_iqvia_census
from cdc import load_wonder
from cdc import merge_iqvia_cdc
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
        export_to_csv(df_zip, "geo_zip_medicaid.csv")

        print("\n  Medicaid % by zip code (derived from above — no DB call) …")
        df_pct = geographic.medicaid_pct_by_zipcode(df_zip)
        print(df_pct.head(20).to_string(index=False))
        export_to_csv(df_pct, "geo_zip_medicaid_pct.csv")
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
    export_to_csv(df, "medicaid_vs_nonmedicaid_by_state.csv")
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
    export_to_csv(df, "medicaid_vs_nonmedicaid_by_drug.csv")
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
    export_to_csv(df, "medicaid_vs_nonmedicaid_by_specialty.csv")
    print(f"  Q5 done in {(time.time()-t0)/60:.1f} min")


def run_cdc():
    """Step 6 – Merge IQVIA state data with CDC WONDER overdose deaths."""
    print("\n" + "=" * 60)
    print("STEP 6: MERGE IQVIA + CDC WONDER OVERDOSE DATA")
    print("=" * 60)
    df = merge_iqvia_cdc.merge_iqvia_cdc()
    if not df.empty:
        export_to_csv(df, "iqvia_cdc_merged_by_state.csv")
        merge_iqvia_cdc.analyze_merged(df)


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
    elif mode == "all":
        run_explore()
        run_medicaid()
        run_geo(light=False)
        run_census()
        run_merge()
    else:
        print(f"Unknown mode '{mode}'. Use: explore | medicaid | q3 | q4 | q5 | q3q4q5 | q4q5 | geo | geo-light | census | merge | cdc | all")
        sys.exit(1)

    elapsed = time.time() - start
    print(f"\n Done in {elapsed / 60:.1f} minutes.")


if __name__ == "__main__":
    main()
