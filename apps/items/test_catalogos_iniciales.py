from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from .catalogos_iniciales import (
    ALICUOTAS_IVA_INICIALES,
    UNIDADES_MEDIDA_INICIALES,
    verificar_catalogos_items_iniciales,
)
from .models import AlicuotaIVA, UnidadMedida


class CatalogosInicialesItemsTests(TestCase):
    def ejecutar_comando(self):
        salida = StringIO()
        call_command(
            "cargar_catalogos_items_iniciales",
            stdout=salida,
        )
        return salida.getvalue()

    def test_migracion_carga_catalogos_completos(self):
        self.assertEqual(
            UnidadMedida.objects.filter(sistema=True).count(),
            len(UNIDADES_MEDIDA_INICIALES),
        )
        self.assertEqual(
            AlicuotaIVA.objects.filter(sistema=True).count(),
            len(ALICUOTAS_IVA_INICIALES),
        )
        self.assertEqual(len(UNIDADES_MEDIDA_INICIALES), 46)
        self.assertEqual(len(ALICUOTAS_IVA_INICIALES), 6)

    def test_unidades_principales_tienen_codigo_arca(self):
        self.assertEqual(
            UnidadMedida.objects.get(codigo="KILOGRAMO").codigo_arca,
            1,
        )
        self.assertEqual(
            UnidadMedida.objects.get(codigo="UNIDAD").codigo_arca,
            7,
        )
        self.assertEqual(
            UnidadMedida.objects.get(codigo="PACK").codigo_arca,
            96,
        )
        self.assertEqual(
            UnidadMedida.objects.get(codigo="OTRAS_UNIDADES").codigo_arca,
            99,
        )

    def test_alicuotas_tienen_codigo_y_porcentaje_correctos(self):
        iva_21 = AlicuotaIVA.objects.get(codigo="IVA_21")
        iva_5 = AlicuotaIVA.objects.get(codigo="IVA_5")
        iva_2_5 = AlicuotaIVA.objects.get(codigo="IVA_2_5")

        self.assertEqual(iva_21.codigo_arca, 5)
        self.assertEqual(iva_21.porcentaje, Decimal("21.00"))
        self.assertEqual(iva_5.codigo_arca, 8)
        self.assertEqual(iva_5.porcentaje, Decimal("5.00"))
        self.assertEqual(iva_2_5.codigo_arca, 9)
        self.assertEqual(iva_2_5.porcentaje, Decimal("2.50"))

    def test_comando_es_idempotente(self):
        self.ejecutar_comando()
        self.ejecutar_comando()

        self.assertEqual(
            UnidadMedida.objects.filter(sistema=True).count(),
            len(UNIDADES_MEDIDA_INICIALES),
        )
        self.assertEqual(
            AlicuotaIVA.objects.filter(sistema=True).count(),
            len(ALICUOTAS_IVA_INICIALES),
        )
        self.assertEqual(verificar_catalogos_items_iniciales(), [])

    def test_comando_repara_datos_del_snapshot(self):
        UnidadMedida.objects.filter(codigo="UNIDAD").update(
            nombre="Modificada",
            activo=False,
        )
        AlicuotaIVA.objects.filter(codigo="IVA_21").update(
            porcentaje=Decimal("20.00"),
            activo=False,
        )

        salida = self.ejecutar_comando()

        unidad = UnidadMedida.objects.get(codigo="UNIDAD")
        iva_21 = AlicuotaIVA.objects.get(codigo="IVA_21")
        self.assertEqual(unidad.nombre, "Unidades")
        self.assertTrue(unidad.activo)
        self.assertEqual(iva_21.porcentaje, Decimal("21.00"))
        self.assertTrue(iva_21.activo)
        self.assertIn("cargados correctamente", salida)

    def test_comando_conserva_registros_adicionales(self):
        UnidadMedida.objects.create(
            codigo="CAJA_INTERNA",
            nombre="Caja interna",
            simbolo="caja",
            activo=True,
            sistema=False,
        )

        self.ejecutar_comando()

        self.assertTrue(
            UnidadMedida.objects.filter(codigo="CAJA_INTERNA").exists()
        )
        self.assertEqual(
            UnidadMedida.objects.filter(sistema=True).count(),
            len(UNIDADES_MEDIDA_INICIALES),
        )

    def test_verificador_detecta_desvio(self):
        AlicuotaIVA.objects.filter(codigo="IVA_10_5").update(
            nombre="Nombre incorrecto"
        )

        errores = verificar_catalogos_items_iniciales()

        self.assertTrue(
            any("IVA_10_5" in error for error in errores),
            errores,
        )
