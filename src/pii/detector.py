"""
Part 2: PII Detection

Identifies personally identifiable information in the dataset using
regex pattern matching and column-level classification.
"""

import re
import pandas as pd


# PII classification map
PII_COLUMNS = {
    "first_name": {"category": "Name", "risk": "HIGH"},
    "last_name": {"category": "Name", "risk": "HIGH"},
    "email": {"category": "Contact", "risk": "HIGH"},
    "phone": {"category": "Contact", "risk": "HIGH"},
    "date_of_birth": {"category": "Sensitive Personal", "risk": "HIGH"},
    "address": {"category": "Sensitive Personal", "risk": "HIGH"},
    "income": {"category": "Financial", "risk": "MEDIUM"},
}

# Regex patterns for PII detection
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(r"\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}")


def detect_pii(df: pd.DataFrame) -> dict:
    """
    Scan the DataFrame for PII and return a structured detection result.

    Returns
    -------
    dict with keys: risk_assessment, detected_pii, exposure_risk
    """
    total_rows = len(df)
    result = {
        "risk_assessment": {
            "HIGH": ["Names", "Emails", "Phone numbers", "Addresses", "Dates of birth"],
            "MEDIUM": ["Income (financial sensitivity)"],
        },
        "detected_pii": {},
        "pattern_matches": {},
    }

    # Count non-null values per PII column
    for col, info in PII_COLUMNS.items():
        if col in df.columns:
            count = int(df[col].notna().sum())
            pct = round(100 * count / total_rows, 1)
            result["detected_pii"][col] = {
                "category": info["category"],
                "risk": info["risk"],
                "count": count,
                "pct": pct,
            }

    # Pattern-based detection for emails
    if "email" in df.columns:
        matches = int(
            df["email"].astype(str).apply(lambda x: bool(EMAIL_PATTERN.search(x))).sum()
        )
        result["pattern_matches"]["email"] = matches

    # Pattern-based detection for phones
    if "phone" in df.columns:
        matches = int(
            df["phone"].astype(str).apply(lambda x: bool(PHONE_PATTERN.search(x))).sum()
        )
        result["pattern_matches"]["phone"] = matches

    return result


def generate_report(detection: dict) -> str:
    """Render the PII detection result as a formatted text report."""
    lines = ["PII DETECTION REPORT", "======================", ""]

    # Risk assessment
    lines.append("RISK ASSESSMENT:")
    for level, items in detection["risk_assessment"].items():
        lines.append(f"- {level}: {', '.join(items)}")
    lines.append("")

    # Detected PII
    lines.append("DETECTED PII:")
    for col, info in detection["detected_pii"].items():
        lines.append(
            f"- {col} ({info['category']}): {info['count']} rows ({info['pct']}%)"
        )
    lines.append("")

    # Pattern matches
    if detection["pattern_matches"]:
        lines.append("PATTERN MATCHES:")
        for field, count in detection["pattern_matches"].items():
            lines.append(f"- {field}: {count} values matched regex pattern")
        lines.append("")

    # Exposure risk
    lines.append("EXPOSURE RISK:")
    lines.append("If this dataset were breached, attackers could:")
    lines.append("- Phish customers using their email addresses")
    lines.append("- Spoof identities using names + DOB + address")
    lines.append("- Social-engineer targets using phone numbers")
    lines.append("- Assess financial standing using income data")
    lines.append("")

    # Mitigation
    lines.append("MITIGATION:")
    lines.append("- Mask all PII before sharing with analytics teams")
    lines.append("- Apply role-based access control to raw data")
    lines.append("- Encrypt PII at rest and in transit")
    lines.append("- Conduct regular access audits")

    return "\n".join(lines)
