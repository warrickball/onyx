from rest_framework import serializers
from rest_framework.validators import ValidationError
from datetime import date


class YearMonthField(serializers.Field):
    def to_representation(self, value):
        try:
            year, month, _ = str(value).split("-")
        except ValueError as e:
            raise ValidationError("must be in YYYY-WW-DD format")

        return year + "-" + month

    def to_internal_value(self, data):
        try:
            year, month = str(data).split("-")
        except ValueError as e:
            raise ValidationError("must be in YYYY-WW format")
        
        try:
            value = date(int(year), int(month), 1)
        except ValueError as e:
            raise ValidationError(e)
        
        return value
