from .record import Record

try:
    from . import projects
except (ImportError, ModuleNotFoundError):
    pass
