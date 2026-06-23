"""Snapshot inicial controlado de unidades de medida y alícuotas ARCA."""

from decimal import Decimal

from django.db import transaction

from .models import AlicuotaIVA, UnidadMedida


FUENTE_UNIDADES = (
    "https://www.afip.gov.ar/fe/documentos/"
    "FormatoEnvioFacturadorPlus/fp_formato_archivo_tablas.html"
)
FUENTE_ALICUOTAS = (
    "https://servicios1.afip.gov.ar/wsfev1/"
    "service.asmx?op=FEParamGetTiposIva"
)
FECHA_SNAPSHOT = "2026-06-23"


UNIDADES_MEDIDA_INICIALES = (
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


ALICUOTAS_IVA_INICIALES = (
    ("IVA_0", "IVA 0%", Decimal("0.00"), 3),
    ("IVA_10_5", "IVA 10,5%", Decimal("10.50"), 4),
    ("IVA_21", "IVA 21%", Decimal("21.00"), 5),
    ("IVA_27", "IVA 27%", Decimal("27.00"), 6),
    ("IVA_5", "IVA 5%", Decimal("5.00"), 8),
    ("IVA_2_5", "IVA 2,5%", Decimal("2.50"), 9),
)


def _obtener_unico(modelo, *, codigo, codigo_arca):
    por_codigo = (
        modelo.objects.select_for_update().filter(codigo=codigo).first()
    )
    por_arca = (
        modelo.objects.select_for_update()
        .filter(codigo_arca=codigo_arca)
        .first()
    )

    if por_codigo and por_arca and por_codigo.pk != por_arca.pk:
        raise RuntimeError(
            f"Conflicto en {modelo.__name__}: código {codigo} y "
            f"código ARCA {codigo_arca} pertenecen a registros distintos."
        )
    if por_arca and por_arca.codigo != codigo:
        raise RuntimeError(
            f"Conflicto en {modelo.__name__}: el código ARCA "
            f"{codigo_arca} ya pertenece a {por_arca.codigo}."
        )
    if (
        por_codigo
        and por_codigo.codigo_arca is not None
        and por_codigo.codigo_arca != codigo_arca
    ):
        raise RuntimeError(
            f"Conflicto en {modelo.__name__}: {codigo} ya tiene "
            f"código ARCA {por_codigo.codigo_arca}."
        )

    return por_codigo or por_arca


@transaction.atomic
def cargar_catalogos_items_iniciales():
    resumen = {
        "unidades_creadas": 0,
        "unidades_actualizadas": 0,
        "unidades_sin_cambios": 0,
        "alicuotas_creadas": 0,
        "alicuotas_actualizadas": 0,
        "alicuotas_sin_cambios": 0,
    }

    for codigo, nombre, simbolo, codigo_arca in UNIDADES_MEDIDA_INICIALES:
        unidad = _obtener_unico(
            UnidadMedida,
            codigo=codigo,
            codigo_arca=codigo_arca,
        )
        creada = unidad is None
        if creada:
            unidad = UnidadMedida(codigo=codigo)

        cambios = False
        valores = {
            "nombre": nombre,
            "simbolo": simbolo,
            "codigo_arca": codigo_arca,
            "activo": True,
            "sistema": True,
        }
        for campo, valor in valores.items():
            if getattr(unidad, campo) != valor:
                setattr(unidad, campo, valor)
                cambios = True

        unidad.full_clean()
        if creada or cambios:
            unidad.save()

        clave = (
            "unidades_creadas"
            if creada
            else "unidades_actualizadas"
            if cambios
            else "unidades_sin_cambios"
        )
        resumen[clave] += 1

    for codigo, nombre, porcentaje, codigo_arca in ALICUOTAS_IVA_INICIALES:
        alicuota = _obtener_unico(
            AlicuotaIVA,
            codigo=codigo,
            codigo_arca=codigo_arca,
        )
        creada = alicuota is None
        if creada:
            alicuota = AlicuotaIVA(codigo=codigo)

        cambios = False
        valores = {
            "nombre": nombre,
            "porcentaje": porcentaje,
            "codigo_arca": codigo_arca,
            "activo": True,
            "sistema": True,
        }
        for campo, valor in valores.items():
            if getattr(alicuota, campo) != valor:
                setattr(alicuota, campo, valor)
                cambios = True

        alicuota.full_clean()
        if creada or cambios:
            alicuota.save()

        clave = (
            "alicuotas_creadas"
            if creada
            else "alicuotas_actualizadas"
            if cambios
            else "alicuotas_sin_cambios"
        )
        resumen[clave] += 1

    return resumen


def verificar_catalogos_items_iniciales():
    errores = []

    for codigo, nombre, simbolo, codigo_arca in UNIDADES_MEDIDA_INICIALES:
        unidad = UnidadMedida.objects.filter(codigo=codigo).first()
        if unidad is None:
            errores.append(f"Falta unidad: {codigo}")
            continue

        esperados = {
            "nombre": nombre,
            "simbolo": simbolo,
            "codigo_arca": codigo_arca,
            "activo": True,
            "sistema": True,
        }
        for campo, valor in esperados.items():
            if getattr(unidad, campo) != valor:
                errores.append(
                    f"Unidad {codigo}: {campo} esperado={valor!r} "
                    f"actual={getattr(unidad, campo)!r}"
                )

    for codigo, nombre, porcentaje, codigo_arca in ALICUOTAS_IVA_INICIALES:
        alicuota = AlicuotaIVA.objects.filter(codigo=codigo).first()
        if alicuota is None:
            errores.append(f"Falta alícuota: {codigo}")
            continue

        esperados = {
            "nombre": nombre,
            "porcentaje": porcentaje,
            "codigo_arca": codigo_arca,
            "activo": True,
            "sistema": True,
        }
        for campo, valor in esperados.items():
            if getattr(alicuota, campo) != valor:
                errores.append(
                    f"Alícuota {codigo}: {campo} esperado={valor!r} "
                    f"actual={getattr(alicuota, campo)!r}"
                )

    return errores
