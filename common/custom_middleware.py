import jwt
from fastapi import HTTPException, Request

from config import app_config
from main import app

SECRET_KEY = app_config.JWT_SECRET_KEY


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Skip authentication for certain endpoints (e.g., login, public APIs)
    public_paths = ["/login", "/docs", "/open-api"]
    if request.url.path in public_paths:
        return await call_next(request)

    # Get Authorization Header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Access token required")

    # Extract Token
    token = auth_header.split(" ")[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

        # Extract user data from token payload
        user_data = {
            "user_id": payload.get("user_id"),
            "username": payload.get("username"),
            "email": payload.get("email"),
        }
        if not user_data["user_id"]:
            raise HTTPException(status_code=403, detail="Invalid token structure")

        # Store user data in request state (accessible in routes)
        request.state.user = user_data

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=403, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=403, detail="Invalid token")

    # Proceed with the request
    response = await call_next(request)
    return response
