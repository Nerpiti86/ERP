from django.conf import settings


IDENTIDADES_APLICACION = {
    "integrado": {
        "nombre": "NeriSoft ERP",
        "producto": "ERP",
        "descripcion": "Sistema integrado de gestión y contabilidad",
    },
    "gestion": {
        "nombre": "NeriSoft Gestión",
        "producto": "Gestión",
        "descripcion": "Gestión comercial y operativa",
    },
    "contabilidad": {
        "nombre": "NeriSoft Contabilidad",
        "producto": "Contabilidad",
        "descripcion": "Gestión y representación contable",
    },
}


def modo_aplicacion(request):
    modo = getattr(settings, "ERP_APP_MODE", "integrado")
    if modo not in IDENTIDADES_APLICACION:
        modo = "integrado"

    identidad = IDENTIDADES_APLICACION[modo]

    return {
        "erp_aplicacion": {
            "modo": modo,
            "gestion": modo in {"integrado", "gestion"},
            "contabilidad": modo in {"integrado", "contabilidad"},
            **identidad,
        }
    }
