from django_filters import rest_framework as filters
from utils.fields import YearMonthField
from django.db import models


# TODO: ranges dont seem to work with dates, and 'in' isn't working properly. Check these for each data type
BASE_LOOKUPS = ["exact", "contains", "in", "range", "ne", "lt", "gt", "lte", "gte"] # TODO isempty?
CHAR_LOOKUPS = BASE_LOOKUPS + ["startswith", "endswith", "iexact", "icontains", "istartswith", "iendswith", "regex", "iregex"]
NUMBER_LOOKUPS = BASE_LOOKUPS
DATE_LOOKUPS = BASE_LOOKUPS



class METADBFilter(filters.FilterSet):
    def __init__(self, pathogen, fields, *args, **kwargs):
        super().__init__(*args, **kwargs)

        aliases = pathogen.aliases()
        choice_fields = pathogen.choice_filter_fields()

        for field, field_type in fields.items():
            if field in aliases:
                filter_name = aliases[field]
            else:
                filter_name = field

            if field in choice_fields:
                choices = pathogen.get_choices(field)
                self.filters[filter_name] = filters.ChoiceFilter(field_name=field, choices=choices)
            else:
                if field_type in [models.CharField, models.TextField]:
                    self.filters[filter_name] = filters.CharFilter(field_name=field)

                    for lookup in CHAR_LOOKUPS:
                        self.filters[filter_name + "__" + lookup] = filters.CharFilter(field_name=field, lookup_expr=lookup)

                elif field_type == YearMonthField:
                    self.filters[filter_name] = filters.DateFilter(field_name=field, input_formats=["%Y-%m"])
                    
                    for lookup in DATE_LOOKUPS:
                        self.filters[filter_name + "__" + lookup] = filters.DateFilter(field_name=field, lookup_expr=lookup, input_formats=["%Y-%m"])
                
                elif field_type == models.DateField:
                    self.filters[filter_name] = filters.DateFilter(field_name=field, input_formats=["%Y-%m-%d"])
                    
                    for lookup in DATE_LOOKUPS:
                        self.filters[filter_name + "__" + lookup] = filters.DateFilter(field_name=field, lookup_expr=lookup, input_formats=["%Y-%m-%d"])
