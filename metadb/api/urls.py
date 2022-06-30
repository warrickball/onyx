from django.urls import path
from . import views

urlpatterns = [
    path("create/", views.create),
    # path("<model_name>/create/", views.create),

    # model name is known
    path("get/<model_name>/", views.get),
    path("update/<model_name>/<cid>/", views.update),
    path("delete/<model_name>/<cid>/", views.delete),

    # cid specific
    path("cid/get/<cid>/", views.get_cid),
    path("cid/update/<cid>/", views.update_cid),
    path("cid/delete/<cid>/", views.delete_cid)
]