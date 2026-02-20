"""
Part 1: Exploratory Data Quality Analysis

Profiles the raw customer data to identify completeness, type mismatches,
format inconsistencies, uniqueness violations, and invalid values.
"""

import pandas as pd


def profile_data(df: pd.DataFrame) -> dict:
    """
    Analyse the raw DataFrame and return a structured profile dictionary.

    Returns
    -------
    dict with keys: completeness, data_types, quality_issues, severity
    """
    profile = {
        "completeness": {},
        "data_types": {},
        "quality_issues": [],
        "severity": {"critical": 0, "high": 0, "medium": 0},
    }

    total_rows = len(df)

    # --- Completeness ---
    for col in df.columns:
        missing = int(df[col].isnull().sum())
        pct = round(100 * (1 - missing / total_rows), 1)
        profile["completeness"][col] = {"pct": pct, "missing": missing}

    # --- Data types ---
    expected_types = {
        "customer_id": "INT",
        "first_name": "STRING",
        "last_name": "STRING",
        "email": "STRING",
        "phone": "STRING",
        "date_of_birth": "DATE",
        "address": "STRING",
        "income": "NUMERIC",
        "account_status": "STRING",
        "created_date": "DATE",
    }
    for col in df.columns:
        detected = str(df[col].dtype)
        expected = expected_types.get(col, "UNKNOWN")
        ok = True
        if expected == "DATE" and detected == "object":
            ok = False
        if expected == "NUMERIC" and detected == "object":
            ok = False
        profile["data_types"][col] = {
            "detected": detected,
            "expected": expected,
            "ok": ok,
        }

    # --- Quality Issues ---
    # Invalid dates
    for col in ["date_of_birth", "created_date"]:
        if col in df.columns:
            parsed = pd.to_datetime(df[col], errors="coerce")
            invalid = df[parsed.isna() & df[col].notna()]
            if not invalid.empty:
                vals = invalid[col].tolist()
                profile["quality_issues"].append(
                    {
                        "column": col,
                        "issue": "Invalid date values",
                        "examples": vals,
                        "rows_affected": len(vals),
                    }
                )
                profile["severity"]["high"] += 1

    # Non-numeric income
    if "income" in df.columns:
        parsed = pd.to_numeric(df["income"], errors="coerce")
        invalid = df[parsed.isna() & df["income"].notna()]
        if not invalid.empty:
            vals = invalid["income"].tolist()
            profile["quality_issues"].append(
                {
                    "column": "income",
                    "issue": "Non-numeric income values",
                    "examples": vals,
                    "rows_affected": len(vals),
                }
            )
            profile["severity"]["critical"] += 1

    # Invalid account_status
    if "account_status" in df.columns:
        valid_statuses = ["active", "inactive", "suspended"]
        invalid = df[
            ~df["account_status"].isin(valid_statuses) & df["account_status"].notna()
        ]
        if not invalid.empty:
            vals = invalid["account_status"].tolist()
            profile["quality_issues"].append(
                {
                    "column": "account_status",
                    "issue": "Invalid status values",
                    "examples": vals,
                    "rows_affected": len(vals),
                }
            )
            profile["severity"]["high"] += 1

    # Missing names
    for col in ["first_name", "last_name"]:
        missing = df[col].isnull().sum()
        if missing > 0:
            profile["quality_issues"].append(
                {
                    "column": col,
                    "issue": f"Missing {col}",
                    "examples": [f"Row {i+2}" for i in df[df[col].isnull()].index],
                    "rows_affected": int(missing),
                }
            )
            profile["severity"]["medium"] += 1

    # Missing address
    if "address" in df.columns:
        missing = df["address"].isnull().sum()
        if missing > 0:
            profile["quality_issues"].append(
                {
                    "column": "address",
                    "issue": "Missing address",
                    "examples": [f"Row {i+2}" for i in df[df["address"].isnull()].index],
                    "rows_affected": int(missing),
                }
            )
            profile["severity"]["medium"] += 1

    # Inconsistent phone formats
    if "phone" in df.columns:
        formats_found = set()
        for val in df["phone"].dropna():
            s = str(val).strip()
            if "(" in s:
                formats_found.add("(XXX) XXX-XXXX")
            elif "." in s:
                formats_found.add("XXX.XXX.XXXX")
            elif "-" in s:
                formats_found.add("XXX-XXX-XXXX")
            elif s.isdigit():
                formats_found.add("XXXXXXXXXX (no separators)")
        if len(formats_found) > 1:
            profile["quality_issues"].append(
                {
                    "column": "phone",
                    "issue": "Inconsistent phone formats",
                    "examples": list(formats_found),
                    "rows_affected": len(df),
                }
            )
            profile["severity"]["medium"] += 1

    # Uniqueness check on customer_id
    if "customer_id" in df.columns:
        dupes = df["customer_id"].duplicated().sum()
        if dupes > 0:
            profile["quality_issues"].append(
                {
                    "column": "customer_id",
                    "issue": "Duplicate customer_id values",
                    "examples": df[df["customer_id"].duplicated()]["customer_id"].tolist(),
                    "rows_affected": int(dupes),
                }
            )
            profile["severity"]["critical"] += 1

    return profile


def generate_report(profile: dict) -> str:
    """Render the profile dict as a formatted text report."""
    lines = ["DATA QUALITY PROFILE REPORT", "===========================", ""]

    # Completeness
    lines.append("COMPLETENESS:")
    for col, info in profile["completeness"].items():
        status = f"{info['missing']} missing" if info["missing"] else "complete"
        lines.append(f"- {col}: {info['pct']}% ({status})")
    lines.append("")

    # Data types
    lines.append("DATA TYPES:")
    for col, info in profile["data_types"].items():
        marker = "✓" if info["ok"] else "✗"
        note = f" (should be {info['expected']})" if not info["ok"] else ""
        lines.append(f"- {col}: {info['detected'].upper()} {marker}{note}")
    lines.append("")

    # Quality issues
    lines.append("QUALITY ISSUES:")
    for i, issue in enumerate(profile["quality_issues"], 1):
        lines.append(
            f"{i}. [{issue['column']}] {issue['issue']} "
            f"({issue['rows_affected']} rows affected)"
        )
        lines.append(f"   Examples: {issue['examples']}")
    lines.append("")

    # Severity
    sev = profile["severity"]
    lines.append("SEVERITY:")
    lines.append(f"- Critical (blocks processing): {sev['critical']}")
    lines.append(f"- High (data incorrect): {sev['high']}")
    lines.append(f"- Medium (needs cleaning): {sev['medium']}")

    return "\n".join(lines)
