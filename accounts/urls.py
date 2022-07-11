from django.urls import path
from . import views

urlpatterns = [
    path("create/", views.CreateUserView.as_view()),
    path("get/", views.ListUserView.as_view()),
    path("approve/<username>/", views.approve)
]
