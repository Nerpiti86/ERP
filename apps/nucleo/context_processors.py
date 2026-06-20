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
            "parametros_ver": puede_ver_parametros,
            "parametros_editar": puede_editar_parametros,
            "contabilidad_ver": puede_ver_contabilidad,
            "contabilidad_editar": puede_editar_contabilidad,
        }
    }
