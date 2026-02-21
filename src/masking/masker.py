"""
Part 5: PII Masking

Provides functions to mask sensitive data while preserving its format
(e.g., keeping email domains, masking names, hiding exact dates/phones)
so the data remains useful for analytics without exposing privacy.
"""

import pandas as pd


def mask_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mask PII fields in a DataFrame.

    Returns
    -------
    pd.DataFrame: A new DataFrame with masked values.
    """
    masked_df = df.copy()

    def mask_email(email):
        if pd.isna(email) or "@" not in str(email):
            return email
        user, domain = str(email).split("@", 1)
        if len(user) > 1:
            return f"{user[0]}***@{domain}"
        return f"***@{domain}"

    def mask_phone(phone):
        if pd.isna(phone):
            return phone
        p = str(phone)
        if len(p) >= 4:
            return f"***-***-{p[-4:]}"
        return "***-***-****"

    def mask_name(name):
        if pd.isna(name):
            return name
        n = str(name)
        if len(n) > 1:
            return f"{n[0]}***"
        return "***"

    def mask_address(addr):
        return "[MASKED ADDRESS]" if pd.notna(addr) else addr

    def mask_dob(dob):
        if pd.isna(dob):
            return dob
        d = str(dob)
        if len(d) >= 4:
            return f"{d[:4]}-**-**"
        return "****-**-**"

    if "email" in masked_df.columns:
        masked_df["email"] = masked_df["email"].apply(mask_email)
    if "phone" in masked_df.columns:
        masked_df["phone"] = masked_df["phone"].apply(mask_phone)
    if "first_name" in masked_df.columns:
        masked_df["first_name"] = masked_df["first_name"].apply(mask_name)
    if "last_name" in masked_df.columns:
        masked_df["last_name"] = masked_df["last_name"].apply(mask_name)
    if "address" in masked_df.columns:
        masked_df["address"] = masked_df["address"].apply(mask_address)
    if "date_of_birth" in masked_df.columns:
        masked_df["date_of_birth"] = masked_df["date_of_birth"].apply(mask_dob)

    return masked_df


def generate_sample_report(original_df: pd.DataFrame, masked_df: pd.DataFrame, num_rows: int = 2) -> str:
    """Render a text report showing a before/after comparison of masking."""
    lines = [
        f"BEFORE MASKING (first {num_rows} rows):",
        "-" * 30,
        original_df.head(num_rows).to_csv(index=False).strip(),
        "",
        f"AFTER MASKING (first {num_rows} rows):",
        "-" * 30,
        masked_df.head(num_rows).to_csv(index=False).strip(),
        "",
        "ANALYSIS:",
        "- Data structure preserved (rows and columns intact)",
        "- PII masked (names, emails, phones, addresses, DOBs hidden)",
        "- Business data intact (income, account_status, created_dates remain)",
        "- Use case: Safe for internal analytics (Privacy-preserving)"
    ]
    return "\n".join(lines)
