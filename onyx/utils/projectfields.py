from django.core.exceptions import FieldDoesNotExist, PermissionDenied
from django.db.models import ForeignKey, ManyToOneRel
from django.contrib.auth.models import Group
from data.filters import ALL_LOOKUPS
from utils.fields import ModelChoiceField


class OnyxField:
    def __init__(self, project, field_model, field_path, field_name, lookup):
        self.project = project
        self.field_model = field_model
        self.field_instance = self.field_model._meta.get_field(field_name)
        self.field_type = type(self.field_instance)
        self.field_path = field_path
        self.field_name = field_name
        self.lookup = lookup


def _get_fields_from_permissions(fields_dict, permissions, exclude):
    for permission in permissions:
        _, _, field = permission.codename.partition("__")
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

    for field in exclude:
        fs = field.split("__")
        level = fields_dict
        last_index = len(fs) - 1

        for i, f in enumerate(fs):
            if f not in level:
                break

            if i == last_index:
                level.pop(f)
            else:
                level = level[f]

    return fields_dict


def resolve_fields(project, model, user, action, fields):
    """
    * Resolves provided `fields`, determining which models they come from.

    * Checks `user` permissions to view and perform given `action` on these.
    """
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
            if isinstance(component_instance, ForeignKey):
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
                    x.name: x for x in current_model._meta.get_fields()  #  type: ignore
                }
                continue

            # The component is a many-to-one relationship
            elif isinstance(component_instance, ManyToOneRel):
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
                    x.name: x for x in current_model._meta.get_fields()  #  type: ignore
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
        raise FieldDoesNotExist(unknown)

    if required:
        raise PermissionDenied(required)

    return resolved


def view_fields(code, scopes=None, exclude=None):
    project_view_group = Group.objects.get(name=f"view.project.{code}")

    if scopes:
        scope_view_groups = [
            Group.objects.get(name=f"view.scope.{code}.{scope}") for scope in scopes
        ]
    else:
        scope_view_groups = []

    if not exclude:
        exclude = []

    # Dictionary structure detailing all viewable fields based on
    # the project code and the scopes provided
    fields_dict = {}

    # Update the fields dict with all viewable fields in the base project
    fields_dict = _get_fields_from_permissions(
        fields_dict,
        project_view_group.permissions.all(),
        exclude,
    )

    # For each scope
    # Update the fields dict with any additional viewable fields
    for scope_view_group in scope_view_groups:
        fields_dict = _get_fields_from_permissions(
            fields_dict,
            scope_view_group.permissions.all(),
            exclude,
        )

    return fields_dict
