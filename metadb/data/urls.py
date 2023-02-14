from django.urls import path
from . import views

urlpatterns = [
    path(
        "create/<project_code>/",
        views.CreateRecordView.as_view(),
    ),
    path(
        "testcreate/<project_code>/",
        views.CreateRecordView.as_view(),
        kwargs={"test": True},
    ),
    path(
        "get/<project_code>/",
        views.GetRecordView.as_view(),
    ),
    path(
        "query/<project_code>/",
        views.QueryRecordView.as_view(),
    ),
    path(
        "update/<project_code>/<cid>/",
        views.UpdateRecordView.as_view(),
    ),
    path(
        "testupdate/<project_code>/<cid>/",
        views.UpdateRecordView.as_view(),
        kwargs={"test": True},
    ),
    path(
        "suppress/<project_code>/<cid>/",
        views.SuppressRecordView.as_view(),
    ),
    path(
        "testsuppress/<project_code>/<cid>/",
        views.SuppressRecordView.as_view(),
        kwargs={"test": True},
    ),
    path(
        "delete/<project_code>/<cid>/",
        views.DeleteRecordView.as_view(),
    ),
    path(
        "testdelete/<project_code>/<cid>/",
        views.DeleteRecordView.as_view(),
        kwargs={"test": True},
    ),
]
