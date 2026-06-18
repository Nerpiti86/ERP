from django.contrib import admin

from .models import (
    Auditoria,
    DocumentoAdjunto,
    EventoNegocio,
    Empresa,
    EjercicioFiscal,
    PeriodoContable,
    ParametroSistema,
    Sucursal,
    UsuarioEmpresa,
    UsuarioSucursal,
)


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



@admin.register(ParametroSistema)
class ParametroSistemaAdmin(admin.ModelAdmin):
    list_display = (
        "clave",
        "ambito",
        "empresa",
        "tipo_valor",
        "valor",
        "activo",
    )
    list_filter = (
        "ambito",
        "tipo_valor",
        "activo",
        "empresa",
    )
    search_fields = (
        "clave",
        "valor",
        "descripcion",
        "empresa__razon_social",
        "empresa__cuit",
    )


@admin.register(Auditoria)
class AuditoriaAdmin(admin.ModelAdmin):
    list_display = (
        "creado_en",
        "empresa",
        "usuario",
        "accion",
        "tabla",
        "registro_id",
        "ip",
    )
    list_filter = (
        "accion",
        "empresa",
        "creado_en",
    )
    search_fields = (
        "tabla",
        "registro_id",
        "usuario__username",
        "usuario__email",
        "empresa__razon_social",
        "empresa__cuit",
        "ip",
        "user_agent",
    )
    date_hierarchy = "creado_en"
    list_select_related = (
        "empresa",
        "usuario",
    )
    readonly_fields = (
        "empresa",
        "usuario",
        "accion",
        "tabla",
        "registro_id",
        "datos_anteriores",
        "datos_nuevos",
        "ip",
        "user_agent",
        "creado_en",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(EventoNegocio)
class EventoNegocioAdmin(admin.ModelAdmin):
    list_display = (
        "fecha_evento",
        "empresa",
        "usuario",
        "tipo_evento",
        "entidad_tipo",
        "entidad_id",
        "estado",
    )
    list_filter = (
        "estado",
        "tipo_evento",
        "empresa",
        "fecha_evento",
    )
    search_fields = (
        "tipo_evento",
        "entidad_tipo",
        "entidad_id",
        "usuario__username",
        "usuario__email",
        "empresa__razon_social",
        "empresa__cuit",
    )
    date_hierarchy = "fecha_evento"
    list_select_related = (
        "empresa",
        "usuario",
    )
    readonly_fields = (
        "empresa",
        "usuario",
        "tipo_evento",
        "entidad_tipo",
        "entidad_id",
        "fecha_evento",
        "payload_json",
        "estado",
        "creado_en",
        "actualizado_en",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DocumentoAdjunto)
class DocumentoAdjuntoAdmin(admin.ModelAdmin):
    list_display = (
        "creado_en",
        "empresa",
        "entidad_tipo",
        "entidad_id",
        "nombre_original",
        "tipo_mime",
        "tamanio_bytes",
        "activo",
    )
    list_filter = (
        "activo",
        "empresa",
        "tipo_mime",
        "creado_en",
    )
    search_fields = (
        "nombre_original",
        "nombre_archivo",
        "ruta",
        "tipo_mime",
        "entidad_tipo",
        "entidad_id",
        "empresa__razon_social",
        "empresa__cuit",
        "usuario__username",
        "usuario__email",
    )
    date_hierarchy = "creado_en"
    list_select_related = (
        "empresa",
        "usuario",
    )
    readonly_fields = (
        "empresa",
        "entidad_tipo",
        "entidad_id",
        "nombre_original",
        "nombre_archivo",
        "tipo_mime",
        "ruta",
        "tamanio_bytes",
        "usuario",
        "activo",
        "creado_en",
        "actualizado_en",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(UsuarioEmpresa)
class UsuarioEmpresaAdmin(admin.ModelAdmin):
    list_display = (
        "usuario",
        "empresa",
        "activo",
    )
    list_filter = (
        "activo",
        "empresa",
    )
    search_fields = (
        "usuario__username",
        "usuario__email",
        "empresa__razon_social",
        "empresa__cuit",
    )


@admin.register(UsuarioSucursal)
class UsuarioSucursalAdmin(admin.ModelAdmin):
    list_display = (
        "usuario",
        "sucursal",
        "empresa",
        "activo",
    )
    list_filter = (
        "activo",
        "sucursal__empresa",
    )
    search_fields = (
        "usuario__username",
        "usuario__email",
        "sucursal__nombre",
        "sucursal__codigo",
        "sucursal__empresa__razon_social",
    )
