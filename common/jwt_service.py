import datetime

import jwt
from fastapi import HTTPException, status

from config import app_config


class JWTService:
    """
        A service class for handling JWT-based authentication, including access token and refresh token generation,
        verification, and revocation.
    """

    # Secret keys (Load from environment variables)
    SECRET_KEY = app_config.JWT_SECRET_KEY
    REFRESH_SECRET_KEY = app_config.JWT_REFRESH_SECRET_KEY
    ALGORITHM = "HS256"

    # Token Expiry Durations
    ACCESS_TOKEN_EXPIRY_MINUTES = 15  # Access Token expires in 15 minutes
    REFRESH_TOKEN_EXPIRY_DAYS = 7  # Refresh Token expires in 7 days

    REVOKED_REFRESH_TOKENS = set()

    @classmethod
    def create_tokens(cls, data: dict) -> dict:
        """
        Generates both access and refresh tokens with respective expiration times.

        Args:
            data (dict): The payload data to encode in the tokens.

        Returns:
            dict: A dictionary containing both access and refresh tokens.
        """
        try:
            now = datetime.datetime.now(datetime.UTC)

            # Create Access Token
            access_payload = data.copy()
            access_payload.update({"exp": now + datetime.timedelta(minutes=cls.ACCESS_TOKEN_EXPIRY_MINUTES)})
            access_token = jwt.encode(access_payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)

            # Create Refresh Token
            refresh_payload = data.copy()
            refresh_payload.update({"exp": now + datetime.timedelta(days=cls.REFRESH_TOKEN_EXPIRY_DAYS)})
            refresh_token = jwt.encode(refresh_payload, cls.REFRESH_SECRET_KEY, algorithm=cls.ALGORITHM)

            return {
                "access_token": access_token,
                "refresh_token": refresh_token
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating tokens: {str(e)}"
            )

    @classmethod
    def revoke_refresh_token(cls, refresh_token: str):
        """
            Invalidates a refresh token by adding it to a revoked token list.

            Args:
                refresh_token (str): The refresh token to revoke.
        """
        try:
            cls.REVOKED_REFRESH_TOKENS.add(refresh_token)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error revoking refresh token: {str(e)}"
            )

    @classmethod
    def is_refresh_token_revoked(cls, refresh_token: str) -> bool:
        """
            Checks if a given refresh token has been revoked.

            Args:
                refresh_token (str): The refresh token to check.

            Returns:
                bool: True if the token is revoked, False otherwise.
        """
        try:
            return refresh_token in cls.REVOKED_REFRESH_TOKENS
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error checking refresh token revocation: {str(e)}"
            )
