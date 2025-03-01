import re
from datetime import date
from typing import Optional

from fastapi import Form
from pydantic import BaseModel, EmailStr, field_validator


class UserBase(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: Optional[EmailStr] = None
    birth_date: Optional[date] = None
    profile_image: Optional[str] = None

    @classmethod
    def as_form(
            cls,
            first_name: str = Form(...),
            last_name: str = Form(...),
            phone: str = Form(...),
            email: Optional[EmailStr] = Form(None),
            birth_date: Optional[date] = Form(None),
    ):
        return cls(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email=email,
            birth_date=birth_date,
        )

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, phone: str) -> str:
        """
        Validate phone number:
            - Must contain only digits, spaces, and dashes.
            - Must have at least 10 digits (ignoring spaces & dashes).
            - Other special characters are **not allowed**.
        """
        if not re.fullmatch(r"[\d\s\-]+", phone):
            raise ValueError("Phone number can only contain digits, spaces, and dashes.")

        # Count only digits (ignoring spaces and dashes)
        digit_count = sum(c.isdigit() for c in phone)
        if digit_count < 10 or digit_count > 15:
            raise ValueError("Phone number must have between 10 and 15 digits.")

        return phone

    @field_validator("email")
    @classmethod
    def validate_email(cls, email: Optional[str]) -> Optional[str]:
        """
        Validate email:
        - Only checked if provided (optional).
        - Ensures correct email format.
        """
        if email == "":
            return None

        if email and not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Invalid email format.")
        return email


class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    phone: str
    email: Optional[EmailStr] = None
    birth_date: Optional[date] = None
    profile_image: Optional[str] = None
    profile_thumbnail_image: Optional[str] = None  # Add this field

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    phone_number: str


class VerifyOTPRequest(BaseModel):
    phone_number: str
    otp: str
    otp_secret : str
