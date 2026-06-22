from .models import Empresa, Sucursal
from .permisos import (
    usuario_tiene_alguno_de_permisos,
    usuario_tiene_permiso,
)


def empresa_activa(request):
    return {
        "empresa_activa": getattr(request, "empresa_activa", None),
        "empresas_disponibles": getattr(
            request,
            "empresas_disponibles",
            Empresa.objects.none(),
        ),
        "sucursal_activa": getattr(request, "sucursal_activa", None),
        "sucursales_disponibles": getattr(
            request,
            "sucursales_disponibles",
            Sucursal.objects.none(),
        ),
    }


def permisos_funcionales(request):
    empresa = getattr(request, "empresa_activa", None)
    usuario = getattr(request, "user", None)

    puede_editar_empresas = usuario_tiene_permiso(
        usuario,
        empresa,
        "empresas.editar",
    )
    puede_ver_empresas = usuario_tiene_alguno_de_permisos(
        usuario,
        empresa,
        ("empresas.ver", "empresas.editar"),
    )
    puede_crear_sucursales = usuario_tiene_permiso(
        usuario,
        empresa,
        "sucursales.crear",
    )
    puede_editar_sucursales = usuario_tiene_permiso(
        usuario,
        empresa,
        "sucursales.editar",
    )
    puede_ver_sucursales = usuario_tiene_alguno_de_permisos(
        usuario,
        empresa,
        (
            "sucursales.ver",
            "sucursales.crear",
            "sucursales.editar",
        ),
    )
    puede_crear_actividades = usuario_tiene_permiso(
        usuario,
        empresa,
        "actividades.crear",
    )
    puede_editar_actividades = usuario_tiene_permiso(
        usuario,
        empresa,
        "actividades.editar",
    )
    puede_ver_actividades = usuario_tiene_alguno_de_permisos(
        usuario,
        empresa,
        (
            "actividades.ver",
            "actividades.crear",
            "actividades.editar",
        ),
    )
    puede_crear_iibb = usuario_tiene_permiso(
        usuario,
        empresa,
        "iibb.crear",
    )
    puede_editar_iibb = usuario_tiene_permiso(
        usuario,
        empresa,
        "iibb.editar",
    )
    puede_ver_iibb = usuario_tiene_alguno_de_permisos(
        usuario,
        empresa,
        (
            "iibb.ver",
            "iibb.crear",
            "iibb.editar",
        ),
    )
    puede_crear_puntos_venta = usuario_tiene_permiso(
        usuario,
        empresa,
        "puntos_venta.crear",
    )
    puede_editar_puntos_venta = usuario_tiene_permiso(
        usuario,
        empresa,
        "puntos_venta.editar",
    )
    puede_ver_puntos_venta = usuario_tiene_alguno_de_permisos(
        usuario,
        empresa,
        (
            "puntos_venta.ver",
            "puntos_venta.crear",
            "puntos_venta.editar",
        ),
    )
    puede_crear_terceros = usuario_tiene_permiso(
        usuario,
        empresa,
        "terceros.crear",
    )
    puede_editar_terceros = usuario_tiene_permiso(
        usuario,
        empresa,
        "terceros.editar",
    )
    puede_ver_terceros = usuario_tiene_alguno_de_permisos(
        usuario,
        empresa,
        (
            "terceros.ver",
            "terceros.crear",
            "terceros.editar",
        ),
    )
    puede_editar_parametros = usuario_tiene_permiso(
        usuario,
        empresa,
        "parametros.editar",
    )
    puede_ver_parametros = usuario_tiene_alguno_de_permisos(
        usuario,
        empresa,
        ("parametros.ver", "parametros.editar"),
    )
    puede_editar_contabilidad = usuario_tiene_permiso(
        usuario,
        empresa,
        "contabilidad.editar",
    )
    puede_ver_contabilidad = usuario_tiene_alguno_de_permisos(
        usuario,
        empresa,
        ("contabilidad.ver", "contabilidad.editar"),
    )

    return {
        "permisos_erp": {
            "configuracion_ver": (
                puede_ver_empresas
                or puede_ver_sucursales
                or puede_ver_actividades
                or puede_ver_iibb
                or puede_ver_puntos_venta
                or puede_ver_parametros
            ),
            "empresas_ver": puede_ver_empresas,
            "empresas_editar": puede_editar_empresas,
            "sucursales_ver": puede_ver_sucursales,
            "sucursales_crear": puede_crear_sucursales,
            "sucursales_editar": puede_editar_sucursales,
            "actividades_ver": puede_ver_actividades,
            "actividades_crear": puede_crear_actividades,
            "actividades_editar": puede_editar_actividades,
            "iibb_ver": puede_ver_iibb,
            "iibb_crear": puede_crear_iibb,
            "iibb_editar": puede_editar_iibb,
            "puntos_venta_ver": puede_ver_puntos_venta,
            "puntos_venta_crear": puede_crear_puntos_venta,
            "puntos_venta_editar": puede_editar_puntos_venta,
            "terceros_ver": puede_ver_terceros,
            "terceros_crear": puede_crear_terceros,
            "terceros_editar": puede_editar_terceros,
            "parametros_ver": puede_ver_parametros,
            "parametros_editar": puede_editar_parametros,
            "contabilidad_ver": puede_ver_contabilidad,
            "contabilidad_editar": puede_editar_contabilidad,
        }
    }
