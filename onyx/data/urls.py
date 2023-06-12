from django.urls import path
from . import views

urlpatterns = [
    path(
        "create/<code>/",
        views.CreateRecordView.as_view(),
    ),
    path(
        "testcreate/<code>/",
        views.CreateRecordView.as_view(),
        kwargs={"test": True},
    ),
    path(
        "get/<code>/<cid>/",
        views.GetRecordView.as_view(),
    ),
    path(
        "filter/<code>/",
        views.FilterRecordView.as_view(),
    ),
    path(
        "query/<code>/",
        views.QueryRecordView.as_view(),
    ),
    path(
        "update/<code>/<cid>/",
        views.UpdateRecordView.as_view(),
    ),
    path(
        "testupdate/<code>/<cid>/",
        views.UpdateRecordView.as_view(),
        kwargs={"test": True},
    ),
    path(
        "suppress/<code>/<cid>/",
        views.SuppressRecordView.as_view(),
    ),
    path(
        "testsuppress/<code>/<cid>/",
        views.SuppressRecordView.as_view(),
        kwargs={"test": True},
    ),
    path(
        "delete/<code>/<cid>/",
        views.DeleteRecordView.as_view(),
    ),
    path(
        "testdelete/<code>/<cid>/",
        views.DeleteRecordView.as_view(),
        kwargs={"test": True},
    ),
    path(
        "choices/<code>/<field>/",
        views.ChoicesView.as_view(),
    ),
]
