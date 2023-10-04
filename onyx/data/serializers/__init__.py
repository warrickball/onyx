import pkgutil
import importlib, inspect
from django.db.models import Model
from rest_framework.serializers import ModelSerializer
from . import projects
from .serializers import SerializerNode, ProjectRecordSerializer


class ModelSerializerMap:
    MAPPING = {}

    @classmethod
    def add(cls, model: type[Model], serializer: type[ModelSerializer]):
        """
        Add a `Model` and its `ModelSerializer` to the `ModelSerializerMap`.
        """
        cls.MAPPING[model] = serializer

    @classmethod
    def get(cls, model: type[Model]) -> type[ModelSerializer]:
        """
        Retrieve the `ModelSerializer` for a `Model`.
        """
        return cls.MAPPING[model]


for module_info in pkgutil.iter_modules(
    path=projects.__path__,
    prefix=".projects.",
):
    module = importlib.import_module(
        name=module_info.name,
        package=__package__,
    )

    # Predicate that ensures members satisfy the following:
    # - The member is a subclass of ProjectRecordSerializer
    # - The member has a Meta.model attribute
    predicate = (
        lambda x: inspect.isclass(x)
        and issubclass(x, ProjectRecordSerializer)
        and hasattr(x.Meta, "model")
    )

    # For each member of the module that satisfies the predicate
    # Add it to the mapping
    for name, cls in inspect.getmembers(module, predicate):
        ModelSerializerMap.add(
            model=cls.Meta.model,
            serializer=cls,
        )
