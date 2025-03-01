from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse

from common import enums as en


class ApiResponse:
    @staticmethod
    def create_response(success: bool, message: str, status_code: int, data: list = None) -> JSONResponse:
        data_dict = {"message": message, "success": success, "status_code": status_code}
        if data:
            if 'data' in data:
                data_dict |= data
            else:
                data_dict['data'] = data
        else:
            data_dict['data'] = []
        response_headers = {"Content-Type": "application/json"}
        return JSONResponse(content=jsonable_encoder(data_dict),
                            status_code=status_code,
                            headers=response_headers)

    @staticmethod
    def create_error_response(http_status_code: int, message: str = None) -> JSONResponse:
        message = message or en.HTTPErrorMessage.get_message_for(http_status_code=http_status_code)
        return ApiResponse.create_response(success=False,
                                           message=message,
                                           status_code=http_status_code)
