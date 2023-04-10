from rest_framework import serializers
from rest_framework.validators import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import smart_str
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from datetime import date


class YearMonthField(serializers.Field):
    def to_internal_value(self, data):
        if not data:
            if self.allow_null:
                return None
            else:
                self.fail("null")

        try:
            year, month = str(data).split("-")
            if not (len(year) == 4 and 1 <= len(month) <= 2):
                raise ValueError
            value = date(int(year), int(month), 1)
        except ValueError:
            raise ValidationError("Enter a valid date in YYYY-MM format.")

        return value

    def to_representation(self, value):
        try:
            year, month, _ = str(value).split("-")
        except ValueError:
            raise ValidationError("Must be in YYYY-MM-DD format.")

        return year + "-" + month


class ChoiceField(serializers.RelatedField):
    default_error_messages = {
        "does_not_exist": _(
            "Select a valid choice. That choice is not one of the available choices."
        ),
        "invalid": _("Invalid value."),
    }

    def __init__(self, **kwargs):
        self.model = kwargs["model"]
        kwargs.pop("model")
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        queryset = self.get_queryset()
        content_type = ContentType.objects.get_for_model(self.model)

        try:
            return queryset.get(  # type: ignore
                **{
                    "content_type": content_type,
                    "field": self.source,
                    "choice": data,
                }
            )
        except ObjectDoesNotExist:
            self.fail("does_not_exist", slug_name="choice", value=smart_str(data))
        except (TypeError, ValueError):
            self.fail("invalid")

    def to_representation(self, obj):
        return getattr(obj, "choice")  # type: ignore
