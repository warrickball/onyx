from data.models.projects import Mpx
from data.serializers.projects import MpxSerializer


def get_serializer(model):
    """
    Function that returns the appropriate serializer for the given model.
    """
    return {
        Mpx: MpxSerializer,
    }[model]
