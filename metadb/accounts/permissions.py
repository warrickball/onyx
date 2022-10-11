from rest_framework import permissions, exceptions
from data.models import Pathogen
from accounts.models import User


class AllowAny(permissions.BasePermission):
    """
    Allow any access.
    """

    message = "Anyone should be able to do this! Let an admin know you saw this message, as its an issue with the system."

    def has_permission(self, request, view):
        return True


class IsAuthenticated(permissions.BasePermission):
    """
    Allows access only to authenticated users.
    """

    message = "You need to provide authentication credentials."

    def has_permission(self, request, view):
        return bool(request.user and getattr(request.user, "is_authenticated", False))


class IsActiveUser(permissions.BasePermission):
    """
    Allows access only to users who are still active.
    """

    message = "Your account needs to be reactivated."

    def has_permission(self, request, view):
        return bool(request.user and getattr(request.user, "is_active", False))


class IsInstituteApproved(permissions.BasePermission):
    """
    Allows access only to users that have been approved by an authority for their institute.
    """

    message = "You need to be approved by an authority from your institute."

    def has_permission(self, request, view):
        return bool(
            request.user and getattr(request.user, "is_institute_approved", False)
        )


class IsAdminApproved(permissions.BasePermission):
    """
    Allows access only to users that have been approved by an admin.
    """

    message = "You need to be approved by an admin."

    def has_permission(self, request, view):
        return bool(request.user and getattr(request.user, "is_admin_approved", False))


class IsInstituteAuthority(permissions.BasePermission):
    """
    Allows access only to users who are an authority for their institute.
    """

    message = "You need to be an authority for your institute."

    def has_permission(self, request, view):
        return bool(
            request.user and getattr(request.user, "is_institute_authority", False)
        )


class IsActiveInstitute(permissions.BasePermission):
    """
    Allows access only to users who are still in an active institute.
    """

    message = "Your institute needs to be reactivated."

    def has_permission(self, request, view):
        return bool(
            request.user
            and getattr(getattr(request.user, "institute", False), "is_active", False)
        )


class IsPHAMember(permissions.BasePermission):
    """
    Allows access only to users who are a member of a Public Health Agency.
    """

    message = "Your institute would need to be a Public Health Agency."

    def has_permission(self, request, view):
        return bool(
            request.user
            and getattr(getattr(request.user, "institute", False), "is_pha", False)
        )


class IsAdminUser(permissions.BasePermission):
    """
    Allows access only to admin users.
    """

    message = "You need to be an admin."

    def has_permission(self, request, view):
        return bool(request.user and getattr(request.user, "is_staff", False))


class IsSameInstituteAsUnsuppressedCID(permissions.BasePermission):
    """
    Allows access only to users of the same institute as the (unsuppressed) cid they are accessing.
    """

    def has_permission(self, request, view):
        cid = view.kwargs["cid"]

        try:
            obj = Pathogen.objects.get(suppressed=False, cid=cid)
        except Pathogen.DoesNotExist:
            raise exceptions.NotFound({cid: "Not found."})

        self.message = f"You need to be from institute {obj.institute.code}"

        return bool(
            request.user and getattr(request.user, "institute", False) == obj.institute
        )


class IsSameInstituteAsUser(permissions.BasePermission):
    """
    Allows access only to users of the same institute as the user they are accessing.
    """

    def has_permission(self, request, view):
        username = view.kwargs["username"]

        # Get user to be approved
        try:
            obj = User.objects.get(username=username)
        except User.DoesNotExist:
            raise exceptions.NotFound({username: "Not found."})

        self.message = f"You need to be from institute {obj.institute.code}"

        # Check that request user is in the same institute as the target user
        return bool(
            request.user and getattr(request.user, "institute", False) == obj.institute
        )
