from django.db import migrations


FUENTE_URL = "https://www.ca.gob.ar/datos-jurisdicciones"

JURISDICCIONES = (
    ("901", "Ciudad Autónoma de Buenos Aires", 1),
    ("902", "Buenos Aires", 2),
    ("903", "Catamarca", 3),
    ("904", "Córdoba", 4),
    ("905", "Corrientes", 5),
    ("906", "Chaco", 6),
    ("907", "Chubut", 7),
    ("908", "Entre Ríos", 8),
    ("909", "Formosa", 9),
    ("910", "Jujuy", 10),
    ("911", "La Pampa", 11),
    ("912", "La Rioja", 12),
    ("913", "Mendoza", 13),
    ("914", "Misiones", 14),
    ("915", "Neuquén", 15),
    ("916", "Río Negro", 16),
    ("917", "Salta", 17),
    ("918", "San Juan", 18),
    ("919", "San Luis", 19),
    ("920", "Santa Cruz", 20),
    ("921", "Santa Fe", 21),
    ("922", "Santiago del Estero", 22),
    ("923", "Tierra del Fuego", 23),
    ("924", "Tucumán", 24),
)


def cargar_jurisdicciones(apps, schema_editor):
    JurisdiccionFiscal = apps.get_model(
        "nucleo",
        "JurisdiccionFiscal",
    )

    for codigo, nombre, orden in JURISDICCIONES:
        JurisdiccionFiscal.objects.update_or_create(
            codigo=codigo,
            defaults={
                "nombre": nombre,
                "activa": True,
                "orden": orden,
                "fuente_url": FUENTE_URL,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("nucleo", "0013_ingresos_brutos_jurisdicciones"),
    ]

    operations = [
        migrations.RunPython(
            cargar_jurisdicciones,
            migrations.RunPython.noop,
        ),
    ]
