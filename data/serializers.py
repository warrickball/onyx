from rest_framework import serializers
from django.db.utils import OperationalError
from datetime import date
from .models import Uploader, Pathogen, Mpx, Covid


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


class PathogenSerializer(serializers.ModelSerializer):
    collection_date = YearMonthField()
    received_date = YearMonthField() 
    uploader = serializers.ChoiceField(choices=get_choices(model=Uploader, field="code"))

    class Meta:
        model = Pathogen
        exclude = ("id", )


class MpxSerializer(PathogenSerializer):
    class Meta:
        model = Mpx
        exclude = ("id", )
    

class CovidSerializer(PathogenSerializer):
    class Meta:
        model = Covid
        exclude = ("id", )
