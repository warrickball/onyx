from rest_framework import serializers
from data.models import Organism, MPX, COVID


class OrganismSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organism
        fields = "__all__"

    # Additional custom validation
    def validate(self, data):
        # Formatting constraint on the cid
        if data.get("cid") and data.get("sender_sample_id") and data.get("run_name"):
            if data["cid"] != f"{data['sender_sample_id']}.{data['run_name']}":
                raise serializers.ValidationError("The cid must be of the form sender_sample_id.run_name")
        return data


class MPXSerializer(OrganismSerializer):
    class Meta:
        model = MPX
        fields = "__all__"


class COVIDSerializer(OrganismSerializer):
    class Meta:
        model = COVID
        fields = "__all__"
