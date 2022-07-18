from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.CreateUserView.as_view()),
    path("list/", views.ListUserView.as_view()),
    path("list-all/", views.ListAllUserView.as_view()),
    path("approve/<username>/", views.approve)
]
