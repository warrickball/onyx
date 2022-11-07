def enforce_optional_value_groups_update(instance, data, groups):
    errors = {}

    # Want to ensure each group still has at least one non-null field after update
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

    return errors


def enforce_optional_value_groups_create(data, groups):
    errors = {}

    # Want to ensure each group has at least one non-null field when creating
    for group in groups:
        for field in group:
            if field in data and data[field] is not None:
                break
        else:
            # If you're reading this I'm sorry
            # I couldn't help but try a for-else
            # I just found out it can be done, so I did it :)
            errors.setdefault("at_least_one_required", []).append(group)

    return errors
