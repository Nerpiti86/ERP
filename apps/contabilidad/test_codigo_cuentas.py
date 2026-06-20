from django.test import SimpleTestCase

from .codigo_cuentas import (
    codigo_padre_desde_codigo,
    nivel_desde_codigo,
    segmentos_desde_codigo,
)


class CodigoCuentaTests(SimpleTestCase):
    def test_detecta_los_cinco_niveles(self):
        casos = {
            "1.0.00.00.000": 1,
            "1.1.00.00.000": 2,
            "1.1.01.00.000": 3,
            "1.1.01.01.000": 4,
            "1.1.01.01.001": 5,
        }

        for codigo, nivel in casos.items():
            with self.subTest(codigo=codigo):
                self.assertEqual(nivel_desde_codigo(codigo), nivel)

    def test_rechaza_huecos_estructurales(self):
        codigos = [
            "1.0.01.00.000",
            "1.1.00.01.000",
            "1.1.01.00.001",
        ]

        for codigo in codigos:
            with self.subTest(codigo=codigo):
                self.assertIsNone(nivel_desde_codigo(codigo))

    def test_rechaza_formato_fuera_de_mascara(self):
        codigos = [
            "1.1.1.1.1",
            "1.01.01.01.001",
            "1.1.01.01.0001",
            "1-1-01-01-001",
        ]

        for codigo in codigos:
            with self.subTest(codigo=codigo):
                self.assertIsNone(segmentos_desde_codigo(codigo))

    def test_deriva_codigo_del_padre(self):
        casos = {
            "1.1.00.00.000": "1.0.00.00.000",
            "1.1.01.00.000": "1.1.00.00.000",
            "1.1.01.01.000": "1.1.01.00.000",
            "1.1.01.01.001": "1.1.01.01.000",
        }

        for codigo, padre in casos.items():
            with self.subTest(codigo=codigo):
                self.assertEqual(codigo_padre_desde_codigo(codigo), padre)

    def test_raiz_no_tiene_codigo_padre(self):
        self.assertIsNone(codigo_padre_desde_codigo("1.0.00.00.000"))
