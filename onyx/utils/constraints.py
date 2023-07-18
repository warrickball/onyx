import functools
import operator
from django.db import models
from django.db.models import Q


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


def conditional_required(model_name, field, required):
    return models.CheckConstraint(
        check=Q(**{f"{field}__isnull": True})
        | functools.reduce(
            operator.and_, [Q(**{f"{req}__isnull": False}) for req in required]
        ),
        name=f"conditional_required_{model_name}_{field}_requires_{'_'.join(required)}",
        violation_error_message="All of '"
        + "', '".join(required)
        + "' are required in order to set "
        + field
        + ".",
    )
