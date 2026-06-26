from django.conf import settings


def modo_aplicacion(request):
    modo = getattr(settings, "ERP_APP_MODE", "integrado")
    if modo not in {"integrado", "gestion", "contabilidad"}:
        modo = "integrado"

    return {
        "erp_aplicacion": {
            "modo": modo,
            "gestion": modo in {"integrado", "gestion"},
            "contabilidad": modo in {"integrado", "contabilidad"},
        }
    }
