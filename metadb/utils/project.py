from rest_framework import status
from rest_framework.response import Response
from internal.models import Project, Scope
from utils.fieldcontext import get_field_contexts
from utils.response import METADBAPIResponse
from utils.permissions import get_fields_from_permissions
from utils.errors import (
    ProjectDoesNotExist,
    ProjectPermissionError,
    ScopesDoNotExist,
    FieldsDoNotExist,
)


def init_project_queryset(model, user):
    """
    Return an initial queryset of the provided `model`.

    If `user.is_staff = True`, returns all objects, otherwise only returns objects with `suppressed = False`.
    """
    if user.is_staff:
        qs = model.objects.all()
    else:
        qs = model.objects.filter(suppressed=False)
    return qs


def init_queryset(model, view_fields):
    qs = model.objects.select_related()

    if "suppressed" not in view_fields:
        qs = qs.filter(suppressed=False)

    return qs


class ProjectAPI:
    def __init__(self, code, user, action, fields=None, scopes=None):
        # Save the user + action
        self.user = user
        self.action = action

        # Get project instance
        code = code.lower()
        try:
            self.project = Project.objects.get(code=code)
        except Project.DoesNotExist:
            raise ProjectDoesNotExist(code)

        # Get scope instance
        if scopes:
            scopes = set(scopes)
            self.scopes = []
            unknown = []
            for scope in scopes:
                scope = scope.lower()
                try:
                    self.scopes.append(
                        Scope.objects.get(
                            project=self.project,
                            code=scope,
                            action=self.action,
                        )
                    )
                except Scope.DoesNotExist:
                    unknown.append(scope)
            if unknown:
                raise ScopesDoNotExist(unknown)
        else:
            self.scopes = None

        # Assign data model to the project
        model = self.project.content_type.model_class()
        if not model:
            raise Exception("Model could not be found when loading project")
        self.model = model

        # (Parent) model and contenttype for each field in the model
        self.field_contexts = get_field_contexts(self.model)

        # Check permission to view + action on the project
        self.check_permissions()

        # Check permission to view + action on each field provided
        if fields:
            self.check_field_permissions(fields)

    def check_permissions(self):
        app_label = self.project.content_type.app_label

        # Check permission to view the project + scope
        # If the user cannot view the project + scope, then it doesn't exist
        view_project_permission = f"{app_label}.view_{self.project.code}"
        if not self.user.has_perm(view_project_permission):
            raise ProjectDoesNotExist(self.project.code)

        if self.scopes:
            view_scope_permissions = [
                f"{app_label}.view_{self.project.code}-{s.code}" for s in self.scopes
            ]
            unknown = [
                perm for perm in view_scope_permissions if not self.user.has_perm(perm)
            ]

            if unknown:
                raise ScopesDoNotExist(unknown)

        # Check permission to perform action on the project + scope
        # If the user cannot perform action, return permissions required
        action_permissions = [f"{app_label}.{self.action}_{self.project.code}"]
        if self.scopes:
            for scope in self.scopes:
                action_permissions.append(
                    f"{app_label}.{self.action}_{self.project.code}-{scope.code}"
                )

        required = [
            perm
            for perm in sorted(set(action_permissions))
            if not self.user.has_perm(perm)
        ]

        if required:
            raise ProjectPermissionError(required)

    def check_field_permissions(self, fields):
        # Get and check each permission required by the user
        required = []
        unknown = []
        for field in fields:
            if field not in self.field_contexts:
                unknown.append(field)
            else:
                field_model = self.field_contexts[field].model

                # If the user cannot view the field, it doesn't exist
                view_field_permission = f"{field_model._meta.app_label}.view_{field_model._meta.model_name}__{field}"
                if not self.user.has_perm(view_field_permission):
                    unknown.append(field)
                else:
                    # If the user cannot perform action on field, return permissions required
                    field_permission = f"{field_model._meta.app_label}.{self.action}_{field_model._meta.model_name}__{field}"
                    if not self.user.has_perm(field_permission):
                        required.append(field_permission)

        if unknown:
            raise FieldsDoNotExist(unknown)

        if required:
            raise ProjectPermissionError(required)

    @classmethod
    def not_found_response(cls, code):
        return Response(
            {code.lower(): [METADBAPIResponse.NOT_FOUND]},
            status=status.HTTP_404_NOT_FOUND,
        )

    @classmethod
    def unauthorised_response(cls, required):
        return Response(
            {"denied_permissions": sorted(set(required))},
            status=status.HTTP_403_FORBIDDEN,
        )

    @classmethod
    def unknown_scopes_response(cls, unknown):
        return Response(
            {scope: [METADBAPIResponse.UNKNOWN_SCOPE] for scope in unknown},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @classmethod
    def unknown_fields_response(cls, unknown):
        return Response(
            {field: [METADBAPIResponse.UNKNOWN_FIELD] for field in unknown},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def get_view_fields(self):
        view_fields = get_fields_from_permissions(
            self.project.view_group.permissions.all()
        )

        if self.scopes:
            for scope in self.scopes:
                view_fields += get_fields_from_permissions(
                    scope.group.permissions.all()
                )

        return set(view_fields)
