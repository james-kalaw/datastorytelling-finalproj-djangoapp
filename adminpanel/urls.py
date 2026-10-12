from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "adminpanel"

urlpatterns = [
    path("login/", views.PanelLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("", views.home, name="home"),
    path("<str:key>/", views.section_view, name="section"),
    path("<str:key>/<int:pk>/delete/", views.delete_view, name="delete"),
]
