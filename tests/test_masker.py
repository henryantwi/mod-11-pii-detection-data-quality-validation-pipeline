import pandas as pd
from src.masking.masker import mask_data, generate_sample_report

def test_mask_data_redacts_email():
    # Arrange
    raw_data = {"email": ["john.doe@gmail.com", "jane@company.com", "invalid"]}
    df = pd.DataFrame(raw_data)
    
    # Act
    masked_df = mask_data(df)
    
    # Assert
    assert masked_df["email"].iloc[0] == "j***@gmail.com"
    assert masked_df["email"].iloc[1] == "j***@company.com"
    assert masked_df["email"].iloc[2] == "invalid"  # Leaves unchanged if no @

def test_mask_data_redacts_phone():
    # Arrange
    raw_data = {"phone": ["555-123-4567", "123", None]}
    df = pd.DataFrame(raw_data)
    
    # Act
    masked_df = mask_data(df)
    
    # Assert
    assert masked_df["phone"].iloc[0] == "***-***-4567"
    assert masked_df["phone"].iloc[1] == "***-***-****"  # Too short to keep 4 digits
    assert pd.isna(masked_df["phone"].iloc[2])

def test_mask_data_redacts_names_and_dob():
    # Arrange
    raw_data = {
        "first_name": ["Alice", "B"],
        "last_name": ["Smith", None],
        "date_of_birth": ["1990-05-20", "2000"]
    }
    df = pd.DataFrame(raw_data)
    
    # Act
    masked_df = mask_data(df)
    
    # Assert
    assert masked_df["first_name"].iloc[0] == "A***"
    assert masked_df["first_name"].iloc[1] == "***"
    assert masked_df["last_name"].iloc[0] == "S***"
    assert pd.isna(masked_df["last_name"].iloc[1])
    assert masked_df["date_of_birth"].iloc[0] == "1990-**-**"
    assert masked_df["date_of_birth"].iloc[1] == "2000-**-**"

def test_mask_data_redacts_address():
    # Arrange
    raw_data = {"address": ["123 Main St", None]}
    df = pd.DataFrame(raw_data)
    
    # Act
    masked_df = mask_data(df)
    
    # Assert
    assert masked_df["address"].iloc[0] == "[MASKED ADDRESS]"
    assert pd.isna(masked_df["address"].iloc[1])


def test_mask_data_preserves_non_pii_columns():
    raw_data = {
        "customer_id": [1, 2],
        "income": [50000, 60000],
        "account_status": ["active", "inactive"],
    }
    df = pd.DataFrame(raw_data)
    masked_df = mask_data(df)
    assert list(masked_df["customer_id"]) == [1, 2]
    assert list(masked_df["income"]) == [50000, 60000]
    assert list(masked_df["account_status"]) == ["active", "inactive"]


def test_mask_data_single_char_email():
    raw_data = {"email": ["a@example.com"]}
    df = pd.DataFrame(raw_data)
    masked_df = mask_data(df)
    # Single-char user part → fully masked per masker logic
    assert masked_df["email"].iloc[0] == "***@example.com"


def test_mask_data_dob_short_string():
    raw_data = {"date_of_birth": ["90"]}
    df = pd.DataFrame(raw_data)
    masked_df = mask_data(df)
    assert masked_df["date_of_birth"].iloc[0] == "****-**-**"


def test_mask_data_empty_dataframe():
    df = pd.DataFrame({"email": pd.Series([], dtype="object")})
    masked_df = mask_data(df)
    assert len(masked_df) == 0


def test_generate_sample_report_structure():
    original = pd.DataFrame({
        "first_name": ["Alice", "Bob"],
        "email": ["alice@example.com", "bob@example.com"],
        "income": [50000, 60000],
    })
    masked = mask_data(original)
    report = generate_sample_report(original, masked)
    assert "BEFORE MASKING" in report
    assert "AFTER MASKING" in report
    assert "ANALYSIS:" in report
    assert "PII masked" in report


def test_generate_sample_report_custom_rows():
    original = pd.DataFrame({
        "first_name": ["Alice", "Bob", "Charlie"],
        "income": [50000, 60000, 70000],
    })
    masked = mask_data(original)
    report = generate_sample_report(original, masked, num_rows=1)
    assert "first 1 rows" in report
