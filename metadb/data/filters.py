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

# Additional lookups for text fields
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
    ("true", "true"),
    ("false", "false"),
)

# TODO: Ordering filters?


class METADBFilter(filters.FilterSet):
    def __init__(self, model, fields, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in fields:
            if not any(d.startswith(field) for d in self.data):
                continue

            model_field = model._meta.get_field(field)

            if isinstance(model_field, ForeignKey):
                print("Hi")
                related_field = model_field.foreign_related_fields[0].name  # type: ignore
                field_type = type(
                    model_field.related_model._meta.get_field(related_field)
                )
                field_path = field + "__" + related_field
            else:
                related_field = field
                field_type = type(model_field)
                field_path = field

            if model_field.related_model == Choice:
                content_type = ContentType.objects.get_for_model(model)
                qs = Choice.objects.filter(
                    content_type=content_type,
                    field=field,
                )
                self.filters[field] = filters.ModelChoiceFilter(
                    field_name=field,
                    queryset=qs,
                    to_field_name="choice",
                )
                self.filters[f"{field}__in"] = ModelChoiceInFilter(
                    field_name=field,
                    queryset=qs,
                    to_field_name="choice",
                    lookup_expr="in",
                )
                self.filters[f"{field}__range"] = ModelChoiceRangeFilter(
                    field_name=field,
                    queryset=qs,
                    to_field_name="choice",
                    lookup_expr="range",
                )
                self.filters[f"{field}__isnull"] = filters.TypedChoiceFilter(
                    field_name=field,
                    choices=BOOLEAN_CHOICES,
                    coerce=strtobool,
                    lookup_expr="isnull",
                )

                for lookup in BASE_LOOKUPS:
                    self.filters[f"{field}__{lookup}"] = filters.ModelChoiceFilter(
                        field_name=field,
                        queryset=qs,
                        to_field_name="choice",
                        lookup_expr=lookup,
                    )

                if field_type in [LowerCharField, models.CharField, models.TextField]:
                    for lookup in CHAR_LOOKUPS:
                        self.filters[f"{field}__{lookup}"] = filters.CharFilter(
                            field_name=f"{field}__choice", lookup_expr=lookup
                        )

            elif field in model.CustomMeta.db_choice_fields:
                db_model = model._meta.get_field(field).related_model

                self.filters[field] = filters.ModelChoiceFilter(
                    field_name=field,
                    queryset=db_model.objects.all(),
                    to_field_name=related_field,
                )
                self.filters[f"{field}__in"] = ModelChoiceInFilter(
                    field_name=field,
                    queryset=db_model.objects.all(),
                    to_field_name=related_field,
                    lookup_expr="in",
                )
                self.filters[f"{field}__range"] = ModelChoiceRangeFilter(
                    field_name=field,
                    queryset=db_model.objects.all(),
                    to_field_name=related_field,
                    lookup_expr="range",
                )
                self.filters[f"{field}__isnull"] = filters.TypedChoiceFilter(
                    field_name=field,  # TODO: Was originally field_path but I think it can just be field
                    choices=BOOLEAN_CHOICES,
                    coerce=strtobool,
                    lookup_expr="isnull",
                )

                for lookup in BASE_LOOKUPS:
                    self.filters[f"{field}__{lookup}"] = filters.ModelChoiceFilter(
                        field_name=field,
                        queryset=db_model.objects.all(),
                        to_field_name=related_field,
                        lookup_expr=lookup,
                    )

                if field_type in [LowerCharField, models.CharField, models.TextField]:
                    for lookup in CHAR_LOOKUPS:
                        self.filters[f"{field}__{lookup}"] = filters.CharFilter(
                            field_name=field_path, lookup_expr=lookup
                        )

            elif field_type in [LowerCharField, models.CharField, models.TextField]:
                self.filters[field] = filters.CharFilter(field_name=field_path)
                self.filters[f"{field}__in"] = CharInFilter(
                    field_name=field_path, lookup_expr="in"
                )
                self.filters[f"{field}__range"] = CharRangeFilter(
                    field_name=field_path, lookup_expr="range"
                )
                self.filters[f"{field}__isnull"] = filters.TypedChoiceFilter(
                    field_name=field_path,
                    choices=BOOLEAN_CHOICES,
                    coerce=strtobool,
                    lookup_expr="isnull",
                )

                for lookup in BASE_LOOKUPS:
                    self.filters[f"{field}__{lookup}"] = filters.CharFilter(
                        field_name=field_path, lookup_expr=lookup
                    )

                for lookup in CHAR_LOOKUPS:
                    self.filters[f"{field}__{lookup}"] = filters.CharFilter(
                        field_name=field_path, lookup_expr=lookup
                    )

            elif field_type in [models.IntegerField, models.FloatField]:
                self.filters[field] = filters.NumberFilter(field_name=field_path)

                self.filters[f"{field}__in"] = NumberInFilter(
                    field_name=field_path, lookup_expr="in"
                )
                self.filters[f"{field}__range"] = NumberRangeFilter(
                    field_name=field_path, lookup_expr="range"
                )
                self.filters[f"{field}__isnull"] = filters.TypedChoiceFilter(
                    field_name=field_path,
                    choices=BOOLEAN_CHOICES,
                    coerce=strtobool,
                    lookup_expr="isnull",
                )

                for lookup in BASE_LOOKUPS:
                    self.filters[f"{field}__{lookup}"] = filters.NumberFilter(
                        field_name=field_path, lookup_expr=lookup
                    )

            elif field_type == YearMonthField:
                self.filters[field] = filters.DateFilter(
                    field_name=field_path, input_formats=["%Y-%m"]
                )
                self.filters[f"{field}__in"] = DateInFilter(
                    field_name=field_path,
                    input_formats=["%Y-%m"],
                    lookup_expr="in",
                )
                self.filters[f"{field}__range"] = DateRangeFilter(
                    field_name=field_path, input_formats=["%Y-%m"], lookup_expr="range"
                )
                self.filters[f"{field}__isnull"] = filters.TypedChoiceFilter(
                    field_name=field_path,
                    choices=BOOLEAN_CHOICES,
                    coerce=strtobool,
                    lookup_expr="isnull",
                )
                self.filters[f"{field}__iso_year"] = filters.NumberFilter(
                    field_name=field_path, lookup_expr="iso_year"
                )
                self.filters[f"{field}__iso_year__in"] = NumberInFilter(
                    field_name=field_path,
                    lookup_expr="iso_year__in",
                )
                self.filters[f"{field}__iso_year__range"] = NumberRangeFilter(
                    field_name=field_path,
                    lookup_expr="iso_year__range",
                )

                for lookup in BASE_LOOKUPS:
                    self.filters[f"{field}__{lookup}"] = filters.DateFilter(
                        field_name=field_path,
                        input_formats=["%Y-%m"],
                        lookup_expr=lookup,
                    )

            elif field_type == models.DateField:
                self.filters[field] = filters.DateFilter(
                    field_name=field_path, input_formats=["%Y-%m-%d"]
                )
                self.filters[f"{field}__in"] = DateInFilter(
                    field_name=field_path, input_formats=["%Y-%m-%d"], lookup_expr="in"
                )
                self.filters[f"{field}__range"] = DateRangeFilter(
                    field_name=field_path,
                    input_formats=["%Y-%m-%d"],
                    lookup_expr="range",
                )
                self.filters[f"{field}__isnull"] = filters.TypedChoiceFilter(
                    field_name=field_path,
                    choices=BOOLEAN_CHOICES,
                    coerce=strtobool,
                    lookup_expr="isnull",
                )
                self.filters[f"{field}__iso_year"] = filters.NumberFilter(
                    field_name=field_path, lookup_expr="iso_year"
                )
                self.filters[f"{field}__iso_year__in"] = NumberInFilter(
                    field_name=field_path,
                    lookup_expr="iso_year__in",
                )
                self.filters[f"{field}__iso_year__range"] = NumberRangeFilter(
                    field_name=field_path,
                    lookup_expr="iso_year__range",
                )
                self.filters[f"{field}__week"] = filters.NumberFilter(
                    field_name=field_path, lookup_expr="week"
                )
                self.filters[f"{field}__week__in"] = NumberInFilter(
                    field_name=field_path,
                    lookup_expr="week__in",
                )
                self.filters[f"{field}__week__range"] = NumberRangeFilter(
                    field_name=field_path,
                    lookup_expr="week__range",
                )

                for lookup in BASE_LOOKUPS:
                    self.filters[f"{field}__{lookup}"] = filters.DateFilter(
                        field_name=field_path,
                        input_formats=["%Y-%m-%d"],
                        lookup_expr=lookup,
                    )

            elif field_type == models.DateTimeField:
                self.filters[field] = filters.DateTimeFilter(
                    field_name=field_path, input_formats=["%Y-%m-%d"]
                )
                self.filters[f"{field}__in"] = DateTimeInFilter(
                    field_name=field_path, input_formats=["%Y-%m-%d"], lookup_expr="in"
                )
                self.filters[f"{field}__range"] = DateTimeRangeFilter(
                    field_name=field_path,
                    input_formats=["%Y-%m-%d"],
                    lookup_expr="range",
                )
                self.filters[f"{field}__isnull"] = filters.TypedChoiceFilter(
                    field_name=field_path,
                    choices=BOOLEAN_CHOICES,
                    coerce=strtobool,
                    lookup_expr="isnull",
                )
                self.filters[f"{field}__iso_year"] = filters.NumberFilter(
                    field_name=field_path, lookup_expr="iso_year"
                )
                self.filters[f"{field}__iso_year__in"] = NumberInFilter(
                    field_name=field_path,
                    lookup_expr="iso_year__in",
                )
                self.filters[f"{field}__iso_year__range"] = NumberRangeFilter(
                    field_name=field_path,
                    lookup_expr="iso_year__range",
                )
                self.filters[f"{field}__week"] = filters.NumberFilter(
                    field_name=field_path, lookup_expr="week"
                )
                self.filters[f"{field}__week__in"] = NumberInFilter(
                    field_name=field_path,
                    lookup_expr="week__in",
                )
                self.filters[f"{field}__week__range"] = NumberRangeFilter(
                    field_name=field_path,
                    lookup_expr="week__range",
                )

                for lookup in BASE_LOOKUPS:
                    self.filters[f"{field}__{lookup}"] = filters.DateTimeFilter(
                        field_name=field_path,
                        input_formats=["%Y-%m-%d"],
                        lookup_expr=lookup,
                    )

            elif field_type == models.BooleanField:
                self.filters[field] = filters.TypedChoiceFilter(
                    field_name=field_path, choices=BOOLEAN_CHOICES, coerce=strtobool
                )
                self.filters[f"{field}__in"] = TypedChoiceInFilter(
                    field_name=field_path,
                    choices=BOOLEAN_CHOICES,
                    coerce=strtobool,
                    lookup_expr="in",
                )
                self.filters[f"{field}__range"] = TypedChoiceRangeFilter(
                    field_name=field_path,
                    choices=BOOLEAN_CHOICES,
                    coerce=strtobool,
                    lookup_expr="range",
                )
                self.filters[f"{field}__isnull"] = filters.TypedChoiceFilter(
                    field_name=field_path,
                    choices=BOOLEAN_CHOICES,
                    coerce=strtobool,
                    lookup_expr="isnull",
                )

                for lookup in BASE_LOOKUPS:
                    self.filters[f"{field}__{lookup}"] = filters.TypedChoiceFilter(
                        field_name=field_path,
                        choices=BOOLEAN_CHOICES,
                        coerce=strtobool,
                        lookup_expr=lookup,
                    )
