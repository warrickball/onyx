from data.models import BaseRecord, ProjectRecord, TestModel
from .serializers import (
    BaseRecordSerializer,
    ProjectRecordSerializer,
    SerializerNode,
)
from .testserializers import TestSerializer


class ModelSerializerMap:
    MAPPING = {
        BaseRecord: BaseRecordSerializer,
        ProjectRecord: ProjectRecordSerializer,
        TestModel: TestSerializer,
    }

    @classmethod
    def get(cls, model):
        return cls.MAPPING.get(model)

    @classmethod
    def update(cls, mapping):
        cls.MAPPING = cls.MAPPING | mapping


try:
    from .projects import *

    if hasattr(projects, "mapping"):
        ModelSerializerMap.update(projects.mapping)
except (ImportError, ModuleNotFoundError):
    pass
