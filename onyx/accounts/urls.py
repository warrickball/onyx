from django.urls import path, re_path
from . import views
from knox import views as knox_views

urlpatterns = [
    path("accounts/register/", views.CreateUserView.as_view()),
    path("accounts/login/", views.LoginView.as_view(), name="knox_login"),
    path("accounts/logout/", knox_views.LogoutView.as_view(), name="knox_logout"),
    path(
        "accounts/logoutall/", knox_views.LogoutAllView.as_view(), name="knox_logoutall"
    ),
    re_path(
        r"^accounts/site/approve/(?P<username>[a-zA-Z_]*)/$",
        views.SiteApproveView.as_view(),
    ),
    path("accounts/site/waiting/", views.SiteWaitingView.as_view()),
    path("accounts/site/users/", views.SiteUsersView.as_view()),
    re_path(
        r"^accounts/admin/approve/(?P<username>[a-zA-Z_]*)/$",
        views.AdminApproveView.as_view(),
    ),
    path("accounts/admin/waiting/", views.AdminWaitingView.as_view()),
    path("accounts/admin/users/", views.AdminUsersView.as_view()),
    re_path(
        r"^control/projectgroups/(?P<username>[a-zA-Z_]*)/$",
        views.ControlProjectGroupsView.as_view(),
    ),
    re_path(
        r"^control/projectuser/(?P<code>[a-zA-Z_]*)/(?P<username>[a-zA-Z_]*)/$",
        views.ControlProjectUserView.as_view(),
    ),
]
