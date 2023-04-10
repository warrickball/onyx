from rest_framework import serializers
from internal.serializers import DynamicFieldsModelSerializer
from internal.models import Choice
from data.models import Record, Genomic, Mpx, ThresholdCycle
from utils import fieldserializers
from utils.validation import (
    enforce_optional_value_groups_create,
    enforce_optional_value_groups_update,
    enforce_yearmonth_order_create,
    enforce_yearmonth_order_update,
    enforce_yearmonth_non_future,
)


class ThresholdCycleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThresholdCycle
        fields = ["test_id", "ct_value"]


class RecordSerializer(DynamicFieldsModelSerializer):
    thresholdcycle = ThresholdCycleSerializer(
        many=True, required=False, allow_null=True
    )

    class Meta:
        model = Record
        fields = [
            "created",
            "last_modified",
            "suppressed",
            "user",
            "site",
            "cid",
            "published_date",
            "thresholdcycle",
        ]

    def create(self, validated_data):
        cts = validated_data.pop("thresholdcycle", None)

        record = super().create(validated_data)

        if cts:
            for ct in cts:
                ThresholdCycle.objects.create(record=record, **ct)

        return record

    def validate(self, data):
        """
        Additional validation carried out on either object creation or update
        """
        model = self.Meta.model
        errors = {}

        # Object update validation
        if self.instance:
            enforce_optional_value_groups_update(
                errors=errors,
                instance=self.instance,
                data=data,
                groups=model.CustomMeta.optional_value_groups,
            )
            for (
                lower_yearmonth,
                higher_yearmonth,
            ) in model.CustomMeta.yearmonth_orderings:
                enforce_yearmonth_order_update(
                    errors=errors,
                    instance=self.instance,
                    lower_yearmonth=lower_yearmonth,
                    higher_yearmonth=higher_yearmonth,
                    data=data,
                )
        # Object create validation
        else:
            enforce_optional_value_groups_create(
                errors=errors,
                data=data,
                groups=model.CustomMeta.optional_value_groups,
            )
            for (
                lower_yearmonth,
                higher_yearmonth,
            ) in model.CustomMeta.yearmonth_orderings:
                enforce_yearmonth_order_create(
                    errors=errors,
                    lower_yearmonth=lower_yearmonth,
                    higher_yearmonth=higher_yearmonth,
                    data=data,
                )
        # Object create and update validation
        for yearmonth in model.CustomMeta.yearmonths:
            if data.get(yearmonth):
                enforce_yearmonth_non_future(
                    errors=errors,
                    name=yearmonth,
                    value=data[yearmonth],
                )

        if errors:
            raise serializers.ValidationError(errors)

        return data


class GenomicSerializer(RecordSerializer):
    collection_month = fieldserializers.YearMonthField(required=False, allow_null=True)
    received_month = fieldserializers.YearMonthField()

    class Meta:
        model = Genomic
        fields = RecordSerializer.Meta.fields + [
            "sample_id",
            "run_name",
            "collection_month",
            "received_month",
            "fasta_path",
            "bam_path",
        ]


class MpxSerializer(GenomicSerializer):
    sample_type = fieldserializers.ChoiceField(
        model=Mpx,
        queryset=Choice.objects.all(),
    )
    seq_platform = fieldserializers.ChoiceField(
        model=Mpx,
        queryset=Choice.objects.all(),
    )
    enrichment_method = fieldserializers.ChoiceField(
        model=Mpx,
        queryset=Choice.objects.all(),
    )
    seq_strategy = fieldserializers.ChoiceField(
        model=Mpx,
        queryset=Choice.objects.all(),
    )
    source_of_library = fieldserializers.ChoiceField(
        model=Mpx,
        queryset=Choice.objects.all(),
    )
    country = fieldserializers.ChoiceField(
        model=Mpx,
        queryset=Choice.objects.all(),
    )
    run_layout = fieldserializers.ChoiceField(
        model=Mpx,
        queryset=Choice.objects.all(),
    )
    patient_ageband = fieldserializers.ChoiceField(
        model=Mpx,
        queryset=Choice.objects.all(),
        required=False,
        allow_null=True,
    )
    sample_site = fieldserializers.ChoiceField(
        model=Mpx,
        queryset=Choice.objects.all(),
        required=False,
        allow_null=True,
    )
    ukhsa_region = fieldserializers.ChoiceField(
        model=Mpx,
        queryset=Choice.objects.all(),
        required=False,
        allow_null=True,
    )
    travel_status = fieldserializers.ChoiceField(
        model=Mpx,
        queryset=Choice.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Mpx
        fields = GenomicSerializer.Meta.fields + [
            "sample_type",
            "seq_platform",
            "instrument_model",
            "enrichment_method",
            "seq_strategy",
            "source_of_library",
            "bioinfo_pipe_name",
            "bioinfo_pipe_version",
            "country",
            "run_layout",
            "patient_ageband",
            "patient_id",
            "sample_site",
            "ukhsa_region",
            "travel_status",
            "outer_postcode",
            "epi_cluster",
            "csv_template_version",
        ]


def get_serializer(model):
    """
    Function that returns the appropriate serializer for the given model.
    """
    return {
        Mpx: MpxSerializer,
    }[model]
