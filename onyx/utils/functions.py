import difflib


def get_suggestions(unknown: str, fields: list[str], n=4, cutoff=0.4) -> list[str]:
    fields_map = {field.lower().strip(): field for field in fields}

    close_matches = difflib.get_close_matches(
        word=unknown.lower().strip(),
        possibilities=fields_map.keys(),
        n=n,
        cutoff=cutoff,
    )

    return [fields_map[close_match] for close_match in close_matches]


def strtobool(val):
    val = val.lower()
    if val == "true":
        return True
    elif val == "false":
        return False
    else:
        raise ValueError(f"Invalid truth value: {val}")
