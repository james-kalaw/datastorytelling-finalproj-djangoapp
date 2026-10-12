from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.overview, name="overview"),
    path("recommendations/", views.recommendations, name="recommendations"),
    path("<slug:slug>/", views.page_detail, name="page"),
]
