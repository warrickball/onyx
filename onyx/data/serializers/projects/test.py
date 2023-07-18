from rest_framework.validators import UniqueTogetherValidator
from ..serializers import ProjectRecordSerializer
from data.models.projects.test import BaseTestModel, TestModel
from utils.fieldserializers import ChoiceField, YearMonthField


class BaseTestSerializer(ProjectRecordSerializer):
    collection_month = YearMonthField(required=False, allow_null=True)
    received_month = YearMonthField(required=False, allow_null=True)
    country = ChoiceField("test", "country")
    region = ChoiceField("test", "region", required=False, allow_null=True)

    class Meta:
        model = BaseTestModel
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
            "start",
            "end",
        ]
        validators = [
            UniqueTogetherValidator(
                queryset=BaseTestModel.objects.all(),
                fields=["sample_id", "run_name"],
            )
        ]

    class OnyxMeta(ProjectRecordSerializer.OnyxMeta):
        optional_value_groups = (
            ProjectRecordSerializer.OnyxMeta.optional_value_groups
            + [("collection_month", "received_month")]
        )
        orderings = ProjectRecordSerializer.OnyxMeta.orderings + [
            ("collection_month", "received_month"),
            ("start", "end"),
        ]
        non_futures = ProjectRecordSerializer.OnyxMeta.non_futures + [
            "collection_month",
            "received_month",
            "submission_date",
        ]
        choice_constraints = ProjectRecordSerializer.OnyxMeta.choice_constraints + [
            ("country", "region")
        ]


class TestSerializer(BaseTestSerializer):
    class Meta:
        model = TestModel
        fields = BaseTestSerializer.Meta.fields


mapping = {TestModel: TestSerializer}
