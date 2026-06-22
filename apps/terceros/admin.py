from django.contrib import admin

from .models import (
    CondicionIVA,
    ContactoTercero,
    DomicilioTercero,
    Tercero,
    TerceroRol,
    TipoDocumento,
)


class SoloLecturaAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TipoDocumento)
class TipoDocumentoAdmin(SoloLecturaAdmin):
    list_display = (
        "codigo",
        "nombre",
        "codigo_arca",
        "requiere_numero",
        "activo",
    )
    list_filter = ("activo", "requiere_numero")
    search_fields = ("codigo", "nombre")


@admin.register(CondicionIVA)
class CondicionIVAAdmin(SoloLecturaAdmin):
    list_display = ("codigo", "nombre", "codigo_arca", "activo")
    list_filter = ("activo",)
    search_fields = ("codigo", "nombre")


@admin.register(Tercero)
class TerceroAdmin(SoloLecturaAdmin):
    list_display = (
        "empresa",
        "codigo",
        "denominacion",
        "tipo_documento",
        "numero_documento",
        "condicion_iva",
        "activo",
    )
    list_filter = (
        "activo",
        "tipo_persona",
        "tipo_documento",
        "condicion_iva",
        "empresa",
    )
    search_fields = (
        "codigo",
        "denominacion",
        "nombre_fantasia",
        "numero_documento",
        "email",
    )
    list_select_related = (
        "empresa",
        "tipo_documento",
        "condicion_iva",
    )


@admin.register(TerceroRol)
class TerceroRolAdmin(SoloLecturaAdmin):
    list_display = ("tercero", "rol", "fecha_alta", "fecha_baja", "activo")
    list_filter = ("rol", "activo")


@admin.register(DomicilioTercero)
class DomicilioTerceroAdmin(SoloLecturaAdmin):
    list_display = (
        "tercero",
        "tipo",
        "localidad",
        "provincia",
        "principal",
        "activo",
    )
    list_filter = ("tipo", "principal", "activo", "provincia")
    search_fields = ("tercero__denominacion", "calle", "localidad")


@admin.register(ContactoTercero)
class ContactoTerceroAdmin(SoloLecturaAdmin):
    list_display = (
        "tercero",
        "nombre",
        "cargo",
        "telefono",
        "email",
        "principal",
        "activo",
    )
    list_filter = ("principal", "activo")
    search_fields = (
        "tercero__denominacion",
        "nombre",
        "telefono",
        "email",
    )
