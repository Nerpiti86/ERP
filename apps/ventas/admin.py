from django.contrib import admin

from .models import (
    ComprobanteVenta,
    ComprobanteVentaAsociado,
    ComprobanteVentaIVA,
    ComprobanteVentaLinea,
    ComprobanteVentaTributo,
    TipoComprobanteVenta,
)


class SoloLecturaAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TipoComprobanteVenta)
class TipoComprobanteVentaAdmin(SoloLecturaAdmin):
    list_display = (
        "codigo_arca",
        "nombre",
        "clase",
        "especie",
        "signo",
        "activo",
    )
    list_filter = ("activo", "clase", "especie", "signo")
    search_fields = ("codigo_arca", "nombre", "abreviatura")


class ComprobanteVentaLineaInline(admin.TabularInline):
    model = ComprobanteVentaLinea
    extra = 0
    can_delete = False
    readonly_fields = [field.name for field in ComprobanteVentaLinea._meta.fields]

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ComprobanteVenta)
class ComprobanteVentaAdmin(SoloLecturaAdmin):
    list_display = (
        "empresa",
        "fecha",
        "tipo_comprobante",
        "punto_venta",
        "numero",
        "cliente_denominacion",
        "estado",
        "total",
    )
    list_filter = ("estado", "empresa", "tipo_comprobante")
    search_fields = (
        "cliente_denominacion",
        "cliente_numero_documento",
        "numero",
    )
    list_select_related = (
        "empresa",
        "sucursal",
        "punto_venta",
        "tipo_comprobante",
        "cliente",
    )
    inlines = [ComprobanteVentaLineaInline]


@admin.register(ComprobanteVentaIVA)
class ComprobanteVentaIVAAdmin(SoloLecturaAdmin):
    list_display = ("comprobante", "alicuota_iva", "base_imponible", "importe_iva")
    list_select_related = ("comprobante", "alicuota_iva")


@admin.register(ComprobanteVentaTributo)
class ComprobanteVentaTributoAdmin(SoloLecturaAdmin):
    list_display = ("comprobante", "codigo", "nombre", "importe")
    list_select_related = ("comprobante",)


@admin.register(ComprobanteVentaAsociado)
class ComprobanteVentaAsociadoAdmin(SoloLecturaAdmin):
    list_display = ("comprobante", "comprobante_asociado", "tipo")
    list_select_related = ("comprobante", "comprobante_asociado")
