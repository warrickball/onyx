from data.models import TestModel
from .serializers import RecordSerializer
from .testserializers import TestSerializer

mapping = {TestModel: TestSerializer}

try:
    from . import projects

    if hasattr(projects, "mapping"):
        mapping = mapping | projects.mapping
except (ImportError, ModuleNotFoundError):
    pass
