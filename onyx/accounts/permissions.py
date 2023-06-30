from rest_framework import permissions


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


# Useful permissions groupings
Any = [
    AllowAny,
]

Approved = [
    IsAuthenticated,
    IsActiveSite,
    IsActiveUser,
    IsSiteApproved,
    IsAdminApproved,
]

SiteAuthority = [
    IsAuthenticated,
    IsActiveSite,
    IsActiveUser,
    IsSiteApproved,
    IsAdminApproved,
    IsSiteAuthority,
]


Admin = [
    IsAuthenticated,
    IsActiveSite,
    IsActiveUser,
    IsAdminUser,
]


SiteAuthorityForObject = [
    IsAuthenticated,
    IsActiveSite,
    IsActiveUser,
    IsSiteApproved,
    IsAdminApproved,
    IsSiteAuthority,
    IsSameSiteAsObject,
]
