from django.test import TestCase

from apps.nucleo.models import Empresa

from .models import CuentaContable
from .services import crear_cuenta_contable


class CuentaContableTestCase(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            cuit="30755555558",
            razon_social="Empresa Contable SA",
        )
        self.otra_empresa = Empresa.objects.create(
            cuit="30766666668",
            razon_social="Otra Empresa Contable SA",
        )

    def crear_activo_hasta_nivel_cuatro(self, empresa=None):
        empresa = empresa or self.empresa
        raiz = crear_cuenta_contable(
            empresa=empresa,
            codigo="1.0.00.00.000",
            nombre="Activo",
            tipo_contable=CuentaContable.TipoContable.ACTIVO,
        )
        nivel_2 = crear_cuenta_contable(
            empresa=empresa,
            codigo="1.1.00.00.000",
            nombre="Activo corriente",
            tipo_contable=CuentaContable.TipoContable.ACTIVO,
        )
        nivel_3 = crear_cuenta_contable(
            empresa=empresa,
            codigo="1.1.01.00.000",
            nombre="Cajas y bancos",
            tipo_contable=CuentaContable.TipoContable.ACTIVO,
        )
        nivel_4 = crear_cuenta_contable(
            empresa=empresa,
            codigo="1.1.01.01.000",
            nombre="Cajas en moneda nacional",
            tipo_contable=CuentaContable.TipoContable.ACTIVO,
        )
        return raiz, nivel_2, nivel_3, nivel_4
