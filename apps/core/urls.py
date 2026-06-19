from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("ingresar/", views.iniciar_sesion, name="login"),
    path("salir/", views.cerrar_sesion, name="logout"),
    path("", views.home, name="home"),
    path(
        "empresa/seleccionar/",
        views.seleccionar_empresa,
        name="seleccionar_empresa",
    ),
    path(
        "sucursal/seleccionar/",
        views.seleccionar_sucursal,
        name="seleccionar_sucursal",
    ),
]
