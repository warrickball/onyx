from rest_framework.validators import UniqueTogetherValidator
from ..serializers import RecordSerializer
from data.models import TestModel
from utils.fieldserializers import ChoiceField, YearMonthField


class TestSerializer(RecordSerializer):
    collection_month = YearMonthField(required=False, allow_null=True)
    received_month = YearMonthField(required=False, allow_null=True)
    country = ChoiceField(TestModel, "country")
    region = ChoiceField(TestModel, "region", required=False, allow_null=True)

    class Meta:
        model = TestModel
        fields = RecordSerializer.Meta.fields + [
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

    class ExtraMeta(RecordSerializer.ExtraMeta):
        optional_value_groups = RecordSerializer.ExtraMeta.optional_value_groups + [
            ("collection_month", "received_month")
        ]
        orderings = RecordSerializer.ExtraMeta.orderings + [
            ("collection_month", "received_month")
        ]
        non_futures = RecordSerializer.ExtraMeta.non_futures + [
            "collection_month",
            "received_month",
            "submission_date",
        ]
