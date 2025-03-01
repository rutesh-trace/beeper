import datetime
from gettext import gettext
from typing import Optional

import jwt
from fastapi import HTTPException, status

from common.cache_string import gettext
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
    def create_access_token(cls, data: dict) -> str:
        """
            Generates a short-lived access token with an expiration time.

            Args:
                data (dict): The payload data to encode in the token.

            Returns:
                str: A JWT access token.
        """
        try:
            to_encode = data.copy()
            expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=cls.ACCESS_TOKEN_EXPIRY_MINUTES)
            to_encode.update({"exp": expire})

            token = jwt.encode(to_encode, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
            return token
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating access token: {str(e)}"
            )

    @classmethod
    def create_refresh_token(cls, data: dict) -> str:
        """
            Generates a long-lived refresh token with an expiration time.

            Args:
                data (dict): The payload data to encode in the refresh token.

            Returns:
                str: A JWT refresh token.
        """
        try:
            to_encode = data.copy()
            expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=cls.REFRESH_TOKEN_EXPIRY_DAYS)
            to_encode.update({"exp": expire})

            token = jwt.encode(to_encode, cls.REFRESH_SECRET_KEY, algorithm=cls.ALGORITHM)
            return token
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating refresh token: {str(e)}"
            )

    @classmethod
    def verify_token(cls, token: str, secret_key: str) -> Optional[dict]:
        """
            Verifies the JWT token and decodes its payload.

            Args:
                token (str): The JWT token to verify.
                secret_key (str): The secret key used to verify the token.

            Returns:
                dict: The decoded payload if the token is valid.

            Raises:
                HTTPException: If the token is expired or invalid.
        """
        try:
            payload = jwt.decode(token, secret_key, algorithms=[cls.ALGORITHM])
            return payload  # Valid token data
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=gettext("token_expired")  # "Token has expired."
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=gettext("invalid_token")  # "Invalid token."
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error verifying token: {str(e)}"
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
