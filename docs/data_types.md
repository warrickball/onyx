# Data types

## Text
**OnyxType**: `OnyxType.TEXT` 

**Label**: `text`

**Lookups**:
```
{
    "": "<class 'django_filters.filters.CharFilter'>",
    "exact": "<class 'django_filters.filters.CharFilter'>",
    "ne": "<class 'django_filters.filters.CharFilter'>",
    "in": "<class 'data.filters.CharInFilter'>",
    "contains": "<class 'django_filters.filters.CharFilter'>",
    "startswith": "<class 'django_filters.filters.CharFilter'>",
    "endswith": "<class 'django_filters.filters.CharFilter'>",
    "iexact": "<class 'django_filters.filters.CharFilter'>",
    "icontains": "<class 'django_filters.filters.CharFilter'>",
    "istartswith": "<class 'django_filters.filters.CharFilter'>",
    "iendswith": "<class 'django_filters.filters.CharFilter'>",
    "regex": "<class 'data.filters.RegexFilter'>",
    "iregex": "<class 'data.filters.RegexFilter'>",
    "length": "<class 'django_filters.filters.NumberFilter'>",
    "length__in": "<class 'data.filters.NumberInFilter'>",
    "length__range": "<class 'data.filters.NumberRangeFilter'>",
    "isnull": "<class 'data.filters.BooleanFilter'>"
}
```

## Choice
**OnyxType**: `OnyxType.CHOICE`

**Label**: `choice`

**Lookups**:
```
{
    "": "<class 'data.filters.ChoiceFilter'>",
    "exact": "<class 'data.filters.ChoiceFilter'>",
    "ne": "<class 'data.filters.ChoiceFilter'>",
    "in": "<class 'data.filters.ChoiceInFilter'>",
    "isnull": "<class 'data.filters.BooleanFilter'>"
}
```

## Integer
**OnyxType**: `OnyxType.INTEGER`

**Label**: `integer`

**Lookups**:
```
{
    "": "<class 'django_filters.filters.NumberFilter'>",
    "exact": "<class 'django_filters.filters.NumberFilter'>",
    "ne": "<class 'django_filters.filters.NumberFilter'>",
    "in": "<class 'data.filters.NumberInFilter'>",
    "lt": "<class 'django_filters.filters.NumberFilter'>",
    "lte": "<class 'django_filters.filters.NumberFilter'>",
    "gt": "<class 'django_filters.filters.NumberFilter'>",
    "gte": "<class 'django_filters.filters.NumberFilter'>",
    "range": "<class 'data.filters.NumberRangeFilter'>",
    "isnull": "<class 'data.filters.BooleanFilter'>"
}
```

## Decimal
**OnyxType**: `OnyxType.DECIMAL`

**Label**: `decimal`

**Lookups**:
```
{
    "": "<class 'django_filters.filters.NumberFilter'>",
    "exact": "<class 'django_filters.filters.NumberFilter'>",
    "ne": "<class 'django_filters.filters.NumberFilter'>",
    "in": "<class 'data.filters.NumberInFilter'>",
    "lt": "<class 'django_filters.filters.NumberFilter'>",
    "lte": "<class 'django_filters.filters.NumberFilter'>",
    "gt": "<class 'django_filters.filters.NumberFilter'>",
    "gte": "<class 'django_filters.filters.NumberFilter'>",
    "range": "<class 'data.filters.NumberRangeFilter'>",
    "isnull": "<class 'data.filters.BooleanFilter'>"
}
```

## Date (YYYY-MM)
**OnyxType**: `OnyxType.DATE_YYYY_MM`

**Label**: `date (YYYY-MM)`

**Lookups**:
```
{
    "": "<class 'data.filters.YearMonthFilter'>",
    "exact": "<class 'data.filters.YearMonthFilter'>",
    "ne": "<class 'data.filters.YearMonthFilter'>",
    "in": "<class 'data.filters.YearMonthInFilter'>",
    "lt": "<class 'data.filters.YearMonthFilter'>",
    "lte": "<class 'data.filters.YearMonthFilter'>",
    "gt": "<class 'data.filters.YearMonthFilter'>",
    "gte": "<class 'data.filters.YearMonthFilter'>",
    "range": "<class 'data.filters.YearMonthRangeFilter'>",
    "year": "<class 'django_filters.filters.NumberFilter'>",
    "year__in": "<class 'data.filters.NumberInFilter'>",
    "year__range": "<class 'data.filters.NumberRangeFilter'>",
    "isnull": "<class 'data.filters.BooleanFilter'>",
    "iso_year": "<class 'django_filters.filters.NumberFilter'>",
    "iso_year__in": "<class 'data.filters.NumberInFilter'>",
    "iso_year__range": "<class 'data.filters.NumberRangeFilter'>",
    "week": "<class 'django_filters.filters.NumberFilter'>",
    "week__in": "<class 'data.filters.NumberInFilter'>",
    "week__range": "<class 'data.filters.NumberRangeFilter'>"
}
```

## Date (YYYY-MM-DD)
**OnyxType**: `OnyxType.DATE_YYYY_MM_DD`

**Label**: `date (YYYY-MM-DD)`

**Lookups**:
```
 {
    "": "<class 'data.filters.DateFilter'>",
    "exact": "<class 'data.filters.DateFilter'>",
    "ne": "<class 'data.filters.DateFilter'>",
    "in": "<class 'data.filters.DateInFilter'>",
    "lt": "<class 'data.filters.DateFilter'>",
    "lte": "<class 'data.filters.DateFilter'>",
    "gt": "<class 'data.filters.DateFilter'>",
    "gte": "<class 'data.filters.DateFilter'>",
    "range": "<class 'data.filters.DateRangeFilter'>",
    "year": "<class 'django_filters.filters.NumberFilter'>",
    "year__in": "<class 'data.filters.NumberInFilter'>",
    "year__range": "<class 'data.filters.NumberRangeFilter'>",
    "iso_year": "<class 'django_filters.filters.NumberFilter'>",
    "iso_year__in": "<class 'data.filters.NumberInFilter'>",
    "iso_year__range": "<class 'data.filters.NumberRangeFilter'>",
    "week": "<class 'django_filters.filters.NumberFilter'>",
    "week__in": "<class 'data.filters.NumberInFilter'>",
    "week__range": "<class 'data.filters.NumberRangeFilter'>",
    "isnull": "<class 'data.filters.BooleanFilter'>"
}
```

## Datetime (YYYY-MM-DD HH:MM:SS)
**OnyxType**: `OnyxType.DATETIME`

**Label**: `date (YYYY-MM-DD HH:MM:SS)`

**Lookups**:
```
{
    "": "<class 'data.filters.DateTimeFilter'>",
    "exact": "<class 'data.filters.DateTimeFilter'>",
    "ne": "<class 'data.filters.DateTimeFilter'>",
    "in": "<class 'data.filters.DateTimeInFilter'>",
    "lt": "<class 'data.filters.DateTimeFilter'>",
    "lte": "<class 'data.filters.DateTimeFilter'>",
    "gt": "<class 'data.filters.DateTimeFilter'>",
    "gte": "<class 'data.filters.DateTimeFilter'>",
    "range": "<class 'data.filters.DateTimeRangeFilter'>",
    "year": "<class 'django_filters.filters.NumberFilter'>",
    "year__in": "<class 'data.filters.NumberInFilter'>",
    "year__range": "<class 'data.filters.NumberRangeFilter'>",
    "iso_year": "<class 'django_filters.filters.NumberFilter'>",
    "iso_year__in": "<class 'data.filters.NumberInFilter'>",
    "iso_year__range": "<class 'data.filters.NumberRangeFilter'>",
    "week": "<class 'django_filters.filters.NumberFilter'>",
    "week__in": "<class 'data.filters.NumberInFilter'>",
    "week__range": "<class 'data.filters.NumberRangeFilter'>",
    "isnull": "<class 'data.filters.BooleanFilter'>"
}
```

## Boolean
**OnyxType**: `OnyxType.BOOLEAN`

**Label**: `bool`

**Lookups**:
```
{
    "": "<class 'data.filters.BooleanFilter'>",
    "exact": "<class 'data.filters.BooleanFilter'>",
    "ne": "<class 'data.filters.BooleanFilter'>",
    "in": "<class 'data.filters.BooleanInFilter'>",
    "isnull": "<class 'data.filters.BooleanFilter'>"
}
```

## Relation
**OnyxType**: `OnyxType.RELATION`

**Label**: `relation`

**Lookups**:
```
{
    "isnull": "<class 'data.filters.BooleanFilter'>"
}
```