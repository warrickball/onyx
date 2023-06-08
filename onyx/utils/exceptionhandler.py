from django.core.exceptions import FieldDoesNotExist, ValidationError, PermissionDenied
from utils.errors import ProjectDoesNotExist, ScopesDoNotExist
from utils.response import OnyxResponse


def handle_exception(e):
    if isinstance(e, ProjectDoesNotExist):
        return OnyxResponse.not_found("project")

    elif isinstance(e, ScopesDoNotExist):
        return OnyxResponse.unknown_aspect("scopes", e.args[0])

    elif isinstance(e, PermissionDenied):
        return OnyxResponse.forbidden(e.args[0])

    elif isinstance(e, FieldDoesNotExist):
        return OnyxResponse.unknown_aspect("fields", e.args[0])

    elif isinstance(e, ValidationError):
        return OnyxResponse.validation_error(e.args[0])

    else:
        raise e
