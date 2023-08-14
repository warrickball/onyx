from rest_framework import permissions, exceptions


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

    message = "Your site needs to be reactivated."

    def has_permission(self, request, view):
        return bool(request.user and request.user.site.is_active)


class IsActiveUser(permissions.BasePermission):
    """
    Allows access only to users who are still active.
    """

    message = "Your account needs to be reactivated."

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

    def has_object_permission(self, request, view, obj):
        self.message = f"You need to be from site {obj.site.code}."

        return bool(
            request.user and (request.user.site == obj.site or request.user.is_staff)
        )


# TODO: Maybe split this up, and not require view group on everything
class IsInProjectGroup(permissions.BasePermission):
    """
    Allows access only to users who are in the view group and the given action group for the given project.
    """

    def has_permission(self, request, view):
        project_code = view.kwargs["code"].lower()
        view_group = f"view.project.{project_code}"
        action_group = f"{view.action}.project.{project_code}"

        # Check the user's permission to view the project
        # If the project isn't found, or the user doesn't have permission, tell them it doesn't exist
        if not request.user.groups.filter(name=view_group).exists():
            raise exceptions.NotFound({"detail": "Project not found."})

        # Check the user's permission to perform action on the project
        # If the user is missing permissions, tell them
        if (
            view.action != "view"
            and not request.user.groups.filter(name=action_group).exists()
        ):
            self.message = f"You do not have permission to perform action '{view.action}' on project '{project_code}'."
            return False

        return True


class IsInScopeGroups(permissions.BasePermission):
    """
    Allows access only to users who are in the view group and the given action group for the given scope.
    """

    def has_permission(self, request, view):
        project_code = view.kwargs["code"].lower()
        scope_codes = [code.lower() for code in request.query_params.getlist("scope")]

        for scope_code in scope_codes:
            view_group = f"view.scope.{project_code}.{scope_code}"
            action_group = f"{view.action}.scope.{project_code}.{scope_code}"

            # Check the user's permission to view the scope
            # If the scope isn't found, or the user doesn't have permission, tell them it doesn't exist
            if not request.user.groups.filter(name=view_group).exists():
                raise exceptions.NotFound({"detail": "Scope not found."})

            # Check the user's permission to perform action on the scope
            # If the user is missing permissions, tell them
            if (
                view.action != "view"
                and not request.user.groups.filter(name=action_group).exists()
            ):
                self.message = f"You do not have permission to perform action '{view.action}' on scope '{scope_code}'."
                return False

        return True


# Useful permissions groupings
Any = [AllowAny]
Active = [IsAuthenticated, IsActiveSite, IsActiveUser]
Approved = Active + [IsSiteApproved, IsAdminApproved]
SiteAuthority = Approved + [IsSiteAuthority]
SiteAuthorityForObject = SiteAuthority + [IsSameSiteAsObject]
Admin = Approved + [IsAdminUser]
