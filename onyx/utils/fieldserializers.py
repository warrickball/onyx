from datetime import date
from rest_framework import serializers, exceptions
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import smart_str
from django.utils.translation import gettext_lazy as _
from data.models import Choice


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
            raise exceptions.ValidationError("Enter a valid date in YYYY-MM format.")

        return value

    def to_representation(self, value):
        try:
            year, month, _ = str(value).split("-")
        except ValueError:
            raise exceptions.ValidationError("Must be in YYYY-MM-DD format.")

        return year + "-" + month


class ModelChoiceField(serializers.RelatedField):
    default_error_messages = {
        "does_not_exist": _(
            "Select a valid choice. That choice is not one of the available choices."
        ),
        "invalid": _("Invalid value."),
    }

    def __init__(self, project, **kwargs):
        self.project = project
        super().__init__(queryset=Choice.objects.all(), **kwargs)

    def to_internal_value(self, data):
        queryset = self.get_queryset()

        try:
            return queryset.get(  # type: ignore
                **{
                    "project_id": self.project,
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


class ChoiceField(serializers.ChoiceField):
    default_error_messages = {
        "invalid_choice": "Select a valid choice. That choice is not one of the available choices."
    }

    def __init__(self, project, field, **kwargs):
        self.project = project
        self.field = field
        super().__init__([], **kwargs)

    def to_internal_value(self, data):
        self.choices = list(
            Choice.objects.filter(
                project_id=self.project,
                field=self.field,
                is_active=True,
            ).values_list(
                "choice",
                flat=True,
            )
        )
        self.choice_map = {choice.lower().strip(): choice for choice in self.choices}

        if isinstance(data, str):
            data = data.lower().strip()

            if data in self.choice_map:
                data = self.choice_map[data]

        return super().to_internal_value(data)
