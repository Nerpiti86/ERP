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
        "configuracion/parametros/",
        views.parametros_operativos,
        name="parametros_operativos",
    ),
    path(
        "configuracion/parametros/inicializar/",
        views.inicializar_configuracion_empresa,
        name="inicializar_configuracion_empresa",
    ),
]
