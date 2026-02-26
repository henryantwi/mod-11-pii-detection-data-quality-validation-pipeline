import pytest
import pandas as pd
from pydantic import ValidationError

from src.validation.models import CustomerRecord
from src.validation.validator import validate_dataframe, generate_report


# ---------------------------------------------------------------------------
# CustomerRecord model tests
# ---------------------------------------------------------------------------

class TestCustomerRecordValid:
    """Tests that valid records are accepted."""

    def test_valid_record(self):
        record = CustomerRecord(
            customer_id=1,
            first_name="Alice",
            last_name="Smith",
            email="alice@example.com",
            phone="555-123-4567",
            date_of_birth="1990-05-20",
            address="123 Main Street, Apt 4",
            income=75000.0,
            account_status="active",
            created_date="2024-01-15",
        )
        assert record.customer_id == 1
        assert record.first_name == "Alice"

    def test_valid_compound_name(self):
        record = CustomerRecord(
            customer_id=2,
            first_name="Mary-Jane",
            last_name="O'Brien",
            email="mj@example.com",
            phone="555-123-4567",
            date_of_birth="1985-03-10",
            address="456 Oak Avenue, Suite 100",
            income=0,
            account_status="inactive",
            created_date="2023-06-01",
        )
        assert record.first_name == "Mary-Jane"
        assert record.last_name == "O'Brien"

    def test_valid_date_formats(self):
        """Model should accept multiple date formats."""
        record = CustomerRecord(
            customer_id=3,
            first_name="Bob",
            last_name="Jones",
            email="bob@example.com",
            phone="555-123-4567",
            date_of_birth="05/20/1990",
            address="789 Pine Road, Building A",
            income=100000,
            account_status="suspended",
            created_date="2024/01/15",
        )
        assert str(record.date_of_birth) == "1990-05-20"
        assert str(record.created_date) == "2024-01-15"

    def test_all_valid_statuses(self):
        base = dict(
            customer_id=1, first_name="Al", last_name="Bo",
            email="a@b.com", phone="555-123-4567",
            date_of_birth="1990-01-01", address="123 Main Street Town",
            income=50000, created_date="2024-01-01",
        )
        for status in ["active", "inactive", "suspended"]:
            record = CustomerRecord(**{**base, "account_status": status})
            assert record.account_status == status


class TestCustomerRecordInvalid:
    """Tests that invalid records are rejected."""

    def _base(self, **overrides):
        defaults = dict(
            customer_id=1, first_name="Alice", last_name="Smith",
            email="a@b.com", phone="555-123-4567",
            date_of_birth="1990-01-01", address="123 Main Street Town",
            income=50000, account_status="active", created_date="2024-01-01",
        )
        defaults.update(overrides)
        return defaults

    def test_customer_id_must_be_positive(self):
        with pytest.raises(ValidationError):
            CustomerRecord(**self._base(customer_id=0))

    def test_customer_id_negative(self):
        with pytest.raises(ValidationError):
            CustomerRecord(**self._base(customer_id=-5))

    def test_name_too_short(self):
        with pytest.raises(ValidationError):
            CustomerRecord(**self._base(first_name="A"))

    def test_name_non_alphabetic(self):
        with pytest.raises(ValidationError):
            CustomerRecord(**self._base(first_name="Al1ce"))

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            CustomerRecord(**self._base(email="not-an-email"))

    def test_phone_too_few_digits(self):
        with pytest.raises(ValidationError):
            CustomerRecord(**self._base(phone="12345"))

    def test_phone_too_many_digits(self):
        with pytest.raises(ValidationError):
            CustomerRecord(**self._base(phone="1234567890123456"))

    def test_invalid_date_format(self):
        with pytest.raises(ValidationError):
            CustomerRecord(**self._base(date_of_birth="not-a-date"))

    def test_address_too_short(self):
        with pytest.raises(ValidationError):
            CustomerRecord(**self._base(address="Short"))

    def test_negative_income(self):
        with pytest.raises(ValidationError):
            CustomerRecord(**self._base(income=-1000))

    def test_income_too_high(self):
        with pytest.raises(ValidationError):
            CustomerRecord(**self._base(income=99_999_999))

    def test_invalid_account_status(self):
        with pytest.raises(ValidationError):
            CustomerRecord(**self._base(account_status="deleted"))


# ---------------------------------------------------------------------------
# validate_dataframe() tests
# ---------------------------------------------------------------------------

def _valid_row():
    return {
        "customer_id": 1,
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice@example.com",
        "phone": "555-123-4567",
        "date_of_birth": "1990-05-20",
        "address": "123 Main Street, Apt 4",
        "income": 75000.0,
        "account_status": "active",
        "created_date": "2024-01-15",
    }


def test_validate_all_valid_rows():
    df = pd.DataFrame([_valid_row(), {**_valid_row(), "customer_id": 2}])
    result = validate_dataframe(df)
    assert result["pass_count"] == 2
    assert result["fail_count"] == 0
    assert result["failures"] == []


def test_validate_catches_invalid_row():
    bad_row = {**_valid_row(), "email": "not-email", "customer_id": 2}
    df = pd.DataFrame([_valid_row(), bad_row])
    result = validate_dataframe(df)
    assert result["pass_count"] == 1
    assert result["fail_count"] == 1
    assert len(result["failures"]) >= 1
    assert any(f["field"] == "email" for f in result["failures"])


def test_validate_captures_row_number():
    bad_row = {**_valid_row(), "income": -100}
    df = pd.DataFrame([bad_row])
    result = validate_dataframe(df)
    # Row 0 in DataFrame → row 2 in 1-based + header
    assert result["failures"][0]["row"] == 2


def test_validate_multiple_errors_per_row():
    bad_row = {
        **_valid_row(),
        "first_name": "A",   # too short
        "income": -100,       # negative
        "account_status": "deleted",  # invalid
    }
    df = pd.DataFrame([bad_row])
    result = validate_dataframe(df)
    assert result["fail_count"] == 1
    assert len(result["failures"]) >= 3


def test_validate_handles_none_values():
    row = _valid_row()
    row["email"] = None
    df = pd.DataFrame([row])
    result = validate_dataframe(df)
    assert result["fail_count"] == 1


# ---------------------------------------------------------------------------
# generate_report() tests
# ---------------------------------------------------------------------------

def test_generate_report_structure():
    bad_row = {**_valid_row(), "income": -100}
    df = pd.DataFrame([bad_row])
    result = validate_dataframe(df)
    report = generate_report(result)
    assert "VALIDATION RESULTS" in report
    assert "PASS:" in report
    assert "FAIL:" in report
    assert "FAILURES BY COLUMN:" in report


def test_generate_report_shows_field_errors():
    bad_row = {**_valid_row(), "account_status": "bogus"}
    df = pd.DataFrame([bad_row])
    result = validate_dataframe(df)
    report = generate_report(result)
    assert "account_status" in report


def test_generate_report_clean_data():
    df = pd.DataFrame([_valid_row()])
    result = validate_dataframe(df)
    report = generate_report(result)
    assert "PASS: 1" in report
    assert "FAIL: 0" in report
