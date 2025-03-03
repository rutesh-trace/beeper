import random
import string

import pyotp


class OTPService:
    @staticmethod
    def generate_secret():
        """Generate a random secret key for TOTP."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

    @classmethod
    def generate_otp(cls, phone: str):
        """Generate and store OTP for a given phone number."""
        secret = cls.generate_secret()
        totp = pyotp.TOTP(secret, interval=60)
        otp = totp.now()

        print(f"OTP for {phone}: {otp}")
        print(f"OTP Secret for {phone}: {secret}")

        return otp, secret

    @classmethod
    def verify_otp(cls, otp: str, otp_secret: str):
        """Verify OTP for a given phone number."""

        totp = pyotp.TOTP(otp_secret, interval=60)

        if totp.verify(otp):
            return True, "OTP verified successfully"
        return False, "Invalid OTP or expired"
