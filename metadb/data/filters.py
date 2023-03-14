from django.db import models
from django.db.models import ForeignKey
from django_filters import rest_framework as filters
from utils.fields import YearMonthField, LowerCharField, UpperCharField
from utils.filters import (
    ModelChoiceInFilter,
    ModelChoiceRangeFilter,
    CharInFilter,
    CharRangeFilter,
    NumberInFilter,
    NumberRangeFilter,
    DateInFilter,
    DateRangeFilter,
    DateTimeInFilter,
    DateTimeRangeFilter,
    TypedChoiceInFilter,
    TypedChoiceRangeFilter,
)
from distutils.util import strtobool
from internal.models import Choice


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

# Accepted strings for True and False when validating BooleanField
BOOLEAN_CHOICES = (
    ("true", "true"),
    ("false", "false"),
)

# Mappings from field type + lookup to filter
FILTERS = {
    ("choice", "in"): ModelChoiceInFilter,
    ("choice", "range"): ModelChoiceRangeFilter,
    ("text", "in"): CharInFilter,
    ("text", "range"): CharRangeFilter,
    ("number", "in"): NumberInFilter,
    ("number", "range"): NumberRangeFilter,
    ("date", "in"): DateInFilter,
    ("date", "range"): DateRangeFilter,
    ("datetime", "in"): DateTimeInFilter,
    ("datetime", "range"): DateTimeRangeFilter,
    ("bool", "in"): TypedChoiceInFilter,
    ("bool", "range"): TypedChoiceRangeFilter,
}


def isnull(field):
    return filters.TypedChoiceFilter(
        field_name=field,
        choices=BOOLEAN_CHOICES,
        coerce=strtobool,
        lookup_expr="isnull",
    )


def get_filter(model, user_field, field_contexts):
    # Get the field and the lookup
    field, underscore, lookup = user_field.partition("__")

    # Check that there is no trailing underscore
    if underscore and not lookup:
        return None, None

    # Retrieve the provided field from the model
    model_field = model._meta.get_field(field)

    # Determine whether the field is a foreign key to another field
    # If it is, the field_path will map to a related field on the foreign model
    if isinstance(model_field, ForeignKey):
        related_field = model_field.foreign_related_fields[0].name  # type: ignore
        field_type = type(model_field.related_model._meta.get_field(related_field))
        field_path = field + "__" + related_field
    else:
        related_field = field
        field_type = type(model_field)
        field_path = field

    # Return the correct filter, based on the field's type and the lookup string
    # Choice
    if (
        field in model.CustomMeta.db_choice_fields
        or model_field.related_model == Choice
    ):
        if field in model.CustomMeta.db_choice_fields:
            db_model = model._meta.get_field(field).related_model
            qs = db_model.objects.all()
            to_field_name = related_field
        else:
            qs = Choice.objects.filter(
                content_type=field_contexts[field].content_type,
                field=field,
            )
            to_field_name = "choice"
            field_type = LowerCharField
            field_path = field + "__choice"

        if not lookup:
            return f"{field}", filters.ModelChoiceFilter(
                field_name=field,
                queryset=qs,
                to_field_name=to_field_name,
            )
        elif lookup in BASE_LOOKUPS:
            filter = FILTERS.get(("choice", lookup), filters.ModelChoiceFilter)
            return f"{field}__{lookup}", filter(
                field_name=field,
                queryset=qs,
                to_field_name=to_field_name,
                lookup_expr=lookup,
            )
        elif field_type in TEXT_FIELDS and lookup in TEXT_LOOKUPS:
            return f"{field}__{lookup}", filters.CharFilter(
                field_name=field_path,
                lookup_expr=lookup,
            )
        elif lookup == "isnull":
            return f"{field}__isnull", isnull(field)
    # Text
    elif field_type in TEXT_FIELDS:
        if not lookup:
            return f"{field}", filters.CharFilter(
                field_name=field_path,
            )
        elif lookup in BASE_LOOKUPS or lookup in TEXT_LOOKUPS:
            filter = FILTERS.get(("text", lookup), filters.CharFilter)
            return f"{field}__{lookup}", filter(
                field_name=field_path,
                lookup_expr=lookup,
            )
        elif lookup == "isnull":
            return f"{field}__isnull", isnull(field_path)
    # Number
    elif field_type in NUMBER_FIELDS:
        if not lookup:
            return f"{field}", filters.NumberFilter(
                field_name=field_path,
            )
        elif lookup in BASE_LOOKUPS:
            filter = FILTERS.get(("number", lookup), filters.NumberFilter)
            return f"{field}__{lookup}", filter(
                field_name=field_path,
                lookup_expr=lookup,
            )
        elif lookup == "isnull":
            return f"{field}__isnull", isnull(field_path)
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
            return f"{field}", filter(
                field_name=field_path,
                input_formats=input_formats,
            )
        elif lookup in BASE_LOOKUPS:
            filter = FILTERS.get((filter_type, lookup), filter)  # type: ignore
            return f"{field}__{lookup}", filter(
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
            return f"{field}__{lookup}", filter(
                field_name=field_path,
                lookup_expr=lookup,
            )
        elif lookup == "isnull":
            return f"{field}__isnull", isnull(field_path)
    # True/false
    elif field_type == models.BooleanField:
        if not lookup:
            return f"{field}", filters.TypedChoiceFilter(
                field_name=field_path,
                choices=BOOLEAN_CHOICES,
                coerce=strtobool,
            )
        elif lookup in BASE_LOOKUPS:
            filter = FILTERS.get(("bool", lookup), filters.TypedChoiceFilter)
            return f"{field}__{lookup}", filter(
                field_name=field_path,
                choices=BOOLEAN_CHOICES,
                coerce=strtobool,
                lookup_expr=lookup,
            )
        elif lookup == "isnull":
            return f"{field}__isnull", isnull(field_path)

    return None, None


class METADBFilter(filters.FilterSet):
    def __init__(self, model, field_contexts, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for user_field in self.data:
            name, filter = get_filter(
                model,
                user_field,
                field_contexts,
            )
            if name:
                self.filters[name] = filter
