from .fields import ChoiceField
from data.filters import TEXT_FIELDS, NUMBER_FIELDS


def parse_dunders(obj):
    """
    Flatten a JSON object into a set of dunderised keys.
    """
    dunders = []
    if isinstance(obj, dict):
        for key, item in obj.items():
            prefix = key
            values = parse_dunders(item)

            if values:
                for v in values:
                    dunders.append(f"{prefix}__{v}")
            else:
                dunders.append(prefix)

    elif isinstance(obj, list):
        for item in obj:
            values = parse_dunders(item)

            for v in values:
                dunders.append(v)
    else:
        return []

    return list(set(dunders))


def prefetch_nested(qs, fields, prefix=None):
    """
    For each field in `fields` that contains nested data, apply prefetching to the QuerySet `qs`.
    """
    for field, nested in fields.items():
        if nested:
            if prefix:
                field = f"{prefix}__{field}"

            qs = qs.prefetch_related(field)
            qs = prefetch_nested(qs, nested, prefix=field)

    return qs


# TODO: Not sure the best way to use this, but its here if I need it.
def lowercase_keys(obj):
    """
    Create a new object from the provided JSON object, with lowercased keys.
    """
    if isinstance(obj, dict):
        return {key.lower(): lowercase_keys(value) for key, value in obj.items()}

    elif isinstance(obj, list):
        return [lowercase_keys(item) for item in obj]

    else:
        return obj


def assign_field_types(fields, field_types, prefix=None):
    for field, nested in fields.items():
        if prefix:
            field_path = f"{prefix}__{field}"
        else:
            field_path = field

        if nested:
            assign_field_types(nested, field_types, prefix=field_path)
        else:
            field_type = field_types[field_path].field_type
            if field_type in TEXT_FIELDS:
                fields[field] = "text"
            elif field_type == ChoiceField:
                fields[field] = "choice"
            elif field_type in NUMBER_FIELDS:
                fields[field] = "number"
