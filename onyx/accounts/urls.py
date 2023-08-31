from django.urls import path
from . import views
from knox import views as knox_views

urlpatterns = [
    path("register/", views.CreateUserView.as_view()),
    path("login/", views.LoginView.as_view(), name="knox_login"),
    path("logout/", knox_views.LogoutView.as_view(), name="knox_logout"),
    path("logoutall/", knox_views.LogoutAllView.as_view(), name="knox_logoutall"),
    path("site/approve/<username>/", views.SiteApproveView.as_view()),
    path("site/waiting/", views.SiteWaitingView.as_view()),
    path("site/users/", views.SiteUsersView.as_view()),
    path("admin/approve/<username>/", views.AdminApproveView.as_view()),
    path("admin/waiting/", views.AdminWaitingView.as_view()),
    path("admin/users/", views.AdminUsersView.as_view()),
    path("admin/projects/<username>/", views.AdminUserProjectsView.as_view()),
    path("admin/projectuser/<code>/<username>/", views.CreateProjectUserView.as_view()),
]
