import pandas as pd
from src.cleaning.cleaner import clean_data, generate_report

def test_clean_data_normalizes_phones():
    # Arrange
    raw_data = {"phone": ["555.123.4567", "(555) 987-6543", "5551112222", "invalid_phone"]}
    df = pd.DataFrame(raw_data)
    
    # Act
    cleaned_df, _ = clean_data(df)
    
    # Assert
    assert cleaned_df["phone"].iloc[0] == "555-123-4567"
    assert cleaned_df["phone"].iloc[1] == "555-987-6543"
    assert cleaned_df["phone"].iloc[2] == "555-111-2222"
    assert cleaned_df["phone"].iloc[3] == "invalid_phone"  # Leaves unchanged if not 10 digits

def test_clean_data_normalizes_dates():
    # Arrange
    raw_data = {"date_of_birth": ["1990/05/20", "01/15/1985", "invalid_date", None]}
    df = pd.DataFrame(raw_data)
    
    # Act
    cleaned_df, _ = clean_data(df)
    
    # Assert
    assert cleaned_df["date_of_birth"].iloc[0] == "1990-05-20"
    assert cleaned_df["date_of_birth"].iloc[1] == "1985-01-15"
    assert cleaned_df["date_of_birth"].iloc[2] == "1900-01-01"  # invalid_date is nullified then filled
    assert cleaned_df["date_of_birth"].iloc[3] == "1900-01-01"  # Default for missing DOB

def test_clean_data_fixes_shifted_rows():
    # Arrange: Simulate the shifted row problem
    raw_data = {
        "address": [100000],          # Income slipped here
        "income": ["active"],         # Status slipped here
        "account_status": ["2024-01-01"],  # Date slipped here
        "created_date": [None],       # None
    }
    df = pd.DataFrame(raw_data)
    
    # Act
    cleaned_df, log = clean_data(df)
    
    # Assert
    assert cleaned_df["address"].iloc[0] == "[MISSING ADDRESS]"
    assert cleaned_df["income"].iloc[0] == 100000
    assert cleaned_df["account_status"].iloc[0] == "active"
    assert cleaned_df["created_date"].iloc[0] == "2024-01-01"
    assert any("Fixed column misalignment" in entry for entry in log)


def test_clean_data_title_cases_names():
    raw_data = {
        "first_name": ["alice", "BOB", "charlie brown"],
        "last_name": ["smith", "JONES", "de la cruz"],
    }
    df = pd.DataFrame(raw_data)
    cleaned_df, _ = clean_data(df)
    assert cleaned_df["first_name"].iloc[0] == "Alice"
    assert cleaned_df["first_name"].iloc[1] == "Bob"
    assert cleaned_df["last_name"].iloc[0] == "Smith"
    assert cleaned_df["last_name"].iloc[1] == "Jones"


def test_clean_data_fills_missing_values():
    raw_data = {
        "first_name": [None],
        "last_name": [None],
        "email": [None],
        "phone": [None],
        "address": [None],
        "income": [None],
        "account_status": [None],
        "date_of_birth": [None],
    }
    df = pd.DataFrame(raw_data)
    cleaned_df, log = clean_data(df)
    assert cleaned_df["first_name"].iloc[0] == "[UNKNOWN]"
    assert cleaned_df["last_name"].iloc[0] == "[UNKNOWN]"
    assert cleaned_df["email"].iloc[0] == "missing@example.com"
    assert cleaned_df["phone"].iloc[0] == "000-000-0000"
    assert cleaned_df["income"].iloc[0] == 0
    assert cleaned_df["account_status"].iloc[0] == "unknown"
    assert cleaned_df["date_of_birth"].iloc[0] == "1900-01-01"
    assert any("Missing" in entry for entry in log)


def test_clean_data_normalizes_created_date():
    raw_data = {"created_date": ["01/15/2024", "2024/06/01"]}
    df = pd.DataFrame(raw_data)
    cleaned_df, _ = clean_data(df)
    assert cleaned_df["created_date"].iloc[0] == "2024-01-15"
    assert cleaned_df["created_date"].iloc[1] == "2024-06-01"


def test_clean_data_returns_copy():
    raw_data = {"first_name": ["alice"]}
    df = pd.DataFrame(raw_data)
    cleaned_df, _ = clean_data(df)
    assert cleaned_df is not df


def test_generate_report_format():
    log = ["Phone format: Converted 3 rows to XXX-XXX-XXXX", "Missing email: 1 rows filled with 'missing@example.com'"]
    report = generate_report(log)
    assert "DATA CLEANING LOG" in report
    assert "ACTIONS TAKEN:" in report
    assert "Phone format" in report
    assert "Missing email" in report


def test_generate_report_empty_log():
    report = generate_report([])
    assert "DATA CLEANING LOG" in report
