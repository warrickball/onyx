from rest_framework import status
from rest_framework.response import Response


class OnyxResponse:
    @classmethod
    def invalid_query(cls):
        return Response(
            {"detail": f"Encountered error while parsing query."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @classmethod
    def forbidden(cls, required):
        return Response(
            {"required_permissions": sorted(set(required))},
            status=status.HTTP_403_FORBIDDEN,
        )

    @classmethod
    def _not_found(cls, name):
        return {"detail": f"{str(name)} not found."}

    @classmethod
    def not_found(cls, name):
        return Response(
            cls._not_found(name),
            status=status.HTTP_404_NOT_FOUND,
        )

    @classmethod
    def unknown_aspect(cls, aspect, values):
        return Response(
            {f"unknown_{aspect}": [value for value in values]},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    @classmethod
    def action_success(cls, action, cid, test=False, status=None):
        return Response(
            {"action": f"test-{action}" if test else action, "cid": cid},
            status=status,
        )

    @classmethod
    def validation_error(cls, errors):
        return Response(
            errors,
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
