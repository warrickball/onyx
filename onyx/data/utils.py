from contextlib import contextmanager
from django.db import models
from django.contrib.auth.models import Group
from rest_framework import exceptions
from utils.fields import ChoiceField, YearMonthField, ModelChoiceField
from .filters import TEXT_FIELDS, ALL_LOOKUPS


@contextmanager
def mutable(obj):
    """
    If the provided `obj` has a `_mutable` property, this context manager temporarily sets it to `True`
    """
    _mutable = getattr(obj, "_mutable", None)
    if _mutable is not None:
        obj._mutable = True

    try:
        yield obj
    finally:
        # Reset object's mutability
        if _mutable is not None:
            obj._mutable = _mutable


def parse_dunders(obj):
    """
    Flatten a JSON object into a set of dunderised keys.
    """
    dunders = []
    if isinstance(obj, dict):
        for key, item in obj.items():
            prefix = key
            values = parse_dunders(item)

            if values:
                for v in values:
                    dunders.append(f"{prefix}__{v}")
            else:
                dunders.append(prefix)

    elif isinstance(obj, list):
        for item in obj:
            values = parse_dunders(item)

            for v in values:
                dunders.append(v)
    else:
        return []

    return list(set(dunders))


def prefetch_nested(qs, fields, prefix=None):
    """
    For each field in `fields` that contains nested data, apply prefetching to the QuerySet `qs`.
    """
    for field, nested in fields.items():
        if nested:
            if prefix:
                field = f"{prefix}__{field}"

            qs = qs.prefetch_related(field)
            qs = prefetch_nested(qs, nested, prefix=field)

    return qs


# TODO: Not sure the best way to use this, but its here if I need it.
def lowercase_keys(obj):
    """
    Create a new object from the provided JSON object, with lowercased keys.
    """
    if isinstance(obj, dict):
        return {key.lower(): lowercase_keys(value) for key, value in obj.items()}

    elif isinstance(obj, list):
        return [lowercase_keys(item) for item in obj]

    else:
        return obj


def assign_field_types(fields, field_types, prefix=None):
    for field, nested in fields.items():
        if prefix:
            field_path = f"{prefix}__{field}"
        else:
            field_path = field

        if nested:
            assign_field_types(nested, field_types, prefix=field_path)
        else:
            field_type = field_types[field_path].field_type
            if field_type in TEXT_FIELDS:
                fields[field] = "text"
            elif field_type == ChoiceField:
                fields[field] = "choice"
            elif field_type in [models.IntegerField, models.FloatField]:
                fields[field] = "number"
            elif field_type in [models.DateField, models.DateTimeField]:
                fields[field] = "date (YYYY-MM-DD)"
            elif field_type == YearMonthField:
                fields[field] = "date (YYYY-MM)"
            elif field_type == models.BooleanField:
                fields[field] = "bool"


# TODO: All the below needs some serious TLC


class OnyxField:
    def __init__(self, project, field_model, field_path, field_name, lookup):
        self.project = project
        self.field_model = field_model
        self.field_instance = self.field_model._meta.get_field(field_name)
        self.field_type = type(self.field_instance)
        self.field_path = field_path
        self.field_name = field_name
        self.lookup = lookup


def resolve_fields(project, user, action, fields):
    """
    * Resolves provided `fields`, determining which models they come from.

    * Checks `user` permissions to view and perform given `action` on these.
    """
    model = project.content_type.model_class()
    resolved = {}
    unknown = []

    # Resolve each field
    for field in fields:
        # Check for trailing double underscore
        if field.endswith("__"):
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
            field_name = field_path.split("__")[-1]
            lookup = "__".join(components[i + 1 :])

            # The component is a foreign key relationship
            if isinstance(component_instance, models.ForeignKey):
                # TODO: Handle db_choice_fields (or omit them entirely?)

                if not lookup or lookup in ALL_LOOKUPS:
                    # The field is determined, and the lookup is recognised
                    # So we instantiate the resolved field instance
                    resolved[field] = OnyxField(
                        project=project.code,
                        field_model=current_model,
                        field_path=field_path,
                        field_name=field_name,
                        lookup=lookup,
                    )
                    break
                else:
                    if isinstance(component_instance, ModelChoiceField):
                        # A ModelChoiceField can only be followed by a valid lookup
                        # If it is invalid, return unknown
                        unknown.append(field)

                # These may be remaining components
                # Move on to them
                current_model = component_instance.related_model

                model_fields = {
                    x.name: x for x in current_model._meta.get_fields()  # type: ignore
                }
                continue

            # The component is a many-to-one relationship
            elif isinstance(component_instance, models.ManyToOneRel):
                if not lookup or lookup in ALL_LOOKUPS:
                    # The field is determined, and the lookup is recognised
                    # So we instantiate the resolved field instance
                    resolved[field] = OnyxField(
                        project=project.code,
                        field_model=current_model,
                        field_path=field_path,
                        field_name=field_name,
                        lookup=lookup,
                    )
                    break

                # These may be remaining components
                # Move on to them
                current_model = component_instance.related_model

                model_fields = {
                    x.name: x for x in current_model._meta.get_fields()  # type: ignore
                }
                continue

            # The component is not a relation
            else:  # not component_instance.is_relation
                if not lookup or lookup in ALL_LOOKUPS:
                    # The field is determined, and the lookup is recognised
                    # So we instantiate the resolved field instance
                    resolved[field] = OnyxField(
                        project=project.code,
                        field_model=current_model,
                        field_path=field_path,
                        field_name=field_name,
                        lookup=lookup,
                    )
                else:
                    unknown.append(field)

                break

    required = []

    app_label = project.content_type.app_label

    # Get and check each field permission required by the user
    for field_path, field_obj in resolved.items():
        # Check whether the user can perform the action on the field
        field_permission = (
            f"{app_label}.{action}_{project.code}__{field_obj.field_path}"
        )
        if not user.has_perm(field_permission):
            # If they do not have permission, check whether they can view the field
            # If they can't view the field, tell them it doesn't exist
            # If they can, return the permissions required
            view_field_permission = (
                f"{app_label}.view_{project.code}__{field_obj.field_path}"
            )

            if action != "view" and user.has_perm(view_field_permission):
                required.append(field_permission)
                continue
            else:
                unknown.append(field_path)
                continue

    if unknown:
        raise exceptions.ValidationError({"unknown_fields": unknown})

    if required:
        raise exceptions.PermissionDenied(
            {"required_permissions": sorted(set(required))}
        )

    return resolved


def get_fields_from_permissions(fields_dict, permissions, include=None, exclude=None):
    for permission in permissions:
        _, _, field = permission.codename.partition("__")

        if include and not any(field.startswith(inc) for inc in include):
            continue

        if exclude and any(field.startswith(exc) for exc in exclude):
            continue

        field_path = field.split("__")

        if field_path:
            current_dict = fields_dict

            for p in field_path:
                if not p:
                    # Ignore empty strings
                    # These come from permissions where there is no field attached
                    # So there is no __ to split on
                    break

                current_dict.setdefault(p, {})
                current_dict = current_dict[p]

    return fields_dict


def view_fields(code, scopes=None, include=None, exclude=None):
    project_view_group = Group.objects.get(
        projectgroup__project__code=code,
        projectgroup__action="view",
        projectgroup__scope="base",
    )

    if scopes:
        scope_view_groups = [
            Group.objects.get(
                projectgroup__project__code=code,
                projectgroup__action="view",
                projectgroup__scope=scope,
            )
            for scope in scopes
        ]
    else:
        scope_view_groups = []

    # Dictionary structure detailing all viewable fields based on
    # the project code and the scopes provided
    fields_dict = {}

    # Update the fields dict with all viewable fields in the base project
    fields_dict = get_fields_from_permissions(
        fields_dict,
        project_view_group.permissions.all(),
        include=include,
        exclude=exclude,
    )

    # For each scope
    # Update the fields dict with any additional viewable fields
    for scope_view_group in scope_view_groups:
        fields_dict = get_fields_from_permissions(
            fields_dict,
            scope_view_group.permissions.all(),
            include=include,
            exclude=exclude,
        )

    return fields_dict
