from rest_framework import serializers
from .models import Pathogen, Mpx, Covid
from accounts.models import Institute
from utils.functions import get_choices
from utils.fieldserializers import YearMonthField


class PathogenSerializer(serializers.ModelSerializer):
    collection_date = YearMonthField()
    received_date = YearMonthField() 
    institute = serializers.ChoiceField(choices=get_choices(model=Institute, field="code"))

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
