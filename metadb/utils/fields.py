from django.db import models
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_date
from django.utils.translation import gettext_lazy as _
from datetime import date, datetime


# TODO: Improve and test
# https://stackoverflow.com/questions/1110153/what-is-the-most-efficient-way-to-store-a-list-in-the-django-models
# Might help with making custom types
class YearMonthField(models.DateField):
    '''
    Minimal override of DateField to support YYYY-MM format.
    '''
    default_error_messages = {
        "invalid": _(
            "“%(value)s” value has an invalid date format. It must be "
            "in YYYY-MM format."
        ),
        "invalid_date": _(
            "“%(value)s” value has the correct format (YYYY-MM) "
            "but it is an invalid date."
        ),
    }
    description = _("Date (without time OR day)")

    def to_python(self, value):
        if value is None:
            return value

        if isinstance(value, date):
            return value

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, str):
            try:
                parsed = parse_date(value + "-01")
                if parsed is not None:
                    return parsed
            except ValueError:
                raise ValidationError(
                    self.error_messages["invalid_date"],
                    code="invalid_date",
                    params={"value": value},
                )
        raise ValidationError(
            self.error_messages["invalid"],
            code="invalid",
            params={"value": value},
        )
