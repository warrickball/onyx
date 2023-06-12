from .models import Project, Scope, Signal, Choice, Record, History

try:
    from . import projects
except (ImportError, ModuleNotFoundError):
    pass
