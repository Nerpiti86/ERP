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
        "configuracion/datos-contribuyente/",
        views.datos_contribuyente,
        name="datos_contribuyente",
    ),
    path(
        "configuracion/sucursales/",
        views.sucursales,
        name="sucursales",
    ),
    path(
        "configuracion/sucursales/nueva/",
        views.sucursal_crear,
        name="sucursal_crear",
    ),
    path(
        "configuracion/sucursales/<int:sucursal_id>/editar/",
        views.sucursal_editar,
        name="sucursal_editar",
    ),
    path(
        "configuracion/actividades/",
        views.actividades_empresa,
        name="actividades_empresa",
    ),
    path(
        "configuracion/actividades/nueva/",
        views.actividad_empresa_crear,
        name="actividad_empresa_crear",
    ),
    path(
        (
            "configuracion/actividades/"
            "<int:empresa_actividad_id>/editar/"
        ),
        views.actividad_empresa_editar,
        name="actividad_empresa_editar",
    ),
    path(
        (
            "configuracion/actividades/"
            "<int:empresa_actividad_id>/inactivar/"
        ),
        views.actividad_empresa_inactivar,
        name="actividad_empresa_inactivar",
    ),
    path(
        "configuracion/actividades/catalogo/buscar/",
        views.catalogo_actividades_buscar,
        name="catalogo_actividades_buscar",
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
