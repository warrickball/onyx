from rest_framework import serializers
from .models import Pathogen, Mpx, Covid
from accounts.models import Institute
from utils.fieldserializers import YearMonthField


EXCLUDED_FIELDS = ("id", "created", "last_modified")


class PathogenSerializer(serializers.ModelSerializer):
    collection_month = YearMonthField()
    received_month = YearMonthField() 
    institute = serializers.SlugRelatedField(queryset=Institute.objects.all(), slug_field="code")

    # These are the last line of defence in case view validation somehow fails
    def validate_cid(self, value):                                     
        if self.instance and value != self.instance.cid:
            raise serializers.ValidationError("cid is forbidden from being updated.")
        return value

    def validate_sender_sample_id(self, value):                                     
        if self.instance and value != self.instance.sender_sample_id:
            raise serializers.ValidationError("sender_sample_id is forbidden from being updated.")
        return value

    def validate_run_name(self, value):                                     
        if self.instance and value != self.instance.run_name:
            raise serializers.ValidationError("run_name is forbidden from being updated.")
        return value

    def validate_pathogen_code(self, value):                                     
        if self.instance and value != self.instance.pathogen_code:
            raise serializers.ValidationError("pathogen_code is forbidden from being updated.")
        return value

    def validate_institute(self, value):                                     
        if self.instance and value != self.instance.institute:
            raise serializers.ValidationError("institute is forbidden from being updated.")
        return value
    
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
