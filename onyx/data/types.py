from enum import Enum


class OnyxType(Enum):
    HASH = (
        "hash",
        [
            "",
            "exact",
            "ne",
            "in",
        ],
    )
    TEXT = (
        "text",
        [
            "",
            "exact",
            "ne",
            "in",
            "contains",
            "startswith",
            "endswith",
            "iexact",
            "icontains",
            "istartswith",
            "iendswith",
            "regex",
            "iregex",
            "length",
            "length__in",
            "length__range",
        ],
    )
    CHOICE = (
        "choice",
        [
            "",
            "exact",
            "ne",
            "in",
        ],
    )
    INTEGER = (
        "integer",
        [
            "",
            "exact",
            "ne",
            "in",
            "isnull",
            "lt",
            "lte",
            "gt",
            "gte",
            "range",
        ],
    )
    DECIMAL = (
        "decimal",
        [
            "",
            "exact",
            "ne",
            "in",
            "isnull",
            "lt",
            "lte",
            "gt",
            "gte",
            "range",
        ],
    )
    DATE_YYYY_MM = (
        "date (YYYY-MM)",
        [
            "",
            "exact",
            "ne",
            "in",
            "isnull",
            "lt",
            "lte",
            "gt",
            "gte",
            "range",
            "year",
            "year__in",
            "year__range",
        ],
    )
    DATE_YYYY_MM_DD = (
        "date (YYYY-MM-DD)",
        [
            "",
            "exact",
            "ne",
            "in",
            "isnull",
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
        ],
    )
    DATETIME = (
        "date (YYYY-MM-DD HH:MM:SS)",
        [
            "",
            "exact",
            "ne",
            "in",
            "isnull",
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
        ],
    )
    BOOLEAN = (
        "bool",
        [
            "",
            "exact",
            "ne",
            "in",
            "isnull",
        ],
    )
    RELATION = (
        "relation",
        [
            "isnull",
        ],
    )

    def __init__(self, label, lookups) -> None:
        self.label = label
        self.lookups = lookups
