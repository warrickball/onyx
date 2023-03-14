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
