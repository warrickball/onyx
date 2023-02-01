from django.urls import path
from . import views

urlpatterns = [
    path("pathogens/", views.ProjectView.as_view()),
    path("<project>/query/", views.QueryPathogenView.as_view()),
    path("<project>/", views.CreateGetPathogenView.as_view()),
    path("<project>/<cid>/delete/", views.DeletePathogenView.as_view()),
    path("<project>/<cid>/", views.UpdateSuppressPathogenView.as_view()),
]
