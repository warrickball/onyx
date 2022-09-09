from django.urls import path
from . import views

urlpatterns = [
    path("pathogen-codes/", views.PathogenCodeView.as_view()),
    path("<pathogen_code>/", views.CreateGetPathogenView.as_view()),
    path("<pathogen_code>/<cid>/delete/", views.DeletePathogenView.as_view()),
    path("<pathogen_code>/<cid>/", views.UpdateSuppressPathogenView.as_view()),
]
