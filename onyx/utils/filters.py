from django_filters import rest_framework as filters
from utils.forms import ChoiceField


class CharInFilter(filters.BaseInFilter, filters.CharFilter):
    pass


class CharRangeFilter(filters.BaseRangeFilter, filters.CharFilter):
    pass


class NumberInFilter(filters.BaseInFilter, filters.NumberFilter):
    pass


class NumberRangeFilter(filters.BaseRangeFilter, filters.NumberFilter):
    pass


class DateInFilter(filters.BaseInFilter, filters.DateFilter):
    pass


class DateRangeFilter(filters.BaseRangeFilter, filters.DateFilter):
    pass


class DateTimeInFilter(filters.BaseInFilter, filters.DateTimeFilter):
    pass


class DateTimeRangeFilter(filters.BaseRangeFilter, filters.DateTimeFilter):
    pass


class TypedChoiceInFilter(filters.BaseInFilter, filters.TypedChoiceFilter):
    pass


class ModelChoiceInFilter(filters.BaseInFilter, filters.ModelChoiceFilter):
    pass


class ChoiceFilter(filters.Filter):
    field_class = ChoiceField


class ChoiceInFilter(filters.BaseInFilter, ChoiceFilter):
    pass
