from datetime import date as dt_date
import re

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserModel(BaseModel):
    """Pydantic model representing a user in the time management system.

    Fields:
        employee_id: Unique employee ID for the user.
        full_name: Full name of the user.
        email: Email address of the user.
        department: Department the user belongs to.
        site: Site/location where the user works from.
        active: Boolean indicating if the user is active or inactive.
    """
    employee_id: str = Field(..., description="Unique employee ID")
    full_name: str = Field(..., description="Full name of the user")
    email: EmailStr = Field(..., description="Email address of the user")
    department: str
    site: str
    active: bool


class TimeLogModel(BaseModel):
    """Pydantic model representing a user's daily time log in the time management system.

    Fields:
        employee_id: Employee ID, references UserModel.employee_id.
        date: Date of the log entry.
        hostname: Workstation hostname used by the user.
        os: Operating system of the workstation.
        login_time: Login time in HH:MM 24-hour format.
        logout_time: Logout time in HH:MM 24-hour format.
        active_hours: Number of active hours for the day.
    """
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
        """
        Validate that the time string is in HH:MM 24-hour format.

        Args:
            time_value (str): The time string to validate.

        Returns:
            str: The validated time string if it matches the required format.

        Raises:
            ValueError: If the time string does not match the HH:MM 24-hour format.

        Example:
            >>> TimeLogModel.validate_time_format("09:30")
            '09:30'
            >>> TimeLogModel.validate_time_format("25:00")
            ValueError: Time must be in HH:MM 24-hour format
        """
        if not re.match(r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$", time_value):
            raise ValueError("Time must be in HH:MM 24-hour format")
        return time_value
