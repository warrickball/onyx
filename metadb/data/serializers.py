from rest_framework import serializers
from .models import FastaStats, BamStats, VAF, Pathogen, Mpx, Covid
from accounts.models import Institute
from utils.fieldserializers import YearMonthField


class FastaStatsSerializer(serializers.ModelSerializer):    
    class Meta:
        model = FastaStats
        exclude = ("id", "metadata")


class VAFSerializer(serializers.ModelSerializer):
    class Meta:
        model = VAF
        exclude = ("id", "bam_stats")


class BamStatsSerializer(serializers.ModelSerializer):
    vafs = VAFSerializer(many=True)

    class Meta:
        model = BamStats
        exclude = ("id", "metadata")


class PathogenSerializer(serializers.ModelSerializer):
    collection_month = YearMonthField(required=False)
    received_month = YearMonthField(required=False) 
    institute = serializers.SlugRelatedField(queryset=Institute.objects.all(), slug_field="code")

    # These are the last line of defence in case view validation somehow fails
    # TODO: Don't really need these. Double check and get rid
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
        exclude = Pathogen.excluded_fields()


class MpxSerializer(PathogenSerializer):
    class Meta:
        model = Mpx
        exclude = Mpx.excluded_fields()


class CovidSerializer(PathogenSerializer):
    class Meta:
        model = Covid
        exclude = Covid.excluded_fields()


class PathogenStatsSerializer(PathogenSerializer):
    fasta = FastaStatsSerializer()
    bam = BamStatsSerializer()


class MpxStatsSerializer(MpxSerializer):
    fasta = FastaStatsSerializer()
    bam = BamStatsSerializer()


class CovidStatsSerializer(CovidSerializer):
    fasta = FastaStatsSerializer()
    bam = BamStatsSerializer()
