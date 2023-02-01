from django.urls import path
from . import views

urlpatterns = [
    path("projects/", views.ProjectView.as_view()),
    path("create/<project>/", views.CreateProjectItemView.as_view()),
    path("get/<project>/", views.GetProjectItemView.as_view()),
    path("query/<project>/", views.QueryProjectItemView.as_view()),
    path("update/<project>/<cid>/", views.UpdateProjectItemView.as_view()),
    path("suppress/<project>/<cid>/", views.SuppressProjectItemView.as_view()),
    path("delete/<project>/<cid>/", views.DeleteProjectItemView.as_view()),
    # path("testcreate/<project>/", views.TestCreateProjectItemView.as_view()),
    # path("testupdate/<project>/", views.TestUpdateProjectItemView.as_view()),
]
