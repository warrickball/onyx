from django.http import HttpResponse
import json


def custom_page_not_found_view(request, exception):
    return HttpResponse(
        content=json.dumps(
            {
                "status": "fail",
                "messages": {"detail": "Endpoint not found."},
            }
        ),
        content_type="application/json",
        status=404,
    )


def custom_error_view(request, exception=None):
    return HttpResponse(
        content=json.dumps(
            {
                "status": "error",
                "messages": {
                    "detail": "Internal server error. If this error persists please contact an admin."
                },
            }
        ),
        content_type="application/json",
        status=500,
    )


def custom_permission_denied_view(request, exception=None):
    return HttpResponse(
        content=json.dumps(
            {
                "status": "fail",
                "messages": {"detail": "Permission denied."},
            }
        ),
        content_type="application/json",
        status=403,
    )


def custom_bad_request_view(request, exception=None):
    return HttpResponse(
        content=json.dumps(
            {
                "status": "fail",
                "messages": {"detail": "Bad request."},
            }
        ),
        content_type="application/json",
        status=400,
    )
