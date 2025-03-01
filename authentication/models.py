from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import declarative_base
import re

from db_domains import CreateUpdateTime


class User(CreateUpdateTime):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    phone = Column(String(15), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=True)
    birth_date = Column(Date, nullable=True)
    profile_image = Column(String, nullable=True)
    profile_thumbnail_image = Column(String, nullable=True)

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """
        Validate phone number:
        - Must contain only digits, spaces, and dashes.
        - Must have at least 10 digits (excluding spaces & dashes).
        """
        if not re.fullmatch(r"[\d\s\-]+", phone):  # Ensure only digits, spaces, and dashes
            return False

        # Count only digits (ignore spaces & dashes)
        digit_count = sum(c.isdigit() for c in phone)
        return 10 <= digit_count <= 15  # Ensure valid length

    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email format.
        """
        return bool(re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email)) if email else True
