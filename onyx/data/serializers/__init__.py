from data.models import AbstractRecord, Record, TestModel
from .serializers import AbstractRecordSerializer, RecordSerializer, SerializerNode
from .testserializers import TestSerializer


class ModelSerializerMap:
    MAPPING = {
        AbstractRecord: AbstractRecordSerializer,
        Record: RecordSerializer,
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
