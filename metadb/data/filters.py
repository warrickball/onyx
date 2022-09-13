from django_filters import rest_framework as filters
from django.db import models
from utils.fields import YearMonthField
from distutils.util import strtobool


class AllValuesFilter(filters.AllValuesFilter):
    def __init__(self, *args, model, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model


class NumericInFilter(filters.BaseInFilter, filters.NumberFilter):
    pass


class CharInFilter(filters.BaseInFilter, filters.CharFilter):
    pass


class DateInFilter(filters.BaseInFilter, filters.DateFilter):
    pass


class ChoiceInFilter(filters.BaseInFilter, filters.ChoiceFilter):
    pass


class AllValuesInFilter(filters.BaseInFilter, AllValuesFilter):
    pass


class TypedChoiceInFilter(filters.BaseInFilter, filters.TypedChoiceFilter):
    pass


class CharRangeFilter(filters.BaseRangeFilter, filters.CharFilter):
    pass


class DateRangeFilter(filters.BaseRangeFilter, filters.DateFilter):
    pass


class ChoiceRangeFilter(filters.BaseRangeFilter, filters.ChoiceFilter):
    pass


class AllValuesRangeFilter(filters.BaseRangeFilter, AllValuesFilter):
    pass


class TypedChoiceRangeFilter(filters.BaseInFilter, filters.TypedChoiceFilter):
    pass


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

        for field, field_data in pathogen_model.FILTER_FIELDS.items():
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

            # Name for the field, used by the user when filtering
            # An alias allows for renaming of fields, e.g. institute__code is renamed to institute
            filter_name = field_data["alias"] if "alias" in field_data else field

            if is_choice_field:
                choices = pathogen_model._meta.get_field(field).choices

                self.filters[filter_name] = filters.ChoiceFilter(
                    field_name=field, choices=choices
                )
                self.filters[filter_name + "__in"] = ChoiceInFilter(
                    field_name=field, choices=choices, lookup_expr="in"
                )
                self.filters[filter_name + "__notin"] = ChoiceInFilter(
                    field_name=field, choices=choices, lookup_expr="in", exclude=True
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

                if field_type in [models.CharField, models.TextField]:
                    for lookup in CHAR_LOOKUPS:
                        self.filters[filter_name + "__" + lookup] = filters.CharFilter(
                            field_name=field, lookup_expr=lookup
                        )

            elif is_db_choice_field:
                self.filters[filter_name] = AllValuesFilter(
                    field_name=field,
                    model=pathogen_model,
                )
                self.filters[filter_name + "__in"] = AllValuesInFilter(
                    field_name=field,
                    lookup_expr="in",
                    model=pathogen_model,
                )
                self.filters[filter_name + "__notin"] = AllValuesInFilter(
                    field_name=field,
                    lookup_expr="in",
                    exclude=True,
                    model=pathogen_model,
                )
                self.filters[filter_name + "__range"] = AllValuesRangeFilter(
                    field_name=field, lookup_expr="range", model=pathogen_model
                )
                self.filters[filter_name + "__isnull"] = filters.TypedChoiceFilter(
                    field_name=field,
                    choices=BOOLEAN_CHOICES,
                    coerce=strtobool,
                    lookup_expr="isnull",
                )

                for lookup in BASE_LOOKUPS:
                    self.filters[filter_name + "__" + lookup] = AllValuesFilter(
                        field_name=field, lookup_expr=lookup, model=pathogen_model
                    )

                if field_type in [models.CharField, models.TextField]:
                    for lookup in CHAR_LOOKUPS:
                        self.filters[filter_name + "__" + lookup] = filters.CharFilter(
                            field_name=field, lookup_expr=lookup
                        )

            elif field_type in [models.CharField, models.TextField]:
                self.filters[filter_name] = filters.CharFilter(field_name=field)
                self.filters[filter_name + "__in"] = CharInFilter(
                    field_name=field, lookup_expr="in"
                )
                self.filters[filter_name + "__notin"] = CharInFilter(
                    field_name=field, lookup_expr="in", exclude=True
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

            elif field_type == YearMonthField:
                self.filters[filter_name] = filters.DateFilter(
                    field_name=field, input_formats=["%Y-%m"]
                )
                self.filters[filter_name + "__in"] = DateInFilter(
                    field_name=field,
                    input_formats=["%Y-%m"],
                    lookup_expr="in",
                )
                self.filters[filter_name + "__notin"] = DateInFilter(
                    field_name=field,
                    input_formats=["%Y-%m"],
                    lookup_expr="in",
                    exclude=True,
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
                self.filters[filter_name + "__iso_year__in"] = NumericInFilter(
                    field_name=field,
                    lookup_expr="iso_year__in",
                )
                self.filters[
                    filter_name + "__iso_year__range"
                ] = filters.NumericRangeFilter(
                    field_name=field,
                    lookup_expr="iso_year__range",
                )

                for lookup in BASE_LOOKUPS:
                    self.filters[filter_name + "__" + lookup] = filters.DateFilter(
                        field_name=field, input_formats=["%Y-%m"], lookup_expr=lookup
                    )

            elif field_type == models.DateField:
                self.filters[filter_name] = filters.DateFilter(
                    field_name=field, input_formats=["%Y-%m-%d"], lookup_expr="in"
                )
                self.filters[filter_name + "__in"] = DateInFilter(
                    field_name=field, input_formats=["%Y-%m-%d"], lookup_expr="in"
                )
                self.filters[filter_name + "__notin"] = DateInFilter(
                    field_name=field,
                    input_formats=["%Y-%m-%d"],
                    lookup_expr="in",
                    exclude=True,
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
                self.filters[filter_name + "__iso_year__in"] = NumericInFilter(
                    field_name=field,
                    lookup_expr="iso_year__in",
                )
                self.filters[
                    filter_name + "__iso_year__range"
                ] = filters.NumericRangeFilter(
                    field_name=field,
                    lookup_expr="iso_year__range",
                )
                self.filters[filter_name + "__iso_week"] = filters.NumberFilter(
                    field_name=field, lookup_expr="week"
                )
                self.filters[filter_name + "__iso_week__in"] = NumericInFilter(
                    field_name=field,
                    lookup_expr="week__in",
                )
                self.filters[
                    filter_name + "__iso_week__range"
                ] = filters.NumericRangeFilter(
                    field_name=field,
                    lookup_expr="week__range",
                )

                for lookup in BASE_LOOKUPS:
                    self.filters[filter_name + "__" + lookup] = filters.DateFilter(
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
                self.filters[filter_name + "__notin"] = TypedChoiceInFilter(
                    field_name=field,
                    choices=BOOLEAN_CHOICES,
                    coerce=strtobool,
                    lookup_expr="in",
                    exclude=True,
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
