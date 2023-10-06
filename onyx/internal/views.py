from django.http import JsonResponse
from rest_framework import status


def custom_page_not_found_view(*args, **kwargs):
    return JsonResponse(
        {
            "status": "fail",
            "code": status.HTTP_404_NOT_FOUND,
            "messages": {"detail": "Not found."},
        },
        status=status.HTTP_404_NOT_FOUND,
    )


def custom_error_view(*args, **kwargs):
    return JsonResponse(
        {
            "status": "error",
            "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "messages": {"detail": "Internal server error. Please contact an admin."},
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def custom_permission_denied_view(*args, **kwargs):
    return JsonResponse(
        {
            "status": "fail",
            "code": status.HTTP_403_FORBIDDEN,
            "messages": {"detail": "Permission denied."},
        },
        status=status.HTTP_403_FORBIDDEN,
    )


def custom_bad_request_view(*args, **kwargs):
    return JsonResponse(
        {
            "status": "fail",
            "code": status.HTTP_400_BAD_REQUEST,
            "messages": {"detail": "Bad request."},
        },
        status=status.HTTP_400_BAD_REQUEST,
    )
