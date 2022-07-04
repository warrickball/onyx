from rest_framework import serializers
from data.models import Pathogen, Mpx, Covid


class PathogenSerializer(serializers.ModelSerializer):
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
