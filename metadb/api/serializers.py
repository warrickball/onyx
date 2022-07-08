from rest_framework import serializers
from data.models import Uploader, Pathogen, Mpx, Covid
from api.utils import YearMonthField, get_choices


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
