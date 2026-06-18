from django.contrib import admin

from .models import Empresa, EjercicioFiscal, PeriodoContable, Sucursal


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


@admin.register(EjercicioFiscal)
class EjercicioFiscalAdmin(admin.ModelAdmin):
    list_display = (
        "empresa",
        "codigo",
        "nombre",
        "fecha_inicio",
        "fecha_cierre",
        "estado",
        "activo",
    )
    list_filter = (
        "estado",
        "activo",
        "empresa",
    )
    search_fields = (
        "empresa__razon_social",
        "codigo",
        "nombre",
    )
    date_hierarchy = "fecha_inicio"


@admin.register(PeriodoContable)
class PeriodoContableAdmin(admin.ModelAdmin):
    list_display = (
        "ejercicio",
        "codigo",
        "nombre",
        "fecha_inicio",
        "fecha_cierre",
        "estado",
        "activo",
    )
    list_filter = (
        "estado",
        "activo",
        "ejercicio__empresa",
    )
    search_fields = (
        "ejercicio__empresa__razon_social",
        "ejercicio__codigo",
        "codigo",
        "nombre",
    )
    date_hierarchy = "fecha_inicio"
