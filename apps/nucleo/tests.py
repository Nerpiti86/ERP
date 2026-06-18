from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import (
    Auditoria,
    EventoNegocio,
    Empresa,
    EjercicioFiscal,
    PeriodoContable,
    ParametroSistema,
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



class ParametroSistemaModelTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            cuit="30712345678",
            razon_social="Empresa Demo SA",
        )

    def test_crear_parametro_global_valido(self):
        parametro = ParametroSistema(
            ambito=ParametroSistema.Ambito.GLOBAL,
            clave="moneda_funcional",
            valor="ARS",
            tipo_valor=ParametroSistema.TipoValor.TEXTO,
            descripcion="Moneda funcional global.",
        )
        parametro.full_clean()
        parametro.save()

        self.assertEqual(str(parametro), "GLOBAL - moneda_funcional")
        self.assertIsNone(parametro.empresa)
        self.assertTrue(parametro.activo)

    def test_crear_parametro_empresa_valido(self):
        parametro = ParametroSistema(
            ambito=ParametroSistema.Ambito.EMPRESA,
            empresa=self.empresa,
            clave="permite_stock_negativo",
            valor="no",
            tipo_valor=ParametroSistema.TipoValor.BOOLEANO,
        )
        parametro.full_clean()
        parametro.save()

        self.assertEqual(
            str(parametro),
            "Empresa Demo SA - permite_stock_negativo",
        )
        self.assertEqual(parametro.empresa, self.empresa)

    def test_parametro_global_rechaza_empresa(self):
        parametro = ParametroSistema(
            ambito=ParametroSistema.Ambito.GLOBAL,
            empresa=self.empresa,
            clave="moneda_funcional",
            valor="ARS",
        )

        with self.assertRaises(ValidationError):
            parametro.full_clean()

    def test_parametro_empresa_requiere_empresa(self):
        parametro = ParametroSistema(
            ambito=ParametroSistema.Ambito.EMPRESA,
            clave="moneda_funcional",
            valor="ARS",
        )

        with self.assertRaises(ValidationError):
            parametro.full_clean()

    def test_clave_global_es_unica(self):
        ParametroSistema.objects.create(
            ambito=ParametroSistema.Ambito.GLOBAL,
            clave="moneda_funcional",
            valor="ARS",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ParametroSistema.objects.create(
                    ambito=ParametroSistema.Ambito.GLOBAL,
                    clave="moneda_funcional",
                    valor="USD",
                )

    def test_clave_empresa_es_unica_por_empresa(self):
        ParametroSistema.objects.create(
            ambito=ParametroSistema.Ambito.EMPRESA,
            empresa=self.empresa,
            clave="permite_stock_negativo",
            valor="no",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ParametroSistema.objects.create(
                    ambito=ParametroSistema.Ambito.EMPRESA,
                    empresa=self.empresa,
                    clave="permite_stock_negativo",
                    valor="si",
                )

    def test_misma_clave_en_empresas_distintas_es_valida(self):
        otra_empresa = Empresa.objects.create(
            cuit="30712345679",
            razon_social="Otra Empresa SA",
        )

        ParametroSistema.objects.create(
            ambito=ParametroSistema.Ambito.EMPRESA,
            empresa=self.empresa,
            clave="permite_stock_negativo",
            valor="no",
        )
        parametro = ParametroSistema.objects.create(
            ambito=ParametroSistema.Ambito.EMPRESA,
            empresa=otra_empresa,
            clave="permite_stock_negativo",
            valor="si",
        )

        self.assertEqual(parametro.empresa, otra_empresa)

    def test_valida_valor_booleano(self):
        parametro = ParametroSistema(
            ambito=ParametroSistema.Ambito.EMPRESA,
            empresa=self.empresa,
            clave="permite_stock_negativo",
            valor="tal vez",
            tipo_valor=ParametroSistema.TipoValor.BOOLEANO,
        )

        with self.assertRaises(ValidationError):
            parametro.full_clean()

    def test_valida_valor_json(self):
        parametro = ParametroSistema(
            ambito=ParametroSistema.Ambito.EMPRESA,
            empresa=self.empresa,
            clave="configuracion_json",
            valor="{invalido",
            tipo_valor=ParametroSistema.TipoValor.JSON,
        )

        with self.assertRaises(ValidationError):
            parametro.full_clean()

    def test_normaliza_clave_a_minusculas(self):
        parametro = ParametroSistema(
            ambito=ParametroSistema.Ambito.EMPRESA,
            empresa=self.empresa,
            clave="MONEDA_FUNCIONAL",
            valor="ARS",
        )
        parametro.full_clean()

        self.assertEqual(parametro.clave, "moneda_funcional")

class AuditoriaModelTests(TestCase):
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

    def test_crear_auditoria_valida(self):
        auditoria = Auditoria.objects.create(
            empresa=self.empresa,
            usuario=self.usuario,
            accion=Auditoria.Accion.INSERT,
            tabla="nucleo_empresa",
            registro_id=str(self.empresa.id),
            datos_anteriores=None,
            datos_nuevos={"razon_social": "Empresa Demo SA"},
            ip="127.0.0.1",
            user_agent="pytest",
        )

        self.assertEqual(
            str(auditoria),
            f"INSERT nucleo_empresa #{self.empresa.id}",
        )
        self.assertEqual(auditoria.empresa, self.empresa)
        self.assertEqual(auditoria.usuario, self.usuario)
        self.assertEqual(
            auditoria.datos_nuevos,
            {"razon_social": "Empresa Demo SA"},
        )

    def test_auditoria_permite_empresa_y_usuario_nulos(self):
        auditoria = Auditoria.objects.create(
            accion=Auditoria.Accion.LOGIN,
            tabla="auth_user",
            registro_id="ADMIN",
            datos_nuevos={"resultado": "ok"},
        )

        self.assertIsNone(auditoria.empresa)
        self.assertIsNone(auditoria.usuario)
        self.assertEqual(str(auditoria), "LOGIN auth_user #ADMIN")

    def test_auditoria_rechaza_accion_invalida(self):
        auditoria = Auditoria(
            empresa=self.empresa,
            usuario=self.usuario,
            accion="ACCION_INVALIDA",
            tabla="nucleo_empresa",
            registro_id=str(self.empresa.id),
        )

        with self.assertRaises(ValidationError):
            auditoria.full_clean()


class EventoNegocioModelTests(TestCase):
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

    def test_crear_evento_negocio_valido(self):
        evento = EventoNegocio.objects.create(
            empresa=self.empresa,
            usuario=self.usuario,
            tipo_evento="EMPRESA_CREADA",
            entidad_tipo="nucleo.Empresa",
            entidad_id=str(self.empresa.id),
            payload_json={"razon_social": "Empresa Demo SA"},
        )

        self.assertEqual(
            str(evento),
            f"EMPRESA_CREADA nucleo.Empresa #{self.empresa.id}",
        )
        self.assertEqual(evento.empresa, self.empresa)
        self.assertEqual(evento.usuario, self.usuario)
        self.assertEqual(evento.estado, EventoNegocio.Estado.PENDIENTE)
        self.assertIsNotNone(evento.fecha_evento)
        self.assertEqual(
            evento.payload_json,
            {"razon_social": "Empresa Demo SA"},
        )

    def test_evento_negocio_permite_empresa_y_usuario_nulos(self):
        evento = EventoNegocio.objects.create(
            tipo_evento="USUARIO_CREADO",
            entidad_tipo="auth.User",
            entidad_id="ADMIN",
            payload_json={"username": "ADMIN"},
        )

        self.assertIsNone(evento.empresa)
        self.assertIsNone(evento.usuario)
        self.assertEqual(str(evento), "USUARIO_CREADO auth.User #ADMIN")

    def test_evento_negocio_normaliza_tipo_evento_a_mayusculas(self):
        evento = EventoNegocio(
            empresa=self.empresa,
            usuario=self.usuario,
            tipo_evento=" periodo_cerrado ",
            entidad_tipo="nucleo.PeriodoContable",
            entidad_id="1",
        )

        evento.full_clean()

        self.assertEqual(evento.tipo_evento, "PERIODO_CERRADO")

    def test_evento_negocio_rechaza_tipo_evento_invalido(self):
        evento = EventoNegocio(
            empresa=self.empresa,
            usuario=self.usuario,
            tipo_evento="PERIODO CERRADO",
            entidad_tipo="nucleo.PeriodoContable",
            entidad_id="1",
        )

        with self.assertRaises(ValidationError):
            evento.full_clean()

