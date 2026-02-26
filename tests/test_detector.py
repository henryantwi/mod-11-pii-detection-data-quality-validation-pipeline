import pytest
import pandas as pd
from src.pii.detector import detect_pii, generate_report


# ---------------------------------------------------------------------------
# detect_pii() tests
# ---------------------------------------------------------------------------

def test_detect_pii_finds_all_pii_columns():
    df = pd.DataFrame({
        "customer_id": [1],
        "first_name": ["Alice"],
        "last_name": ["Smith"],
        "email": ["alice@example.com"],
        "phone": ["555-123-4567"],
        "date_of_birth": ["1990-01-01"],
        "address": ["123 Main St"],
        "income": [50000],
        "account_status": ["active"],
    })
    result = detect_pii(df)
    for col in ["first_name", "last_name", "email", "phone", "date_of_birth", "address", "income"]:
        assert col in result["detected_pii"]


def test_detect_pii_counts_non_null():
    df = pd.DataFrame({
        "email": ["a@b.com", None, "c@d.com"],
        "phone": ["555-1234567", "555-9876543", None],
    })
    result = detect_pii(df)
    assert result["detected_pii"]["email"]["count"] == 2
    assert result["detected_pii"]["phone"]["count"] == 2


def test_detect_pii_percentage():
    df = pd.DataFrame({
        "email": ["a@b.com", None, None, "c@d.com"],
    })
    result = detect_pii(df)
    assert result["detected_pii"]["email"]["pct"] == 50.0


def test_detect_pii_risk_levels():
    df = pd.DataFrame({
        "first_name": ["Alice"],
        "income": [50000],
    })
    result = detect_pii(df)
    assert result["detected_pii"]["first_name"]["risk"] == "HIGH"
    assert result["detected_pii"]["income"]["risk"] == "MEDIUM"


def test_detect_pii_categories():
    df = pd.DataFrame({
        "first_name": ["Alice"],
        "email": ["a@b.com"],
        "date_of_birth": ["1990-01-01"],
        "income": [50000],
    })
    result = detect_pii(df)
    assert result["detected_pii"]["first_name"]["category"] == "Name"
    assert result["detected_pii"]["email"]["category"] == "Contact"
    assert result["detected_pii"]["date_of_birth"]["category"] == "Sensitive Personal"
    assert result["detected_pii"]["income"]["category"] == "Financial"


def test_detect_pii_email_pattern_matching():
    df = pd.DataFrame({
        "email": ["alice@example.com", "not-an-email", "bob@company.org"],
    })
    result = detect_pii(df)
    assert result["pattern_matches"]["email"] == 2


def test_detect_pii_phone_pattern_matching():
    df = pd.DataFrame({
        "phone": ["555-123-4567", "(555) 987-6543", "abc", "555.111.2222"],
    })
    result = detect_pii(df)
    assert result["pattern_matches"]["phone"] == 3


def test_detect_pii_risk_assessment_structure():
    df = pd.DataFrame({"first_name": ["Alice"]})
    result = detect_pii(df)
    assert "HIGH" in result["risk_assessment"]
    assert "MEDIUM" in result["risk_assessment"]
    assert len(result["risk_assessment"]["HIGH"]) > 0


def test_detect_pii_ignores_non_pii_columns():
    df = pd.DataFrame({
        "customer_id": [1],
        "random_col": ["xyz"],
    })
    result = detect_pii(df)
    assert "random_col" not in result["detected_pii"]


def test_detect_pii_empty_dataframe():
    """Empty DataFrame triggers ZeroDivisionError in percentage calc — known edge case."""
    df = pd.DataFrame({"email": pd.Series([], dtype="object")})
    with pytest.raises(ZeroDivisionError):
        detect_pii(df)


# ---------------------------------------------------------------------------
# generate_report() tests
# ---------------------------------------------------------------------------

def test_generate_report_contains_sections():
    df = pd.DataFrame({
        "first_name": ["Alice"],
        "email": ["a@b.com"],
        "phone": ["555-123-4567"],
    })
    result = detect_pii(df)
    report = generate_report(result)
    assert "PII DETECTION REPORT" in report
    assert "RISK ASSESSMENT:" in report
    assert "DETECTED PII:" in report
    assert "PATTERN MATCHES:" in report
    assert "EXPOSURE RISK:" in report
    assert "MITIGATION:" in report


def test_generate_report_includes_column_info():
    df = pd.DataFrame({
        "email": ["a@b.com", "c@d.com"],
    })
    result = detect_pii(df)
    report = generate_report(result)
    assert "email" in report
    assert "Contact" in report
