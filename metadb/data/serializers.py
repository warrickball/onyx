from rest_framework import serializers
from accounts.models import Site
from data.models import PathogenCode, Pathogen, Mpx
from utils import fieldserializers
from utils.functions import (
    enforce_optional_value_groups_create,
    enforce_optional_value_groups_update,
    enforce_yearmonth_order_create,
    enforce_yearmonth_order_update,
    enforce_yearmonth_non_future,
)


class PathogenSerializer(serializers.ModelSerializer):
    pathogen_code = serializers.SlugRelatedField(
        queryset=PathogenCode.objects.all(), slug_field="code"
    )
    site = serializers.SlugRelatedField(queryset=Site.objects.all(), slug_field="code")
    collection_month = fieldserializers.YearMonthField(required=False, allow_null=True)
    received_month = fieldserializers.YearMonthField()

    class Meta:
        model = Pathogen
        fields = [
            "pathogen_code",
            "site",
            "cid",
            "sample_id",
            "run_name",
            "collection_month",
            "received_month",
            "published_date",
            "fasta_path",
            "bam_path",
        ]

    def validate(self, data):
        """
        Additional validation carried out on either object creation or update

        Update is indicated by the existence of a `self.instance`

        Creation is indicated by `self.instance = None`
        """
        model = self.Meta.model
        errors = {}

        if self.instance:
            enforce_optional_value_groups_update(
                errors=errors,
                instance=self.instance,
                data=data,
                groups=model.OPTIONAL_VALUE_GROUPS,
            )
            enforce_yearmonth_order_update(
                errors=errors,
                instance=self.instance,
                lower_yearmonth="collection_month",
                higher_yearmonth="received_month",
                data=data,
            )

        else:
            enforce_optional_value_groups_create(
                errors=errors,
                data=data,
                groups=model.OPTIONAL_VALUE_GROUPS,
            )
            enforce_yearmonth_order_create(
                errors=errors,
                lower_yearmonth="collection_month",
                higher_yearmonth="received_month",
                data=data,
            )

        if data.get("collection_month"):
            enforce_yearmonth_non_future(
                errors=errors,
                name="collection_month",
                value=data["collection_month"],
            )

        if data.get("received_month"):
            enforce_yearmonth_non_future(
                errors=errors,
                name="received_month",
                value=data["received_month"],
            )

        if errors:
            raise serializers.ValidationError(errors)

        return data


class AdminPathogenSerializer(PathogenSerializer):
    class Meta:
        model = Pathogen
        fields = PathogenSerializer.Meta.fields + [
            "id",
            "created",
            "last_modified",
            "suppressed",
        ]


class MpxSerializer(PathogenSerializer):
    sample_type = fieldserializers.LowerChoiceField(
        choices=Mpx._meta.get_field("sample_type").choices
    )
    seq_platform = fieldserializers.LowerChoiceField(
        choices=Mpx._meta.get_field("seq_platform").choices
    )
    enrichment_method = fieldserializers.LowerChoiceField(
        choices=Mpx._meta.get_field("enrichment_method").choices
    )
    seq_strategy = fieldserializers.LowerChoiceField(
        choices=Mpx._meta.get_field("seq_strategy").choices
    )
    source_of_library = fieldserializers.LowerChoiceField(
        choices=Mpx._meta.get_field("source_of_library").choices,
    )
    country = fieldserializers.LowerChoiceField(
        choices=Mpx._meta.get_field("country").choices,
    )
    run_layout = fieldserializers.LowerChoiceField(
        choices=Mpx._meta.get_field("run_layout").choices
    )
    patient_ageband = fieldserializers.LowerChoiceField(
        choices=Mpx._meta.get_field("patient_ageband").choices,
        required=False,
        allow_null=True,
    )
    sample_site = fieldserializers.LowerChoiceField(
        choices=Mpx._meta.get_field("sample_site").choices,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Mpx
        fields = PathogenSerializer.Meta.fields + [
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
        ]


class PhaMpxSerializer(MpxSerializer):
    ukhsa_region = fieldserializers.LowerChoiceField(
        choices=Mpx._meta.get_field("ukhsa_region").choices,
    )
    travel_status = fieldserializers.LowerChoiceField(
        choices=Mpx._meta.get_field("travel_status").choices,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Mpx
        fields = MpxSerializer.Meta.fields + [
            "ukhsa_region",
            "travel_status",
            "outer_postcode",
            "epi_cluster",
        ]


class AdminMpxSerializer(PhaMpxSerializer):
    class Meta:
        model = Mpx
        fields = PhaMpxSerializer.Meta.fields + [
            "id",
            "created",
            "last_modified",
            "suppressed",
            "csv_template_version",
        ]


serializer_map = {
    Pathogen: {
        "any": PathogenSerializer,
        "admin": AdminPathogenSerializer,
    },
    Mpx: {
        "any": MpxSerializer,
        "pha": PhaMpxSerializer,
        "admin": AdminMpxSerializer,
    },
}


def get_serializer(model, user, group=None):
    """
    Function that returns the appropriate serializer for the given model, depending on the user's permissions.
    """
    if group == "admin":
        if user.is_staff:
            return serializer_map[model].get("admin", serializer_map[model]["any"])
        else:
            return "You do not have permission to view this."

    elif group == "pha":
        if user.is_staff or user.site.is_pha:
            return serializer_map[model].get("pha", serializer_map[model]["any"])
        else:
            return "You do not have permission to view this."

    elif group == "any" or group is None:
        return serializer_map[model]["any"]

    else:
        return "Not found."
