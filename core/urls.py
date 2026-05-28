from django.urls import path

from . import views

urlpatterns = [
    path("upload/", views.upload, name="upload"),
    path("records/", views.list_records, name="list-records"),
    path("records/<int:record_id>/approve/", views.approve, name="approve-record"),
    path("records/<int:record_id>/reject/", views.reject, name="reject-record"),
]
