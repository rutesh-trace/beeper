from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.encoders import jsonable_encoder
from starlette import status

from authentication.schemas import UserResponse, UserBase, LoginRequest, VerifyOTPRequest
from common.cache_string import gettext
from common.response import ApiResponse
from config import app_config
from .models import User
from .service import UserServices

router = APIRouter()
user_service = UserServices(User)
BASE_MEDIA_URL = f"http://{app_config.HOST_URL}:{app_config.HOST_PORT}"


@router.get("/user")
def get_users_api():
    users = user_service.get_all_user()
    user_data = []
    for user in users:
        if user.profile_image:
            user.profile_image = f"{BASE_MEDIA_URL}/{user.profile_image}"

        if user.email:
            user.profile_thumbnail_image = f"{BASE_MEDIA_URL}/{user.profile_thumbnail_image}"
        user_data.append(user)

    message_key = "not_found" if not users else "retrieved_successfully"
    message = gettext(message_key).format("Users")

    return ApiResponse.create_response(
        success=True,
        message=message,
        status_code=status.HTTP_200_OK,
        data=user_data if user_data else None
    )


@router.get("/user/{user_id}")
def get_users_api(user_id: int):
    user = user_service.get_user_details_by_id(user_id)
    user_data = UserResponse(**user)

    message_key = "not_found" if not user else "retrieved_successfully"
    message = gettext(message_key).format("User")

    return ApiResponse.create_response(
        success=True,
        message=message,
        status_code=status.HTTP_200_OK,
        data=jsonable_encoder(user_data) if user_data else None
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserBase = Depends(UserBase.as_form), profile_image: UploadFile = File(None)):
    """
    Registers a new user if the phone number is not already registered.
    """
    response = user_service.register_user(user_data, profile_image)

    message = gettext("created_successfully").format("User")
    return ApiResponse.create_response(
        success=True,
        message=message,
        status_code=status.HTTP_200_OK,
        data=jsonable_encoder(response) if response else None
    )


@router.post("/send-otp")
async def send_otp(request: LoginRequest):
    response = user_service.send_otp(request)

    return ApiResponse.create_response(
        success=True,
        message=f"OTP sent successfully on {request.phone_number}",
        status_code=status.HTTP_200_OK,
        data=[{"otp": response.get("otp"), "otp_secret": response.get("secret")}] if response else []
    )


#
# @router.post("/verify-otp")
async def verify_otp(request: VerifyOTPRequest):
    """Verify OTP and authenticate user"""
    response = user_service.verify_otp(request)

    return ApiResponse.create_response(
        success=True,
        message=f"OTP verified successfully for {request.phone_number} number",
        status_code=status.HTTP_200_OK,
        data=[{"otp": response.get("otp"), "otp_secret": response.get("secret")}] if response else []
    )
