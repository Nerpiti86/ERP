from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import (
    Empresa,
    EjercicioFiscal,
    PeriodoContable,
    Sucursal,
    UsuarioEmpresa,
    UsuarioSucursal,
)


User = get_user_model()


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


class EjercicioFiscalModelTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            cuit="30712345678",
            razon_social="Empresa Demo SA",
        )

    def test_crear_ejercicio_fiscal_valido(self):
        ejercicio = EjercicioFiscal.objects.create(
            empresa=self.empresa,
            codigo="2026",
            nombre="Ejercicio fiscal 2026",
            fecha_inicio=date(2026, 1, 1),
            fecha_cierre=date(2026, 12, 31),
        )

        self.assertEqual(str(ejercicio), "Empresa Demo SA - 2026")
        self.assertEqual(ejercicio.estado, EjercicioFiscal.Estado.ABIERTO)
        self.assertTrue(ejercicio.activo)

    def test_ejercicio_rechaza_fecha_cierre_anterior_a_inicio(self):
        ejercicio = EjercicioFiscal(
            empresa=self.empresa,
            codigo="2026",
            nombre="Ejercicio fiscal 2026",
            fecha_inicio=date(2026, 12, 31),
            fecha_cierre=date(2026, 1, 1),
        )

        with self.assertRaises(ValidationError):
            ejercicio.full_clean()

    def test_codigo_ejercicio_es_unico_por_empresa(self):
        EjercicioFiscal.objects.create(
            empresa=self.empresa,
            codigo="2026",
            nombre="Ejercicio fiscal 2026",
            fecha_inicio=date(2026, 1, 1),
            fecha_cierre=date(2026, 12, 31),
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                EjercicioFiscal.objects.create(
                    empresa=self.empresa,
                    codigo="2026",
                    nombre="Ejercicio fiscal duplicado",
                    fecha_inicio=date(2026, 1, 1),
                    fecha_cierre=date(2026, 12, 31),
                )


class PeriodoContableModelTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            cuit="30712345678",
            razon_social="Empresa Demo SA",
        )
        self.ejercicio = EjercicioFiscal.objects.create(
            empresa=self.empresa,
            codigo="2026",
            nombre="Ejercicio fiscal 2026",
            fecha_inicio=date(2026, 1, 1),
            fecha_cierre=date(2026, 12, 31),
        )

    def test_crear_periodo_contable_valido(self):
        periodo = PeriodoContable.objects.create(
            ejercicio=self.ejercicio,
            codigo="2026-01",
            nombre="Enero 2026",
            fecha_inicio=date(2026, 1, 1),
            fecha_cierre=date(2026, 1, 31),
        )

        self.assertEqual(str(periodo), "Empresa Demo SA - 2026 - 2026-01")
        self.assertEqual(periodo.empresa, self.empresa)
        self.assertEqual(periodo.estado, PeriodoContable.Estado.ABIERTO)
        self.assertTrue(periodo.activo)

    def test_periodo_rechaza_fecha_cierre_anterior_a_inicio(self):
        periodo = PeriodoContable(
            ejercicio=self.ejercicio,
            codigo="2026-01",
            nombre="Enero 2026",
            fecha_inicio=date(2026, 1, 31),
            fecha_cierre=date(2026, 1, 1),
        )

        with self.assertRaises(ValidationError):
            periodo.full_clean()

    def test_periodo_rechaza_fecha_fuera_del_ejercicio(self):
        periodo = PeriodoContable(
            ejercicio=self.ejercicio,
            codigo="2027-01",
            nombre="Enero 2027",
            fecha_inicio=date(2027, 1, 1),
            fecha_cierre=date(2027, 1, 31),
        )

        with self.assertRaises(ValidationError):
            periodo.full_clean()

    def test_codigo_periodo_es_unico_por_ejercicio(self):
        PeriodoContable.objects.create(
            ejercicio=self.ejercicio,
            codigo="2026-01",
            nombre="Enero 2026",
            fecha_inicio=date(2026, 1, 1),
            fecha_cierre=date(2026, 1, 31),
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PeriodoContable.objects.create(
                    ejercicio=self.ejercicio,
                    codigo="2026-01",
                    nombre="Enero duplicado",
                    fecha_inicio=date(2026, 1, 1),
                    fecha_cierre=date(2026, 1, 31),
                )


class UsuarioEmpresaModelTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username="operador",
            email="operador@example.com",
            password="password-test",
        )
        self.empresa = Empresa.objects.create(
            cuit="30712345678",
            razon_social="Empresa Demo SA",
        )

    def test_crear_usuario_empresa_valido(self):
        acceso = UsuarioEmpresa.objects.create(
            usuario=self.usuario,
            empresa=self.empresa,
        )

        self.assertEqual(str(acceso), "operador - Empresa Demo SA")
        self.assertTrue(acceso.activo)

    def test_usuario_empresa_es_unico(self):
        UsuarioEmpresa.objects.create(
            usuario=self.usuario,
            empresa=self.empresa,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                UsuarioEmpresa.objects.create(
                    usuario=self.usuario,
                    empresa=self.empresa,
                )


class UsuarioSucursalModelTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username="operador",
            email="operador@example.com",
            password="password-test",
        )
        self.superusuario = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password-test",
        )
        self.empresa = Empresa.objects.create(
            cuit="30712345678",
            razon_social="Empresa Demo SA",
        )
        self.sucursal = Sucursal.objects.create(
            empresa=self.empresa,
            codigo="CASA",
            nombre="Casa central",
        )

    def test_crear_usuario_sucursal_valido_si_tiene_empresa_asignada(self):
        UsuarioEmpresa.objects.create(
            usuario=self.usuario,
            empresa=self.empresa,
        )

        acceso = UsuarioSucursal(
            usuario=self.usuario,
            sucursal=self.sucursal,
        )
        acceso.full_clean()
        acceso.save()

        self.assertEqual(
            str(acceso),
            "operador - Empresa Demo SA - Casa central",
        )
        self.assertEqual(acceso.empresa, self.empresa)
        self.assertTrue(acceso.activo)

    def test_usuario_sucursal_rechaza_usuario_sin_empresa_asignada(self):
        acceso = UsuarioSucursal(
            usuario=self.usuario,
            sucursal=self.sucursal,
        )

        with self.assertRaises(ValidationError):
            acceso.full_clean()

    def test_superusuario_puede_tener_sucursal_sin_asignacion_empresa(self):
        acceso = UsuarioSucursal(
            usuario=self.superusuario,
            sucursal=self.sucursal,
        )
        acceso.full_clean()
        acceso.save()

        self.assertEqual(acceso.empresa, self.empresa)

    def test_usuario_sucursal_es_unico(self):
        UsuarioEmpresa.objects.create(
            usuario=self.usuario,
            empresa=self.empresa,
        )
        UsuarioSucursal.objects.create(
            usuario=self.usuario,
            sucursal=self.sucursal,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                UsuarioSucursal.objects.create(
                    usuario=self.usuario,
                    sucursal=self.sucursal,
                )
