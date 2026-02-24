import pandas as pd
from src.cleaning.cleaner import clean_data

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
