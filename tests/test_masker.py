import pandas as pd
from src.masking.masker import mask_data

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
