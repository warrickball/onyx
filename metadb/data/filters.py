from django.db import models
from django.db.models import ForeignKey, ManyToOneRel
from django_filters import rest_framework as filters
from internal.models import Choice
from utils.fields import ChoiceField, YearMonthField, LowerCharField, UpperCharField
from utils.filters import (
    ModelChoiceInFilter,
    CharInFilter,
    CharRangeFilter,
    NumberInFilter,
    NumberRangeFilter,
    DateInFilter,
    DateRangeFilter,
    DateTimeInFilter,
    DateTimeRangeFilter,
    TypedChoiceInFilter,
)


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
    + CHOICE_LOOKUPS
    + TEXT_LOOKUPS
    + YEARMONTH_LOOKUPS
    + DATE_LOOKUPS
    + ["isnull"]
)

# Text field types
TEXT_FIELDS = [
    LowerCharField,
    UpperCharField,
    models.CharField,
    models.TextField,
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
BOOLEAN_CHOICES = (
    ("true", "true"),
    ("True", "True"),
    ("false", "false"),
    ("False", "False"),
)

# Mappings from field type + lookup to filter
FILTERS = {
    ("choice", "in"): ModelChoiceInFilter,
    ("text", "in"): CharInFilter,
    ("text", "range"): CharRangeFilter,
    ("number", "in"): NumberInFilter,
    ("number", "range"): NumberRangeFilter,
    ("date", "in"): DateInFilter,
    ("date", "range"): DateRangeFilter,
    ("datetime", "in"): DateTimeInFilter,
    ("datetime", "range"): DateTimeRangeFilter,
    ("bool", "in"): TypedChoiceInFilter,
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
    field_type,
    field_path,
    field_name,
    lookup,
    content_type=None,
):
    # Text
    if field_type in TEXT_FIELDS:
        if not lookup:
            return f"{field_path}", filters.CharFilter(
                field_name=field_path,
            )
        elif lookup in BASE_LOOKUPS or lookup in TEXT_LOOKUPS:
            filter = FILTERS.get(("text", lookup), filters.CharFilter)
            return f"{field_path}__{lookup}", filter(
                field_name=field_path,
                lookup_expr=lookup,
            )
        elif lookup == "isnull":
            return f"{field_path}__isnull", isnull(field_path)
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
    # Choice
    elif field_type == ChoiceField:
        qs = Choice.objects.filter(
            content_type=content_type,
            field=field_name,
        )
        if not lookup:
            return f"{field_path}", filters.ModelChoiceFilter(
                field_name=field_path,
                queryset=qs,
                to_field_name="choice",
            )
        elif lookup in CHOICE_LOOKUPS:
            filter = FILTERS.get(("choice", lookup), filters.ModelChoiceFilter)
            return f"{field_path}__{lookup}", filter(
                field_name=field_path,
                queryset=qs,
                to_field_name="choice",
                lookup_expr=lookup,
            )
        elif lookup == "isnull":
            return f"{field_path}__isnull", isnull(field_path)
    # Relations
    elif field_type in RELATIONS:
        if lookup == "isnull":
            return f"{field_path}__isnull", isnull(field_path)

    return None, None


class METADBFilter(filters.FilterSet):
    def __init__(self, project, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Constructing the filterset dynamically enables:
        # Checking whether the provided field_path and lookup can be used together
        # Validating the values provided by the user for the fields
        # Returning cleaned values from user inputs, using the filterset's underlying form
        for field in self.data:
            mfield = project.fields[field]

            name, filter = get_filter(
                field_type=mfield.field_type,
                field_path=mfield.field_path,
                field_name=mfield.field_name,
                lookup=mfield.lookup,
                content_type=mfield.content_type,
            )
            if name:
                self.filters[name] = filter
