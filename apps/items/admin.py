from django.contrib import admin

from .models import (
    AlicuotaIVA,
    CategoriaItem,
    Item,
    ItemProveedor,
    Marca,
    UnidadMedida,
)


class SoloLecturaAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(CategoriaItem)
class CategoriaItemAdmin(SoloLecturaAdmin):
    list_display = ("empresa", "codigo", "nombre", "activo")
    list_filter = ("activo", "empresa")
    search_fields = ("codigo", "nombre", "descripcion")
    list_select_related = ("empresa",)


@admin.register(Marca)
class MarcaAdmin(SoloLecturaAdmin):
    list_display = ("empresa", "codigo", "nombre", "activo")
    list_filter = ("activo", "empresa")
    search_fields = ("codigo", "nombre")
    list_select_related = ("empresa",)


@admin.register(UnidadMedida)
class UnidadMedidaAdmin(SoloLecturaAdmin):
    list_display = ("codigo", "nombre", "simbolo", "codigo_arca", "activo")
    list_filter = ("activo", "sistema")
    search_fields = ("codigo", "nombre", "simbolo")


@admin.register(AlicuotaIVA)
class AlicuotaIVAAdmin(SoloLecturaAdmin):
    list_display = ("codigo", "nombre", "porcentaje", "codigo_arca", "activo")
    list_filter = ("activo", "sistema")
    search_fields = ("codigo", "nombre")


@admin.register(Item)
class ItemAdmin(SoloLecturaAdmin):
    list_display = (
        "empresa",
        "codigo",
        "nombre",
        "tipo",
        "se_compra",
        "se_vende",
        "controla_stock",
        "activo",
    )
    list_filter = (
        "activo",
        "tipo",
        "se_compra",
        "se_vende",
        "controla_stock",
        "tratamiento_iva",
        "empresa",
    )
    search_fields = ("codigo", "nombre", "descripcion", "observaciones")
    list_select_related = (
        "empresa",
        "categoria",
        "marca",
        "unidad_medida",
        "alicuota_iva",
    )

@admin.register(ItemProveedor)
class ItemProveedorAdmin(SoloLecturaAdmin):
    list_display = (
        "empresa",
        "item",
        "proveedor",
        "codigo_proveedor",
        "activo",
        "fecha_alta",
        "fecha_baja",
    )
    list_filter = ("activo", "empresa")
    search_fields = (
        "item__codigo",
        "item__nombre",
        "proveedor__codigo",
        "proveedor__denominacion",
        "codigo_proveedor",
    )
    list_select_related = ("empresa", "item", "proveedor")
