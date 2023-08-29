from django.urls import path, re_path
from . import views


urlpatterns = [
    path(
        "",
        views.ProjectsView.as_view(),
        name="data.project.list",
    ),
    path(
        "<code>/fields/",
        views.FieldsView.as_view(),
        name="data.project.fields",
    ),
    path(
        "<code>/choices/<field>/",
        views.ChoicesView.as_view(),
        name="data.project.choices",
    ),
    path(
        "<code>/",
        views.ProjectRecordsViewSet.as_view({"post": "create", "get": "list"}),
        name="data.project",
    ),
    re_path(
        r"^(?P<code>[A-z]*)/(?P<cid>[cC]-[A-z0-9]{10})/$",
        views.ProjectRecordsViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="data.project.cid",
    ),
    path(
        "<code>/query/",
        views.ProjectRecordsViewSet.as_view({"post": "query"}),
        name="data.project.query",
    ),
    path(
        "<code>/test/",
        views.ProjectRecordsViewSet.as_view({"post": "create"}),
        name="data.project.test",
        kwargs={"test": True},
    ),
    re_path(
        r"^(?P<code>[A-z]*)/test/(?P<cid>[cC]-[A-z0-9]{10})/$",
        views.ProjectRecordsViewSet.as_view({"patch": "partial_update"}),
        name="data.project.test.cid",
        kwargs={"test": True},
    ),
]
