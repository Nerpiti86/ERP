from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError

from .models import CuentaContable
from .services import crear_cuenta_contable
from .tests_support import CuentaContableTestCase


class CuentaContableReglasTests(CuentaContableTestCase):
    def test_naturaleza_es_obligatoria_para_imputable(self):
        self.crear_activo_hasta_nivel_cuatro()

        with self.assertRaises(ValidationError) as contexto:
            crear_cuenta_contable(
                empresa=self.empresa,
                codigo="1.1.01.01.001",
                nombre="Caja ARS",
                tipo_contable=CuentaContable.TipoContable.ACTIVO,
            )

        self.assertIn("naturaleza", contexto.exception.message_dict)

    def test_agrupadora_no_admite_naturaleza(self):
        crear_cuenta_contable(
            empresa=self.empresa,
            codigo="1.0.00.00.000",
            nombre="Activo",
            tipo_contable=CuentaContable.TipoContable.ACTIVO,
        )

        with self.assertRaises(ValidationError) as contexto:
            crear_cuenta_contable(
                empresa=self.empresa,
                codigo="1.1.00.00.000",
                nombre="Activo corriente",
                tipo_contable=CuentaContable.TipoContable.ACTIVO,
                naturaleza=CuentaContable.Naturaleza.DEUDORA,
            )

        self.assertIn("naturaleza", contexto.exception.message_dict)

    def test_regularizadora_admite_naturaleza_contraria(self):
        self.crear_activo_hasta_nivel_cuatro()
        prevision = crear_cuenta_contable(
            empresa=self.empresa,
            codigo="1.1.01.01.001",
            nombre="Prevision para incobrables",
            tipo_contable=CuentaContable.TipoContable.ACTIVO,
            naturaleza=CuentaContable.Naturaleza.ACREEDORA,
        )

        self.assertEqual(
            prevision.naturaleza,
            CuentaContable.Naturaleza.ACREEDORA,
        )

    def test_hijos_quedan_ordenados_por_codigo(self):
        _, _, _, nivel_4 = self.crear_activo_hasta_nivel_cuatro()
        for numero in (3, 1, 2):
            crear_cuenta_contable(
                empresa=self.empresa,
                codigo=f"1.1.01.01.{numero:03d}",
                nombre=f"Caja {numero}",
                tipo_contable=CuentaContable.TipoContable.ACTIVO,
                naturaleza=CuentaContable.Naturaleza.DEUDORA,
            )

        self.assertEqual(
            list(nivel_4.get_children().values_list("codigo", flat=True)),
            [
                "1.1.01.01.001",
                "1.1.01.01.002",
                "1.1.01.01.003",
            ],
        )

    def test_no_deshabilita_agrupadora_con_descendientes_habilitados(self):
        raiz, _, _, _ = self.crear_activo_hasta_nivel_cuatro()
        raiz.habilitada = False

        with self.assertRaises(ValidationError) as contexto:
            raiz.save(update_fields=["habilitada"])

        self.assertIn("habilitada", contexto.exception.message_dict)

    def test_no_crea_habilitada_bajo_superior_deshabilitada(self):
        raiz = crear_cuenta_contable(
            empresa=self.empresa,
            codigo="1.0.00.00.000",
            nombre="Activo",
            tipo_contable=CuentaContable.TipoContable.ACTIVO,
            habilitada=False,
        )

        with self.assertRaises(ValidationError) as contexto:
            raiz.add_child(
                empresa=self.empresa,
                codigo="1.1.00.00.000",
                nombre="Activo corriente",
                tipo_contable=CuentaContable.TipoContable.ACTIVO,
                habilitada=True,
            )

        self.assertIn("parent", contexto.exception.message_dict)

    def test_protege_superior_con_hijos_frente_a_borrado(self):
        raiz, _, _, _ = self.crear_activo_hasta_nivel_cuatro()

        with self.assertRaises(ProtectedError):
            raiz.delete()

    def test_bloquea_cambio_estructural_directo_de_rama(self):
        raiz, _, _, _ = self.crear_activo_hasta_nivel_cuatro()
        raiz.nombre = "Activo actualizado"
        raiz.save(update_fields=["nombre", "actualizada_en"])

        self.assertEqual(raiz.nombre, "Activo actualizado")

        raiz.codigo = "6.0.00.00.000"
        with self.assertRaises(ValidationError) as contexto:
            raiz.save(update_fields=["codigo", "actualizada_en"])

        self.assertIn("codigo", contexto.exception.message_dict)

    def test_no_permite_trasladar_cuenta_a_otra_empresa(self):
        raiz = crear_cuenta_contable(
            empresa=self.empresa,
            codigo="1.0.00.00.000",
            nombre="Activo",
            tipo_contable=CuentaContable.TipoContable.ACTIVO,
        )
        raiz.empresa = self.otra_empresa

        with self.assertRaises(ValidationError) as contexto:
            raiz.save(update_fields=["empresa", "actualizada_en"])

        self.assertIn("empresa", contexto.exception.message_dict)
