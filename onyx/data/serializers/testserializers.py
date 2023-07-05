from rest_framework.validators import UniqueTogetherValidator
from ..serializers import ProjectRecordSerializer
from data.models import TestModel
from utils.fieldserializers import ChoiceField, YearMonthField


class TestSerializer(ProjectRecordSerializer):
    collection_month = YearMonthField(required=False, allow_null=True)
    received_month = YearMonthField(required=False, allow_null=True)
    country = ChoiceField(TestModel, "country")
    region = ChoiceField(TestModel, "region", required=False, allow_null=True)

    class Meta:
        model = TestModel
        fields = ProjectRecordSerializer.Meta.fields + [
            "sample_id",
            "run_name",
            "collection_month",
            "received_month",
            "submission_date",
            "country",
            "region",
            "concern",
            "tests",
            "score",
        ]
        validators = [
            UniqueTogetherValidator(
                queryset=TestModel.objects.all(),
                fields=["sample_id", "run_name"],
            )
        ]

    class OnyxMeta(ProjectRecordSerializer.OnyxMeta):
        optional_value_groups = (
            ProjectRecordSerializer.OnyxMeta.optional_value_groups
            + [("collection_month", "received_month")]
        )
        orderings = ProjectRecordSerializer.OnyxMeta.orderings + [
            ("collection_month", "received_month")
        ]
        non_futures = ProjectRecordSerializer.OnyxMeta.non_futures + [
            "collection_month",
            "received_month",
            "submission_date",
        ]
