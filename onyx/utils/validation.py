from django.contrib.contenttypes.models import ContentType
from datetime import datetime
from data.models import Choice


def enforce_optional_value_groups(errors, data, groups, instance=None):
    """
    Ensure each of the provided groups of fields has at least one non-null field.
    """
    if instance:
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
                errors.setdefault("non_field_errors", []).append(
                    f"At least one of {', '.join(group)} is required."
                )
    else:
        for group in groups:
            for field in group:
                if field in data and data[field] is not None:
                    break
            else:
                # If you're reading this I'm sorry
                # I couldn't help but try a for-else
                # I just found out it can be done, so I did it :)
                # And its dreadful
                errors.setdefault("non_field_errors", []).append(
                    f"At least one of {', '.join(group)} is required."
                )


def enforce_orderings(errors, data, orderings, instance=None):
    """
    Ensure the value of `lower` is not greater than `higher`.
    """
    for lower, higher in orderings:
        if instance:
            lower_value = data.get(lower, getattr(instance, lower, None))
            higher_value = data.get(higher, getattr(instance, higher, None))
        else:
            lower_value = data.get(lower)
            higher_value = data.get(higher)

        if (
            lower_value is not None
            and higher_value is not None
            and lower_value > higher_value
        ):
            errors.setdefault("non_field_errors", []).append(
                f"The {lower} cannot be greater than the {higher}."
            )


def enforce_non_futures(errors, data, non_futures):
    """
    Ensure date is not from the future.
    """
    for non_future in non_futures:
        if data.get(non_future) and data[non_future] > datetime.now().date():
            errors.setdefault(non_future, []).append("Value cannot be from the future.")


def enforce_identifiers(errors, data, identifiers):
    for identifier in identifiers:
        if identifier not in data:
            errors.setdefault(identifier, []).append("This field is required.")


def enforce_choice_constraints(errors, data, choice_constraints, model, instance=None):
    """
    Ensure all choices are compatible with each other.
    """
    # Getting a little bit gnarly
    # This is a mapping from tuples of (field_x, choice_x)
    # to all (field_y, choice_y) tuples that are allowed to occur with said tuple
    constraints = {
        (choice.field, choice.choice): {
            (constraint.field, constraint.choice)
            for constraint in choice.constraints.all()
        }
        for choice in Choice.objects.prefetch_related("constraints")
        .filter(content_type=ContentType.objects.get_for_model(model))
        .filter(
            field__in=set(
                field
                for constraint_group in choice_constraints
                for field in constraint_group
            )
        )
    }

    for choice_x, choice_y in choice_constraints:
        if instance:
            choice_x_value = data.get(choice_x, getattr(instance, choice_x, None))
            choice_y_value = data.get(choice_y, getattr(instance, choice_y, None))
        else:
            choice_x_value = data.get(choice_x)
            choice_y_value = data.get(choice_y)

        if (
            choice_x_value is not None
            and choice_y_value is not None
            and (
                (
                    (choice_y, choice_y_value)
                    not in constraints[(choice_x, choice_x_value)]
                )
                or (
                    (choice_x, choice_x_value)
                    not in constraints[(choice_y, choice_y_value)]
                )
            )
        ):
            errors.setdefault("non_field_errors", []).append(
                f"Choices for fields {choice_x}, {choice_y} are incompatible."
            )
