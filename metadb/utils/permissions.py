from rest_framework import status
from rest_framework.response import Response
from utils.response import METADBAPIResponse


def generate_permissions(model_name, fields):
    return [
        (f"{action}_{model_name}__{x}", f"Can {action} {model_name} {x}")
        for action in ["add", "change", "view", "delete", "suppress"]
        for x in fields
    ]


def get_fields_from_permissions(permissions):
    return [
        field
        for (_, _, field) in (
            x.partition("__") for x in permissions.values_list("codename", flat=True)
        )
        if field
    ]


def check_permissions(project, user, action, user_fields, field_contexts):
    """
    Check that the `user` has correct permissions to perform `action` to `user_fields` of the provided `model`.
    """
    # By default, user must be able to view the project and perform intended action on the project
    permissions = [
        f"internal.view_project_{project.code}",
        f"internal.{action}_project_{project.code}",
    ]

    # For each field provided by the user, get the corresponding permission
    unknown = {}
    for user_field in user_fields:
        if user_field in field_contexts:
            field_model = field_contexts[user_field].model
            field_permission = f"{field_model._meta.app_label}.{action}_{field_model._meta.model_name}__{user_field}"
            permissions.append(field_permission)
        else:
            unknown[user_field] = [METADBAPIResponse.UNKNOWN_FIELD]

    # Check the user has all the requested permissions
    required = []
    for perm in sorted(set(permissions)):
        if not user.has_perm(perm):
            required.append(perm)

    return required, unknown


def not_authorised_response(project, user, required):
    can_view = user.has_perm(f"internal.view_project_{project.code}")

    if project.hidden and not can_view:
        # If project is secret, return 404
        return Response(
            {project.code: [METADBAPIResponse.NOT_FOUND]},
            status=status.HTTP_404_NOT_FOUND,
        )
    else:
        # Otherwise, return 403
        return Response(
            {"denied_permissions": required},
            status=status.HTTP_403_FORBIDDEN,
        )
