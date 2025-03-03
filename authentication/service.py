import os
from typing import Any

import requests
from fastapi import HTTPException, UploadFile
from sqlalchemy.exc import SQLAlchemyError
from starlette import status
from starlette.responses import JSONResponse

from app_logging import app_logger
from authentication.models import User
from authentication.schemas import UserBase, LoginRequest, VerifyOTPRequest
from common.cache_string import gettext
from common.jwt_service import JWTService
from common.otp_service import OTPService
from common.response import ApiResponse
from common.utils import save_uploaded_image
from db_domains import Base
from db_domains.db_interface import DBInterface

DataObject = dict[str, Any]


class UserServices:
    def __init__(self, db_model: type[Base]) -> None:
        self.db_class: type[Base] = db_model
        self.db_interface = DBInterface(self.db_class)

    def get_all_user(self) -> JSONResponse | dict[str, Any]:
        try:
            return self.db_interface.read_all()
        except SQLAlchemyError as err:
            app_logger.error(gettext("error_fetching_data_from_db").format("User"))
            return ApiResponse.create_error_response(http_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                                     message=str(err))

    def get_user_details_by_id(self, user_id: Any) -> JSONResponse | dict[str, Any]:
        try:
            return self.db_interface.read_by_id(_id=user_id)
        except SQLAlchemyError as err:
            app_logger.error(gettext("error_fetching_data_from_db").format("User"))
            return ApiResponse.create_error_response(http_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                                     message=str(err))

    def register_user(self, user_data: UserBase, profile_image: UploadFile = None) -> JSONResponse | dict[str, Any]:
        """Registers a new user if the phone number is not already registered."""
        try:
            user_phone_filter = [User.phone == user_data.phone]
            user_email_filter = [User.email == user_data.email]

            if self.db_interface.read_by_fields(user_phone_filter):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=gettext("phone_already_registered")
                )

            if self.db_interface.read_by_fields(user_email_filter):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=gettext("already_exists").format("Email")
                )
            user_dict = user_data.model_dump()
            if profile_image:
                allowed_types = {"image/jpeg", "image/png"}
                if profile_image.content_type not in allowed_types:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid image format. Only JPG, JPEG, PNG allowed."
                    )

                image_path, thumbnail_path = save_uploaded_image(profile_image)

                user_dict["profile_image"] = image_path
                user_dict["profile_thumbnail_image"] = thumbnail_path

            return self.db_interface.create(user_dict)

        except SQLAlchemyError as err:
            app_logger.error(gettext("error_inserting_data_to_db").format("User"))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=gettext("error_inserting_data_to_db").format("User")
            )

    def send_otp(self, login_request: LoginRequest):
        """Generate and send OTP."""
        try:

            phone_number = login_request.phone_number

            # Check if the phone number exists in the database
            user_phone_filter = [User.phone == phone_number]

            if user_details := self.db_interface.read_by_fields(user_phone_filter):
                name = f"{user_details.first_name} {user_details.last_name}"
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=gettext("does_not_exists").format(phone_number)
                )

            if os.getenv("ENV_FASTAPI_SERVER_TYPE") == "development":
                otp = 123456
                secret = "1234567"
            else:
                # Generate OTP
                otp, secret = OTPService.generate_otp(phone_number)

                url = f"http://ahd.sendsmsbox.com/api/mt/SendSMS?user=tracewave&password=tracewave14&senderid=TRNSWV&channel=Trans&DCS=0&flashsms=0&number={phone_number}&text=Hello {name},\nYour OTP for login is {otp}. This OTP is valid for 5 minutes.Please do not share it with anyone.\nTRACEWAVE##&Peid=0&DLTTemplateId=1707173510885060059"

                response = requests.get(url)
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="An error occurred while sending OTP. Please try again."
                    )
                return {"otp": otp, "secret": secret}

            return {"otp": otp, "secret": secret}
        except HTTPException as http_exc:
            raise http_exc

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    def verify_otp(self, verify_otp: VerifyOTPRequest):
        try:
            # Check if the phone number exists in the database
            phone_number = verify_otp.phone_number
            user_phone_filter = [User.phone == phone_number]
            if user_details := self.db_interface.read_by_fields(user_phone_filter):
                message, success = OTPService.verify_otp(otp=verify_otp.otp, otp_secret=verify_otp.otp_secret)
                token_data = {
                    "id": user_details.id,
                    "name": f"{user_details.first_name} {user_details.last_name}",
                    "phone_number": user_details.phone,
                    "email": user_details.email
                }
                jwt_response = JWTService().create_tokens(token_data)

                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=message
                    )

                return {"success": True, "message": message, "token": jwt_response}
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=gettext("does_not_exists").format(phone_number)
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
