import pandas as pd
from src.profiling.profiler import profile_data, generate_report


# ---------------------------------------------------------------------------
# profile_data() tests
# ---------------------------------------------------------------------------

def test_profile_completeness_all_present():
    df = pd.DataFrame({
        "customer_id": [1, 2],
        "first_name": ["Alice", "Bob"],
        "last_name": ["Smith", "Jones"],
        "email": ["a@b.com", "c@d.com"],
        "phone": ["555-123-4567", "555-987-6543"],
        "date_of_birth": ["1990-01-01", "1985-06-15"],
        "address": ["123 Main St", "456 Oak Ave"],
        "income": [50000, 60000],
        "account_status": ["active", "inactive"],
        "created_date": ["2024-01-01", "2024-02-01"],
    })
    profile = profile_data(df)
    assert profile["completeness"]["customer_id"]["pct"] == 100.0
    assert profile["completeness"]["customer_id"]["missing"] == 0


def test_profile_completeness_with_missing():
    df = pd.DataFrame({
        "customer_id": [1, 2, 3],
        "first_name": ["Alice", None, "Charlie"],
        "last_name": ["A", "B", "C"],
    })
    profile = profile_data(df)
    assert profile["completeness"]["first_name"]["missing"] == 1
    assert profile["completeness"]["first_name"]["pct"] == 66.7


def test_profile_data_types_match():
    df = pd.DataFrame({
        "customer_id": [1],
        "first_name": ["Alice"],
        "last_name": ["Smith"],
        "email": ["a@b.com"],
        "phone": ["555-123-4567"],
        "date_of_birth": ["1990-01-01"],
        "address": ["123 Main Street"],
        "income": [50000.0],
        "account_status": ["active"],
        "created_date": ["2024-01-01"],
    })
    profile = profile_data(df)
    assert profile["data_types"]["customer_id"]["ok"] is True
    assert profile["data_types"]["first_name"]["ok"] is True


def test_profile_data_type_mismatch_income():
    df = pd.DataFrame({
        "customer_id": [1],
        "first_name": ["Alice"],
        "last_name": ["Smith"],
        "income": ["not_a_number"],
    })
    profile = profile_data(df)
    # income column is object type but expected NUMERIC → ok should be False
    assert profile["data_types"]["income"]["ok"] is False


def test_profile_detects_invalid_dates():
    df = pd.DataFrame({
        "customer_id": [1],
        "first_name": ["Alice"],
        "last_name": ["Smith"],
        "date_of_birth": ["invalid_date"],
    })
    profile = profile_data(df)
    date_issues = [i for i in profile["quality_issues"] if i["column"] == "date_of_birth"]
    assert len(date_issues) == 1
    assert date_issues[0]["issue"] == "Invalid date values"
    assert profile["severity"]["high"] >= 1


def test_profile_detects_non_numeric_income():
    df = pd.DataFrame({
        "customer_id": [1],
        "first_name": ["Alice"],
        "last_name": ["Smith"],
        "income": ["abc"],
    })
    profile = profile_data(df)
    income_issues = [i for i in profile["quality_issues"] if i["column"] == "income"]
    assert len(income_issues) == 1
    assert income_issues[0]["issue"] == "Non-numeric income values"
    assert profile["severity"]["critical"] >= 1


def test_profile_detects_invalid_account_status():
    df = pd.DataFrame({
        "customer_id": [1],
        "first_name": ["Alice"],
        "last_name": ["Smith"],
        "account_status": ["bogus_status"],
    })
    profile = profile_data(df)
    status_issues = [i for i in profile["quality_issues"] if i["column"] == "account_status"]
    assert len(status_issues) == 1
    assert status_issues[0]["issue"] == "Invalid status values"


def test_profile_valid_account_status_no_issue():
    df = pd.DataFrame({
        "customer_id": [1],
        "first_name": ["Alice"],
        "last_name": ["Smith"],
        "account_status": ["active"],
    })
    profile = profile_data(df)
    status_issues = [i for i in profile["quality_issues"] if i["column"] == "account_status"]
    assert len(status_issues) == 0


def test_profile_detects_missing_names():
    df = pd.DataFrame({
        "customer_id": [1, 2],
        "first_name": [None, "Bob"],
        "last_name": ["Smith", None],
    })
    profile = profile_data(df)
    name_issues = [i for i in profile["quality_issues"] if "Missing" in i["issue"]]
    assert len(name_issues) == 2
    assert profile["severity"]["medium"] >= 2


def test_profile_detects_missing_address():
    df = pd.DataFrame({
        "customer_id": [1],
        "first_name": ["Alice"],
        "last_name": ["Smith"],
        "address": [None],
    })
    profile = profile_data(df)
    addr_issues = [i for i in profile["quality_issues"] if i["column"] == "address"]
    assert len(addr_issues) == 1


def test_profile_detects_inconsistent_phone_formats():
    df = pd.DataFrame({
        "customer_id": [1, 2, 3],
        "first_name": ["A", "B", "C"],
        "last_name": ["A", "B", "C"],
        "phone": ["555.123.4567", "(555) 987-6543", "5551234567"],
    })
    profile = profile_data(df)
    phone_issues = [i for i in profile["quality_issues"] if i["column"] == "phone"]
    assert len(phone_issues) == 1
    assert phone_issues[0]["issue"] == "Inconsistent phone formats"


def test_profile_detects_duplicate_customer_ids():
    df = pd.DataFrame({
        "customer_id": [1, 1, 2],
        "first_name": ["A", "B", "C"],
        "last_name": ["A", "B", "C"],
    })
    profile = profile_data(df)
    dupe_issues = [i for i in profile["quality_issues"] if i["column"] == "customer_id"]
    assert len(dupe_issues) == 1
    assert dupe_issues[0]["issue"] == "Duplicate customer_id values"
    assert profile["severity"]["critical"] >= 1


def test_profile_no_issues_on_clean_data():
    df = pd.DataFrame({
        "customer_id": [1, 2],
        "first_name": ["Alice", "Bob"],
        "last_name": ["Smith", "Jones"],
        "income": [50000.0, 60000.0],
        "account_status": ["active", "inactive"],
        "date_of_birth": ["1990-01-01", "1985-06-15"],
        "phone": ["555-123-4567", "555-987-6543"],
        "address": ["123 Main St", "456 Oak Ave"],
    })
    profile = profile_data(df)
    assert profile["severity"]["critical"] == 0
    assert profile["severity"]["high"] == 0


# ---------------------------------------------------------------------------
# generate_report() tests
# ---------------------------------------------------------------------------

def test_generate_report_contains_sections():
    df = pd.DataFrame({
        "customer_id": [1],
        "first_name": ["Alice"],
        "last_name": ["Smith"],
    })
    profile = profile_data(df)
    report = generate_report(profile)
    assert "DATA QUALITY PROFILE REPORT" in report
    assert "COMPLETENESS:" in report
    assert "DATA TYPES:" in report
    assert "QUALITY ISSUES:" in report
    assert "SEVERITY:" in report


def test_generate_report_shows_missing_info():
    df = pd.DataFrame({
        "customer_id": [1, 2],
        "first_name": [None, "Bob"],
        "last_name": ["Smith", "Jones"],
    })
    profile = profile_data(df)
    report = generate_report(profile)
    assert "1 missing" in report
