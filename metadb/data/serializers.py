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
    collection_month = YearMonthField(required=False, allow_null=True)
    received_month = YearMonthField(required=False, allow_null=True)
    institute = serializers.SlugRelatedField(
        queryset=Institute.objects.all(), slug_field="code"
    )

    class Meta:
        model = Pathogen
        exclude = Pathogen.hidden_fields()

    def validate(self, data):
        """
        Additional validation carried out on either object creation or update

        Update is indicated by the existence of a `self.instance`

        Creation is indicated by `self.instance = None`
        """
        errors = {}
        model = self.Meta.model

        if self.instance:
            # An update is occuring

            # Want to ensure each group still has at least one non-null field after update
            for group in model.OPTIONAL_VALUE_GROUPS:
                # List of non-null fields from the group
                instance_group_fields = [
                    field
                    for field in group
                    if getattr(self.instance, field) is not None
                ]

                # List of fields specified by the request data that are going to be nullified
                fields_to_nullify = [
                    field for field in group if field in data and data[field] is None
                ]

                # If the resulting set is empty, it means one of two not-good things:
                # The request contains enough fields from the group being nullified that there will be no non-null fields left from the group
                # There were (somehow) no non-null fields in the group to begin with
                if set(instance_group_fields) - set(fields_to_nullify) == set():
                    errors.setdefault("at_least_one_required", []).append(group)

        else:
            # Creation is occuring

            # Check that the pathogen code provided is for the same model we are serialising
            pathogen_code = model.__name__.upper()
            request_pathogen_code = data.get("pathogen_code")
            if pathogen_code != request_pathogen_code:
                errors["mismatch_pathogen_code"] = [
                    pathogen_code,
                    request_pathogen_code,
                ]

            # Want to ensure each group has at least one non-null field when creating
            for group in model.OPTIONAL_VALUE_GROUPS:
                for field in group:
                    if field in data and data[field] is not None:
                        break
                else:
                    # If you're reading this I'm sorry
                    # I couldn't help but try a for-else
                    # I just found out it can be done, so I did it :)
                    errors.setdefault("at_least_one_required", []).append(group)

        if errors:
            raise serializers.ValidationError(errors)

        return data


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
