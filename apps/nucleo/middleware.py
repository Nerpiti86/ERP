from .empresa_activa import (
    empresas_disponibles_para_usuario,
    obtener_empresa_activa,
)


class EmpresaActivaMiddleware:
    """Adjunta empresas disponibles y empresa activa a cada request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        empresas_disponibles = empresas_disponibles_para_usuario(request.user)

        request.empresas_disponibles = empresas_disponibles
        request.empresa_activa = obtener_empresa_activa(
            request,
            empresas_disponibles=empresas_disponibles,
        )

        return self.get_response(request)
