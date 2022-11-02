from rest_framework import status
from rest_framework.response import Response
from rest_framework.authentication import BasicAuthentication
from knox.views import LoginView as KnoxLoginView
from datetime import datetime
from .models import User
from .serializers import (
    UserSerializer,
    InstituteWaitingUserSerializer,
    AdminWaitingUserSerializer,
)
from utils.responses import METADBAPIResponse
from utils.views import METADBAPIView, METADBCreateAPIView, METADBListAPIView
from .permissions import (
    AllowAny,
    IsAuthenticated,
    IsActiveUser,
    IsActiveInstitute,
    IsInstituteApproved,
    IsAdminApproved,
    IsInstituteAuthority,
    IsAdminUser,
    IsSameInstituteAsUser,
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

    permission_classes = [AllowAny]
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def post(self, request, *args, **kwargs):
        # Check for first name and last name
        errors = {}
        if not request.data.get("first_name"):
            errors["first_name"] = ["This field is required."]

        if not request.data.get("last_name"):
            errors["last_name"] = ["This field is required."]

        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        # Assign the username to the request
        request.data["username"] = create_username(
            request.data["first_name"], request.data["last_name"]
        )

        # Create the user
        return super().post(request, *args, **kwargs)


class InstituteApproveView(METADBAPIView):
    """
    Grant institute approval to a user.
    """

    permission_classes = [
        IsAuthenticated,
        IsActiveInstitute,
        IsActiveUser,
        (
            [
                IsInstituteApproved,
                IsAdminApproved,
                IsInstituteAuthority,
                IsSameInstituteAsUser,
            ],
            IsAdminUser,
        ),
    ]

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
        user.is_institute_approved = True
        user.date_institute_approved = datetime.now()
        user.save(update_fields=["is_institute_approved", "date_institute_approved"])

        return Response(
            {
                "username": username,
                "is_institute_approved": user.is_institute_approved,
            },
            status=status.HTTP_200_OK,
        )


class AdminApproveView(METADBAPIView):
    """
    Grant admin approval to a user.
    """

    permission_classes = [
        IsAuthenticated,
        IsActiveInstitute,
        IsActiveUser,
        IsAdminUser,
    ]

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
        user.is_admin_approved = True
        user.save(update_fields=["is_admin_approved"])

        return Response(
            {
                "username": username,
                "is_admin_approved": user.is_admin_approved,
            },
            status=status.HTTP_200_OK,
        )


class InstituteWaitingView(METADBListAPIView):
    """
    List all users waiting for institute approval.
    """

    permission_classes = [
        IsAuthenticated,
        IsActiveInstitute,
        IsActiveUser,
        (
            [
                IsInstituteApproved,
                IsAdminApproved,
                IsInstituteAuthority,
            ],
            IsAdminUser,
        ),
    ]
    serializer_class = InstituteWaitingUserSerializer

    def get_queryset(self):
        return (
            User.objects.filter(is_active=True)
            .filter(institute=self.request.user.institute)  # type: ignore
            .filter(is_institute_approved=False)
            .order_by("-date_joined")
        )


class AdminWaitingView(METADBListAPIView):
    """
    List all users waiting for admin approval.
    """

    permission_classes = [
        IsAuthenticated,
        IsActiveInstitute,
        IsActiveUser,
        IsAdminUser,
    ]
    serializer_class = AdminWaitingUserSerializer

    def get_queryset(self):
        return (
            User.objects.filter(is_active=True)
            .filter(is_institute_approved=True)
            .filter(is_admin_approved=False)
            .order_by("-date_institute_approved")
        )


class InstituteUsersView(METADBListAPIView):
    """
    List all users in the institute of the requesting user.
    """

    permission_classes = [
        IsAuthenticated,
        IsActiveInstitute,
        IsActiveUser,
        ([IsInstituteApproved, IsAdminApproved], IsAdminUser),
    ]
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.filter(institute=self.request.user.institute).order_by("-date_joined")  # type: ignore


class AdminUsersView(METADBListAPIView):
    """
    List all users.
    """

    permission_classes = [
        IsAuthenticated,
        IsActiveInstitute,
        IsActiveUser,
        IsAdminUser,
    ]
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.order_by("-date_joined")
