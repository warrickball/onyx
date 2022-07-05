from rest_framework import serializers
from data.models import Pathogen, Mpx, Covid
from api.utils import YearMonthField


class PathogenSerializer(serializers.ModelSerializer):
    # TODO: do they need to be defined here..?
    collection_date = YearMonthField()
    received_date = YearMonthField()

    class Meta:
        model = Pathogen
        fields = "__all__"


class MpxSerializer(PathogenSerializer):
    class Meta:
        model = Mpx
        fields = "__all__"
    

class CovidSerializer(PathogenSerializer):
    class Meta:
        model = Covid
        fields = "__all__"
