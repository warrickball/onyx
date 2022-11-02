from django.urls import path
from . import views

urlpatterns = [
    path("pathogens/", views.PathogenCodeView.as_view()),
    path("<pathogen_code>/query/", views.QueryPathogenView.as_view()),
    path("<pathogen_code>/", views.CreateGetPathogenView.as_view()),
    path("<pathogen_code>/<cid>/delete/", views.DeletePathogenView.as_view()),
    path("<pathogen_code>/<cid>/", views.UpdateSuppressPathogenView.as_view()),
]
