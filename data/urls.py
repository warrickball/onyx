from django.urls import path
from . import views

urlpatterns = [
    path("pathogen_codes/", views.PathogenCodeView.as_view()),
    path("<pathogen_code>/", views.CreateGetPathogenView.as_view()),
    path("<pathogen_code>/<cid>/", views.UpdateDeletePathogenView.as_view())
]
