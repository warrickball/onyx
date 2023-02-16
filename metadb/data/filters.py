from django.db import models
from django.db.models import ForeignKey
from django.contrib.contenttypes.models import ContentType
from django_filters import rest_framework as filters
from utils.fields import YearMonthField, LowerCharField
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
]

TEXT_FIELDS = [
    LowerCharField,
    models.CharField,
    models.TextField,
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

NUMBER_FIELDS = [
    models.IntegerField,
    models.FloatField,
]

DATE_FIELDS = [
    models.DateField,
    models.DateTimeField,
]

# Additional lookups for yearmonth fields
YEARMONTH_LOOKUPS = [
    "year",
    "year__in",
    "year__range",
]

# Additional lookups for date and datetime fields
DATE_LOOKUPS = YEARMONTH_LOOKUPS + [
    "iso_year",
    "iso_year__in",
    "iso_year__range",
    "week",
    "week__in",
    "week__range",
]

# Accepted strings for True and False when validating BooleanField
BOOLEAN_CHOICES = (
    ("true", "true"),
    ("false", "false"),
)


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


def get_filter(model, user_field, fields):
    # Get the field and the lookup
    field, underscore, lookup = user_field.partition("__")

    # Check that the field is a known field
    # Also check that there is no trailing underscore
    if (field not in fields) or (underscore and not lookup):
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
            content_type = ContentType.objects.get_for_model(model)
            qs = Choice.objects.filter(
                content_type=content_type,
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
        elif lookup in ["in", "range"] or lookup in BASE_LOOKUPS:
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
            return f"{field}__isnull", filters.TypedChoiceFilter(
                field_name=field,
                choices=BOOLEAN_CHOICES,
                coerce=strtobool,
                lookup_expr="isnull",
            )
    # Text
    elif field_type in TEXT_FIELDS:
        if not lookup:
            return f"{field}", filters.CharFilter(
                field_name=field_path,
            )
        elif (
            lookup in ["in", "range"]
            or lookup in BASE_LOOKUPS
            or lookup in TEXT_LOOKUPS
        ):
            filter = FILTERS.get(("text", lookup), filters.CharFilter)
            return f"{field}__{lookup}", filter(
                field_name=field_path,
                lookup_expr=lookup,
            )
        elif lookup == "isnull":
            return f"{field}__isnull", filters.TypedChoiceFilter(
                field_name=field_path,
                choices=BOOLEAN_CHOICES,
                coerce=strtobool,
                lookup_expr="isnull",
            )
    # Number
    elif field_type in NUMBER_FIELDS:
        if not lookup:
            return f"{field}", filters.NumberFilter(
                field_name=field_path,
            )
        elif lookup in ["in", "range"] or lookup in BASE_LOOKUPS:
            filter = FILTERS.get(("number", lookup), filters.NumberFilter)
            return f"{field}__{lookup}", filter(
                field_name=field_path,
                lookup_expr=lookup,
            )
        elif lookup == "isnull":
            return f"{field}__isnull", filters.TypedChoiceFilter(
                field_name=field_path,
                choices=BOOLEAN_CHOICES,
                coerce=strtobool,
                lookup_expr="isnull",
            )
    # Yearmonth
    elif field_type == YearMonthField:
        if not lookup:
            return f"{field}", filters.DateFilter(
                field_name=field_path,
                input_formats=["%Y-%m"],
            )
        elif lookup in ["in", "range"] or lookup in BASE_LOOKUPS:
            filter = FILTERS.get(("date", lookup), filters.DateFilter)
            return f"{field}__{lookup}", filter(
                field_name=field_path,
                input_formats=["%Y-%m"],
                lookup_expr=lookup,
            )
        elif lookup in YEARMONTH_LOOKUPS:
            if lookup == "year__in":
                filter = NumberInFilter
            elif lookup == "year__range":
                filter = NumberRangeFilter
            else:
                filter = filters.NumberFilter
            return f"{field}__{lookup}", filter(
                field_name=field_path,
                lookup_expr=lookup,
            )
        elif lookup == "isnull":
            return f"{field}__isnull", filters.TypedChoiceFilter(
                field_name=field_path,
                choices=BOOLEAN_CHOICES,
                coerce=strtobool,
                lookup_expr="isnull",
            )
    # Date
    elif field_type in DATE_FIELDS:
        if field_type == models.DateField:
            filter = filters.DateFilter
            filter_type = "date"
        else:
            filter = filters.DateTimeFilter
            filter_type = "datetime"
        if not lookup:
            return f"{field}", filter(
                field_name=field_path,
                input_formats=["%Y-%m-%d"],
            )
        elif lookup in ["in", "range"] or lookup in BASE_LOOKUPS:
            filter = FILTERS.get((filter_type, lookup), filter)  # type: ignore
            return f"{field}__{lookup}", filter(
                field_name=field_path,
                input_formats=["%Y-%m-%d"],
                lookup_expr=lookup,
            )
        elif lookup in DATE_LOOKUPS:
            if lookup in ["year__in", "iso_year__in", "week__in"]:
                filter = NumberInFilter
            elif lookup in ["year__range", "iso_year__range", "week__range"]:
                filter = NumberRangeFilter
            else:
                filter = filters.NumberFilter
            return f"{field}__{lookup}", filter(
                field_name=field_path,
                lookup_expr=lookup,
            )
        elif lookup == "isnull":
            return f"{field}__isnull", filters.TypedChoiceFilter(
                field_name=field_path,
                choices=BOOLEAN_CHOICES,
                coerce=strtobool,
                lookup_expr="isnull",
            )
    # True/false
    elif field_type == models.BooleanField:
        if not lookup:
            return f"{field}", filters.TypedChoiceFilter(
                field_name=field_path,
                choices=BOOLEAN_CHOICES,
                coerce=strtobool,
            )
        elif lookup in ["in", "range"] or lookup in BASE_LOOKUPS:
            filter = FILTERS.get(("bool", lookup), filters.TypedChoiceFilter)
            return f"{field}__{lookup}", filter(
                field_name=field_path,
                choices=BOOLEAN_CHOICES,
                coerce=strtobool,
                lookup_expr=lookup,
            )
        elif lookup == "isnull":
            return f"{field}__isnull", filters.TypedChoiceFilter(
                field_name=field_path,
                choices=BOOLEAN_CHOICES,
                coerce=strtobool,
                lookup_expr="isnull",
            )
    return None, None


class METADBFilter(filters.FilterSet):
    def __init__(self, model, fields, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for user_field in self.data:
            name, filter = get_filter(
                model,
                user_field,
                fields,
            )
            if name:
                self.filters[name] = filter


# class METADBFilter(filters.FilterSet):
#     def __init__(self, model, fields, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         for field in fields:
#             if not any(d.startswith(field) for d in self.data):
#                 continue

#             model_field = model._meta.get_field(field)

#             if isinstance(model_field, ForeignKey):
#                 related_field = model_field.foreign_related_fields[0].name  # type: ignore
#                 field_type = type(
#                     model_field.related_model._meta.get_field(related_field)
#                 )
#                 field_path = field + "__" + related_field

#             else:
#                 related_field = field
#                 field_type = type(model_field)
#                 field_path = field

#             if (
#                 field in model.CustomMeta.db_choice_fields
#                 or model_field.related_model == Choice
#             ):
#                 if field in model.CustomMeta.db_choice_fields:
#                     db_model = model._meta.get_field(field).related_model
#                     qs = db_model.objects.all()
#                     to_field_name = related_field
#                 else:
#                     content_type = ContentType.objects.get_for_model(model)
#                     qs = Choice.objects.filter(
#                         content_type=content_type,
#                         field=field,
#                     )
#                     to_field_name = "choice"
#                     field_type = LowerCharField
#                     field_path = field + "__choice"

#                 self.filters[field] = filters.ModelChoiceFilter(
#                     field_name=field,
#                     queryset=qs,
#                     to_field_name=to_field_name,
#                 )
#                 self.filters[f"{field}__in"] = ModelChoiceInFilter(
#                     field_name=field,
#                     queryset=qs,
#                     to_field_name=to_field_name,
#                     lookup_expr="in",
#                 )
#                 self.filters[f"{field}__range"] = ModelChoiceRangeFilter(
#                     field_name=field,
#                     queryset=qs,
#                     to_field_name=to_field_name,
#                     lookup_expr="range",
#                 )
#                 self.filters[f"{field}__isnull"] = filters.TypedChoiceFilter(
#                     field_name=field,
#                     choices=BOOLEAN_CHOICES,
#                     coerce=strtobool,
#                     lookup_expr="isnull",
#                 )

#                 for lookup in BASE_LOOKUPS:
#                     self.filters[f"{field}__{lookup}"] = filters.ModelChoiceFilter(
#                         field_name=field,
#                         queryset=qs,
#                         to_field_name=to_field_name,
#                         lookup_expr=lookup,
#                     )

#                 if field_type in [LowerCharField, models.CharField, models.TextField]:
#                     for lookup in TEXT_LOOKUPS:
#                         self.filters[f"{field}__{lookup}"] = filters.CharFilter(
#                             field_name=field_path, lookup_expr=lookup
#                         )

#             elif field_type in [LowerCharField, models.CharField, models.TextField]:
#                 self.filters[field] = filters.CharFilter(field_name=field_path)
#                 self.filters[f"{field}__in"] = CharInFilter(
#                     field_name=field_path, lookup_expr="in"
#                 )
#                 self.filters[f"{field}__range"] = CharRangeFilter(
#                     field_name=field_path, lookup_expr="range"
#                 )
#                 self.filters[f"{field}__isnull"] = filters.TypedChoiceFilter(
#                     field_name=field_path,
#                     choices=BOOLEAN_CHOICES,
#                     coerce=strtobool,
#                     lookup_expr="isnull",
#                 )

#                 for lookup in BASE_LOOKUPS:
#                     self.filters[f"{field}__{lookup}"] = filters.CharFilter(
#                         field_name=field_path, lookup_expr=lookup
#                     )

#                 for lookup in TEXT_LOOKUPS:
#                     self.filters[f"{field}__{lookup}"] = filters.CharFilter(
#                         field_name=field_path, lookup_expr=lookup
#                     )

#             elif field_type in [models.IntegerField, models.FloatField]:
#                 self.filters[field] = filters.NumberFilter(field_name=field_path)

#                 self.filters[f"{field}__in"] = NumberInFilter(
#                     field_name=field_path, lookup_expr="in"
#                 )
#                 self.filters[f"{field}__range"] = NumberRangeFilter(
#                     field_name=field_path, lookup_expr="range"
#                 )
#                 self.filters[f"{field}__isnull"] = filters.TypedChoiceFilter(
#                     field_name=field_path,
#                     choices=BOOLEAN_CHOICES,
#                     coerce=strtobool,
#                     lookup_expr="isnull",
#                 )

#                 for lookup in BASE_LOOKUPS:
#                     self.filters[f"{field}__{lookup}"] = filters.NumberFilter(
#                         field_name=field_path, lookup_expr=lookup
#                     )

#             elif field_type == YearMonthField:
#                 self.filters[field] = filters.DateFilter(
#                     field_name=field_path, input_formats=["%Y-%m"]
#                 )
#                 self.filters[f"{field}__in"] = DateInFilter(
#                     field_name=field_path,
#                     input_formats=["%Y-%m"],
#                     lookup_expr="in",
#                 )
#                 self.filters[f"{field}__range"] = DateRangeFilter(
#                     field_name=field_path, input_formats=["%Y-%m"], lookup_expr="range"
#                 )
#                 self.filters[f"{field}__isnull"] = filters.TypedChoiceFilter(
#                     field_name=field_path,
#                     choices=BOOLEAN_CHOICES,
#                     coerce=strtobool,
#                     lookup_expr="isnull",
#                 )
#                 self.filters[f"{field}__iso_year"] = filters.NumberFilter(
#                     field_name=field_path, lookup_expr="iso_year"
#                 )
#                 self.filters[f"{field}__iso_year__in"] = NumberInFilter(
#                     field_name=field_path,
#                     lookup_expr="iso_year__in",
#                 )
#                 self.filters[f"{field}__iso_year__range"] = NumberRangeFilter(
#                     field_name=field_path,
#                     lookup_expr="iso_year__range",
#                 )

#                 for lookup in BASE_LOOKUPS:
#                     self.filters[f"{field}__{lookup}"] = filters.DateFilter(
#                         field_name=field_path,
#                         input_formats=["%Y-%m"],
#                         lookup_expr=lookup,
#                     )

#             elif field_type == models.DateField:
#                 self.filters[field] = filters.DateFilter(
#                     field_name=field_path, input_formats=["%Y-%m-%d"]
#                 )
#                 self.filters[f"{field}__in"] = DateInFilter(
#                     field_name=field_path, input_formats=["%Y-%m-%d"], lookup_expr="in"
#                 )
#                 self.filters[f"{field}__range"] = DateRangeFilter(
#                     field_name=field_path,
#                     input_formats=["%Y-%m-%d"],
#                     lookup_expr="range",
#                 )
#                 self.filters[f"{field}__isnull"] = filters.TypedChoiceFilter(
#                     field_name=field_path,
#                     choices=BOOLEAN_CHOICES,
#                     coerce=strtobool,
#                     lookup_expr="isnull",
#                 )
#                 self.filters[f"{field}__iso_year"] = filters.NumberFilter(
#                     field_name=field_path, lookup_expr="iso_year"
#                 )
#                 self.filters[f"{field}__iso_year__in"] = NumberInFilter(
#                     field_name=field_path,
#                     lookup_expr="iso_year__in",
#                 )
#                 self.filters[f"{field}__iso_year__range"] = NumberRangeFilter(
#                     field_name=field_path,
#                     lookup_expr="iso_year__range",
#                 )
#                 self.filters[f"{field}__week"] = filters.NumberFilter(
#                     field_name=field_path, lookup_expr="week"
#                 )
#                 self.filters[f"{field}__week__in"] = NumberInFilter(
#                     field_name=field_path,
#                     lookup_expr="week__in",
#                 )
#                 self.filters[f"{field}__week__range"] = NumberRangeFilter(
#                     field_name=field_path,
#                     lookup_expr="week__range",
#                 )

#                 for lookup in BASE_LOOKUPS:
#                     self.filters[f"{field}__{lookup}"] = filters.DateFilter(
#                         field_name=field_path,
#                         input_formats=["%Y-%m-%d"],
#                         lookup_expr=lookup,
#                     )

#             elif field_type == models.DateTimeField:
#                 self.filters[field] = filters.DateTimeFilter(
#                     field_name=field_path, input_formats=["%Y-%m-%d"]
#                 )
#                 self.filters[f"{field}__in"] = DateTimeInFilter(
#                     field_name=field_path, input_formats=["%Y-%m-%d"], lookup_expr="in"
#                 )
#                 self.filters[f"{field}__range"] = DateTimeRangeFilter(
#                     field_name=field_path,
#                     input_formats=["%Y-%m-%d"],
#                     lookup_expr="range",
#                 )
#                 self.filters[f"{field}__isnull"] = filters.TypedChoiceFilter(
#                     field_name=field_path,
#                     choices=BOOLEAN_CHOICES,
#                     coerce=strtobool,
#                     lookup_expr="isnull",
#                 )
#                 self.filters[f"{field}__iso_year"] = filters.NumberFilter(
#                     field_name=field_path, lookup_expr="iso_year"
#                 )
#                 self.filters[f"{field}__iso_year__in"] = NumberInFilter(
#                     field_name=field_path,
#                     lookup_expr="iso_year__in",
#                 )
#                 self.filters[f"{field}__iso_year__range"] = NumberRangeFilter(
#                     field_name=field_path,
#                     lookup_expr="iso_year__range",
#                 )
#                 self.filters[f"{field}__week"] = filters.NumberFilter(
#                     field_name=field_path, lookup_expr="week"
#                 )
#                 self.filters[f"{field}__week__in"] = NumberInFilter(
#                     field_name=field_path,
#                     lookup_expr="week__in",
#                 )
#                 self.filters[f"{field}__week__range"] = NumberRangeFilter(
#                     field_name=field_path,
#                     lookup_expr="week__range",
#                 )

#                 for lookup in BASE_LOOKUPS:
#                     self.filters[f"{field}__{lookup}"] = filters.DateTimeFilter(
#                         field_name=field_path,
#                         input_formats=["%Y-%m-%d"],
#                         lookup_expr=lookup,
#                     )

#             elif field_type == models.BooleanField:
#                 self.filters[field] = filters.TypedChoiceFilter(
#                     field_name=field_path, choices=BOOLEAN_CHOICES, coerce=strtobool
#                 )
#                 self.filters[f"{field}__in"] = TypedChoiceInFilter(
#                     field_name=field_path,
#                     choices=BOOLEAN_CHOICES,
#                     coerce=strtobool,
#                     lookup_expr="in",
#                 )
#                 self.filters[f"{field}__range"] = TypedChoiceRangeFilter(
#                     field_name=field_path,
#                     choices=BOOLEAN_CHOICES,
#                     coerce=strtobool,
#                     lookup_expr="range",
#                 )
#                 self.filters[f"{field}__isnull"] = filters.TypedChoiceFilter(
#                     field_name=field_path,
#                     choices=BOOLEAN_CHOICES,
#                     coerce=strtobool,
#                     lookup_expr="isnull",
#                 )

#                 for lookup in BASE_LOOKUPS:
#                     self.filters[f"{field}__{lookup}"] = filters.TypedChoiceFilter(
#                         field_name=field_path,
#                         choices=BOOLEAN_CHOICES,
#                         coerce=strtobool,
#                         lookup_expr=lookup,
#                     )
