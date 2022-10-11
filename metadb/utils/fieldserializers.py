from rest_framework import serializers
from rest_framework.validators import ValidationError
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


class LowerChoiceField(serializers.ChoiceField):
    def to_internal_value(self, data):
        data = str(data).lower()
        return super().to_internal_value(data)


class LowerCharField(serializers.CharField):
    def to_internal_value(self, data):
        data = str(data).lower()
        return super().to_internal_value(data)
