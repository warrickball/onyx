from rest_framework import status
from rest_framework.response import Response
from rest_framework.authentication import BasicAuthentication
from knox.views import LoginView as KnoxLoginView
from datetime import datetime
from .models import User
from .serializers import (
    UserSerializer,
    SiteWaitingUserSerializer,
    AdminWaitingUserSerializer,
)
from utils.classes import METADBAPIResponse
from utils.views import METADBAPIView, METADBCreateAPIView, METADBListAPIView
from .permissions import (
    Any,
    Admin,
    ApprovedOrAdmin,
    SiteAuthorityOrAdmin,
    SameSiteAuthorityAsUserOrAdmin,
)


def create_username(first_name, last_name):
    return f"{last_name}{first_name[:1]}"


class LoginView(KnoxLoginView):
    """
    Login a user.
    """

    authentication_classes = [BasicAuthentication]


class CreateUserView(METADBCreateAPIView):
    """
    Create a user.
    """

    permission_classes = Any
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def post(self, request, *args, **kwargs):
        errors = {}

        if not request.data.get("first_name"):
            errors["first_name"] = ["This field is required."]

        elif not request.data.get("first_name").isalpha():
            errors["first_name"] = [
                "This field must only contain alphabetic characters."
            ]

        if not request.data.get("last_name"):
            errors["last_name"] = ["This field is required."]

        elif not request.data.get("last_name").isalpha():
            errors["last_name"] = [
                "This field must only contain alphabetic characters."
            ]

        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        # Enable mutability if required
        mutable = getattr(request.data, "_mutable", None)

        if mutable is not None:
            mutable = request.data._mutable
            request.data._mutable = True

        # Create username and add to the request
        request.data["username"] = create_username(
            request.data["first_name"], request.data["last_name"]
        )

        if mutable is not None:
            request.data._mutable = mutable

        # Create the user
        return super().post(request, *args, **kwargs)


class SiteApproveView(METADBAPIView):
    """
    Grant site approval to a user.
    """

    permission_classes = SameSiteAuthorityAsUserOrAdmin

    def patch(self, request, username):
        # Get user to be approved
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {username: METADBAPIResponse.NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Approve user
        user.site_approved = True
        user.date_site_approved = datetime.now()
        user.save(update_fields=["site_approved", "date_site_approved"])

        return Response(
            {
                "username": username,
                "site_approved": user.site_approved,
            },
            status=status.HTTP_200_OK,
        )


class AdminApproveView(METADBAPIView):
    """
    Grant admin approval to a user.
    """

    permission_classes = Admin

    def patch(self, request, username):
        # Get user to be approved
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {username: METADBAPIResponse.NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Approve target user
        user.admin_approved = True
        user.date_admin_approved = datetime.now()
        user.save(update_fields=["admin_approved", "date_admin_approved"])

        return Response(
            {
                "username": username,
                "admin_approved": user.admin_approved,
            },
            status=status.HTTP_200_OK,
        )


class SiteWaitingView(METADBListAPIView):
    """
    List all users waiting for site approval.
    """

    permission_classes = SiteAuthorityOrAdmin
    serializer_class = SiteWaitingUserSerializer

    def get_queryset(self):
        if self.request.user.is_staff:  # type: ignore
            return (
                User.objects.filter(is_active=True)
                .filter(site_approved=False)
                .order_by("-date_joined")
            )
        else:
            return (
                User.objects.filter(is_active=True)
                .filter(site=self.request.user.site)  # type: ignore
                .filter(site_approved=False)
                .order_by("-date_joined")
            )


class AdminWaitingView(METADBListAPIView):
    """
    List all users waiting for admin approval.
    """

    permission_classes = Admin
    serializer_class = AdminWaitingUserSerializer

    def get_queryset(self):
        return (
            User.objects.filter(is_active=True)
            .filter(site_approved=True)
            .filter(admin_approved=False)
            .order_by("-date_site_approved")
        )


class SiteUsersView(METADBListAPIView):
    """
    List all users in the site of the requesting user.
    """

    permission_classes = ApprovedOrAdmin
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.filter(site=self.request.user.site).order_by("-date_joined")  # type: ignore


class AdminUsersView(METADBListAPIView):
    """
    List all users.
    """

    permission_classes = Admin
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.order_by("-date_joined")
