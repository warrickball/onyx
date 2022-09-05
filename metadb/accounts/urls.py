from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.CreateUserView.as_view()),
    path("approve/<username>/", views.approve),
    path("institute-users/", views.ListInstituteUsersView.as_view()),
    path("all-users/", views.ListAllUsersView.as_view())
]
