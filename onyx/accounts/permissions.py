from rest_framework import permissions
from .exceptions import ProjectNotFound, ScopeNotFound


class AllowAny(permissions.AllowAny):
    """
    Allow any access.
    """

    message = "You should be able to do this."


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

    def has_permission(self, request, view):
        return bool(request.user and request.user.site.is_active)


class IsActiveUser(permissions.BasePermission):
    """
    Allows access only to users who are still active.
    """

    message = "Your account needs to be activated."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_active)


class IsSiteApproved(permissions.BasePermission):
    """
    Allows access only to users that have been approved by an authority for their site.
    """

    message = "You need to be approved by an authority from your site."

    def has_permission(self, request, view):
        return bool(
            request.user and (request.user.is_site_approved or request.user.is_staff)
        )


class IsAdminApproved(permissions.BasePermission):
    """
    Allows access only to users that have been approved by an admin.
    """

    message = "You need to be approved by an admin."

    def has_permission(self, request, view):
        return bool(
            request.user and (request.user.is_admin_approved or request.user.is_staff)
        )


class IsSiteAuthority(permissions.BasePermission):
    """
    Allows access only to users who are an authority for their site.
    """

    message = "You need to be an authority for your site."

    def has_permission(self, request, view):
        return bool(
            request.user and (request.user.is_site_authority or request.user.is_staff)
        )


class IsSameSiteAsObject(permissions.BasePermission):
    """
    Allows access only to users of the same site as the object they are accessing.
    """

    message = "You need to be from the object's site."

    def has_object_permission(self, request, view, obj):
        return bool(
            request.user and (request.user.site == obj.site or request.user.is_staff)
        )


class IsProjectApproved(permissions.BasePermission):
    """
    Allows access only to users who can perform action on the project + scopes they are accessing.
    """

    def has_permission(self, request, view):
        project = view.kwargs["code"].lower()
        scopes = ["base"] + [
            code.lower() for code in request.query_params.getlist("scope")
        ]

        for scope in scopes:
            # Check the user's permission to perform action on the project + scope
            if not request.user.groups.filter(
                projectgroup__project__code=project,
                projectgroup__action=view.action,
                projectgroup__scope=scope,
            ).exists():
                # If the user doesn't have permission, check they can view the project + scope
                if (
                    view.action != "view"
                    and request.user.groups.filter(
                        projectgroup__project__code=project,
                        projectgroup__action="view",
                        projectgroup__scope=scope,
                    ).exists()
                ):
                    # If the user has permission to view the project + scope, then tell them they require permission for the action
                    self.message = f"You do not have permission to perform action '{view.action}' for scope '{scope}' on project '{project}'."
                    return False
                else:
                    # If they do not have permission to view the project + scope, tell them the project / scope doesn't exist
                    if scope == "base":
                        raise ProjectNotFound
                    else:
                        raise ScopeNotFound

        return True


# Useful permissions groupings
Any = [AllowAny]
Active = [IsAuthenticated, IsActiveSite, IsActiveUser]
Approved = Active + [IsSiteApproved, IsAdminApproved]
Admin = Approved + [IsAdminUser]

SiteAuthority = Approved + [IsSiteAuthority]
SiteAuthorityForObject = SiteAuthority + [IsSameSiteAsObject]

ProjectApproved = Approved + [IsProjectApproved]
ProjectAdmin = Admin + [IsProjectApproved]
