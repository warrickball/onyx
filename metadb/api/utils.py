from rest_framework import serializers
from django.http import Http404
from datetime import date
import data.models
import inspect


def get_pathogen_model_or_404(pathogen_code):
    '''
    Returns the model for the given `pathogen_code`, raising a `Http404` if it doesn't exist.
    '''
    members = inspect.getmembers(data.models, inspect.isclass)
    for name, model in members:
        if pathogen_code.upper() == name.upper():
            return model
    raise Http404


# TODO: Improve
class YearMonthField(serializers.Field):
    def to_representation(self, value):
        year, month, _ = str(value).split("-")
        return year + "-" + month

    def to_internal_value(self, data):
        year, month = data.split("-")
        value = date(int(year), int(month), 1)
        return value
