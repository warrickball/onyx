from utils.response import METADBAPIResponse


def check_permissions(
    user, model, default_permissions, action, user_fields, view_fields
):
    """
    Check that the `user` has correct permissions to perform `action` to `user_fields` of the provided `model`.
    """
    # Default permissions
    request_permissions = [
        f"{x.content_type.app_label}.{x.codename}" for x in default_permissions
    ]

    # Add global model action permission to required request permissions
    model_permission = f"{model._meta.app_label}.{action}_{model._meta.model_name}"
    request_permissions.append(model_permission)

    # Starting from the grandest parent model
    # Record which fields belong to which model in the inheritance hierarchy
    model_fields = {field.name: model for field in model._meta.get_fields()}
    models = [model] + model._meta.get_parent_list()
    for m in reversed(models):
        for field in m._meta.get_fields(include_parents=False):
            if field.name in model_fields:
                model_fields[field.name] = m

    # For each field provided by the user, get the corresponding permission
    unknown = {}
    for user_field in user_fields:
        if user_field in model_fields and user_field in view_fields:
            field_model = model_fields[user_field]
            field_permission = f"{field_model._meta.app_label}.{action}_{field_model._meta.model_name}__{user_field}"
            request_permissions.append(field_permission)
        else:
            unknown[user_field] = [METADBAPIResponse.UNKNOWN_FIELD]

    request_permissions = sorted(set(request_permissions))

    # Check the user has permissions to perform action to all provided fields
    has_permission = user.has_perms(request_permissions)

    # If not, determine the permissions they need
    required = []
    if not has_permission:
        user_permissions = user.get_all_permissions()

        for request_permission in request_permissions:
            if request_permission not in user_permissions:
                required.append(request_permission)

    return has_permission, required, unknown


def generate_permissions(model_name, fields):
    return [
        (f"{action}_{model_name}", f"Can {action} {model_name}")
        for action in ["suppress"]
    ] + [
        (f"{action}_{model_name}__{x}", f"Can {action} {model_name} {x}")
        for action in ["add", "change", "view", "delete", "suppress"]
        for x in fields
    ]


def get_view_permissions_and_fields(project):
    view_permissions = project.view_group.permissions.all()
    return view_permissions, [
        x.split("__")[1]
        for x in view_permissions.values_list("codename", flat=True)
        if len(x.split("__")) > 1
    ]
