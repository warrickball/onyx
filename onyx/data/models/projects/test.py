from django.db import models
from ..models import ProjectRecord
from utils.fields import YearMonthField, StrippedCharField, ChoiceField
from utils.constraints import unique_together, optional_value_group


class BaseTestModel(ProjectRecord):
    sample_id = StrippedCharField(max_length=24)
    run_name = StrippedCharField(max_length=96)
    collection_month = YearMonthField(null=True)
    received_month = YearMonthField(null=True)
    submission_date = models.DateField()
    country = ChoiceField(max_length=20)
    region = ChoiceField(max_length=20, null=True)
    concern = models.BooleanField()
    tests = models.IntegerField()
    score = models.FloatField()
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
        ]


class TestModel(BaseTestModel):
    class Meta:
        default_permissions = []
