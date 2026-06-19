from django.urls import path

from . import views


app_name = "nucleo"

urlpatterns = [
    path(
        "configuracion/",
        views.configuracion_empresa,
        name="configuracion_empresa",
    ),
    path(
        "configuracion/inicializar/",
        views.inicializar_configuracion_empresa,
        name="inicializar_configuracion_empresa",
    ),
]
