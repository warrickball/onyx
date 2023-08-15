from django import forms
from django.db import models
from django.db.models import ForeignKey, ManyToOneRel
from django_filters import rest_framework as filters
from .models import Choice
from utils.choices import format_choices
from utils.fields import (
    StrippedCharField,
    HashField,
    LowerCharField,
    UpperCharField,
    YearMonthField,
    ModelChoiceField,
    ChoiceField,
)


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


class ChoiceFieldForm(forms.ChoiceField):
    default_error_messages = {
        "invalid_choice": [
            "Select a valid choice. That choice is not one of the available choices."
        ]
    }

    def clean(self, value):
        return super().clean(value.lower())


class ChoiceFilter(filters.Filter):
    field_class = ChoiceFieldForm


class ChoiceInFilter(filters.BaseInFilter, ChoiceFilter):
    pass


# Lookups shared by all fields
BASE_LOOKUPS = [
    "exact",
    "ne",
    "lt",
    "lte",
    "gt",
    "gte",
    "in",
    "range",
]

# Lookups available for hash fields
HASH_LOOKUPS = [
    "exact",
    "ne",
    "in",
]

# Lookups available for choice fields
CHOICE_LOOKUPS = [
    "exact",
    "ne",
    "in",
]

# Additional lookups for text fields
TEXT_LOOKUPS = [
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

# Additional lookups for yearmonth fields
YEARMONTH_LOOKUPS = [
    "year",
    "year__in",
    "year__range",
]

# Additional lookups for other date fields
DATE_LOOKUPS = [
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

ALL_LOOKUPS = set(
    BASE_LOOKUPS
    + HASH_LOOKUPS
    + CHOICE_LOOKUPS
    + TEXT_LOOKUPS
    + YEARMONTH_LOOKUPS
    + DATE_LOOKUPS
    + ["isnull"]
)

# Text field types
TEXT_FIELDS = [
    models.CharField,
    models.TextField,
    StrippedCharField,
    HashField,
    LowerCharField,
    UpperCharField,
]

# Number field types
NUMBER_FIELDS = [
    models.IntegerField,
    models.FloatField,
]

# Date field types
DATE_FIELDS = [
    YearMonthField,
    models.DateField,
    models.DateTimeField,
]

# Relation field types
RELATIONS = [
    ForeignKey,
    ManyToOneRel,
]

# Accepted strings for True and False when validating BooleanField
BOOLEAN_CHOICES = format_choices(["true", "True", "false", "False"])

# Mappings from field type + lookup to filter
FILTERS = {
    ("text", "in"): CharInFilter,
    ("text", "range"): CharRangeFilter,
    ("number", "in"): NumberInFilter,
    ("number", "range"): NumberRangeFilter,
    ("date", "in"): DateInFilter,
    ("date", "range"): DateRangeFilter,
    ("datetime", "in"): DateTimeInFilter,
    ("datetime", "range"): DateTimeRangeFilter,
    ("bool", "in"): TypedChoiceInFilter,
    ("modelchoice", "in"): ModelChoiceInFilter,
    ("choice", "in"): ChoiceInFilter,
}


def strtobool(val):
    val = val.lower()
    if val == "true":
        return True
    elif val == "false":
        return False
    else:
        raise ValueError(f"Invalid truth value: {val}")


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
    # Text
    if field_type in TEXT_FIELDS:
        if not lookup:
            return f"{field_path}", filters.CharFilter(
                field_name=field_path,
            )
        elif field_type == HashField and lookup not in HASH_LOOKUPS:
            # Hash fields have a more restricted set of lookups
            # So if the lookup doesn't match this set, we pass
            pass
        elif lookup in BASE_LOOKUPS or lookup in TEXT_LOOKUPS:
            filter = FILTERS.get(("text", lookup), filters.CharFilter)
            return f"{field_path}__{lookup}", filter(
                field_name=field_path,
                lookup_expr=lookup,
            )

    # Number
    elif field_type in NUMBER_FIELDS:
        if not lookup:
            return f"{field_path}", filters.NumberFilter(
                field_name=field_path,
            )
        elif lookup in BASE_LOOKUPS:
            filter = FILTERS.get(("number", lookup), filters.NumberFilter)
            return f"{field_path}__{lookup}", filter(
                field_name=field_path,
                lookup_expr=lookup,
            )
        elif lookup == "isnull":
            return f"{field_path}__isnull", isnull(field_path)

    # Date
    elif field_type in DATE_FIELDS:
        if field_type == YearMonthField:
            filter = filters.DateFilter
            filter_type = "date"
            lookups = YEARMONTH_LOOKUPS
            input_formats = ["%Y-%m"]
        elif field_type == models.DateField:
            filter = filters.DateFilter
            filter_type = "date"
            lookups = DATE_LOOKUPS
            input_formats = ["%Y-%m-%d"]
        else:
            filter = filters.DateTimeFilter
            filter_type = "datetime"
            lookups = DATE_LOOKUPS
            input_formats = ["%Y-%m-%d"]
        if not lookup:
            return f"{field_path}", filter(
                field_name=field_path,
                input_formats=input_formats,
            )
        elif lookup in BASE_LOOKUPS:
            filter = FILTERS.get((filter_type, lookup), filter)  # type: ignore
            return f"{field_path}__{lookup}", filter(
                field_name=field_path,
                input_formats=input_formats,
                lookup_expr=lookup,
            )
        elif lookup in lookups:
            if lookup.endswith("__in"):
                filter = NumberInFilter
            elif lookup.endswith("__range"):
                filter = NumberRangeFilter
            else:
                filter = filters.NumberFilter
            return f"{field_path}__{lookup}", filter(
                field_name=field_path,
                lookup_expr=lookup,
            )
        elif lookup == "isnull":
            return f"{field_path}__isnull", isnull(field_path)

    # True/false
    elif field_type == models.BooleanField:
        if not lookup:
            return f"{field_path}", filters.TypedChoiceFilter(
                field_name=field_path,
                choices=BOOLEAN_CHOICES,
                coerce=strtobool,
            )
        elif lookup in BASE_LOOKUPS:
            filter = FILTERS.get(("bool", lookup), filters.TypedChoiceFilter)
            return f"{field_path}__{lookup}", filter(
                field_name=field_path,
                choices=BOOLEAN_CHOICES,
                coerce=strtobool,
                lookup_expr=lookup,
            )
        elif lookup == "isnull":
            return f"{field_path}__isnull", isnull(field_path)

    # ModelChoice (TODO: remove as I think its redundant? Or not?)
    elif field_type == ModelChoiceField:
        qs = Choice.objects.filter(
            project_id=project,
            field=field_name,
        )
        if not lookup:
            return f"{field_path}", filters.ModelChoiceFilter(
                field_name=field_path,
                queryset=qs,
                to_field_name="choice",
            )
        elif lookup in CHOICE_LOOKUPS:
            filter = FILTERS.get(("modelchoice", lookup), filters.ModelChoiceFilter)
            return f"{field_path}__{lookup}", filter(
                field_name=field_path,
                queryset=qs,
                to_field_name="choice",
                lookup_expr=lookup,
            )
        elif lookup == "isnull":
            return f"{field_path}__isnull", isnull(field_path)

    # Choice
    elif field_type == ChoiceField:
        choices = format_choices(
            Choice.objects.filter(
                project_id=project,
                field=field_name,
            ).values_list(
                "choice",
                flat=True,
            )
        )
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

    # Relations
    elif field_type in RELATIONS:
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
