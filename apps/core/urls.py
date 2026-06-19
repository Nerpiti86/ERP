from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path(
        "empresa/seleccionar/",
        views.seleccionar_empresa,
        name="seleccionar_empresa",
    ),
]
