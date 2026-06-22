from django.db import migrations


TIPOS_DOCUMENTO = (
    ("CUIT", "CUIT", 80, True),
    ("CUIL", "CUIL", 86, True),
    ("CDI", "CDI", 87, True),
    ("LE", "Libreta de Enrolamiento", 89, True),
    ("LC", "Libreta Cívica", 90, True),
    ("PASAPORTE", "Pasaporte", 94, True),
    ("DNI", "DNI", 96, True),
    ("SIN_IDENTIFICAR", "Sin identificar", 99, False),
)


CONDICIONES_IVA = (
    ("IVA_RESPONSABLE_INSCRIPTO", "IVA Responsable Inscripto", 1),
    ("IVA_SUJETO_EXENTO", "IVA Sujeto Exento", 4),
    ("CONSUMIDOR_FINAL", "Consumidor Final", 5),
    ("RESPONSABLE_MONOTRIBUTO", "Responsable Monotributo", 6),
    ("SUJETO_NO_CATEGORIZADO", "Sujeto No Categorizado", 7),
    ("PROVEEDOR_EXTERIOR", "Proveedor del Exterior", 8),
    ("CLIENTE_EXTERIOR", "Cliente del Exterior", 9),
    ("IVA_LIBERADO_LEY_19640", "IVA Liberado - Ley N° 19.640", 10),
    ("MONOTRIBUTISTA_SOCIAL", "Monotributista Social", 13),
    ("IVA_NO_ALCANZADO", "IVA No Alcanzado", 15),
    (
        "MONOTRIBUTO_PROMOVIDO",
        "Monotributo Trabajador Independiente Promovido",
        16,
    ),
)


def cargar_catalogos(apps, schema_editor):
    TipoDocumento = apps.get_model("terceros", "TipoDocumento")
    CondicionIVA = apps.get_model("terceros", "CondicionIVA")

    for codigo, nombre, codigo_arca, requiere_numero in TIPOS_DOCUMENTO:
        TipoDocumento.objects.update_or_create(
            codigo=codigo,
            defaults={
                "nombre": nombre,
                "codigo_arca": codigo_arca,
                "requiere_numero": requiere_numero,
                "activo": True,
                "sistema": True,
            },
        )

    for codigo, nombre, codigo_arca in CONDICIONES_IVA:
        CondicionIVA.objects.update_or_create(
            codigo=codigo,
            defaults={
                "nombre": nombre,
                "codigo_arca": codigo_arca,
                "activo": True,
                "sistema": True,
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("terceros", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            cargar_catalogos,
            migrations.RunPython.noop,
        ),
    ]
