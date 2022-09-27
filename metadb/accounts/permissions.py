from rest_framework import permissions


class IsActive(permissions.BasePermission):
    """
    Allows access only to users who are still active.
    """

    message = "To perform this action, your account needs to be reactivated."

    def has_permission(self, request, view):
        return request.user.is_active


class IsApproved(permissions.BasePermission):
    """
    Allows access only to users that have been approved by an authority for their institute.
    """

    message = "To perform this action, you need to be approved by an authority from your institute."

    def has_permission(self, request, view):
        return request.user.is_approved


class IsAuthority(permissions.BasePermission):
    """
    Allows access only to users who are an authority for their institute.
    """

    message = "To perform this action, you need to be granted permission by an admin."

    def has_permission(self, request, view):
        return request.user.is_authority
