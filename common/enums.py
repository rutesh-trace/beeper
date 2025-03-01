from fastapi import status


class HTTPErrorMessage:
    """All HTTP related API error messages should be defined here"""
    ERROR_MAP = {
        status.HTTP_404_NOT_FOUND: "Item not found",
        status.HTTP_500_INTERNAL_SERVER_ERROR: "Something went wrong",
        status.HTTP_401_UNAUTHORIZED: "You are not unauthorized to make this action"
    }

    @staticmethod
    def get_message_for(http_status_code: int):
        return HTTPErrorMessage.ERROR_MAP.get(http_status_code)
