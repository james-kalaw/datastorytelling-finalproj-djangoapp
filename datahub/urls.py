from django.urls import path

from . import views

app_name = "datahub"

urlpatterns = [
    path("", views.data_page, name="data"),
    path("download/<slug:slug>/", views.download, name="download"),
]
