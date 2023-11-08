from datetime import datetime
from django.contrib.auth.models import Group
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.authentication import BasicAuthentication
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, ListAPIView
from knox.views import LoginView as KnoxLoginView
from .models import User, Site
from .serializers import (
    RegisterSerializer,
    ViewUserSerializer,
    WaitingUserSerializer,
)
from .permissions import Any, Approved, Admin
from .exceptions import ProjectNotFound, UserNotFound, SiteNotFound


class RegisterView(CreateAPIView):
    """
    Register a user.
    """

    permission_classes = Any
    serializer_class = RegisterSerializer
    queryset = User.objects.all()


class LoginView(KnoxLoginView):
    """
    Login a user.
    """

    permission_classes = Approved
    authentication_classes = [BasicAuthentication]


class ProfileView(APIView):
    """
    View the user's information.
    """

    permission_classes = Approved

    def get(self, request):
        serializer = ViewUserSerializer(instance=request.user)
        return Response(serializer.data)


class WaitingUsersView(ListAPIView):
    """
    List users waiting for approval.
    """

    permission_classes = Admin
    serializer_class = WaitingUserSerializer

    def get_queryset(self):
        return (
            User.objects.filter(is_active=True)
            .filter(is_approved=False)
            .order_by("-date_joined")
        )


class ApproveUserView(APIView):
    """
    Approve a user.
    """

    permission_classes = Admin

    def patch(self, request, username):
        # Get the user to be approved
        try:
            user = User.objects.get(
                username=username,
                is_active=True,
            )
        except User.DoesNotExist:
            raise UserNotFound

        # Approve user
        user.is_approved = True
        user.when_approved = datetime.now()
        user.save(update_fields=["is_approved", "when_approved"])

        return Response(
            {
                "username": username,
                "is_approved": user.is_approved,
            },
        )


class SiteUsersView(ListAPIView):
    """
    List users in the site of the requesting user.
    """

    permission_classes = Approved
    serializer_class = ViewUserSerializer

    def get_queryset(self):
        assert isinstance(self.request.user, User)
        return User.objects.filter(
            is_approved=True,
            site=self.request.user.site,
        ).order_by("-date_joined")


class AllUsersView(ListAPIView):
    """
    List all users.
    """

    permission_classes = Admin
    serializer_class = ViewUserSerializer

    def get_queryset(self):
        return User.objects.order_by("-date_joined")


class ProjectUserView(KnoxLoginView):
    """
    Create/retrieve a user with permission to view a specific project.
    """

    permission_classes = Admin

    def post(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed(self.request.method)

    def get(self, request, code, site_code, username):
        try:
            site = Site.objects.get(code=site_code)
        except Site.DoesNotExist:
            raise SiteNotFound

        user, created = User.objects.get_or_create(
            username=username, site=site, defaults={"is_approved": True}
        )

        if created:
            user.set_unusable_password()
            user.save()
        try:
            view_group = Group.objects.get(
                projectgroup__project__code=code,
                projectgroup__action="view",
                projectgroup__scope="base",
            )
        except Group.DoesNotExist:
            raise ProjectNotFound

        user.groups.add(view_group)

        request.user = user
        return super().post(request)


class ProjectGroupsView(APIView):
    """
    Define projects that can be viewed by a user.
    """

    permission_classes = Admin

    def post(self, request, username):
        # Get user
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise UserNotFound

        if not isinstance(request.data, list):
            raise exceptions.ValidationError({"detail": f"Expected a list."})

        # Remove any project groups with a code not in the request data
        removed = []
        for group in user.groups.filter(projectgroup__isnull=False):
            if group.projectgroup.project.code not in request.data:  # type: ignore
                user.groups.remove(group)
                removed.append(group.name)

        # Add the base view group for any new project groups
        added = []
        for project in request.data:
            try:
                group = Group.objects.get(
                    projectgroup__project__code=project,
                    projectgroup__action="view",
                    projectgroup__scope="base",
                )
            except Group.DoesNotExist:
                raise ProjectNotFound

            if group not in user.groups.all():
                user.groups.add(group)
                added.append(group.name)

        return Response(
            {
                "username": username,
                "added": added,
                "removed": removed,
            },
        )
