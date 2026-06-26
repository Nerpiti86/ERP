from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def estado_aplicacion(request):
    return JsonResponse(
        {
            "estado": "ok",
            "aplicacion": getattr(settings, "ERP_APP_MODE", "integrado"),
        }
    )
