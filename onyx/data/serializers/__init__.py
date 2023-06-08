from .record import RecordSerializer

try:
    from . import projects
except (ImportError, ModuleNotFoundError):
    pass
