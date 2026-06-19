from .models import Empresa


def empresa_activa(request):
    """Expone la empresa activa y las empresas disponibles en plantillas."""

    return {
        "empresa_activa": getattr(request, "empresa_activa", None),
        "empresas_disponibles": getattr(
            request,
            "empresas_disponibles",
            Empresa.objects.none(),
        ),
    }
