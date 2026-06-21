from django.contrib import admin

from .models import (
    UsuarioRolEmpresa,
    RolPermiso,
    RolFuncional,
    PermisoFuncional,
    ActividadEconomica,
    ConfiguracionIIBBEmpresa,
    EmpresaActividad,
    EmpresaJurisdiccionIIBB,
    JurisdiccionFiscal,
    Auditoria,
    ImportacionCatalogoActividad,
    DocumentoAdjunto,
    EventoNegocio,
    Empresa,
    EjercicioFiscal,
    PeriodoContable,
    ParametroSistema,
    PerfilFiscalEmpresa,
    Sucursal,
    UsuarioEmpresa,
    UsuarioSucursal,
)


class PerfilFiscalEmpresaInline(admin.StackedInline):
    model = PerfilFiscalEmpresa
    extra = 0
    can_delete = False
    max_num = 1




@admin.register(ActividadEconomica)
class ActividadEconomicaAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "descripcion",
        "nomenclador",
        "activa",
        "ultima_sincronizacion_en",
    )
    list_filter = (
        "nomenclador",
        "activa",
    )
    search_fields = (
        "codigo",
        "descripcion",
    )
    readonly_fields = (
        "nomenclador",
        "codigo",
        "descripcion",
        "activa",
        "fuente_url",
        "fuente_sha256",
        "primera_importacion_en",
        "ultima_sincronizacion_en",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ImportacionCatalogoActividad)
class ImportacionCatalogoActividadAdmin(admin.ModelAdmin):
    list_display = (
        "importada_en",
        "nomenclador",
        "total_registros",
        "creados",
        "actualizados",
        "reactivados",
        "desactivados",
    )
    list_filter = ("nomenclador",)
    search_fields = (
        "sha256",
        "archivo_nombre",
        "fuente_url",
    )
    readonly_fields = (
        "nomenclador",
        "fuente_url",
        "archivo_nombre",
        "sha256",
        "total_registros",
        "creados",
        "actualizados",
        "reactivados",
        "desactivados",
        "importada_en",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(EmpresaActividad)
class EmpresaActividadAdmin(admin.ModelAdmin):
    list_display = (
        "empresa",
        "codigo_registrado",
        "descripcion_registrada",
        "principal",
        "activa",
        "vigencia_desde",
        "vigencia_hasta",
    )
    list_filter = (
        "activa",
        "principal",
        "nomenclador_registrado",
    )
    search_fields = (
        "empresa__razon_social",
        "empresa__cuit",
        "codigo_registrado",
        "descripcion_registrada",
    )
    readonly_fields = (
        "empresa",
        "actividad",
        "principal",
        "activa",
        "orden",
        "vigencia_desde",
        "vigencia_hasta",
        "observaciones",
        "nomenclador_registrado",
        "codigo_registrado",
        "descripcion_registrada",
        "fuente_sha256_registrada",
        "creada_en",
        "actualizada_en",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(JurisdiccionFiscal)
class JurisdiccionFiscalAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "nombre",
        "activa",
        "orden",
    )
    list_filter = ("activa",)
    search_fields = (
        "codigo",
        "nombre",
    )
    readonly_fields = (
        "codigo",
        "nombre",
        "activa",
        "orden",
        "fuente_url",
        "creada_en",
        "actualizada_en",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ConfiguracionIIBBEmpresa)
class ConfiguracionIIBBEmpresaAdmin(admin.ModelAdmin):
    list_display = (
        "empresa",
        "regimen",
        "tratamiento_general",
        "numero_inscripcion",
        "activa",
        "fecha_alta",
        "fecha_baja",
    )
    list_filter = (
        "regimen",
        "tratamiento_general",
        "activa",
    )
    search_fields = (
        "empresa__razon_social",
        "empresa__cuit",
        "numero_inscripcion",
    )
    readonly_fields = (
        "empresa",
        "regimen",
        "tratamiento_general",
        "numero_inscripcion",
        "fecha_alta",
        "fecha_baja",
        "activa",
        "observaciones",
        "creada_en",
        "actualizada_en",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(EmpresaJurisdiccionIIBB)
class EmpresaJurisdiccionIIBBAdmin(admin.ModelAdmin):
    list_display = (
        "configuracion",
        "codigo_registrado",
        "nombre_registrado",
        "sede",
        "activa",
        "fecha_alta",
        "fecha_baja",
    )
    list_filter = (
        "activa",
        "sede",
        "tratamiento",
    )
    search_fields = (
        "configuracion__empresa__razon_social",
        "configuracion__empresa__cuit",
        "codigo_registrado",
        "nombre_registrado",
    )
    readonly_fields = (
        "configuracion",
        "jurisdiccion",
        "numero_inscripcion",
        "sede",
        "tratamiento",
        "fecha_alta",
        "fecha_baja",
        "activa",
        "observaciones",
        "codigo_registrado",
        "nombre_registrado",
        "fuente_url_registrada",
        "creada_en",
        "actualizada_en",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    inlines = (PerfilFiscalEmpresaInline,)
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
        "es_casa_central",
        "es_domicilio_fiscal_nacional",
        "activa",
    )
    list_filter = (
        "activa",
        "es_casa_central",
        "es_domicilio_fiscal_nacional",
        "es_domicilio_fiscal_provincial",
        "es_domicilio_legal",
        "es_principal_actividades",
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


@admin.register(RolFuncional)
class RolFuncionalAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "activo", "sistema")
    list_filter = ("activo", "sistema")
    search_fields = ("codigo", "nombre", "descripcion")


@admin.register(PermisoFuncional)
class PermisoFuncionalAdmin(admin.ModelAdmin):
    list_display = ("codigo", "modulo", "accion", "activo")
    list_filter = ("activo", "modulo")
    search_fields = ("codigo", "modulo", "accion", "descripcion")


@admin.register(RolPermiso)
class RolPermisoAdmin(admin.ModelAdmin):
    list_display = ("rol", "permiso", "activo")
    list_filter = ("activo", "rol", "permiso__modulo")
    search_fields = (
        "rol__codigo",
        "rol__nombre",
        "permiso__codigo",
        "permiso__descripcion",
    )
    list_select_related = ("rol", "permiso")


@admin.register(UsuarioRolEmpresa)
class UsuarioRolEmpresaAdmin(admin.ModelAdmin):
    list_display = ("usuario", "empresa", "rol", "activo")
    list_filter = ("activo", "empresa", "rol")
    search_fields = (
        "usuario__username",
        "usuario__email",
        "empresa__razon_social",
        "empresa__cuit",
        "rol__codigo",
        "rol__nombre",
    )
    list_select_related = ("usuario", "empresa", "rol")


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
