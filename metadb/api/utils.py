from rest_framework import serializers, status
from rest_framework.response import Response
from django.http import Http404
from django.db.utils import OperationalError
from datetime import date
import data.models
import inspect


class Responses:
    cannot_provide_cid = Response({"detail" : "cids are generated internally and cannot be provided"}, status=status.HTTP_403_FORBIDDEN)
    is_not_uploader = Response({"detail" : "user cannot create/modify data for this uploader"}, status=status.HTTP_403_FORBIDDEN)
    no_pathogen_code = Response({"detail" : "no pathogen_code was provided"}, status=status.HTTP_400_BAD_REQUEST)
    cannot_query_id = Response({"detail" : "cannot query id field"}, status=status.HTTP_403_FORBIDDEN)


def get_pathogen_model_or_404(pathogen_code):
    '''
    Returns the model for the given `pathogen_code`, raising a `Http404` if it doesn't exist.
    '''
    members = inspect.getmembers(data.models, inspect.isclass)
    for name, model in members:
        if pathogen_code.upper() == name.upper():
            return model
    raise Http404


def get_choices(model, field):
    try:
        choices = list(model.objects.values_list(field, flat=True))
    except OperationalError:
        choices = []
    return choices


# TODO: Improve: needs to raise validation errors
class YearMonthField(serializers.Field):
    def to_representation(self, value):
        year, month, _ = str(value).split("-")
        return year + "-" + month

    def to_internal_value(self, data):
        year, month = data.split("-")
        value = date(int(year), int(month), 1)
        return value
