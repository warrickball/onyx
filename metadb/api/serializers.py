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
    
    def create(self, validated_data):
        # Automatically store cid as sender_sample_id.run_name
        validated_data["cid"] = f"{validated_data['sender_sample_id']}.{validated_data['run_name']}"
        pathogen = Mpx.objects.create(**validated_data)
        return pathogen


class CovidSerializer(PathogenSerializer):
    class Meta:
        model = Covid
        fields = "__all__"

    def create(self, validated_data):
        # Automatically store cid as sender_sample_id.run_name
        validated_data["cid"] = f"{validated_data['sender_sample_id']}.{validated_data['run_name']}"
        pathogen = Covid.objects.create(**validated_data)
        return pathogen
