from django.urls import path
from . import views

urlpatterns = [
    path("get/", views.UserViewSet.as_view(actions={"get" : "list"}))
]