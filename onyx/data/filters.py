import hashlib
from datetime import datetime
from distutils.util import strtobool
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django_filters import rest_framework as filters
from utils.functions import get_suggestions
from .utils import OnyxType, FieldInfo


class HashFieldForm(forms.CharField):
    def clean(self, value):
        value = super().clean(value).strip().lower()

        hasher = hashlib.sha256()
        hasher.update(value.encode("utf-8"))
        value = hasher.hexdigest()

        return value


class HashFilter(filters.Filter):
    field_class = HashFieldForm


class HashInFilter(filters.BaseInFilter, HashFilter):
    pass


class CharInFilter(filters.BaseInFilter, filters.CharFilter):
    pass


class CharRangeFilter(filters.BaseRangeFilter, filters.CharFilter):
    pass


class ChoiceFieldMixin:
    default_error_messages = {
        "invalid_choice": _("Select a valid choice.%(suggestions)s"),
    }

    def clean(self, value):
        self.choice_map = {
            choice.lower().strip(): choice
            for choice, _ in self.choices  #  type: ignore
        }

        if isinstance(value, str):
            value = value.strip()
            value_key = value.lower()

            if value_key in self.choice_map:
                value = self.choice_map[value_key]

        return super().clean(value)  #  type: ignore

    def validate(self, value):
        super(forms.ChoiceField, self).validate(value)  #  type: ignore

        if value and not self.valid_value(value):  #  type: ignore
            choices = [str(x) for (_, x) in self.choices]  #  type: ignore
            s = get_suggestions(value, choices, n=1)

            if s:
                suggestions = f" Perhaps you meant: {', '.join(s)}"
            else:
                suggestions = ""

            raise ValidationError(
                self.error_messages["invalid_choice"],  #  type: ignore
                code="invalid_choice",
                params={"suggestions": suggestions},
            )


class ChoiceFieldForm(ChoiceFieldMixin, forms.ChoiceField):
    pass


class ChoiceFilter(filters.Filter):
    field_class = ChoiceFieldForm


class ChoiceInFilter(filters.BaseInFilter, ChoiceFilter):
    pass


class NumberInFilter(filters.BaseInFilter, filters.NumberFilter):
    pass


class NumberRangeFilter(filters.BaseRangeFilter, filters.NumberFilter):
    pass


class YearMonthForm(forms.DateField):
    def __init__(self, **kwargs):
        kwargs["input_formats"] = ["%Y-%m"]
        super().__init__(**kwargs)


class YearMonthFilter(filters.Filter):
    field_class = YearMonthForm


class YearMonthInFilter(filters.BaseInFilter, YearMonthFilter):
    pass


class YearMonthRangeFilter(filters.BaseRangeFilter, YearMonthFilter):
    pass


class DateFieldForm(forms.DateField):
    def __init__(self, **kwargs):
        kwargs["input_formats"] = ["%Y-%m-%d"]
        super().__init__(**kwargs)

    def clean(self, value):
        if isinstance(value, str) and value.strip().lower() == "today":
            value = datetime.now().date()

        return super().clean(value)


class DateFilter(filters.Filter):
    field_class = DateFieldForm


class DateInFilter(filters.BaseInFilter, DateFilter):
    pass


class DateRangeFilter(filters.BaseRangeFilter, DateFilter):
    pass


class DateTimeFieldForm(forms.DateTimeField):
    def __init__(self, **kwargs):
        kwargs["input_formats"] = [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
        ]
        super().__init__(**kwargs)

    def clean(self, value):
        if isinstance(value, str) and value.strip().lower() == "today":
            value = datetime.now()

        return super().clean(value)


class DateTimeFilter(filters.Filter):
    field_class = DateTimeFieldForm


class DateTimeInFilter(filters.BaseInFilter, DateTimeFilter):
    pass


class DateTimeRangeFilter(filters.BaseRangeFilter, DateTimeFilter):
    pass


class BooleanFieldForm(ChoiceFieldMixin, forms.TypedChoiceField):
    def __init__(self, **kwargs):
        kwargs["choices"] = [
            (x, x)
            for x in [
                "y",
                "yes",
                "t",
                "true",
                "on",
                "1",
                "n",
                "no",
                "f",
                "false",
                "off",
                "0",
            ]
        ]
        # TODO: I have a sneaky suspicion that strtobool's [0, 1] coercion
        # was messing up the filtering of isnull for relations. I have
        # yet to confirm this, but would be something good to confirm.
        kwargs["coerce"] = lambda x: bool(strtobool(x))
        super().__init__(**kwargs)


class BooleanFilter(filters.TypedChoiceFilter):
    field_class = BooleanFieldForm


class BooleanInFilter(filters.BaseInFilter, BooleanFilter):
    pass


# Mappings from field type + lookup to filter
FILTERS = {
    OnyxType.HASH: {lookup: HashFilter for lookup in OnyxType.HASH.lookups}
    | {
        "in": HashInFilter,
    },
    OnyxType.TEXT: {lookup: filters.CharFilter for lookup in OnyxType.TEXT.lookups}
    | {
        "in": CharInFilter,
        "range": CharRangeFilter,
    },
    OnyxType.CHOICE: {lookup: ChoiceFilter for lookup in OnyxType.CHOICE.lookups}
    | {
        "in": ChoiceInFilter,
    },
    OnyxType.INTEGER: {
        lookup: filters.NumberFilter for lookup in OnyxType.INTEGER.lookups
    }
    | {
        "in": NumberInFilter,
        "range": NumberRangeFilter,
        "isnull": BooleanFilter,
    },
    OnyxType.DECIMAL: {
        lookup: filters.NumberFilter for lookup in OnyxType.DECIMAL.lookups
    }
    | {
        "in": NumberInFilter,
        "range": NumberRangeFilter,
        "isnull": BooleanFilter,
    },
    OnyxType.DATE_YYYY_MM: {
        lookup: YearMonthFilter for lookup in OnyxType.DATE_YYYY_MM.lookups
    }
    | {
        "in": YearMonthInFilter,
        "range": YearMonthRangeFilter,
        "year": filters.NumberFilter,
        "year__in": NumberInFilter,
        "year__range": NumberRangeFilter,
        "iso_year": filters.NumberFilter,
        "iso_year__in": NumberInFilter,
        "iso_year__range": NumberRangeFilter,
        "week": filters.NumberFilter,
        "week__in": NumberInFilter,
        "week__range": NumberRangeFilter,
        "isnull": BooleanFilter,
    },
    OnyxType.DATE_YYYY_MM_DD: {
        lookup: DateFilter for lookup in OnyxType.DATE_YYYY_MM_DD.lookups
    }
    | {
        "in": DateInFilter,
        "range": DateRangeFilter,
        "year": filters.NumberFilter,
        "year__in": NumberInFilter,
        "year__range": NumberRangeFilter,
        "iso_year": filters.NumberFilter,
        "iso_year__in": NumberInFilter,
        "iso_year__range": NumberRangeFilter,
        "week": filters.NumberFilter,
        "week__in": NumberInFilter,
        "week__range": NumberRangeFilter,
        "isnull": BooleanFilter,
    },
    OnyxType.DATETIME: {lookup: DateTimeFilter for lookup in OnyxType.DATETIME.lookups}
    | {
        "in": DateTimeInFilter,
        "range": DateTimeRangeFilter,
        "year": filters.NumberFilter,
        "year__in": NumberInFilter,
        "year__range": NumberRangeFilter,
        "iso_year": filters.NumberFilter,
        "iso_year__in": NumberInFilter,
        "iso_year__range": NumberRangeFilter,
        "week": filters.NumberFilter,
        "week__in": NumberInFilter,
        "week__range": NumberRangeFilter,
        "isnull": BooleanFilter,
    },
    OnyxType.BOOLEAN: {lookup: BooleanFilter for lookup in OnyxType.BOOLEAN.lookups}
    | {
        "in": BooleanInFilter,
        "isnull": BooleanFilter,
    },
    OnyxType.RELATION: {
        "isnull": BooleanFilter,
    },
}


class OnyxFilter(filters.FilterSet):
    def __init__(self, fields: dict[str, FieldInfo], *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Constructing the filterset dynamically enables:
        # Checking whether the provided field_path and lookup can be used together
        # Validating the values provided by the user for the fields
        # Returning cleaned values from user inputs, using the filterset's underlying form
        for field, field_info in fields.items():
            filter = FILTERS[field_info.onyx_type][field_info.lookup]

            if field_info.onyx_type == OnyxType.CHOICE:
                choices = [(x, x) for x in field_info.choices]
                self.filters[field] = filter(
                    field_name=field_info.field_path,
                    choices=choices,
                    lookup_expr=field_info.lookup,
                )
            else:
                self.filters[field] = filter(
                    field_name=field_info.field_path,
                    lookup_expr=field_info.lookup,
                )
