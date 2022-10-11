from django.urls import path
from . import views
from knox import views as knox_views
from accounts.views import LoginView

urlpatterns = [
    path("register/", views.CreateUserView.as_view()),
    path("login/", LoginView.as_view(), name="knox_login"),
    path("logout/", knox_views.LogoutView.as_view(), name="knox_logout"),
    path("logoutall/", knox_views.LogoutAllView.as_view(), name="knox_logoutall"),
    path("institute/approve/<username>/", views.InstituteApproveView.as_view()),
    path("institute/users/", views.ListInstituteUsersView.as_view()),
    path("admin/approve/<username>/", views.AdminApproveView.as_view()),
    path("admin/users/", views.ListAllUsersView.as_view()),
]
