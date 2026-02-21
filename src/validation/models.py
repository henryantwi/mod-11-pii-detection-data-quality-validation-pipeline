"""
Part 3: Pydantic Data Validation Models

Defines a strict Pydantic model for a customer record. Each field has
type constraints and custom validators matching the expected schema from
the task specification.
"""

import re
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class CustomerRecord(BaseModel):
    """Pydantic model representing a validated customer record."""

    customer_id: int = Field(gt=0, description="Unique positive integer")
    first_name: str = Field(min_length=2, max_length=50, description="Alphabetic name")
    last_name: str = Field(min_length=2, max_length=50, description="Alphabetic name")
    email: EmailStr
    phone: str = Field(description="Phone number in any common format")
    date_of_birth: date
    address: str = Field(min_length=10, max_length=200)
    income: float = Field(ge=0, le=10_000_000)
    account_status: Literal["active", "inactive", "suspended"]
    created_date: date

    # --- Field Validators ---

    @field_validator("first_name", "last_name")
    @classmethod
    def name_must_be_alphabetic(cls, v: str) -> str:
        """Names should only contain letters (and spaces/hyphens for compound names)."""
        cleaned = v.replace(" ", "").replace("-", "").replace("'", "")
        if not cleaned.isalpha():
            raise ValueError(f"Name must be alphabetic, got '{v}'")
        return v

    @field_validator("phone")
    @classmethod
    def phone_must_have_valid_digits(cls, v: str) -> str:
        """Phone must contain 7-15 digits."""
        digits = re.sub(r"\D", "", v)
        if len(digits) < 7 or len(digits) > 15:
            raise ValueError(
                f"Phone must contain 7-15 digits, got {len(digits)} in '{v}'"
            )
        return v

    @field_validator("date_of_birth", "created_date", mode="before")
    @classmethod
    def parse_flexible_date(cls, v):
        """Parse dates from multiple formats: YYYY-MM-DD, MM/DD/YYYY, YYYY/MM/DD."""
        if isinstance(v, date):
            return v
        if not isinstance(v, str):
            raise ValueError(f"Expected a date string, got {type(v)}")

        v = v.strip()
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(v, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Cannot parse date: '{v}'")
