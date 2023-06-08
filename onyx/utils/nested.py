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
