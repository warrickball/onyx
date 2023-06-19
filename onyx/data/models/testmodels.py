from django.db import models
from .models import Record
from utils.fields import YearMonthField, StrippedCharField, ChoiceField
from utils.constraints import unique_together, optional_value_group


class TestModel(Record):
    sample_id = StrippedCharField(max_length=24)
    run_name = StrippedCharField(max_length=96)
    collection_month = YearMonthField(null=True)
    received_month = YearMonthField(null=True)
    submission_date = models.DateField()
    country = ChoiceField(max_length=20)
    region = ChoiceField(max_length=20)
    concern = models.BooleanField(null=True)
    tests = models.IntegerField()
    score = models.FloatField()

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
                model_name="testmodel",
                fields=["sample_id", "run_name"],
            ),
            optional_value_group(
                model_name="testmodel",
                fields=["collection_month", "received_month"],
            ),
        ]
