import pkgutil
import importlib
from . import projects
from .serializers import SerializerNode


class ModelSerializerMap:
    MAPPING = {}

    @classmethod
    def get(cls, model):
        return cls.MAPPING.get(model)

    @classmethod
    def update(cls, mapping):
        cls.MAPPING = cls.MAPPING | mapping


for module in pkgutil.iter_modules(projects.__path__):
    mod = importlib.import_module(f".projects.{module.name}", package=__package__)
    if hasattr(mod, "mapping"):
        ModelSerializerMap.update(mod.mapping)
