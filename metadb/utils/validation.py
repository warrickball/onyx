from datetime import datetime
from utils.response import METADBAPIResponse


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
