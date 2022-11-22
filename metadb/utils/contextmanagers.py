from contextlib import contextmanager


@contextmanager
def mutable(obj):
    """
    If the provided `obj` has a `_mutable` property, this context manager temporarily sets it to true
    """
    mutable = getattr(obj, "_mutable", None)
    if mutable is not None:
        obj._mutable = True

    try:
        yield obj
    finally:
        # Reset object's mutability
        if mutable is not None:
            obj._mutable = mutable
