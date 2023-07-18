from rest_framework.validators import UniqueTogetherValidator
from ..serializers import BaseRecordSerializer, ProjectRecordSerializer
from data.models.projects.test import BaseTestModel, TestModel, TestModelRecord
from utils.fieldserializers import ChoiceField, YearMonthField


class TestModelRecordSerializer(BaseRecordSerializer):
    test_start = YearMonthField()
    test_end = YearMonthField()

    class Meta:
        model = TestModelRecord
        fields = BaseRecordSerializer.Meta.fields + [
            "test_id",
            "test_pass",
            "test_start",
            "test_end",
            "score_a",
            "score_b",
            "score_c",
        ]

    class OnyxMeta(BaseRecordSerializer.OnyxMeta):
        identifiers = BaseRecordSerializer.OnyxMeta.identifiers + ["test_id"]
        orderings = BaseRecordSerializer.OnyxMeta.orderings + [
            ("test_start", "test_end"),
        ]
        optional_value_groups = BaseRecordSerializer.OnyxMeta.optional_value_groups + [
            ("score_a", "score_b")
        ]
        conditional_required = BaseRecordSerializer.OnyxMeta.conditional_required | {
            "score_c": ["score_a", "score_b"]
        }


class BaseTestModelSerializer(ProjectRecordSerializer):
    collection_month = YearMonthField(required=False, allow_null=True)
    received_month = YearMonthField(required=False, allow_null=True)
    country = ChoiceField("test", "country", required=False, allow_null=True)
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
        conditional_required = ProjectRecordSerializer.OnyxMeta.conditional_required | {
            "region": ["country"]
        }


class TestModelSerializer(BaseTestModelSerializer):
    class Meta:
        model = TestModel
        fields = BaseTestModelSerializer.Meta.fields
        # NOTE: Just like fields, validators must be inherited
        validators = BaseTestModelSerializer.Meta.validators

    class OnyxMeta(BaseTestModelSerializer.OnyxMeta):
        relations = BaseTestModelSerializer.OnyxMeta.relations | {
            "records": {
                "serializer": TestModelRecordSerializer,
                "kwargs": {
                    "many": True,
                    "required": False,
                    "allow_null": True,
                },
            }
        }


mapping = {TestModel: TestModelSerializer}
