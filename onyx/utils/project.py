from django.core.exceptions import FieldDoesNotExist, PermissionDenied
from django.contrib.contenttypes.models import ContentType
from django.db.models import ForeignKey, ManyToOneRel
from data.models import Project, Scope
from data.filters import ALL_LOOKUPS
from utils.errors import ProjectDoesNotExist, ScopesDoNotExist
from utils.fields import ModelChoiceField


class OnyxField:
    def __init__(self, field_model, field_path, field_name, lookup):
        self.field_model = field_model
        self.field_instance = self.field_model._meta.get_field(field_name)
        self.field_type = type(self.field_instance)
        self.field_path = field_path
        self.field_name = field_name
        self.lookup = lookup
        # TODO: Needs to be inheritance-aware for Choices
        self.content_type = ContentType.objects.get_for_model(field_model)


class OnyxProject:
    def __init__(self, code, user, action, fields=None, scopes=None):
        """
        * Resolves `Project` and `Scope` instances for the provided `code` and `scopes`.

        * Checks `user` permissions to view and perform given `action` on these.

        * Resolves provided `fields`, determining which models they come from.

        * Checks `user` permissions to view and perform given `action` on these.
        """
        # Get and save the project instance
        try:
            self.project = Project.objects.get(code__iexact=code)
        except Project.DoesNotExist:
            raise ProjectDoesNotExist

        # Get and save the scope instances
        if scopes:
            scopes = set(scopes)
            self.scopes = []
            unknown = []
            for scope in scopes:
                try:
                    self.scopes.append(
                        Scope.objects.get(
                            project=self.project,
                            code__iexact=scope,
                            action=action,
                        )
                    )
                except Scope.DoesNotExist:
                    unknown.append(scope.lower())
            if unknown:
                raise ScopesDoNotExist(unknown)
        else:
            self.scopes = None

        # Assign model to the project
        model = self.project.content_type.model_class()
        if not model:
            raise Exception("Model could not be found when loading project")
        self.model = model

        # Check user's permission to view project and perform action on the project
        self._check_project_permissions(user, action)

        # Check user's permission to view each field provided and perform action on each field provided
        # If passed, stores information on model, contenttype, path etc for each provided field
        if fields:
            self.fields = self._get_fields_check_permissions(user, action, fields)

    def _check_project_permissions(self, user, action):
        app_label = self.project.content_type.app_label

        # Check the user's permission to view the project
        # If the user doesn't have permission, tell them it doesn't exist
        view_project_permission = f"{app_label}.view_{self.project.code}"
        if not user.has_perm(view_project_permission):
            raise ProjectDoesNotExist

        # Check the user's permission to view each scope they provided
        # If the user doesn't have permission on a scope, tell them it doesn't exist
        if self.scopes:
            unknown = []
            for scope in self.scopes:
                view_scope_permission = (
                    f"{app_label}.view_{self.project.code}-{scope.code}"
                )
                if not user.has_perm(view_scope_permission):
                    unknown.append(scope.code)

            if unknown:
                raise ScopesDoNotExist(unknown)

        # Check the user's permission to perform action on the project and the provided scopes
        # If the user is missing permissions, return the ones required
        if action != "view":
            action_permissions = [f"{app_label}.{action}_{self.project.code}"]
            if self.scopes:
                for scope in self.scopes:
                    action_permissions.append(
                        f"{app_label}.{action}_{self.project.code}-{scope.code}"
                    )
            required = [
                perm
                for perm in sorted(set(action_permissions))
                if not user.has_perm(perm)
            ]
            if required:
                raise PermissionDenied(required)

    def _get_fields_check_permissions(self, user, action, fields):
        resolved = {}
        unknown = []

        # Resolve each field
        for field in fields:
            # Check for trailing double underscore
            if field.endswith("__"):
                unknown.append(field)
                continue

            # Base model for the project
            model = self.model
            model_fields = {x.name: x for x in model._meta.get_fields()}

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
                            field_model=model,
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
                    model = component_instance.related_model

                    model_fields = {
                        x.name: x for x in model._meta.get_fields()  #  type: ignore
                    }
                    continue

                # The component is a many-to-one relationship
                elif isinstance(component_instance, ManyToOneRel):
                    if not lookup or lookup in ALL_LOOKUPS:
                        # The field is determined, and the lookup is recognised
                        # So we instantiate the resolved field instance
                        resolved[field] = OnyxField(
                            field_model=model,
                            field_path=field_path,
                            field_name=field_name,
                            lookup=lookup,
                        )
                        break

                    # These may be remaining components
                    # Move on to them
                    model = component_instance.related_model

                    model_fields = {
                        x.name: x for x in model._meta.get_fields()  #  type: ignore
                    }
                    continue

                # The component is not a relation
                else:  # not component_instance.is_relation
                    if not lookup or lookup in ALL_LOOKUPS:
                        # The field is determined, and the lookup is recognised
                        # So we instantiate the resolved field instance
                        resolved[field] = OnyxField(
                            field_model=model,
                            field_path=field_path,
                            field_name=field_name,
                            lookup=lookup,
                        )
                    else:
                        unknown.append(field)

                    break

        required = []

        app_label = self.project.content_type.app_label

        # Get and check each field permission required by the user
        for field_path, field_obj in resolved.items():
            # Check whether the user can perform the action on the field
            field_permission = (
                f"{app_label}.{action}_{self.project.code}__{field_obj.field_path}"
            )
            if not user.has_perm(field_permission):
                # If they do not have permission, check whether they can view the field
                # If they can't view the field, tell them it doesn't exist
                # If they can, return the permissions required
                view_field_permission = (
                    f"{app_label}.view_{self.project.code}__{field_obj.field_path}"
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

    def _get_fields_from_permissions(self, fields_dict, permissions):
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
        return fields_dict

    def view_fields(self):
        # Dictionary structure detailing all viewable fields based on
        # the project code and the scopes provided
        fields_dict = {}

        # Update the fields dict with all viewable fields in the base project
        self._get_fields_from_permissions(
            fields_dict,
            self.project.view_group.permissions.all(),
        )

        # For each scope
        # Update the fields dict with any additional viewable fields
        if self.scopes:
            for scope in self.scopes:
                self._get_fields_from_permissions(
                    fields_dict, scope.group.permissions.all()
                )

        return fields_dict
