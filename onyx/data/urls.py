from django.urls import path
from . import views

urlpatterns = [
    path(
        "create/<code>/",
        views.CreateRecordView.as_view(),
        name="data.create",
    ),
    path(
        "testcreate/<code>/",
        views.CreateRecordView.as_view(),
        kwargs={"test": True},
        name="data.testcreate",
    ),
    path(
        "get/<code>/<cid>/",
        views.GetRecordView.as_view(),
        name="data.get",
    ),
    path(
        "filter/<code>/",
        views.FilterRecordView.as_view(),
    ),
    path(
        "query/<code>/",
        views.QueryRecordView.as_view(),
        name="data.filter",
    ),
    path(
        "update/<code>/<cid>/",
        views.UpdateRecordView.as_view(),
        name="data.update",
    ),
    path(
        "testupdate/<code>/<cid>/",
        views.UpdateRecordView.as_view(),
        kwargs={"test": True},
        name="data.testupdate",
    ),
    path(
        "suppress/<code>/<cid>/",
        views.SuppressRecordView.as_view(),
        name="data.suppress",
    ),
    path(
        "testsuppress/<code>/<cid>/",
        views.SuppressRecordView.as_view(),
        kwargs={"test": True},
        name="data.testsuppress",
    ),
    path(
        "delete/<code>/<cid>/",
        views.DeleteRecordView.as_view(),
        name="data.delete",
    ),
    path(
        "testdelete/<code>/<cid>/",
        views.DeleteRecordView.as_view(),
        kwargs={"test": True},
        name="data.testdelete",
    ),
    path(
        "choices/<code>/<field>/",
        views.ChoicesView.as_view(),
        name="data.choices",
    ),
]
