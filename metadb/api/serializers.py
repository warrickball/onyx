from rest_framework import serializers
from data.models import MPX, COVID


class MPXSerializer(serializers.ModelSerializer):
    class Meta:
        model = MPX
        fields = "__all__"


class COVIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = COVID
        fields = "__all__"