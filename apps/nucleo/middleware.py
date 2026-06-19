from .empresa_activa import (
    empresas_disponibles_para_usuario,
    obtener_empresa_activa,
)
from .sucursal_activa import (
    obtener_sucursal_activa,
    sucursales_disponibles_para_usuario,
)


class EmpresaActivaMiddleware:
    """Adjunta empresa y sucursal activas a cada request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        empresas_disponibles = empresas_disponibles_para_usuario(request.user)

        request.empresas_disponibles = empresas_disponibles
        request.empresa_activa = obtener_empresa_activa(
            request,
            empresas_disponibles=empresas_disponibles,
        )

        sucursales_disponibles = sucursales_disponibles_para_usuario(
            request.user,
            request.empresa_activa,
        )

        request.sucursales_disponibles = sucursales_disponibles
        request.sucursal_activa = obtener_sucursal_activa(
            request,
            empresa_activa=request.empresa_activa,
            sucursales_disponibles=sucursales_disponibles,
        )

        return self.get_response(request)
