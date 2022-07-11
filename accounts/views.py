from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import CreateAPIView, ListAPIView
from django.shortcuts import get_object_or_404
from .models import User
from .serializers import UserSerializer


class Responses:
    # Forbidden
    cannot_approve_user_diff_uploader = Response({"detail" : "cannot approve this user. they belong to a different uploader"}, status=status.HTTP_403_FORBIDDEN)


class IsUploaderApproved(permissions.BasePermission):
    '''
    Allows access only to uploader approved users.
    '''
    message = "You must be uploader approved to perform this action."

    def has_permission(self, request, view):
            return request.user.is_uploader_approved


class IsUploaderAuthority(permissions.BasePermission):
    '''
    Allows access only to users that can uploader approve other users.
    '''
    def has_permission(self, request, view):
            return request.user.is_uploader_authority


class CreateUserView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [
        permissions.AllowAny
    ]


class ListUserView(ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [
        # permissions.IsAdminUser,
        permissions.IsAuthenticated,
        IsUploaderApproved
    ]

    def get_queryset(self):
        return User.objects.filter(uploader=self.request.user.uploader).order_by('-date_joined') # type: ignore


@api_view(["PATCH"])
@permission_classes([permissions.IsAuthenticated, IsUploaderApproved, IsUploaderAuthority])
def approve(request, username):
    user = get_object_or_404(User, username=username)

    if request.user.uploader != user.uploader:
        return Responses.cannot_approve_user_diff_uploader

    user.is_uploader_approved = True
    user.save()
    return Response({"detail" : f"{user.username} has been sucessfully approved"}, status=status.HTTP_200_OK)
