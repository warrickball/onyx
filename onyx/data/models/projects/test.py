from django.db import models
from ..models import BaseRecord, ProjectRecord
from utils.fields import YearMonthField, StrippedCharField, ChoiceField
from utils.constraints import (
    unique_together,
    optional_value_group,
    conditional_required,
)


__version__ = "0.1.0"


class BaseTestModel(ProjectRecord):
    @classmethod
    def version(cls):
        return __version__

    sample_id = StrippedCharField(max_length=24)
    run_name = StrippedCharField(max_length=96)
    collection_month = YearMonthField(null=True)
    received_month = YearMonthField(null=True)
    text_option_1 = models.TextField(blank=True)
    text_option_2 = models.TextField(blank=True)
    submission_date = models.DateField(null=True)
    country = ChoiceField(max_length=20, blank=True)
    region = ChoiceField(max_length=20, blank=True)
    concern = models.BooleanField(null=True)
    tests = models.IntegerField(null=True)
    score = models.FloatField(null=True)
    start = models.IntegerField()
    end = models.IntegerField()

    class Meta:
        default_permissions = []
        indexes = [
            models.Index(fields=["sample_id", "run_name"]),
            models.Index(fields=["sample_id"]),
            models.Index(fields=["run_name"]),
            models.Index(fields=["collection_month"]),
            models.Index(fields=["received_month"]),
        ]
        constraints = [
            unique_together(
                model_name="basetestmodel",
                fields=["sample_id", "run_name"],
            ),
            optional_value_group(
                model_name="basetestmodel",
                fields=["collection_month", "received_month"],
            ),
            optional_value_group(
                model_name="basetestmodel",
                fields=["text_option_1", "text_option_2"],
            ),
            conditional_required(
                model_name="basetestmodel", field="region", required=["country"]
            ),
        ]


class TestModel(BaseTestModel):
    class Meta:
        default_permissions = []


class TestModelRecord(BaseRecord):
    link = models.ForeignKey(
        TestModel, on_delete=models.CASCADE, related_name="records"
    )
    test_id = models.IntegerField()
    test_pass = models.BooleanField()
    test_start = YearMonthField()
    test_end = YearMonthField()
    score_a = models.FloatField(null=True)
    score_b = models.FloatField(null=True)
    score_c = models.FloatField(null=True)

    class Meta:
        default_permissions = []
        constraints = [
            unique_together(
                model_name="testmodelrecords",
                fields=["link", "test_id"],
            ),
            optional_value_group(
                model_name="testmodelrecords",
                fields=["score_a", "score_b"],
            ),
            conditional_required(
                model_name="testmodelrecords",
                field="score_c",
                required=["score_a", "score_b"],
            ),
        ]
