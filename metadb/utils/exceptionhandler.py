from django.core.exceptions import FieldDoesNotExist, ValidationError, PermissionDenied
from utils.errors import ProjectDoesNotExist, ScopesDoNotExist
from utils.response import METADBResponse


def handle_exception(e):
    if isinstance(e, ProjectDoesNotExist):
        return METADBResponse.not_found("project")

    elif isinstance(e, ScopesDoNotExist):
        return METADBResponse.unknown_aspect("scopes", e.args[0])

    elif isinstance(e, PermissionDenied):
        return METADBResponse.forbidden(e.args[0])

    elif isinstance(e, FieldDoesNotExist):
        return METADBResponse.unknown_aspect("fields", e.args[0])

    elif isinstance(e, ValidationError):
        return METADBResponse.validation_error(e.args[0])

    else:
        raise e
