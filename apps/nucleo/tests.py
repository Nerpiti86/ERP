from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Empresa, Sucursal


class EmpresaModelTests(TestCase):
    def test_crear_empresa_valida(self):
        empresa = Empresa.objects.create(
            cuit="30712345678",
            razon_social="Empresa Demo SA",
            nombre_fantasia="Demo",
        )

        self.assertEqual(str(empresa), "Empresa Demo SA")
        self.assertTrue(empresa.activa)
        self.assertEqual(
            empresa.condicion_iva,
            Empresa.CondicionIVA.RESPONSABLE_INSCRIPTO,
        )

    def test_empresa_rechaza_cuit_invalido(self):
        empresa = Empresa(
            cuit="30-71234567-8",
            razon_social="Empresa Inválida SA",
        )

        with self.assertRaises(ValidationError):
            empresa.full_clean()


class SucursalModelTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            cuit="30712345678",
            razon_social="Empresa Demo SA",
        )

    def test_crear_sucursal_valida(self):
        sucursal = Sucursal.objects.create(
            empresa=self.empresa,
            codigo="CASA",
            nombre="Casa central",
            localidad="Rosario",
        )

        self.assertEqual(str(sucursal), "Empresa Demo SA - Casa central")
        self.assertTrue(sucursal.activa)
        self.assertEqual(sucursal.provincia, "Santa Fe")
        self.assertEqual(sucursal.pais, "Argentina")

    def test_codigo_sucursal_es_unico_por_empresa(self):
        Sucursal.objects.create(
            empresa=self.empresa,
            codigo="CASA",
            nombre="Casa central",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Sucursal.objects.create(
                    empresa=self.empresa,
                    codigo="CASA",
                    nombre="Otra sucursal",
                )
