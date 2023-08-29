from datetime import datetime
from django.contrib.auth.models import Group
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.authentication import BasicAuthentication
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, ListAPIView
from knox.views import LoginView as KnoxLoginView
from .models import User
from .serializers import (
    CreateUserSerializer,
    ViewUserSerializer,
    SiteWaitingSerializer,
    AdminWaitingSerializer,
)
from .permissions import Any, Approved, SiteAuthority, Admin
from .exceptions import ProjectNotFound, UserNotFound


class LoginView(KnoxLoginView):
    """
    Login a user.
    """

    authentication_classes = [BasicAuthentication]


class CreateUserView(CreateAPIView):
    """
    Create a user.
    """

    permission_classes = Any
    serializer_class = CreateUserSerializer
    queryset = User.objects.all()


class SiteApproveView(APIView):
    """
    Grant site approval to a user.
    """

    permission_classes = SiteAuthority

    def patch(self, request, username):
        # Get user to be approved
        try:
            # Admins can approve users from any site
            if request.user.is_staff:
                user = User.objects.get(username=username)
            else:
                user = User.objects.filter(site=request.user.site).get(
                    username=username
                )
        except User.DoesNotExist:
            raise UserNotFound

        # Approve user
        user.is_site_approved = True
        user.when_site_approved = datetime.now()
        user.save(update_fields=["is_site_approved", "when_site_approved"])

        return Response(
            {
                "username": username,
                "is_site_approved": user.is_site_approved,
            },
        )


class AdminApproveView(APIView):
    """
    Grant admin approval to a user.
    """

    permission_classes = Admin

    def patch(self, request, username):
        # Get user to be approved
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise UserNotFound

        # Approve user
        user.is_admin_approved = True
        user.when_admin_approved = datetime.now()
        user.save(update_fields=["is_admin_approved", "when_admin_approved"])

        return Response(
            {
                "username": username,
                "is_admin_approved": user.is_admin_approved,
            },
        )


class SiteWaitingView(ListAPIView):
    """
    List all users waiting for site approval.
    """

    permission_classes = SiteAuthority
    serializer_class = SiteWaitingSerializer

    def get_queryset(self):
        # Admins can view users from any site
        if self.request.user.is_staff:  #  type: ignore
            return (
                User.objects.filter(is_active=True)
                .filter(is_site_approved=False)
                .order_by("-date_joined")
            )
        else:
            return (
                User.objects.filter(is_active=True)
                .filter(site=self.request.user.site)  # type: ignore
                .filter(is_site_approved=False)
                .order_by("-date_joined")
            )


class AdminWaitingView(ListAPIView):
    """
    List all users waiting for admin approval.
    """

    permission_classes = Admin
    serializer_class = AdminWaitingSerializer

    def get_queryset(self):
        return (
            User.objects.filter(is_active=True)
            .filter(is_site_approved=True)
            .filter(is_admin_approved=False)
            .order_by("-when_site_approved")
        )


class SiteUsersView(ListAPIView):
    """
    List all users in the site of the requesting user.
    """

    permission_classes = Approved
    serializer_class = ViewUserSerializer

    def get_queryset(self):
        return User.objects.filter(site=self.request.user.site).order_by("-date_joined")  # type: ignore


class AdminUsersView(ListAPIView):
    """
    List all users.
    """

    permission_classes = Admin
    serializer_class = ViewUserSerializer

    def get_queryset(self):
        return User.objects.order_by("-date_joined")


class AdminUserProjectsView(APIView):
    """
    Set projects that can be viewed by a user.
    """

    permission_classes = Admin

    def post(self, request, username):
        # Get user to be approved
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise UserNotFound

        if not isinstance(request.data, list):
            raise exceptions.ValidationError(
                {"detail": f"Expected a list but received type: {type(request.data)}"}
            )

        # TODO: Currently doesn't deal with granting/revoking non-base view groups
        existing_groups = user.groups.filter(
            projectgroup__action="view", projectgroup__scope="base"
        )

        groups = []
        for project in request.data:
            try:
                group = Group.objects.get(
                    projectgroup__project__code=project,
                    projectgroup__action="view",
                    projectgroup__scope="base",
                )
            except Group.DoesNotExist:
                raise ProjectNotFound
            groups.append(group)

        removed = []
        for group in existing_groups:
            if group not in groups:
                user.groups.remove(group)
                removed.append(group.name)

        added = []
        for group in groups:
            user.groups.add(group)
            added.append(group.name)

        return Response(
            {
                "username": username,
                "added": added,
                "removed": removed,
            },
        )


class CreateProjectUserView(APIView):
    permission_classes = Admin

    def post(self, request, code, username):
        pass
