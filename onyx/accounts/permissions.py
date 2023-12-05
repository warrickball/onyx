from rest_framework import permissions
from rest_framework.request import Request
from .exceptions import ProjectNotFound, ScopeNotFound
from utils.functions import get_suggestions


class AllowAny(permissions.AllowAny):
    """
    Allow any access.
    """

    message = "You should be able to do this."


class AllowNobody(permissions.BasePermission):
    """
    Allow no access.
    """

    message = "This endpoint is closed."

    def has_permission(self, request: Request, view):
        return False


class IsAuthenticated(permissions.IsAuthenticated):
    """
    Allows access only to authenticated users.
    """

    message = "You need to provide authentication credentials."


class IsAdminUser(permissions.IsAdminUser):
    """
    Allows access only to admin users.
    """

    message = "You need to be an admin."


class IsActiveSite(permissions.BasePermission):
    """
    Allows access only to users who are still in an active site.
    """

    message = "Your site needs to be activated."

    def has_permission(self, request: Request, view):
        return bool(request.user and request.user.site and request.user.site.is_active)


class IsActiveUser(permissions.BasePermission):
    """
    Allows access only to users who are still active.
    """

    message = "Your account needs to be activated."

    def has_permission(self, request: Request, view):
        return bool(request.user and request.user.is_active)


class IsApproved(permissions.BasePermission):
    """
    Allows access only to users that have been approved.
    """

    message = "Your account needs to be approved."

    def has_permission(self, request: Request, view):
        return bool(
            request.user and (request.user.is_approved or request.user.is_staff)
        )


class IsObjectSite(permissions.BasePermission):
    """
    Allows access only to users of the same site as the object they are accessing.
    """

    message = "You need to be from the object's site."

    def has_object_permission(self, request: Request, view, obj):
        return bool(
            request.user
            and request.user.site
            and (request.user.site == obj.site or request.user.is_staff)
        )


class IsProjectApproved(permissions.BasePermission):
    """
    Allows access only to users who can perform action on the project + scopes they are accessing.
    """

    def has_permission(self, request: Request, view):
        project = view.kwargs["code"].lower()
        scopes = ["base"] + [
            code.lower() for code in request.query_params.getlist("scope")
        ]

        for scope in scopes:
            # Check the user's permission to perform action on the project + scope
            if not request.user.groups.filter(
                projectgroup__project__code=project,
                projectgroup__action=view.project_action,
                projectgroup__scope=scope,
            ).exists():
                # If the user doesn't have permission, check they can view the project + scope
                if (
                    view.project_action != "view"
                    and request.user.groups.filter(
                        projectgroup__project__code=project,
                        projectgroup__action="view",
                        projectgroup__scope=scope,
                    ).exists()
                ):
                    # If the user has permission to view the project + scope, then tell them they require permission for the action
                    self.message = f"You do not have permission to perform action '{view.project_action}' for scope '{scope}' on project '{project}'."
                    return False
                else:
                    # If they do not have permission to view the project + scope, tell them the project / scope doesn't exist
                    if scope == "base":
                        suggestions = get_suggestions(
                            project,
                            options=(
                                request.user.groups.filter(
                                    projectgroup__action=view.project_action
                                )
                                .values_list("projectgroup__project__code", flat=True)
                                .distinct()
                            ),
                            n=1,
                            message_prefix="Project not found.",
                        )

                        raise ProjectNotFound(suggestions)
                    else:
                        suggestions = get_suggestions(
                            scope,
                            options=(
                                request.user.groups.filter(
                                    projectgroup__project__code=project,
                                    projectgroup__action=view.project_action,
                                )
                                .values_list("projectgroup__scope", flat=True)
                                .distinct()
                            ),
                            n=1,
                            message_prefix="Scope not found.",
                        )

                        raise ScopeNotFound(suggestions)

        return True


# Useful permissions groupings
Any = [AllowAny]
Nobody = [AllowNobody]
Active = [IsAuthenticated, IsActiveSite, IsActiveUser]
Approved = Active + [IsApproved]
Admin = Approved + [IsAdminUser]
ProjectApproved = Approved + [IsProjectApproved]
ProjectAdmin = Admin + [IsProjectApproved]
