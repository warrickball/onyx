from rest_framework import serializers
from .models import Pathogen, Mpx, Covid  # , FastaStats, BamStats, VAF
from accounts.models import Institute
from utils.fieldserializers import YearMonthField


# class FastaStatsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = FastaStats
#         exclude = ("id", "metadata")


# class VAFSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = VAF
#         exclude = ("id", "bam_stats")


# class BamStatsSerializer(serializers.ModelSerializer):
#     vafs = VAFSerializer(many=True)

#     class Meta:
#         model = BamStats
#         exclude = ("id", "metadata")


class PathogenSerializer(serializers.ModelSerializer):
    collection_month = YearMonthField(required=False)
    received_month = YearMonthField(required=False)
    institute = serializers.SlugRelatedField(
        queryset=Institute.objects.all(), slug_field="code"
    )

    class Meta:
        model = Pathogen
        exclude = Pathogen.hidden_fields()


class MpxSerializer(PathogenSerializer):
    previous_sample_id = serializers.CharField(required=False)

    class Meta:
        model = Mpx
        exclude = Mpx.hidden_fields()


class CovidSerializer(PathogenSerializer):
    class Meta:
        model = Covid
        exclude = Covid.hidden_fields()


# class PathogenStatsSerializer(PathogenSerializer):
#     fasta = FastaStatsSerializer()
#     bam = BamStatsSerializer()


# class MpxStatsSerializer(MpxSerializer):
#     fasta = FastaStatsSerializer()
#     bam = BamStatsSerializer()


# class CovidStatsSerializer(CovidSerializer):
#     fasta = FastaStatsSerializer()
#     bam = BamStatsSerializer()
