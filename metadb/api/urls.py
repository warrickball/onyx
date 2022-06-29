from django.urls import path
from . import views

urlpatterns = [
    path("post/<model_name>/", views.post),
    path("get/<model_name>/", views.get),
    path("update/<model_name>/<cid>/", views.update),
    path("delete/<model_name>/<cid>/", views.delete)
]