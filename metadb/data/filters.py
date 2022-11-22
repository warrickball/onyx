from django_filters import rest_framework as filters
from django.db import models
from utils.fields import YearMonthField, LowerCharField
from utils.filters import (
    ChoiceInFilter,
    ChoiceRangeFilter,
    DBValuesFilter,
    DBValuesInFilter,
    DBValuesRangeFilter,
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


# Lookups shared by all fields
BASE_LOOKUPS = ["exact", "ne", "lt", "lte", "gt", "gte"]

# Additional lookups for CharField and TextField
CHAR_LOOKUPS = [
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

# Accepted strings for True and False when validating BooleanField
BOOLEAN_CHOICES = (
    ("True", "True"),
    ("true", "true"),
    ("False", "False"),
    ("false", "false"),
)


class METADBFilter(filters.FilterSet):
    def __init__(self, pathogen_model, *args, **kwargs):
        super().__init__(*args, **kwargs)

        pathogen_fields = pathogen_model.FILTER_FIELDS

        for field, value in self.data.items():
            if pathogen_fields.get(field):
                if isinstance(value, str):
                    if pathogen_fields[field].get("choices") or pathogen_fields[
                        field
                    ].get("db_choices"):
                        self.data[field] = value.lower()
            else:
                for f, f_d in pathogen_fields.items():
                    if "alias" in f_d and f_d["alias"] == field:
                        if isinstance(value, str):
                            if f_d.get("choices") or f_d.get("db_choices"):
                                self.data[field] = value.lower()
                        break

        self.base_filters = []

        for field, field_data in pathogen_fields.items():
            # Name for the field, used by the user when filtering
            # An alias allows for renaming of fields, e.g. site__code is renamed to site
            filter_name = field_data["alias"] if "alias" in field_data else field

            # If none of the params provided in the request even begin with the filter name
            # then we know its not needed and can be skipped
            if not any(x.startswith(filter_name) for x in self.data):
                continue

            self.base_filters.append(filter_name)

            # Column type for the field
            field_type = field_data["type"]

            # Boolean determining whether the field is restricted to a set of choices
            is_choice_field = (
                field_data["choices"] if "choices" in field_data else False
            )

            # Boolean determining whether the field is restricted to the pre existing database values
            is_db_choice_field = (
                field_data["db_choices"] if "db_choices" in field_data else False
            )

            if is_choice_field:
                choices = pathogen_model._meta.get_field(field).choices

                self.filters[filter_name] = filters.ChoiceFilter(
                    field_name=field, choices=choices
                )
                self.filters[filter_name + "__in"] = ChoiceInFilter(
                    field_name=field, choices=choices, lookup_expr="in"
                )
                self.filters[filter_name + "__range"] = ChoiceRangeFilter(
                    field_name=field, choices=choices, lookup_expr="range"
                )
                self.filters[filter_name + "__isnull"] = filters.TypedChoiceFilter(
                    field_name=field,
                    choices=BOOLEAN_CHOICES,
                    coerce=strtobool,
                    lookup_expr="isnull",
                )

                for lookup in BASE_LOOKUPS:
                    self.filters[filter_name + "__" + lookup] = filters.ChoiceFilter(
                        field_name=field, choices=choices, lookup_expr=lookup
                    )

                if field_type in [LowerCharField, models.CharField, models.TextField]:
                    for lookup in CHAR_LOOKUPS:
                        self.filters[filter_name + "__" + lookup] = filters.CharFilter(
                            field_name=field, lookup_expr=lookup
                        )

            elif is_db_choice_field:
                self.filters[filter_name] = DBValuesFilter(
                    field_name=field,
                    model=pathogen_model,
                )
                self.filters[filter_name + "__in"] = DBValuesInFilter(
                    field_name=field,
                    lookup_expr="in",
                    model=pathogen_model,
                )
                self.filters[filter_name + "__range"] = DBValuesRangeFilter(
                    field_name=field, lookup_expr="range", model=pathogen_model
                )
                self.filters[filter_name + "__isnull"] = filters.TypedChoiceFilter(
                    field_name=field,
                    choices=BOOLEAN_CHOICES,
                    coerce=strtobool,
                    lookup_expr="isnull",
                )

                for lookup in BASE_LOOKUPS:
                    self.filters[filter_name + "__" + lookup] = DBValuesFilter(
                        field_name=field, lookup_expr=lookup, model=pathogen_model
                    )

                if field_type in [LowerCharField, models.CharField, models.TextField]:
                    for lookup in CHAR_LOOKUPS:
                        self.filters[filter_name + "__" + lookup] = filters.CharFilter(
                            field_name=field, lookup_expr=lookup
                        )

            elif field_type in [LowerCharField, models.CharField, models.TextField]:
                self.filters[filter_name] = filters.CharFilter(field_name=field)
                self.filters[filter_name + "__in"] = CharInFilter(
                    field_name=field, lookup_expr="in"
                )
                self.filters[filter_name + "__range"] = CharRangeFilter(
                    field_name=field, lookup_expr="range"
                )
                self.filters[filter_name + "__isnull"] = filters.TypedChoiceFilter(
                    field_name=field,
                    choices=BOOLEAN_CHOICES,
                    coerce=strtobool,
                    lookup_expr="isnull",
                )

                for lookup in BASE_LOOKUPS:
                    self.filters[filter_name + "__" + lookup] = filters.CharFilter(
                        field_name=field, lookup_expr=lookup
                    )

                for lookup in CHAR_LOOKUPS:
                    self.filters[filter_name + "__" + lookup] = filters.CharFilter(
                        field_name=field, lookup_expr=lookup
                    )

            elif field_type in [models.IntegerField, models.FloatField]:
                self.filters[filter_name] = filters.NumberFilter(field_name=field)

                self.filters[filter_name + "__in"] = NumberInFilter(
                    field_name=field, lookup_expr="in"
                )
                self.filters[filter_name + "__range"] = NumberRangeFilter(
                    field_name=field, lookup_expr="range"
                )
                self.filters[filter_name + "__isnull"] = filters.TypedChoiceFilter(
                    field_name=field,
                    choices=BOOLEAN_CHOICES,
                    coerce=strtobool,
                    lookup_expr="isnull",
                )

                for lookup in BASE_LOOKUPS:
                    self.filters[filter_name + "__" + lookup] = filters.NumberFilter(
                        field_name=field, lookup_expr=lookup
                    )

            elif field_type == YearMonthField:
                self.filters[filter_name] = filters.DateFilter(
                    field_name=field, input_formats=["%Y-%m"]
                )
                self.filters[filter_name + "__in"] = DateInFilter(
                    field_name=field,
                    input_formats=["%Y-%m"],
                    lookup_expr="in",
                )
                self.filters[filter_name + "__range"] = DateRangeFilter(
                    field_name=field, input_formats=["%Y-%m"], lookup_expr="range"
                )
                self.filters[filter_name + "__isnull"] = filters.TypedChoiceFilter(
                    field_name=field,
                    choices=BOOLEAN_CHOICES,
                    coerce=strtobool,
                    lookup_expr="isnull",
                )
                self.filters[filter_name + "__iso_year"] = filters.NumberFilter(
                    field_name=field, lookup_expr="iso_year"
                )
                self.filters[filter_name + "__iso_year__in"] = NumberInFilter(
                    field_name=field,
                    lookup_expr="iso_year__in",
                )
                self.filters[filter_name + "__iso_year__range"] = NumberRangeFilter(
                    field_name=field,
                    lookup_expr="iso_year__range",
                )

                for lookup in BASE_LOOKUPS:
                    self.filters[filter_name + "__" + lookup] = filters.DateFilter(
                        field_name=field, input_formats=["%Y-%m"], lookup_expr=lookup
                    )

            elif field_type == models.DateField:
                self.filters[filter_name] = filters.DateFilter(
                    field_name=field, input_formats=["%Y-%m-%d"]
                )
                self.filters[filter_name + "__in"] = DateInFilter(
                    field_name=field, input_formats=["%Y-%m-%d"], lookup_expr="in"
                )
                self.filters[filter_name + "__range"] = DateRangeFilter(
                    field_name=field, input_formats=["%Y-%m-%d"], lookup_expr="range"
                )
                self.filters[filter_name + "__isnull"] = filters.TypedChoiceFilter(
                    field_name=field,
                    choices=BOOLEAN_CHOICES,
                    coerce=strtobool,
                    lookup_expr="isnull",
                )
                self.filters[filter_name + "__iso_year"] = filters.NumberFilter(
                    field_name=field, lookup_expr="iso_year"
                )
                self.filters[filter_name + "__iso_year__in"] = NumberInFilter(
                    field_name=field,
                    lookup_expr="iso_year__in",
                )
                self.filters[filter_name + "__iso_year__range"] = NumberRangeFilter(
                    field_name=field,
                    lookup_expr="iso_year__range",
                )
                self.filters[filter_name + "__week"] = filters.NumberFilter(
                    field_name=field, lookup_expr="week"
                )
                self.filters[filter_name + "__week__in"] = NumberInFilter(
                    field_name=field,
                    lookup_expr="week__in",
                )
                self.filters[filter_name + "__week__range"] = NumberRangeFilter(
                    field_name=field,
                    lookup_expr="week__range",
                )

                for lookup in BASE_LOOKUPS:
                    self.filters[filter_name + "__" + lookup] = filters.DateFilter(
                        field_name=field, input_formats=["%Y-%m-%d"], lookup_expr=lookup
                    )

            elif field_type == models.DateTimeField:
                self.filters[filter_name] = filters.DateTimeFilter(
                    field_name=field, input_formats=["%Y-%m-%d"]
                )
                self.filters[filter_name + "__in"] = DateTimeInFilter(
                    field_name=field, input_formats=["%Y-%m-%d"], lookup_expr="in"
                )
                self.filters[filter_name + "__range"] = DateTimeRangeFilter(
                    field_name=field, input_formats=["%Y-%m-%d"], lookup_expr="range"
                )
                self.filters[filter_name + "__isnull"] = filters.TypedChoiceFilter(
                    field_name=field,
                    choices=BOOLEAN_CHOICES,
                    coerce=strtobool,
                    lookup_expr="isnull",
                )
                self.filters[filter_name + "__iso_year"] = filters.NumberFilter(
                    field_name=field, lookup_expr="iso_year"
                )
                self.filters[filter_name + "__iso_year__in"] = NumberInFilter(
                    field_name=field,
                    lookup_expr="iso_year__in",
                )
                self.filters[filter_name + "__iso_year__range"] = NumberRangeFilter(
                    field_name=field,
                    lookup_expr="iso_year__range",
                )
                self.filters[filter_name + "__week"] = filters.NumberFilter(
                    field_name=field, lookup_expr="week"
                )
                self.filters[filter_name + "__week__in"] = NumberInFilter(
                    field_name=field,
                    lookup_expr="week__in",
                )
                self.filters[filter_name + "__week__range"] = NumberRangeFilter(
                    field_name=field,
                    lookup_expr="week__range",
                )

                for lookup in BASE_LOOKUPS:
                    self.filters[filter_name + "__" + lookup] = filters.DateTimeFilter(
                        field_name=field, input_formats=["%Y-%m-%d"], lookup_expr=lookup
                    )

            elif field_type == models.BooleanField:
                self.filters[filter_name] = filters.TypedChoiceFilter(
                    field_name=field, choices=BOOLEAN_CHOICES, coerce=strtobool
                )
                self.filters[filter_name + "__in"] = TypedChoiceInFilter(
                    field_name=field,
                    choices=BOOLEAN_CHOICES,
                    coerce=strtobool,
                    lookup_expr="in",
                )
                self.filters[filter_name + "__range"] = TypedChoiceRangeFilter(
                    field_name=field,
                    choices=BOOLEAN_CHOICES,
                    coerce=strtobool,
                    lookup_expr="range",
                )
                self.filters[filter_name + "__isnull"] = filters.TypedChoiceFilter(
                    field_name=field,
                    choices=BOOLEAN_CHOICES,
                    coerce=strtobool,
                    lookup_expr="isnull",
                )

                for lookup in BASE_LOOKUPS:
                    self.filters[
                        filter_name + "__" + lookup
                    ] = filters.TypedChoiceFilter(
                        field_name=field,
                        choices=BOOLEAN_CHOICES,
                        coerce=strtobool,
                        lookup_expr=lookup,
                    )
