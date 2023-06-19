from .models import Project, Scope, Signal, Choice, Record, RecordHistory

try:
    from . import projects
except (ImportError, ModuleNotFoundError):
    pass
