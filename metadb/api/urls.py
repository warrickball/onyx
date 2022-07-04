from django.urls import path
from . import views

urlpatterns = [
    path("create/", views.create),

    # pathogen_code is known (potentially multiple records)
    path("get/<pathogen_code>/", views.get),
    path("update/<pathogen_code>/<cid>/", views.update),
    path("delete/<pathogen_code>/<cid>/", views.delete),

    # cid specific (single record)
    path("cid/get/<cid>/", views.get_cid),
    path("cid/update/<cid>/", views.update_cid),
    path("cid/delete/<cid>/", views.delete_cid)
]