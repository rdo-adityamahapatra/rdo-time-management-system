from datetime import date as dt_date
import re

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserModel(BaseModel):
    employee_id: str = Field(..., description="Unique employee ID")
    full_name: str = Field(..., description="Full name of the user")
    email: EmailStr = Field(..., description="Email address of the user")
    department: str
    site: str
    active: bool


class TimeLogModel(BaseModel):
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
        if not re.match(r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$", time_value):
            raise ValueError("Time must be in HH:MM 24-hour format")
        return time_value
