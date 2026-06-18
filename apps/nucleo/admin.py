from django.contrib import admin

from .models import Empresa, Sucursal


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = (
        "razon_social",
        "cuit",
        "condicion_iva",
        "activa",
    )
    list_filter = (
        "condicion_iva",
        "activa",
    )
    search_fields = (
        "razon_social",
        "nombre_fantasia",
        "cuit",
    )


@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = (
        "empresa",
        "codigo",
        "nombre",
        "localidad",
        "provincia",
        "activa",
    )
    list_filter = (
        "activa",
        "provincia",
    )
    search_fields = (
        "empresa__razon_social",
        "codigo",
        "nombre",
        "localidad",
    )
