from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.nucleo.models import Auditoria

from .models import (
    ContactoTercero,
    DomicilioTercero,
    Tercero,
    TerceroRol,
)
from .services import (
    actualizar_contacto,
    actualizar_domicilio,
    actualizar_tercero,
    crear_contacto,
    crear_domicilio,
    crear_tercero,
    inactivar_contacto,
    inactivar_domicilio,
    inactivar_tercero,
)
from .tests_support import (
    crear_empresa,
    crear_request,
    crear_tercero_prueba,
    crear_usuario,
    obtener_catalogos,
)


class TerceroServicesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.empresa = crear_empresa()
        cls.otra_empresa = crear_empresa(
            cuit="30714202959",
            razon_social="Empresa Dos SA",
        )
        cls.usuario = crear_usuario()
        cls.catalogos = obtener_catalogos()

    def setUp(self):
        self.request = crear_request(self.usuario)

    def test_genera_codigo_automatico_correlativo(self):
        primero = crear_tercero_prueba(
            empresa=self.empresa,
            numero_documento="30711915695",
            denominacion="Primero SA",
            request=self.request,
        )
        segundo = crear_tercero_prueba(
            empresa=self.empresa,
            numero_documento="30714202959",
            denominacion="Segundo SA",
            request=self.request,
        )
        self.assertEqual(primero.codigo, "T000001")
        self.assertEqual(segundo.codigo, "T000002")

    def test_crea_cliente(self):
        tercero = crear_tercero_prueba(
            empresa=self.empresa,
            request=self.request,
        )
        self.assertTrue(tercero.activo)
        self.assertTrue(
            tercero.roles.filter(
                rol=TerceroRol.Rol.CLIENTE,
                activo=True,
            ).exists()
        )

    def test_crea_cliente_y_proveedor(self):
        tercero = crear_tercero_prueba(
            empresa=self.empresa,
            roles={
                TerceroRol.Rol.CLIENTE,
                TerceroRol.Rol.PROVEEDOR,
            },
            request=self.request,
        )
        self.assertEqual(
            tercero.roles.filter(activo=True).count(),
            2,
        )

    def test_rechaza_creacion_sin_roles(self):
        with self.assertRaises(ValidationError):
            crear_tercero_prueba(
                empresa=self.empresa,
                roles=set(),
                request=self.request,
            )

    def test_audita_alta(self):
        tercero = crear_tercero_prueba(
            empresa=self.empresa,
            request=self.request,
        )
        auditoria = Auditoria.objects.get(
            tabla=Tercero._meta.db_table,
            registro_id=str(tercero.pk),
            accion=Auditoria.Accion.INSERT,
        )
        self.assertEqual(auditoria.usuario, self.usuario)
        self.assertIn(
            TerceroRol.Rol.CLIENTE,
            auditoria.datos_nuevos["roles"],
        )

    def test_actualiza_identidad_y_roles(self):
        tercero = crear_tercero_prueba(
            empresa=self.empresa,
            request=self.request,
        )
        actualizado = actualizar_tercero(
            empresa=self.empresa,
            tercero=tercero,
            tipo_persona=Tercero.TipoPersona.PERSONA_JURIDICA,
            tipo_documento=self.catalogos["cuit"],
            numero_documento="30711915695",
            denominacion="Cliente Actualizado SA",
            nombre_fantasia="Actualizado",
            condicion_iva=self.catalogos["ri"],
            telefono="3415551111",
            email="nuevo@example.com",
            sitio_web="",
            fecha_alta="2026-06-21",
            roles={TerceroRol.Rol.PROVEEDOR},
            observaciones="Actualizado",
            request=self.request,
        )
        self.assertEqual(
            actualizado.denominacion,
            "Cliente Actualizado SA",
        )
        self.assertFalse(
            actualizado.roles.filter(
                rol=TerceroRol.Rol.CLIENTE,
                activo=True,
            ).exists()
        )
        self.assertTrue(
            actualizado.roles.filter(
                rol=TerceroRol.Rol.PROVEEDOR,
                activo=True,
            ).exists()
        )

    def test_no_actualiza_tercero_de_otra_empresa(self):
        tercero = crear_tercero_prueba(
            empresa=self.empresa,
            request=self.request,
        )
        with self.assertRaises(ValidationError):
            actualizar_tercero(
                empresa=self.otra_empresa,
                tercero=tercero,
                tipo_persona=tercero.tipo_persona,
                tipo_documento=tercero.tipo_documento,
                numero_documento=tercero.numero_documento,
                denominacion=tercero.denominacion,
                nombre_fantasia="",
                condicion_iva=tercero.condicion_iva,
                telefono="",
                email="",
                sitio_web="",
                fecha_alta=tercero.fecha_alta,
                roles={TerceroRol.Rol.CLIENTE},
                observaciones="",
                request=self.request,
            )

    def test_inactivar_tercero_inactiva_dependencias(self):
        tercero = crear_tercero_prueba(
            empresa=self.empresa,
            request=self.request,
        )
        domicilio = crear_domicilio(
            empresa=self.empresa,
            tercero=tercero,
            tipo=DomicilioTercero.Tipo.FISCAL,
            nombre="",
            calle="Brasil",
            numero="151",
            sector="",
            torre="",
            piso="",
            departamento="",
            barrio="",
            localidad="Rosario",
            codigo_postal="2000",
            partido_departamento="Rosario",
            provincia="Santa Fe",
            pais="Argentina",
            principal=True,
            fecha_alta="2026-06-21",
            observaciones="",
            request=self.request,
        )
        contacto = crear_contacto(
            empresa=self.empresa,
            tercero=tercero,
            nombre="Administración",
            cargo="",
            area="",
            telefono="3415550000",
            email="",
            principal=True,
            fecha_alta="2026-06-21",
            observaciones="",
            request=self.request,
        )

        inactivar_tercero(
            empresa=self.empresa,
            tercero=tercero,
            request=self.request,
        )
        tercero.refresh_from_db()
        domicilio.refresh_from_db()
        contacto.refresh_from_db()
        self.assertFalse(tercero.activo)
        self.assertFalse(domicilio.activo)
        self.assertFalse(contacto.activo)
        self.assertFalse(
            tercero.roles.filter(activo=True).exists()
        )


class DomiciliosServicesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.empresa = crear_empresa()
        cls.usuario = crear_usuario()
        cls.tercero = crear_tercero_prueba(
            empresa=cls.empresa,
        )

    def setUp(self):
        self.request = crear_request(self.usuario)

    def _crear(self, **cambios):
        datos = {
            "empresa": self.empresa,
            "tercero": self.tercero,
            "tipo": DomicilioTercero.Tipo.FISCAL,
            "nombre": "",
            "calle": "Brasil",
            "numero": "151",
            "sector": "",
            "torre": "",
            "piso": "",
            "departamento": "",
            "barrio": "",
            "localidad": "Rosario",
            "codigo_postal": "2000",
            "partido_departamento": "Rosario",
            "provincia": "Santa Fe",
            "pais": "Argentina",
            "principal": False,
            "fecha_alta": "2026-06-21",
            "observaciones": "",
            "request": self.request,
        }
        datos.update(cambios)
        return crear_domicilio(**datos)

    def test_primer_domicilio_del_tipo_es_principal(self):
        domicilio = self._crear()
        self.assertTrue(domicilio.principal)

    def test_segundo_no_reemplaza_principal_si_no_se_pide(self):
        primero = self._crear()
        segundo = self._crear(
            calle="Córdoba",
            numero="1000",
        )
        primero.refresh_from_db()
        self.assertTrue(primero.principal)
        self.assertFalse(segundo.principal)

    def test_nuevo_principal_desmarca_anterior(self):
        primero = self._crear()
        segundo = self._crear(
            calle="Córdoba",
            numero="1000",
            principal=True,
        )
        primero.refresh_from_db()
        self.assertFalse(primero.principal)
        self.assertTrue(segundo.principal)

    def test_inactivar_principal_promueve_siguiente(self):
        primero = self._crear()
        segundo = self._crear(
            calle="Córdoba",
            numero="1000",
        )
        inactivar_domicilio(
            empresa=self.empresa,
            domicilio=primero,
            request=self.request,
        )
        segundo.refresh_from_db()
        self.assertTrue(segundo.principal)

    def test_actualizar_cambio_de_tipo_conserva_principal_origen(self):
        primero = self._crear()
        segundo = self._crear(
            calle="Córdoba",
            numero="1000",
        )
        actualizado = actualizar_domicilio(
            empresa=self.empresa,
            domicilio=primero,
            tipo=DomicilioTercero.Tipo.COMERCIAL,
            nombre="Comercial",
            calle="Brasil",
            numero="151",
            sector="",
            torre="",
            piso="",
            departamento="",
            barrio="",
            localidad="Rosario",
            codigo_postal="2000",
            partido_departamento="Rosario",
            provincia="Santa Fe",
            pais="Argentina",
            principal=True,
            fecha_alta="2026-06-21",
            observaciones="",
            request=self.request,
        )
        segundo.refresh_from_db()
        self.assertEqual(
            actualizado.tipo,
            DomicilioTercero.Tipo.COMERCIAL,
        )
        self.assertTrue(actualizado.principal)
        self.assertTrue(segundo.principal)


class ContactosServicesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.empresa = crear_empresa()
        cls.usuario = crear_usuario()
        cls.tercero = crear_tercero_prueba(
            empresa=cls.empresa,
        )

    def setUp(self):
        self.request = crear_request(self.usuario)

    def _crear(self, **cambios):
        datos = {
            "empresa": self.empresa,
            "tercero": self.tercero,
            "nombre": "Administración",
            "cargo": "",
            "area": "",
            "telefono": "3415550000",
            "email": "",
            "principal": False,
            "fecha_alta": "2026-06-21",
            "observaciones": "",
            "request": self.request,
        }
        datos.update(cambios)
        return crear_contacto(**datos)

    def test_primer_contacto_es_principal(self):
        contacto = self._crear()
        self.assertTrue(contacto.principal)

    def test_nuevo_principal_desmarca_anterior(self):
        primero = self._crear()
        segundo = self._crear(
            nombre="Cobranzas",
            telefono="3415550001",
            principal=True,
        )
        primero.refresh_from_db()
        self.assertFalse(primero.principal)
        self.assertTrue(segundo.principal)

    def test_inactivar_principal_promueve_siguiente(self):
        primero = self._crear()
        segundo = self._crear(
            nombre="Cobranzas",
            telefono="3415550001",
        )
        inactivar_contacto(
            empresa=self.empresa,
            contacto=primero,
            request=self.request,
        )
        segundo.refresh_from_db()
        self.assertTrue(segundo.principal)

    def test_actualiza_contacto(self):
        contacto = self._crear()
        actualizado = actualizar_contacto(
            empresa=self.empresa,
            contacto=contacto,
            nombre="Administración General",
            cargo="Responsable",
            area="Administración",
            telefono="3415559999",
            email="admin@example.com",
            principal=True,
            fecha_alta="2026-06-21",
            observaciones="",
            request=self.request,
        )
        self.assertEqual(
            actualizado.nombre,
            "Administración General",
        )
        self.assertEqual(actualizado.email, "admin@example.com")
