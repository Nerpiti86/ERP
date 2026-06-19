from .models import Empresa, Sucursal


def empresa_activa(request):
    """Expone empresa y sucursal activas en las plantillas."""

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
