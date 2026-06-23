from decimal import Decimal

from django.db import migrations


UNIDADES_MEDIDA = (
    ("KILOGRAMO", "Kilogramos", "kg", 1),
    ("METRO", "Metros", "m", 2),
    ("METRO_CUADRADO", "Metros cuadrados", "m²", 3),
    ("METRO_CUBICO", "Metros cúbicos", "m³", 4),
    ("LITRO", "Litros", "l", 5),
    ("MIL_KWH", "1000 kWh", "1000 kWh", 6),
    ("UNIDAD", "Unidades", "u", 7),
    ("PAR", "Pares", "par", 8),
    ("DOCENA", "Docenas", "doc", 9),
    ("QUILATE", "Quilates", "q", 10),
    ("MILLAR", "Millares", "millar", 11),
    ("GRAMO", "Gramos", "g", 14),
    ("MILIMETRO", "Milímetros", "mm", 15),
    ("MILIMETRO_CUBICO", "Milímetros cúbicos", "mm³", 16),
    ("KILOMETRO", "Kilómetros", "km", 17),
    ("HECTOLITRO", "Hectolitros", "hl", 18),
    ("CENTIMETRO", "Centímetros", "cm", 20),
    (
        "JUEGO_PAQUETE_MAZO_NAIPES",
        "Juego, paquete o mazo de naipes",
        "juego",
        25,
    ),
    ("CENTIMETRO_CUBICO", "Centímetros cúbicos", "cm³", 27),
    ("TONELADA", "Toneladas", "t", 29),
    ("DECAMETRO_CUBICO", "Decámetros cúbicos", "dam³", 30),
    ("HECTOMETRO_CUBICO", "Hectómetros cúbicos", "hm³", 31),
    ("KILOMETRO_CUBICO", "Kilómetros cúbicos", "km³", 32),
    ("MICROGRAMO", "Microgramos", "µg", 33),
    ("NANOGRAMO", "Nanogramos", "ng", 34),
    ("PICOGRAMO", "Picogramos", "pg", 35),
    ("MILIGRAMO", "Miligramos", "mg", 41),
    ("MILILITRO", "Mililitros", "ml", 47),
    ("CURIE", "Curie", "Ci", 48),
    ("MILICURIE", "Milicurie", "mCi", 49),
    ("MICROCURIE", "Microcurie", "µCi", 50),
    ("UI_ACT_HORMONAL", "UIACTHOR", "UIACTHOR", 51),
    ("MUI_ACT_HORMONAL", "MUIACTHOR", "MUIACTHOR", 52),
    ("KILOGRAMO_BASE", "Kilogramo base", "kg base", 53),
    ("GRUESA", "Gruesa", "gruesa", 54),
    ("KILOGRAMO_BRUTO", "Kilogramo bruto", "kg bruto", 61),
    ("UI_ACT_ANTIBIOTICO", "UIACTANT", "UIACTANT", 62),
    ("MUI_ACT_ANTIBIOTICO", "MUIACTANT", "MUIACTANT", 63),
    ("UI_ACT_INMUNOGLOBULINA", "UIACTIG", "UIACTIG", 64),
    ("MUI_ACT_INMUNOGLOBULINA", "MUIACTIG", "MUIACTIG", 65),
    ("KILOGRAMO_ACTIVO", "Kilogramo activo", "kg activo", 66),
    ("GRAMO_ACTIVO", "Gramo activo", "g activo", 67),
    ("GRAMO_BASE", "Gramo base", "g base", 68),
    ("PACK", "Packs", "pack", 96),
    ("HORMA", "Hormas", "horma", 97),
    ("OTRAS_UNIDADES", "Otras unidades", "otra", 99),
)


ALICUOTAS_IVA = (
    ("IVA_0", "IVA 0%", Decimal("0.00"), 3),
    ("IVA_10_5", "IVA 10,5%", Decimal("10.50"), 4),
    ("IVA_21", "IVA 21%", Decimal("21.00"), 5),
    ("IVA_27", "IVA 27%", Decimal("27.00"), 6),
    ("IVA_5", "IVA 5%", Decimal("5.00"), 8),
    ("IVA_2_5", "IVA 2,5%", Decimal("2.50"), 9),
)


def cargar_catalogos(apps, schema_editor):
    UnidadMedida = apps.get_model("items", "UnidadMedida")
    AlicuotaIVA = apps.get_model("items", "AlicuotaIVA")

    for codigo, nombre, simbolo, codigo_arca in UNIDADES_MEDIDA:
        UnidadMedida.objects.update_or_create(
            codigo=codigo,
            defaults={
                "nombre": nombre,
                "simbolo": simbolo,
                "codigo_arca": codigo_arca,
                "activo": True,
                "sistema": True,
            },
        )

    for codigo, nombre, porcentaje, codigo_arca in ALICUOTAS_IVA:
        AlicuotaIVA.objects.update_or_create(
            codigo=codigo,
            defaults={
                "nombre": nombre,
                "porcentaje": porcentaje,
                "codigo_arca": codigo_arca,
                "activo": True,
                "sistema": True,
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("items", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            cargar_catalogos,
            migrations.RunPython.noop,
        ),
    ]
