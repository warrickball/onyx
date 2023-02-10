from rest_framework import serializers
from rest_framework.validators import ValidationError
from django.utils.translation import gettext_lazy as _
from internal.models import Choice
from datetime import date


class YearMonthField(serializers.Field):
    def to_internal_value(self, data):
        try:
            year, month = str(data).split("-")
        except ValueError:
            raise ValidationError("Must be in YYYY-MM format.")

        try:
            value = date(int(year), int(month), 1)
        except ValueError as e:
            raise ValidationError(e)

        return value

    def to_representation(self, value):
        try:
            year, month, _ = str(value).split("-")
        except ValueError:
            raise ValidationError("Must be in YYYY-MM-DD format.")

        return year + "-" + month


class LowerCharField(serializers.CharField):
    def to_internal_value(self, data):
        data = str(data).lower()
        return super().to_internal_value(data)


# TODO: Currently no support for choice fields from inherited models
class ChoiceField(serializers.PrimaryKeyRelatedField):
    default_error_messages = {
        "does_not_exist": _(
            "Select a valid choice. That choice is not one of the available choices."
        )
    }

    def to_internal_value(self, data):
        content_type = self.context["project"].content_type
        app_label = content_type.app_label
        model_name = content_type.name
        model_field = self.source
        choice_key = f"{app_label}.{model_name}.{model_field}.{data}"

        try:
            instance = Choice.objects.get(choice_key=choice_key)
        except Choice.DoesNotExist:
            self.fail("does_not_exist", pk_value=data)

        data = instance.id  # type: ignore
        return super().to_internal_value(data)

    def to_representation(self, value):
        value = super().to_representation(value)
        return value.split(".")[-1]
