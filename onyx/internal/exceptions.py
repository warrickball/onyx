from rest_framework import status, exceptions


class UnprocessableEntityError(exceptions.ValidationError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
