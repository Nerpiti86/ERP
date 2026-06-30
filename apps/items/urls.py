from django.urls import path

from . import views


app_name = "items"

urlpatterns = [
    path("", views.item_list, name="item_list"),
    path("nuevo/", views.item_create, name="item_create"),
    path("categorias/", views.categoria_list, name="categoria_list"),
    path(
        "categorias/nueva/",
        views.categoria_create,
        name="categoria_create",
    ),
    path(
        "categorias/<int:categoria_id>/editar/",
        views.categoria_edit,
        name="categoria_edit",
    ),
    path(
        "categorias/<int:categoria_id>/inactivar/",
        views.categoria_deactivate,
        name="categoria_deactivate",
    ),
    path("marcas/", views.marca_list, name="marca_list"),
    path("marcas/nueva/", views.marca_create, name="marca_create"),
    path(
        "marcas/<int:marca_id>/editar/",
        views.marca_edit,
        name="marca_edit",
    ),
    path(
        "marcas/<int:marca_id>/inactivar/",
        views.marca_deactivate,
        name="marca_deactivate",
    ),
    path(
        "<int:item_id>/proveedores/nuevo/",
        views.item_proveedor_create,
        name="item_proveedor_create",
    ),
    path(
        "<int:item_id>/proveedores/<int:relacion_id>/editar/",
        views.item_proveedor_edit,
        name="item_proveedor_edit",
    ),
    path(
        "<int:item_id>/proveedores/<int:relacion_id>/inactivar/",
        views.item_proveedor_deactivate,
        name="item_proveedor_deactivate",
    ),
    path(
        "<int:item_id>/proveedores/<int:relacion_id>/reactivar/",
        views.item_proveedor_reactivate,
        name="item_proveedor_reactivate",
    ),
    path("<int:item_id>/", views.item_detail, name="item_detail"),
    path(
        "<int:item_id>/editar/",
        views.item_edit,
        name="item_edit",
    ),
    path(
        "<int:item_id>/reactivar/",
        views.item_reactivate,
        name="item_reactivate",
    ),
    path(
        "<int:item_id>/inactivar/",
        views.item_deactivate,
        name="item_deactivate",
    ),
]
