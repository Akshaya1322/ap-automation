from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """Wraps DRF's default handler to produce a consistent error envelope."""
    response = exception_handler(exc, context)

    if response is not None:
        detail = response.data
        message = None
        if isinstance(detail, dict) and "detail" in detail and len(detail) == 1:
            message = str(detail["detail"])
        response.data = {
            "error": True,
            "message": message or "One or more fields are invalid.",
            "errors": detail if message is None else None,
            "status_code": response.status_code,
        }
    return response
