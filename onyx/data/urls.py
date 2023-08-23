from django.urls import path
from . import views


urlpatterns = [
    path(
        "projects/",
        views.ProjectsView.as_view(),
        name="data.projects",
    ),
    path(
        "scopes/<code>/",
        views.ScopesView.as_view(),
        name="data.scopes",
    ),
    path(
        "fields/<code>/",
        views.FieldsView.as_view(),
        name="data.fields",
    ),
    path(
        "choices/<code>/<field>/",
        views.ChoicesView.as_view(),
        name="data.choices",
    ),
    path(
        "projects/test/<code>/",
        views.ProjectRecordsViewSet.as_view({"post": "create"}),
        name="data.projects.test.records",
        kwargs={"test": True},
    ),
    path(
        "projects/test/<code>/<cid>/",
        views.ProjectRecordsViewSet.as_view(
            {"patch": "partial_update", "delete": "destroy"}
        ),
        name="data.projects.test.records.cid",
        kwargs={"test": True},
    ),
    path(
        "projects/<code>/",
        views.ProjectRecordsViewSet.as_view({"post": "create", "get": "list"}),
        name="data.projects.records",
    ),
    path(
        "projects/<code>/query/",
        views.QueryProjectRecordsView.as_view(),
        name="data.projects.records.query",
    ),
    path(
        "projects/<code>/<cid>/",
        views.ProjectRecordsViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="data.projects.records.cid",
    ),
]
