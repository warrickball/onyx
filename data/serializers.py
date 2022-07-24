from rest_framework import serializers
from .models import Pathogen, Mpx, Covid
from accounts.models import Institute
from utils.functions import get_choices
from utils.fieldserializers import YearMonthField


EXCLUDED_FIELDS = ("id", "created", "last_modified")


class PathogenSerializer(serializers.ModelSerializer):
    collection_month = YearMonthField()
    received_month = YearMonthField() 
    institute = serializers.ChoiceField(choices=get_choices(model=Institute, field="code"))

    class Meta:
        model = Pathogen
        exclude = EXCLUDED_FIELDS


class MpxSerializer(PathogenSerializer):
    class Meta:
        model = Mpx
        exclude = EXCLUDED_FIELDS
    

class CovidSerializer(PathogenSerializer):
    class Meta:
        model = Covid
        exclude = EXCLUDED_FIELDS
