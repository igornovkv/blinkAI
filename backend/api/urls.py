from django.urls import path
from .views import UploadView

urlpatterns = [
    path("upload/", UploadView.as_view(), name="file-upload"),
]
