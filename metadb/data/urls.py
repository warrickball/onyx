from django.urls import path
from . import views

urlpatterns = [
    path("create/<project_code>/", views.CreateRecordView.as_view()),
    path("get/<project_code>/", views.GetRecordView.as_view()),
    path("query/<project_code>/", views.QueryRecordView.as_view()),
    path("update/<project_code>/<cid>/", views.UpdateRecordView.as_view()),
    path("suppress/<project_code>/<cid>/", views.SuppressRecordView.as_view()),
    path("delete/<project_code>/<cid>/", views.DeleteRecordView.as_view()),
    # path("testcreate/<project_code>/", views.TestCreateRecordView.as_view()),
    # path("testupdate/<project_code>/", views.TestUpdateRecordView.as_view()),
]
