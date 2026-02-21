"""
Part 4: Data Cleaning

Normalizes formats (phone, dates, names), handles missing values,
and fixes known structural issues (row misalignment) in the raw dataset.
"""

import re
import datetime

import numpy as np
import pandas as pd


def clean_data(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """
    Clean the raw DataFrame and return a cleaned copy along with a log
    of actions taken.

    Returns
    -------
    (cleaned_df, log_lines)
    """
    log = []
    df_clean = df.copy()

    # -----------------------------------------------------------------
    # 1. Fix Misaligned Rows
    #    Row 2 (Jane Smith) is missing `address`, causing fields to shift
    #    left. Detectable because `account_status` contains a date.
    # -----------------------------------------------------------------
    date_in_status = df_clean["account_status"].astype(str).str.match(r"\d{4}-\d{2}-\d{2}")
    if date_in_status.any():
        for idx in df_clean[date_in_status].index:
            val_address = df_clean.at[idx, "address"]      # actually income
            val_income = df_clean.at[idx, "income"]         # actually status
            val_status = df_clean.at[idx, "account_status"] # actually created_date

            df_clean.at[idx, "income"] = val_address
            df_clean.at[idx, "account_status"] = val_income
            df_clean.at[idx, "created_date"] = val_status
            df_clean.at[idx, "address"] = None
            log.append(f"Fixed column misalignment for Row {idx + 2}")

    # -----------------------------------------------------------------
    # 2. Normalize Phone Numbers → XXX-XXX-XXXX
    # -----------------------------------------------------------------
    def normalize_phone(p):
        if pd.isna(p):
            return p
        digits = re.sub(r"\D", "", str(p))
        if len(digits) == 10:
            return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
        return str(p)

    phone_before = df_clean["phone"].tolist()
    df_clean["phone"] = df_clean["phone"].apply(normalize_phone)
    phone_changes = sum(1 for a, b in zip(phone_before, df_clean["phone"]) if a != b)
    if phone_changes:
        log.append(f"Phone format: Converted {phone_changes} rows to XXX-XXX-XXXX")

    # -----------------------------------------------------------------
    # 3. Normalize Dates → YYYY-MM-DD
    # -----------------------------------------------------------------
    def normalize_date(d):
        if pd.isna(d):
            return d
        s = str(d).strip()
        if s.lower() == "invalid_date":
            return None
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
            try:
                return datetime.datetime.strptime(s, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None

    for col in ["date_of_birth", "created_date"]:
        before = df_clean[col].tolist()
        df_clean[col] = df_clean[col].apply(normalize_date)
        changes = sum(1 for a, b in zip(before, df_clean[col]) if str(a) != str(b))
        if changes:
            log.append(f"Date format in {col}: Normalized {changes} rows to YYYY-MM-DD")

    # -----------------------------------------------------------------
    # 4. Name Case → Title Case
    # -----------------------------------------------------------------
    for col in ["first_name", "last_name"]:
        before = df_clean[col].copy()
        df_clean[col] = (
            df_clean[col]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.title()
        )
        # Restore true missing values
        df_clean[col] = df_clean[col].replace({"Nan": np.nan, "": np.nan})
        changes = sum(
            1
            for a, b in zip(before, df_clean[col])
            if pd.notna(a) and a != b
        )
        if changes:
            log.append(f"Name case in {col}: Title-cased {changes} rows")

    # -----------------------------------------------------------------
    # 5. Handle Missing Values
    # -----------------------------------------------------------------
    defaults = {
        "first_name": "[UNKNOWN]",
        "last_name": "[UNKNOWN]",
        "address": "[MISSING ADDRESS]",
        "income": 0,
        "account_status": "unknown",
        "email": "missing@example.com",
        "phone": "000-000-0000",
        "date_of_birth": "1900-01-01",
        "created_date": datetime.date.today().strftime("%Y-%m-%d"),
    }
    for col, default_val in defaults.items():
        if col in df_clean.columns:
            missing_count = int(df_clean[col].isnull().sum())
            if missing_count > 0:
                df_clean[col].fillna(default_val, inplace=True)
                log.append(f"Missing {col}: {missing_count} rows filled with '{default_val}'")

    return df_clean, log


def generate_report(log: list[str]) -> str:
    """Render the cleaning log as a formatted text report."""
    lines = [
        "DATA CLEANING LOG",
        "=================",
        "",
        "ACTIONS TAKEN:",
        "--------------",
    ]
    for entry in log:
        lines.append(f"- {entry}")
    return "\n".join(lines)
