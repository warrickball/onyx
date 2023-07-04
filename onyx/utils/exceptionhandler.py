from django.core.exceptions import FieldDoesNotExist, ValidationError, PermissionDenied
from utils.response import OnyxResponse


def handle_exception(e):
    if isinstance(e, PermissionDenied):
        return OnyxResponse.forbidden(e.args[0])

    elif isinstance(e, FieldDoesNotExist):
        return OnyxResponse.unknown_aspect("fields", e.args[0])

    elif isinstance(e, ValidationError):
        return OnyxResponse.validation_error(e.args[0])

    else:
        raise e
