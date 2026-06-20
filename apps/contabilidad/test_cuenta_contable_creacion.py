from django.core.exceptions import ValidationError

from .models import CuentaContable
from .services import crear_cuenta_contable
from .tests_support import CuentaContableTestCase


class CuentaContableCreacionTests(CuentaContableTestCase):
    def test_crea_jerarquia_valida_y_deriva_propiedades(self):
        raiz, _, _, nivel_4 = self.crear_activo_hasta_nivel_cuatro()
        caja = crear_cuenta_contable(
            empresa=self.empresa,
            codigo="1.1.01.01.001",
            nombre="  Caja   ARS  ",
            tipo_contable=CuentaContable.TipoContable.ACTIVO,
            naturaleza=CuentaContable.Naturaleza.DEUDORA,
        )

        self.assertEqual(raiz.nivel, 1)
        self.assertTrue(raiz.es_raiz)
        self.assertFalse(raiz.imputable)
        self.assertEqual(caja.nivel, 5)
        self.assertTrue(caja.imputable)
        self.assertFalse(caja.es_raiz)
        self.assertEqual(caja.codigo_padre_esperado, nivel_4.codigo)
        self.assertEqual(caja.parent, nivel_4)
        self.assertEqual(caja.nombre, "Caja ARS")

    def test_servicio_exige_que_exista_el_padre_derivado(self):
        with self.assertRaises(ValidationError) as contexto:
            crear_cuenta_contable(
                empresa=self.empresa,
                codigo="1.1.00.00.000",
                nombre="Activo corriente",
                tipo_contable=CuentaContable.TipoContable.ACTIVO,
            )

        self.assertIn("parent", contexto.exception.message_dict)

    def test_rechaza_codigo_con_hueco_estructural(self):
        with self.assertRaises(ValidationError) as contexto:
            crear_cuenta_contable(
                empresa=self.empresa,
                codigo="1.0.01.00.000",
                nombre="Codigo invalido",
                tipo_contable=CuentaContable.TipoContable.ACTIVO,
            )

        self.assertIn("codigo", contexto.exception.message_dict)

    def test_rechaza_codigo_raiz_incompatible_con_tipo(self):
        with self.assertRaises(ValidationError) as contexto:
            crear_cuenta_contable(
                empresa=self.empresa,
                codigo="2.0.00.00.000",
                nombre="Activo mal codificado",
                tipo_contable=CuentaContable.TipoContable.ACTIVO,
            )

        self.assertIn("codigo", contexto.exception.message_dict)

    def test_permite_mismo_codigo_en_empresas_distintas(self):
        cuenta_a = crear_cuenta_contable(
            empresa=self.empresa,
            codigo="1.0.00.00.000",
            nombre="Activo",
            tipo_contable=CuentaContable.TipoContable.ACTIVO,
        )
        cuenta_b = crear_cuenta_contable(
            empresa=self.otra_empresa,
            codigo="1.0.00.00.000",
            nombre="Activo",
            tipo_contable=CuentaContable.TipoContable.ACTIVO,
        )

        self.assertNotEqual(cuenta_a.pk, cuenta_b.pk)

    def test_rechaza_codigo_duplicado_en_la_misma_empresa(self):
        crear_cuenta_contable(
            empresa=self.empresa,
            codigo="1.0.00.00.000",
            nombre="Activo",
            tipo_contable=CuentaContable.TipoContable.ACTIVO,
        )

        with self.assertRaises(ValidationError):
            crear_cuenta_contable(
                empresa=self.empresa,
                codigo="1.0.00.00.000",
                nombre="Activo duplicado",
                tipo_contable=CuentaContable.TipoContable.ACTIVO,
            )

    def test_rechaza_tipo_distinto_del_padre(self):
        self.crear_activo_hasta_nivel_cuatro()

        with self.assertRaises(ValidationError) as contexto:
            crear_cuenta_contable(
                empresa=self.empresa,
                codigo="1.1.01.01.001",
                nombre="Caja ARS",
                tipo_contable=CuentaContable.TipoContable.PASIVO,
                naturaleza=CuentaContable.Naturaleza.DEUDORA,
            )

        self.assertIn("tipo_contable", contexto.exception.message_dict)

    def test_rechaza_padre_de_otra_empresa(self):
        _, _, _, nivel_4 = self.crear_activo_hasta_nivel_cuatro(
            empresa=self.otra_empresa
        )
        cuenta = CuentaContable(
            empresa=self.empresa,
            parent=nivel_4,
            codigo="1.1.01.01.001",
            nombre="Caja ARS",
            tipo_contable=CuentaContable.TipoContable.ACTIVO,
            naturaleza=CuentaContable.Naturaleza.DEUDORA,
        )

        with self.assertRaises(ValidationError) as contexto:
            cuenta.full_clean()

        self.assertIn("parent", contexto.exception.message_dict)
