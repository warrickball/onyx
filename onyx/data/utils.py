from enum import Enum
from typing import Any
from django.db import models
from django.contrib.auth.models import Group, Permission
from rest_framework import exceptions
from utils.fields import HashField, ChoiceField, YearMonthField, TEXT_FIELDS
from utils.functions import get_suggestions
from accounts.models import User
from .models import Choice


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


ALL_LOOKUPS = set(lookup for onyx_type in OnyxType for lookup in onyx_type.lookups)


class InvalidLookup(Exception):
    pass


class FieldInfo:
    """
    Class for storing information on a field (and lookup) requested by a user.
    """

    def __init__(
        self,
        project: str,
        field_model: type[models.Model],
        field_path: str,
        lookup: str,
        ignore_lookup=False,
    ):
        self.project = project
        self.field_model = field_model
        self.field_path = field_path
        self.field_name = self.field_path.split("__")[-1]
        self.field_instance = self.field_model._meta.get_field(self.field_name)
        self.field_type = type(self.field_instance)

        if self.field_type == HashField:
            self.onyx_type = OnyxType.HASH
            self.required = not self.field_instance.blank

        elif self.field_type in TEXT_FIELDS:
            self.onyx_type = OnyxType.TEXT
            self.required = not self.field_instance.blank

        elif self.field_type == ChoiceField:
            self.onyx_type = OnyxType.CHOICE
            self.required = not self.field_instance.blank
            self.choices = Choice.objects.filter(
                project=self.project,
                field=self.field_name,
            ).values_list("choice", flat=True)

        elif self.field_type == models.IntegerField:
            self.onyx_type = OnyxType.INTEGER
            self.required = not self.field_instance.null

        elif self.field_type == models.FloatField:
            self.onyx_type = OnyxType.DECIMAL
            self.required = not self.field_instance.null

        elif self.field_type == YearMonthField:
            self.onyx_type = OnyxType.DATE_YYYY_MM
            self.required = not self.field_instance.null

        elif self.field_type == models.DateField:
            self.onyx_type = OnyxType.DATE_YYYY_MM_DD
            self.required = not self.field_instance.null

        elif self.field_type == models.DateTimeField:
            self.onyx_type = OnyxType.DATETIME
            self.required = not self.field_instance.null

        elif self.field_type == models.BooleanField:
            self.onyx_type = OnyxType.BOOLEAN
            self.required = not self.field_instance.null

        elif self.field_instance.is_relation:
            self.onyx_type = OnyxType.RELATION
            self.required = not self.field_instance.null

        else:
            raise NotImplementedError(
                f"Field {self.field_type} did not match an OnyxType."
            )

        if lookup not in self.onyx_type.lookups:
            if ignore_lookup:
                pass
            else:
                raise InvalidLookup

        self.lookup = lookup


def resolve_fields(
    code: str,
    model: type[models.Model],
    fields: list[str],
    ignore_lookup=False,
) -> tuple[dict[str, FieldInfo], list[str]]:
    """
    Resolves provided `fields`, determining which models they come from.

    This information is returned in `FieldInfo` objects.
    """

    resolved = {}
    unknown = []

    # Resolve each field
    for field in fields:
        # Check for trailing underscore
        # This is required because if a field ends in "__"
        # Splitting will result in some funky stuff
        if field.endswith("_"):
            unknown.append(field)
            continue

        # Base model for the project
        current_model = model
        model_fields = {x.name: x for x in current_model._meta.get_fields()}

        # Split the field into its individual components
        # If there are multiple components, these should specify
        # a chain of relations through multiple models
        components = field.split("__")
        for i, component in enumerate(components):
            # If the current component is not known on the current model
            # Then add to unknown fields
            if component not in model_fields:
                unknown.append(field)
                break

            # Corresponding field instance for the component
            component_instance = model_fields[component]
            field_path = "__".join(components[: i + 1])
            lookup = "__".join(components[i + 1 :])

            if lookup in ALL_LOOKUPS:
                # The field is valid, and the lookup is not sus
                # So we attempt to instantiate the field instance
                # This could fail if the lookup is not allowed for the given field
                try:
                    field_info = FieldInfo(
                        project=code,
                        field_model=current_model,
                        field_path=field_path,
                        lookup=lookup,
                        ignore_lookup=ignore_lookup,
                    )
                    resolved[field] = field_info
                except InvalidLookup:
                    unknown.append(field)
                break

            elif component_instance.is_relation:
                # The field's 'lookup' may be remaining components in a relation
                # Move on to them
                current_model = component_instance.related_model
                assert current_model is not None

                model_fields = {x.name: x for x in current_model._meta.get_fields()}
                continue

            else:
                # Otherwise, it is unknown
                unknown.append(field)
                break

    return resolved, unknown


def assign_fields_info(
    fields_dict: dict,
    fields_info: dict[str, FieldInfo],
    prefix: str | None = None,
) -> dict[str, Any]:
    for field, nested in fields_dict.items():
        if prefix:
            field_path = f"{prefix}__{field}"
        else:
            field_path = field

        if nested:
            onyx_type = fields_info[field_path].onyx_type
            required = fields_info[field_path].required
            assign_fields_info(
                fields_dict=nested,
                fields_info=fields_info,
                prefix=field_path,
            )
            fields_dict[field] = {
                "type": onyx_type.label,
                "required": required,
                "fields": nested,
            }
        else:
            onyx_type = fields_info[field_path].onyx_type
            field_instance = fields_info[field_path].field_instance
            required = fields_info[field_path].required

            if onyx_type == OnyxType.CHOICE:
                choices = fields_info[field_path].choices
                fields_dict[field] = {
                    "description": field_instance.help_text,
                    "type": onyx_type.label,
                    "required": required,
                    "values": choices,
                }
            else:
                fields_dict[field] = {
                    "description": field_instance.help_text,
                    "type": onyx_type.label,
                    "required": required,
                }

    return fields_dict


def get_field_from_permission(
    permission: Permission,
) -> str:
    _, _, field = permission.codename.partition("__")
    return field


def get_fields(
    code: str,
    action: str,
    scopes: list[str] | None = None,
) -> list[str]:
    if scopes:
        scopes = ["base"] + scopes
    else:
        scopes = ["base"]

    groups = Group.objects.filter(
        projectgroup__project__code=code,
        projectgroup__action=action,
        projectgroup__scope__in=scopes,
    )

    permissions = [
        permission for group in groups for permission in group.permissions.all()
    ]

    fields = [get_field_from_permission(permission) for permission in permissions]

    return fields


# TODO: This function feels very hacky.
# A lack of type-checking is required on obj in order for request.data to pass.
# Which does make me wonder: is this robust against whatever could be provided through request.data?
# E.g. how sure are we that all 'fields' have been flattened from obj?
def flatten_fields(obj) -> list[str]:
    """
    Flatten a JSON-like `obj` into a list of dunderised keys.
    """

    dunders = []
    if isinstance(obj, dict):
        for key, item in obj.items():
            # TODO: An ugly but effective fix until I come up with a more elegant solution
            # Basically just want to prevent any dunder separators in keys
            # Long-term would be nice to not need the flatten_fields function, and check perms recursively
            if "__" in key:
                raise exceptions.ValidationError(
                    {
                        "detail": "Field names in request body cannot contain '__' separator."
                    }
                )
            prefix = key
            values = flatten_fields(item)

            if values:
                for v in values:
                    dunders.append(f"{prefix}__{v}")
            else:
                dunders.append(prefix)
    elif isinstance(obj, list):
        for item in obj:
            values = flatten_fields(item)

            for v in values:
                dunders.append(v)
    else:
        return []

    return list(set(dunders))


def unflatten_fields(
    fields: list[str],
) -> dict[str, Any]:
    fields_dict = {}

    for field in fields:
        field_pieces = field.split("__")

        if field_pieces:
            current_dict = fields_dict

            for piece in field_pieces:
                if not piece:
                    # Ignore empty strings
                    # These come from permissions where there is no field attached
                    # So there is no __ to split on
                    break

                current_dict.setdefault(piece, {})
                current_dict = current_dict[piece]

    return fields_dict


def include_exclude_fields(
    fields: list[str],
    include: list[str] | None = None,
    exclude: list[str] | None = None,
) -> list[str]:
    if include:
        fields = [
            field for field in fields if any(field.startswith(inc) for inc in include)
        ]

    if exclude:
        fields = [
            field
            for field in fields
            if not any(field.startswith(exc) for exc in exclude)
        ]

    return fields


def get_user_fields(
    user: User,
    code: str,
    action: str,
) -> list[str]:
    groups = user.groups.filter(
        projectgroup__project__code=code,
        projectgroup__action=action,
    )

    permissions = [
        permission for group in groups for permission in group.permissions.all()
    ]

    fields = [get_field_from_permission(permission) for permission in permissions]

    return fields


def validate_fields(
    user: User,
    code: str,
    app_label: str,
    action: str,
    fields: list[str],
    required: list[str] | None = None,
    unknown: list[str] | None = None,
) -> None:
    if not required:
        required = []

    if not unknown:
        unknown = []

    for field in fields:
        # Check whether the user can perform the action on the field
        field_action_permission = f"{app_label}.{action}_{code}__{field}"

        if not user.has_perm(field_action_permission):
            # If they do not have permission, check whether they can view the field
            field_view_permission = f"{app_label}.view_{code}__{field}"

            if action != "view" and user.has_perm(field_view_permission):
                # If the user has permission to view the field, return the action permission required
                required.append(field)
            else:
                # If the user does not have permission, tell them it is unknown
                unknown.append(field)

    # Form error messages for fields with permissions required
    required_dict = {}
    for r in required:
        required_dict[r] = [f"You cannot {action} this field."]

    # Form error messages for unknown fields
    unknown_dict = {}
    if unknown:
        user_fields = get_user_fields(user, code, action)

        for u in unknown:
            suggestions = get_suggestions(u, user_fields)

            if suggestions:
                unknown_dict[u] = [
                    f"This field is unknown. Perhaps you meant: {', '.join(suggestions)}"
                ]
            else:
                unknown_dict[u] = ["This field is unknown."]

    errors = unknown_dict | required_dict

    if errors:
        raise exceptions.ValidationError(errors)


def init_project_queryset(
    model: type[models.Model],
    user: User,
    fields: list[str] | None = None,
) -> models.manager.BaseManager[models.Model]:
    qs = model.objects.select_related()

    if not user.is_staff:
        # If the user is not a member of staff:
        # - Ignore suppressed data
        # - Ignore site_restricted objects from other sites
        # TODO: For site_restricted to work properly, need to have site stored directly on project record
        qs = qs.filter(suppressed=False).exclude(
            models.Q(site_restricted=True) & ~models.Q(user__site=user.site)
        )
    elif fields and "suppressed" not in fields:
        # If the user is a member of staff, but the suppressed field is not in scope:
        # - Ignore suppressed data
        qs = qs.filter(suppressed=False)

    return qs


def prefetch_nested(
    qs: models.QuerySet,
    fields_dict: dict,
    prefix: str | None = None,
) -> models.QuerySet:
    """
    For each field in `fields_dict` that contains nested data, apply prefetching to the QuerySet `qs`.
    """

    for field, nested in fields_dict.items():
        if nested:
            if prefix:
                field = f"{prefix}__{field}"

            qs = qs.prefetch_related(field)
            qs = prefetch_nested(
                qs=qs,
                fields_dict=nested,
                prefix=field,
            )

    return qs
