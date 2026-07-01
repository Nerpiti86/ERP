from django.db import migrations

from apps.ventas.catalogos_iniciales import (
    TIPOS_COMPROBANTE_VENTA_INICIALES,
)


def cargar_tipos_comprobante(apps, schema_editor):
    TipoComprobanteVenta = apps.get_model("ventas", "TipoComprobanteVenta")

    for datos in TIPOS_COMPROBANTE_VENTA_INICIALES:
        valores = {
            "nombre": datos["nombre"],
            "abreviatura": datos["abreviatura"],
            "clase": datos["clase"],
            "especie": datos["especie"],
            "signo": datos["signo"],
            "mueve_iva": datos.get("mueve_iva", True),
            "requiere_comprobante_asociado": datos.get(
                "requiere_comprobante_asociado",
                False,
            ),
            "electronico": datos.get("electronico", True),
            "activo": datos.get("activo", True),
            "sistema": True,
        }
        TipoComprobanteVenta.objects.update_or_create(
            codigo_arca=datos["codigo_arca"],
            defaults=valores,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("ventas", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            cargar_tipos_comprobante,
            migrations.RunPython.noop,
        ),
    ]
