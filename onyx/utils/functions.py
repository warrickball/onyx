import difflib
from contextlib import contextmanager


@contextmanager
def mutable(obj):
    """
    If the provided `obj` has a `_mutable` property, this context manager temporarily sets it to `True`.
    """

    _mutable = getattr(obj, "_mutable", None)
    if _mutable is not None:
        obj._mutable = True

    try:
        yield obj
    finally:
        # Reset object's mutability
        if _mutable is not None:
            obj._mutable = _mutable


def get_suggestions(
    unknown: str,
    options: list[str],
    n=3,
    cutoff=0.4,
    message_prefix: str | None = None,
) -> str:
    """
    Performs a case-insensitive comparison of an `unknown` against a list of `options`.

    Returns a message containing the suggestions.
    """

    options_map = {option.lower().strip(): option for option in options}

    close_matches = difflib.get_close_matches(
        word=unknown.lower().strip(),
        possibilities=options_map.keys(),
        n=n,
        cutoff=cutoff,
    )

    suggestions = [options_map[close_match] for close_match in close_matches]

    if message_prefix:
        message = message_prefix
    else:
        message = ""

    if suggestions:
        message += (
            f"{' ' if message else ''}Perhaps you meant: {', '.join(suggestions)}"
        )

    return message


def strtobool(val):
    """
    Convert a string representation of truth to True or False.

    True values are 'y', 'yes', 't', 'true', 'on', and '1'.

    False values are 'n', 'no', 'f', 'false', 'off', and '0'.

    Raises ValueError if 'val' is anything else.
    """

    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return True
    elif val in ("n", "no", "f", "false", "off", "0"):
        return False
    else:
        raise ValueError(f"Invalid truth value: {val}")
