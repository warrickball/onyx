from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import CreateAPIView, ListAPIView
from django.shortcuts import get_object_or_404
from .models import User
from .serializers import UserSerializer
from utils.responses import Responses


class IsApproved(permissions.BasePermission):
    '''
    Allows access only to users that have been approved by an authority for their institute.
    '''
    message = "To perform this action, you need to be approved by an authority from your institute."

    def has_permission(self, request, view):
            return request.user.is_approved


class IsAuthority(permissions.BasePermission):
    '''
    Allows access only to users who are an authority for their institute.
    '''
    message = "To perform this action, you need to be granted permission by an admin."

    def has_permission(self, request, view):
            return request.user.is_authority


class CreateUserView(CreateAPIView):
    '''
    Create a user.
    '''
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]


class ListUserView(ListAPIView):
    '''
    List all users in the institute of the requesting user.
    '''
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsApproved]

    def get_queryset(self):
        return User.objects.filter(institute=self.request.user.institute).order_by('-date_joined') # type: ignore


class ListAllUserView(ListAPIView):
    '''
    List all users.
    '''
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return User.objects.order_by('-date_joined')


@api_view(["PATCH"])
@permission_classes([permissions.IsAuthenticated, IsApproved, IsAuthority])
def approve(request, username):
    # Get user to be approved
    target_user = get_object_or_404(User, username=username)

    # Check that request user is in the same institute as the target user
    if request.user.institute != target_user.institute:
        return Responses.different_institute

    # Approve target user
    target_user.is_approved = True
    target_user.save()
    return Responses.user_approved
