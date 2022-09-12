from rest_framework import status
from rest_framework.response import Response


class APIResponse:
    # Generic 404 message
    NOT_FOUND = "not found"

    def __init__(self):
        self.errors = {}
        self.warnings = {}
        self.results = []
        self.next = None
        self.previous = None

    @property
    def data(self):
        return {
            "next": self.next,
            "previous": self.previous,
            "errors": self.errors,
            "warnings": self.warnings,
            "results": self.results,
        }


class Responses:
    # OK
    _200_user_approved = Response(
        {"detail": f"user was successfully approved"}, status=status.HTTP_200_OK
    )

    # Bad request
    _400_mismatch_pathogen_code = Response(
        {
            "detail": "pathogen_code provided in request body does not match pathogen code in URL"
        },
        status=status.HTTP_400_BAD_REQUEST,
    )
    _400_no_updates_provided = Response(
        {"detail": "no fields were provided for update"},
        status=status.HTTP_400_BAD_REQUEST,
    )

    # Forbidden
    _403_different_institute = Response(
        {"detail": "cannot approve this user. they belong to a different institute"},
        status=status.HTTP_403_FORBIDDEN,
    )
    _403_incorrect_institute_for_user = Response(
        {"detail": "provided institute code does not match user's institute code"},
        status=status.HTTP_403_FORBIDDEN,
    )
