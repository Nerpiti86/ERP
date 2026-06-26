from django.urls import path

from . import views


app_name = "terceros"

urlpatterns = [
    path("", views.tercero_list, name="tercero_list"),
    path("nuevo/", views.tercero_create, name="tercero_create"),
    path(
        "grupos/clientes/",
        views.grupo_cliente_list,
        name="grupo_cliente_list",
    ),
    path(
        "grupos/clientes/nuevo/",
        views.grupo_cliente_create,
        name="grupo_cliente_create",
    ),
    path(
        "grupos/clientes/<int:grupo_id>/editar/",
        views.grupo_cliente_edit,
        name="grupo_cliente_edit",
    ),
    path(
        "grupos/clientes/<int:grupo_id>/inactivar/",
        views.grupo_cliente_deactivate,
        name="grupo_cliente_deactivate",
    ),
    path(
        "grupos/proveedores/",
        views.grupo_proveedor_list,
        name="grupo_proveedor_list",
    ),
    path(
        "grupos/proveedores/nuevo/",
        views.grupo_proveedor_create,
        name="grupo_proveedor_create",
    ),
    path(
        "grupos/proveedores/<int:grupo_id>/editar/",
        views.grupo_proveedor_edit,
        name="grupo_proveedor_edit",
    ),
    path(
        "grupos/proveedores/<int:grupo_id>/inactivar/",
        views.grupo_proveedor_deactivate,
        name="grupo_proveedor_deactivate",
    ),
    path("<int:tercero_id>/", views.tercero_detail, name="tercero_detail"),
    path(
        "<int:tercero_id>/editar/",
        views.tercero_edit,
        name="tercero_edit",
    ),
    path(
        "<int:tercero_id>/inactivar/",
        views.tercero_deactivate,
        name="tercero_deactivate",
    ),
    path(
        "<int:tercero_id>/domicilios/nuevo/",
        views.domicilio_create,
        name="domicilio_create",
    ),
    path(
        "domicilios/<int:domicilio_id>/editar/",
        views.domicilio_edit,
        name="domicilio_edit",
    ),
    path(
        "domicilios/<int:domicilio_id>/inactivar/",
        views.domicilio_deactivate,
        name="domicilio_deactivate",
    ),
    path(
        "<int:tercero_id>/contactos/nuevo/",
        views.contacto_create,
        name="contacto_create",
    ),
    path(
        "contactos/<int:contacto_id>/editar/",
        views.contacto_edit,
        name="contacto_edit",
    ),
    path(
        "contactos/<int:contacto_id>/inactivar/",
        views.contacto_deactivate,
        name="contacto_deactivate",
    ),
]
