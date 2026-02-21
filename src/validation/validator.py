"""
Part 3: Data Validator Runner

Iterates over each row of the raw DataFrame, attempts to parse it through
the Pydantic CustomerRecord model, and collects validation failures with
detailed error messages per field.
"""

import pandas as pd
from pydantic import ValidationError

from src.validation.models import CustomerRecord


def validate_dataframe(df: pd.DataFrame) -> dict:
    """
    Validate every row in the DataFrame against the Pydantic model.

    Returns
    -------
    dict with keys: pass_count, fail_count, failures (list of dicts)
    """
    failures = []
    pass_count = 0
    fail_count = 0

    for idx, row in df.iterrows():
        row_num = idx + 2  # +2 for 1-based + header row

        # Build a dict from the row, converting NaN to None
        record = {}
        for col in df.columns:
            val = row[col]
            if pd.isna(val):
                record[col] = None
            else:
                record[col] = val

        try:
            CustomerRecord(**record)
            pass_count += 1
        except ValidationError as e:
            fail_count += 1
            for error in e.errors():
                field = error["loc"][0] if error["loc"] else "unknown"
                failures.append(
                    {
                        "row": row_num,
                        "field": str(field),
                        "value": str(record.get(str(field), "N/A")),
                        "error": error["msg"],
                    }
                )

    return {
        "pass_count": pass_count,
        "fail_count": fail_count,
        "failures": failures,
    }


def generate_report(result: dict) -> str:
    """Render the validation result as a formatted text report."""
    lines = ["VALIDATION RESULTS", "==================", ""]

    lines.append(f"PASS: {result['pass_count']} rows passed all checks")
    lines.append(f"FAIL: {result['fail_count']} rows failed")
    lines.append("")

    # Group failures by field
    by_field: dict[str, list] = {}
    for f in result["failures"]:
        by_field.setdefault(f["field"], []).append(f)

    lines.append("FAILURES BY COLUMN:")
    lines.append("-------------------")

    for field, fails in by_field.items():
        lines.append(f"{field}:")
        for f in fails:
            lines.append(f"- Row {f['row']}: '{f['value']}' ({f['error']})")
        lines.append("")

    return "\n".join(lines)
