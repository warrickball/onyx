from rest_framework import serializers
from datetime import date


class YearMonthField(serializers.Field):
    def to_representation(self, value):
        year, month, _ = str(value).split("-")
        return year + "-" + month

    def to_internal_value(self, data):
        year, month = str(data).split("-")
        value = date(int(year), int(month), 1)
        return value
