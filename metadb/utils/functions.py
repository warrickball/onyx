from django.db.models import Q
from datetime import datetime
import operator
import functools

from .classes import METADBAPIResponse
from .classes import KeyValue
from internal.models import Project


def get_choices(cs):
    return [(c, c) for c in cs]


def init_pathogen_queryset(pathogen_model, user):
    """
    Return an initial queryset of the provided `pathogen_model`.

    If `user.is_staff = True`, returns all objects, otherwise only returns objects with `suppressed = False`.
    """
    if user.is_staff:
        qs = pathogen_model.objects.all()
    else:
        qs = pathogen_model.objects.filter(suppressed=False)
    return qs


def enforce_field_set(data, user_fields, accepted_fields, rejected_fields):
    """
    Check `data` for unknown fields, or known fields which cannot be accepted.
    """
    rejected = {}
    unknown = {}

    for field in data:
        # Fields that are always rejected in the given scenario
        if field in rejected_fields:
            rejected[field] = [METADBAPIResponse.NON_ACCEPTED_FIELD]

        # Neither accepted or rejected, must be unknown
        elif field not in accepted_fields:
            unknown[field] = [METADBAPIResponse.UNKNOWN_FIELD]

        # By this stage, the field must be acceptable for the given scenario
        # But it may not be acceptable for this particular user
        elif field not in user_fields:
            rejected[field] = [METADBAPIResponse.NON_ACCEPTED_FIELD]

    return rejected, unknown


def enforce_optional_value_groups_create(errors, data, groups):
    """
    Ensure each of the provided groups of fields has at least one non-null field on instance creation.
    """
    for group in groups:
        for field in group:
            if field in data and data[field] is not None:
                break
        else:
            # If you're reading this I'm sorry
            # I couldn't help but try a for-else
            # I just found out it can be done, so I did it :)
            # And its dreadful
            errors.setdefault("at_least_one_required", []).append(group)


def enforce_optional_value_groups_update(errors, instance, data, groups):
    """
    Ensure each of the provided groups of fields has at least one non-null field after instance update.
    """
    for group in groups:
        # List of non-null fields from the group
        instance_group_fields = [
            field for field in group if getattr(instance, field) is not None
        ]

        # List of fields specified by the request data that are going to be nullified
        fields_to_nullify = [
            field for field in group if field in data and data[field] is None
        ]

        # If the resulting set is empty, it means one of two not-good things:
        # The request contains enough fields from the group being nullified that there will be no non-null fields left from the group
        # There were (somehow) no non-null fields in the group to begin with
        if set(instance_group_fields) - set(fields_to_nullify) == set():
            errors.setdefault("at_least_one_required", []).append(group)


def enforce_yearmonth_order_create(errors, lower_yearmonth, higher_yearmonth, data):
    """
    Ensure the datetime value of the `lower_yearmonth` is not greater than the `higher_yearmonth` value on instance creation.
    """
    if data.get(lower_yearmonth) and data.get(higher_yearmonth):
        if data[lower_yearmonth] > data[higher_yearmonth]:
            errors.setdefault("non_field_errors", []).append(
                f"The field {lower_yearmonth} cannot be greater than {higher_yearmonth}"
            )


def enforce_yearmonth_order_update(
    errors, instance, lower_yearmonth, higher_yearmonth, data
):
    """
    Ensure the datetime value of the `lower_yearmonth` is not greater than the `higher_yearmonth` value after instance update.
    """
    lower_yearmonth_value = data.get(
        lower_yearmonth, getattr(instance, lower_yearmonth, None)
    )
    higher_yearmonth_value = data.get(
        higher_yearmonth, getattr(instance, higher_yearmonth, None)
    )

    if (
        lower_yearmonth_value is not None
        and higher_yearmonth_value is not None
        and lower_yearmonth_value > higher_yearmonth_value
    ):
        errors.setdefault("non_field_errors", []).append(
            f"The field {lower_yearmonth} cannot be greater than {higher_yearmonth}"
        )


def enforce_yearmonth_non_future(errors, name, value):
    """
    Ensure yearmonth is not from the future.
    """
    if value.year >= datetime.now().year and value.month > datetime.now().month:
        errors.setdefault(name, []).append("Yearmonth cannot be from the future.")


def make_keyvalues(data):
    """
    Traverses the provided `data` and replaces request values with `KeyValue` objects.
    Returns a list of these `KeyValue` objects.
    """
    key, value = next(iter(data.items()))

    if key in {"&", "|", "^", "~"}:
        keyvalues = [make_keyvalues(k_v) for k_v in value]
        return functools.reduce(operator.add, keyvalues)
    else:
        # Initialise KeyValue object
        keyvalue = KeyValue(key, value)

        # Replace the request.data value with the KeyValue object
        data[key] = keyvalue

        # Now return the Keyvalue object
        # All this is being done so that its easy to modify the key/value in the request.data structure
        # To modify the key/values, we will be able to change them in the returned list
        # And because they are the same objects as in request.data, that will be altered as well
        return [keyvalue]


def get_query(data):
    """
    Traverses the provided `data` and forms the corresponding Q object.
    """
    key, value = next(iter(data.items()))

    # AND of multiple keyvalues
    if key == "&":
        q_objects = [get_query(k_v) for k_v in value]
        return functools.reduce(operator.and_, q_objects)

    # OR of multiple keyvalues
    elif key == "|":
        q_objects = [get_query(k_v) for k_v in value]
        return functools.reduce(operator.or_, q_objects)

    # XOR of multiple keyvalues
    elif key == "^":
        q_objects = [get_query(k_v) for k_v in value]
        return functools.reduce(operator.xor, q_objects)

    # NOT of a single keyvalue
    elif key == "~":
        q_object = [get_query(k_v) for k_v in value][0]
        return ~q_object

    # Base case: a keyvalue to filter on
    else:
        # 'value' here is a KeyValue object
        # That by this point, should have been cleaned and corrected to work in a query
        q = Q(**{value.key: value.value})
        return q


def check_permissions(user, model, default_permissions, action, user_fields):
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
    unknown = []
    for user_field in user_fields:
        if user_field in model_fields:
            field_model = model_fields[user_field]
            field_permission = f"{field_model._meta.app_label}.{action}_{field_model._meta.model_name}__{user_field}"
            request_permissions.append(field_permission)
        else:
            unknown.append(user_field)

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
        if x != f"view_{project.code}"
    ]


def get_project_and_model(project_code):
    try:
        project = Project.objects.get(code=project_code)
        model = project.content_type.model_class()
        return project, model
    except Project.DoesNotExist:
        return None, None
    