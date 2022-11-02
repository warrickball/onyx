from django.urls import path
from . import views
from knox import views as knox_views

urlpatterns = [
    path("register/", views.CreateUserView.as_view()),
    path("login/", views.LoginView.as_view(), name="knox_login"),
    path("logout/", knox_views.LogoutView.as_view(), name="knox_logout"),
    path("logoutall/", knox_views.LogoutAllView.as_view(), name="knox_logoutall"),
    path("institute/approve/<username>/", views.InstituteApproveView.as_view()),
    path("institute/waiting/", views.InstituteWaitingView.as_view()),
    path("institute/users/", views.InstituteUsersView.as_view()),
    path("admin/approve/<username>/", views.AdminApproveView.as_view()),
    path("admin/waiting/", views.AdminWaitingView.as_view()),
    path("admin/users/", views.AdminUsersView.as_view()),
]
