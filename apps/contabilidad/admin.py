from django.contrib import admin

from .models import CuentaContable


@admin.register(CuentaContable)
class CuentaContableAdmin(admin.ModelAdmin):
    list_display = (
        "empresa",
        "codigo",
        "nombre",
        "parent",
        "tipo_contable",
        "naturaleza",
        "nivel_admin",
        "imputable_admin",
        "habilitada",
    )
    list_filter = (
        "empresa",
        "tipo_contable",
        "naturaleza",
        "habilitada",
    )
    search_fields = (
        "codigo",
        "nombre",
        "descripcion",
        "empresa__razon_social",
        "empresa__nombre_fantasia",
        "empresa__cuit",
    )
    list_select_related = (
        "empresa",
        "parent",
    )
    ordering = (
        "empresa_id",
        "codigo",
    )
    readonly_fields = (
        "nivel_admin",
        "imputable_admin",
        "codigo_padre_esperado_admin",
        "creada_en",
        "actualizada_en",
    )
    fieldsets = (
        (
            "Identificacion",
            {
                "fields": (
                    "empresa",
                    "codigo",
                    "nombre",
                    "descripcion",
                )
            },
        ),
        (
            "Estructura contable",
            {
                "fields": (
                    "parent",
                    "tipo_contable",
                    "naturaleza",
                )
            },
        ),
        (
            "Estado",
            {
                "fields": (
                    "habilitada",
                )
            },
        ),
        (
            "Datos derivados",
            {
                "fields": (
                    "nivel_admin",
                    "imputable_admin",
                    "codigo_padre_esperado_admin",
                )
            },
        ),
        (
            "Auditoria tecnica",
            {
                "fields": (
                    "creada_en",
                    "actualizada_en",
                ),
                "classes": (
                    "collapse",
                ),
            },
        ),
    )
    save_on_top = True
    list_per_page = 100

    @admin.display(description="Nivel")
    def nivel_admin(self, obj):
        if obj is None:
            return None
        return obj.nivel

    @admin.display(boolean=True, description="Imputable")
    def imputable_admin(self, obj):
        if obj is None:
            return False
        return obj.imputable

    @admin.display(description="Codigo del superior esperado")
    def codigo_padre_esperado_admin(self, obj):
        if obj is None:
            return None
        return obj.codigo_padre_esperado or "Cuenta raiz"

    def has_delete_permission(self, request, obj=None):
        return False
