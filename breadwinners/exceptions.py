from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    print("CUSTOM EXCEPTION HANDLER CALLED")

    if response is None:
        return response

    if response.status_code == 400:
        return Response({
            "success": False,
            "message": "Validation failed",
            "detail": get_first_error(response.data),
            "errors": response.data
        }, status=400)

    return response


def get_first_error(errors):
    """
    Recursively find the first error message.
    """
    if isinstance(errors, dict):
        for value in errors.values():
            return get_first_error(value)

    if isinstance(errors, list):
        return str(errors[0])

    return str(errors)
