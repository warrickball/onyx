from django.urls import path, re_path
from . import views


urlpatterns = [
    path(
        "projects/",
        views.ProjectsView.as_view(),
        name="data.project.list",
    ),
    re_path(
        r"^projects/(?P<code>[a-zA-Z_]*)/fields/$",
        views.FieldsView.as_view(),
        name="data.project.fields",
    ),
    re_path(
        r"^projects/(?P<code>[a-zA-Z_]*)/choices/(?P<field>[a-zA-Z_]*)/$",
        views.ChoicesView.as_view(),
        name="data.project.choices",
    ),
    re_path(
        r"^projects/(?P<code>[a-zA-Z_]*)/$",
        views.ProjectRecordsViewSet.as_view({"post": "create", "get": "list"}),
        name="data.project",
    ),
    re_path(
        r"^projects/(?P<code>[a-zA-Z_]*)/(?P<cid>[cC]-[a-zA-Z0-9]{10})/$",
        views.ProjectRecordsViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="data.project.cid",
    ),
    re_path(
        r"^projects/(?P<code>[a-zA-Z_]*)/query/$",
        views.ProjectRecordsViewSet.as_view({"post": "list"}),
        name="data.project.query",
    ),
    re_path(
        r"^projects/(?P<code>[a-zA-Z_]*)/test/$",
        views.ProjectRecordsViewSet.as_view({"post": "create"}),
        name="data.project.test",
        kwargs={"test": True},
    ),
    re_path(
        r"^projects/(?P<code>[a-zA-Z_]*)/test/(?P<cid>[cC]-[a-zA-Z0-9]{10})/$",
        views.ProjectRecordsViewSet.as_view({"patch": "partial_update"}),
        name="data.project.test.cid",
        kwargs={"test": True},
    ),
]
