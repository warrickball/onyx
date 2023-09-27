import json
from django.http import HttpResponse
from rest_framework import status


def custom_page_not_found_view(request, exception):
    return HttpResponse(
        content=json.dumps(
            {
                "status": "fail",
                "code": status.HTTP_404_NOT_FOUND,
                "messages": {"detail": "Not found."},
            }
        ),
        content_type="application/json",
        status=status.HTTP_404_NOT_FOUND,
    )


def custom_error_view(request, exception=None):
    return HttpResponse(
        content=json.dumps(
            {
                "status": "error",
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "messages": {
                    "detail": "Internal server error. Please contact an admin."
                },
            }
        ),
        content_type="application/json",
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def custom_permission_denied_view(request, exception=None):
    return HttpResponse(
        content=json.dumps(
            {
                "status": "fail",
                "code": status.HTTP_403_FORBIDDEN,
                "messages": {"detail": "Permission denied."},
            }
        ),
        content_type="application/json",
        status=status.HTTP_403_FORBIDDEN,
    )


def custom_bad_request_view(request, exception=None):
    return HttpResponse(
        content=json.dumps(
            {
                "status": "fail",
                "code": status.HTTP_400_BAD_REQUEST,
                "messages": {"detail": "Bad request."},
            }
        ),
        content_type="application/json",
        status=status.HTTP_400_BAD_REQUEST,
    )
