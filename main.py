"""
Pipeline Orchestrator

Ties together all modular pipeline stages:
1. Profiling
2. PII Detection
3. Validation
4. Cleaning
5. Masking
"""

import os
import datetime

import pandas as pd

from src.profiling import profiler
from src.pii import detector
from src.validation import validator
from src.cleaning import cleaner
from src.masking import masker


# Configuration paths
DATA_DIR = "data"
REPORTS_DIR = "reports"
RAW_FILE = "customers_raw.csv"

# Ensure output directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)


def write_report(filename: str, content: str):
    """Utility to write text content to a report file."""
    filepath = os.path.join(REPORTS_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Wrote {filepath}")


def run_pipeline():
    start_time = datetime.datetime.now()
    exec_log = [
        "PIPELINE EXECUTION REPORT",
        "=========================",
        "",
        f"Timestamp: {start_time}",
        "",
    ]

    print("--- Starting Pipeline ---")

    # -----------------------------------------------------------------
    # Stage 1: Load
    # -----------------------------------------------------------------
    exec_log.append("Stage 1: LOAD")
    try:
        df_raw = pd.read_csv(RAW_FILE, skipinitialspace=True)
        exec_log.append(f"✓ Loaded {RAW_FILE} - {len(df_raw)} rows")
    except Exception as e:
        exec_log.append(f"X Failed to load data: {e}")
        write_report("pipeline_execution_report.txt", "\n".join(exec_log))
        return
    exec_log.append("")

    # -----------------------------------------------------------------
    # Stage 2: Profile (Quality Analysis)
    # -----------------------------------------------------------------
    exec_log.append("Stage 2: PROFILE")
    profile_data = profiler.profile_data(df_raw)
    profile_report = profiler.generate_report(profile_data)
    write_report("data_quality_report.txt", profile_report)
    exec_log.append("✓ Generated data_quality_report.txt")
    exec_log.append("")

    # -----------------------------------------------------------------
    # Stage 3: Detect PII
    # -----------------------------------------------------------------
    exec_log.append("Stage 3: DETECT PII")
    pii_data = detector.detect_pii(df_raw)
    pii_report = detector.generate_report(pii_data)
    write_report("pii_detection_report.txt", pii_report)
    exec_log.append("✓ Generated pii_detection_report.txt")
    exec_log.append("")

    # -----------------------------------------------------------------
    # Stage 4: Validate (Pre-clean)
    # -----------------------------------------------------------------
    exec_log.append("Stage 4: VALIDATE (RAW)")
    val_data = validator.validate_dataframe(df_raw)
    val_report = validator.generate_report(val_data)
    write_report("validation_results.txt", val_report)
    exec_log.append(f"✓ Raw Validation complete. {val_data['fail_count']} rows failed.")
    exec_log.append("")

    # -----------------------------------------------------------------
    # Stage 5: Clean
    # -----------------------------------------------------------------
    exec_log.append("Stage 5: CLEAN")
    df_clean, cleaning_log_entries = cleaner.clean_data(df_raw)
    cleaning_report = cleaner.generate_report(cleaning_log_entries)
    write_report("cleaning_log.txt", cleaning_report)

    cleaned_csv = os.path.join(DATA_DIR, "customers_cleaned.csv")
    df_clean.to_csv(cleaned_csv, index=False)
    exec_log.append("✓ Cleaned data and saved to customers_cleaned.csv")
    exec_log.append("")

    # -----------------------------------------------------------------
    # Stage 6: Validate (Post-clean)
    # -----------------------------------------------------------------
    exec_log.append("Stage 6: VALIDATE (CLEANED)")
    val_clean_data = validator.validate_dataframe(df_clean)
    # Could write this to a separate file, but we'll just log it
    # val_clean_report = validator.generate_report(val_clean_data)
    exec_log.append(
        f"✓ Re-validation complete. {val_clean_data['fail_count']} rows failed."
    )
    exec_log.append("")

    # -----------------------------------------------------------------
    # Stage 7: Mask & Save
    # -----------------------------------------------------------------
    exec_log.append("Stage 7: MASK & SAVE")
    df_masked = masker.mask_data(df_clean)
    
    masked_csv = os.path.join(DATA_DIR, "customers_masked.csv")
    df_masked.to_csv(masked_csv, index=False)
    
    sample_report = masker.generate_sample_report(df_raw, df_masked)
    write_report("masked_sample.txt", sample_report)
    exec_log.append("✓ Masked PII and saved output to customers_masked.csv")
    exec_log.append("✓ Generated masked_sample.txt")
    exec_log.append("")

    # -----------------------------------------------------------------
    # Finalize
    # -----------------------------------------------------------------
    exec_log.append("SUMMARY:")
    exec_log.append(f"- Input: {len(df_raw)} rows")
    exec_log.append(f"- Output: {len(df_clean)} rows")
    exec_log.append("Status: SUCCESS ✓")

    write_report("pipeline_execution_report.txt", "\n".join(exec_log))
    print("--- Pipeline Finished ---")


if __name__ == "__main__":
    run_pipeline()
