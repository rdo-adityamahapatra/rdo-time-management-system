"""Pydantic models and schema validation for the TMS project."""

import re
from datetime import date as dt_date

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserModel(BaseModel):
    """Pydantic model representing a user in the time management system."""

    employee_id: str = Field(..., description="Unique employee ID")
    full_name: str = Field(..., description="Full name of the user")
    email: EmailStr = Field(..., description="Email address of the user")
    department: str
    site: str
    active: bool


class TimeLogModel(BaseModel):
    """Pydantic model representing a user's daily time log in the time management system."""

    employee_id: str = Field(..., description="Employee ID, references UserModel.employee_id")
    date: dt_date = Field(..., description="Date of the log entry")
    hostname: str
    os: str
    login_time: str = Field(..., description="Login time in HH:MM 24-hour format")
    logout_time: str = Field(..., description="Logout time in HH:MM 24-hour format")
    active_hours: float

    @field_validator("login_time", "logout_time")
    @classmethod
    def validate_time_format(cls, time_value: str) -> str:
        """Validate that the time string is in HH:MM 24-hour format.

        This method is called by Pydantic implicitly to validate the `login_time` and `logout_time` fields.
        It does not need to be called explicitly.

        Example:
            >>> TimeLogModel.validate_time_format("09:30")
            '09:30'
            >>> TimeLogModel.validate_time_format("25:00")
            ValueError: Time must be in HH:MM 24-hour format
        """
        if not re.match(r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$", time_value):
            raise ValueError("Time must be in HH:MM 24-hour format")
        return time_value
