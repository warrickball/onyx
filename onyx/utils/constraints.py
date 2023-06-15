from django.db import models
from django.db.models import Q
import functools
import operator


def unique_together(model_name, fields):
    return models.UniqueConstraint(
        fields=fields,
        name=f"unique_together_{model_name}_{'_'.join(fields)}",
    )


def optional_value_group(model_name, fields):
    return models.CheckConstraint(
        check=functools.reduce(
            operator.or_, [Q(**{f"{field}__isnull": False}) for field in fields]
        ),
        name=f"optional_value_group_{model_name}_{'_'.join(fields)}",
        violation_error_message="At least one of '"
        + "', '".join(fields)
        + "' is required.",
    )
