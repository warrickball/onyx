import hashlib
from datetime import datetime
from django import forms
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django_filters import rest_framework as filters
from utils.fields import HashField, ChoiceField, YearMonthField, TEXT_FIELDS
from utils.functions import get_suggestions, strtobool
from .models import Choice


class HashFieldForm(forms.CharField):
    def clean(self, value):
        value = super().clean(value).strip().lower()

        hasher = hashlib.sha256()
        hasher.update(value.encode("utf-8"))
        value = hasher.hexdigest()

        return value


class HashFieldFilter(filters.Filter):
    field_class = HashFieldForm


class CharInFilter(filters.BaseInFilter, filters.CharFilter):
    pass


class CharRangeFilter(filters.BaseRangeFilter, filters.CharFilter):
    pass


class ChoiceFieldForm(forms.ChoiceField):
    default_error_messages = {
        "invalid_choice": _("Select a valid choice.%(suggestions)s"),
    }

    def clean(self, value):
        self.choice_map = {choice.lower().strip(): choice for choice, _ in self.choices}

        if isinstance(value, str):
            value = value.strip()
            value_key = value.lower()

            if value_key in self.choice_map:
                value = self.choice_map[value_key]

        return super().clean(value)

    def validate(self, value):
        super(forms.ChoiceField, self).validate(value)

        if value and not self.valid_value(value):
            choices = [str(x) for (_, x) in self.choices]
            s = get_suggestions(value, choices, n=1)

            if s:
                suggestions = f" Perhaps you meant: {', '.join(s)}"
            else:
                suggestions = ""

            raise ValidationError(
                self.error_messages["invalid_choice"],
                code="invalid_choice",
                params={"suggestions": suggestions},
            )


class ChoiceFilter(filters.Filter):
    field_class = ChoiceFieldForm


class ChoiceInFilter(filters.BaseInFilter, ChoiceFilter):
    pass


class NumberInFilter(filters.BaseInFilter, filters.NumberFilter):
    pass


class NumberRangeFilter(filters.BaseRangeFilter, filters.NumberFilter):
    pass


class DateFieldForm(forms.DateField):
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


class TypedChoiceInFilter(filters.BaseInFilter, filters.TypedChoiceFilter):
    pass


# Lookups shared by all fields
BASE_LOOKUPS = [
    "exact",
    "ne",
    "in",
]

# Lookups available for hash fields
HASH_LOOKUPS = BASE_LOOKUPS

# Lookups available for text fields
TEXT_LOOKUPS = BASE_LOOKUPS + [
    "contains",
    "startswith",
    "endswith",
    "iexact",
    "icontains",
    "istartswith",
    "iendswith",
    "regex",
    "iregex",
]

# Lookups available for choice fields
CHOICE_LOOKUPS = BASE_LOOKUPS

# Lookups available for numeric fields
NUMERIC_LOOKUPS = BASE_LOOKUPS + [
    "lt",
    "lte",
    "gt",
    "gte",
    "range",
]

# Lookups available for date (YYYY-MM) fields
YEARMONTH_LOOKUPS = BASE_LOOKUPS + [
    "lt",
    "lte",
    "gt",
    "gte",
    "range",
    "year",
    "year__in",
    "year__range",
]

# Lookups available for date (YYYY-MM-DD) fields
DATE_LOOKUPS = BASE_LOOKUPS + [
    "lt",
    "lte",
    "gt",
    "gte",
    "range",
    "year",
    "year__in",
    "year__range",
    "iso_year",
    "iso_year__in",
    "iso_year__range",
    "week",
    "week__in",
    "week__range",
]

# Lookups available for boolean fields
BOOLEAN_LOOKUPS = BASE_LOOKUPS

ALL_LOOKUPS = set(
    BASE_LOOKUPS
    + HASH_LOOKUPS
    + TEXT_LOOKUPS
    + CHOICE_LOOKUPS
    + NUMERIC_LOOKUPS
    + YEARMONTH_LOOKUPS
    + DATE_LOOKUPS
    + BOOLEAN_LOOKUPS
    + ["isnull"]
)

# Accepted strings for True and False when validating BooleanField
BOOLEAN_CHOICES = [(x, x) for x in ["true", "True", "TRUE", "false", "False", "FALSE"]]

# Mappings from field type + lookup to filter
FILTERS = {
    ("text", "in"): CharInFilter,
    ("text", "range"): CharRangeFilter,
    ("choice", "in"): ChoiceInFilter,
    ("numeric", "in"): NumberInFilter,
    ("numeric", "range"): NumberRangeFilter,
    ("date", "in"): DateInFilter,
    ("date", "range"): DateRangeFilter,
    ("date", "year"): filters.NumberFilter,
    ("date", "year__in"): NumberInFilter,
    ("date", "year__range"): NumberRangeFilter,
    ("date", "iso_year"): filters.NumberFilter,
    ("date", "iso_year__in"): NumberInFilter,
    ("date", "iso_year__range"): NumberRangeFilter,
    ("date", "week"): filters.NumberFilter,
    ("date", "week__in"): NumberInFilter,
    ("date", "week__range"): NumberRangeFilter,
    ("datetime", "in"): DateTimeInFilter,
    ("datetime", "range"): DateTimeRangeFilter,
    ("datetime", "year"): filters.NumberFilter,
    ("datetime", "year__in"): NumberInFilter,
    ("datetime", "year__range"): NumberRangeFilter,
    ("datetime", "iso_year"): filters.NumberFilter,
    ("datetime", "iso_year__in"): NumberInFilter,
    ("datetime", "iso_year__range"): NumberRangeFilter,
    ("datetime", "week"): filters.NumberFilter,
    ("datetime", "week__in"): NumberInFilter,
    ("datetime", "week__range"): NumberRangeFilter,
    ("boolean", "in"): TypedChoiceInFilter,
}


def isnull(field):
    return filters.TypedChoiceFilter(
        field_name=field,
        choices=BOOLEAN_CHOICES,
        coerce=strtobool,
        lookup_expr="isnull",
    )


def get_filter(
    project,
    field_type,
    field_path,
    field_name,
    lookup,
):
    # Hash
    if field_type == HashField:
        if not lookup:
            return f"{field_path}", HashFieldFilter(
                field_name=field_path,
            )

        elif lookup in HASH_LOOKUPS:
            return f"{field_path}__{lookup}", HashFieldFilter(
                field_name=field_path,
                lookup_expr=lookup,
            )

    # Text
    elif field_type in TEXT_FIELDS:
        if not lookup:
            return f"{field_path}", filters.CharFilter(
                field_name=field_path,
            )
        elif lookup in TEXT_LOOKUPS:
            filter = FILTERS.get(("text", lookup), filters.CharFilter)
            return f"{field_path}__{lookup}", filter(
                field_name=field_path,
                lookup_expr=lookup,
            )

    # Choice
    elif field_type == ChoiceField:
        choices = [
            (x, x)
            for x in Choice.objects.filter(
                project_id=project,
                field=field_name,
            ).values_list(
                "choice",
                flat=True,
            )
        ]
        if not lookup:
            return f"{field_path}", ChoiceFilter(
                field_name=field_path,
                choices=choices,
            )
        elif lookup in CHOICE_LOOKUPS:
            filter = FILTERS.get(("choice", lookup), ChoiceFilter)
            return f"{field_path}__{lookup}", filter(
                field_name=field_path,
                choices=choices,
                lookup_expr=lookup,
            )

    # Numeric
    elif field_type in [models.IntegerField, models.FloatField]:
        if not lookup:
            return f"{field_path}", filters.NumberFilter(
                field_name=field_path,
            )
        elif lookup in NUMERIC_LOOKUPS:
            filter = FILTERS.get(("numeric", lookup), filters.NumberFilter)
            return f"{field_path}__{lookup}", filter(
                field_name=field_path,
                lookup_expr=lookup,
            )
        elif lookup == "isnull":
            return f"{field_path}__isnull", isnull(field_path)

    # Date (YYYY-MM)
    elif field_type == YearMonthField:
        if not lookup:
            return f"{field_path}", filters.DateFilter(
                field_name=field_path,
                input_formats=["%Y-%m"],
            )
        elif lookup in YEARMONTH_LOOKUPS:
            filter = FILTERS.get(("date", lookup), filters.DateFilter)
            if filter in [filters.NumberFilter, NumberInFilter, NumberRangeFilter]:
                return f"{field_path}__{lookup}", filter(
                    field_name=field_path,
                    lookup_expr=lookup,
                )
            else:
                return f"{field_path}__{lookup}", filter(
                    field_name=field_path,
                    input_formats=["%Y-%m"],
                    lookup_expr=lookup,
                )
        elif lookup == "isnull":
            return f"{field_path}__isnull", isnull(field_path)

    # Date (YYYY-MM-DD)
    elif field_type in [models.DateField, models.DateTimeField]:
        if field_type == models.DateField:
            filter = DateFilter
            filter_type = "date"
        else:
            filter = DateTimeFilter
            filter_type = "datetime"

        if not lookup:
            return f"{field_path}", filter(
                field_name=field_path,
                input_formats=["%Y-%m-%d"],
            )
        elif lookup in DATE_LOOKUPS:
            filter = FILTERS.get((filter_type, lookup), filter)  # type: ignore
            if filter in [filters.NumberFilter, NumberInFilter, NumberRangeFilter]:
                return f"{field_path}__{lookup}", filter(
                    field_name=field_path,
                    lookup_expr=lookup,
                )
            else:
                return f"{field_path}__{lookup}", filter(
                    field_name=field_path,
                    input_formats=["%Y-%m-%d"],
                    lookup_expr=lookup,
                )
        elif lookup == "isnull":
            return f"{field_path}__isnull", isnull(field_path)

    # Boolean
    elif field_type == models.BooleanField:
        if not lookup:
            return f"{field_path}", filters.TypedChoiceFilter(
                field_name=field_path,
                choices=BOOLEAN_CHOICES,
                coerce=strtobool,
            )
        elif lookup in BOOLEAN_LOOKUPS:
            filter = FILTERS.get(("boolean", lookup), filters.TypedChoiceFilter)
            return f"{field_path}__{lookup}", filter(
                field_name=field_path,
                choices=BOOLEAN_CHOICES,
                coerce=strtobool,
                lookup_expr=lookup,
            )
        elif lookup == "isnull":
            return f"{field_path}__isnull", isnull(field_path)

    # Relations
    elif field_type in [models.ForeignKey, models.ManyToOneRel]:
        if lookup == "isnull":
            return f"{field_path}__isnull", isnull(field_path)

    return None, None


class OnyxFilter(filters.FilterSet):
    def __init__(self, fields, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Constructing the filterset dynamically enables:
        # Checking whether the provided field_path and lookup can be used together
        # Validating the values provided by the user for the fields
        # Returning cleaned values from user inputs, using the filterset's underlying form
        for field in self.data:
            mfield = fields[field]

            name, filter = get_filter(
                project=mfield.project,
                field_type=mfield.field_type,
                field_path=mfield.field_path,
                field_name=mfield.field_name,
                lookup=mfield.lookup,
            )
            if name:
                self.filters[name] = filter
