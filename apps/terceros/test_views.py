from django.test import TestCase
from django.urls import reverse

from apps.nucleo.empresa_activa import SESSION_EMPRESA_ACTIVA_ID

from .models import (
    ContactoTercero,
    DomicilioTercero,
    Tercero,
    TerceroRol,
)
from .tests_support import (
    asignar_rol,
    crear_empresa,
    crear_tercero_prueba,
    crear_usuario,
    obtener_catalogos,
)


class TercerosViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.empresa = crear_empresa()
        cls.otra_empresa = crear_empresa(
            cuit="30714202959",
            razon_social="Empresa Dos SA",
        )
        cls.operador = crear_usuario(username="operador")
        cls.lector = crear_usuario(username="lector")
        asignar_rol(
            usuario=cls.operador,
            empresa=cls.empresa,
            codigo_rol="OPERADOR",
        )
        asignar_rol(
            usuario=cls.lector,
            empresa=cls.empresa,
            codigo_rol="SOLO_LECTURA",
        )
        cls.tercero = crear_tercero_prueba(
            empresa=cls.empresa,
            denominacion="Cliente Visible SA",
        )
        cls.otro_tercero = crear_tercero_prueba(
            empresa=cls.otra_empresa,
            denominacion="Cliente Oculto SA",
        )
        cls.catalogos = obtener_catalogos()

    def _login_empresa(self, usuario):
        self.client.force_login(usuario)
        session = self.client.session
        session[SESSION_EMPRESA_ACTIVA_ID] = self.empresa.pk
        session.save()

    def _datos_tercero(self, **cambios):
        datos = {
            "codigo": "",
            "tipo_persona": Tercero.TipoPersona.PERSONA_JURIDICA,
            "tipo_documento": self.catalogos["cuit"].pk,
            "numero_documento": "30714202959",
            "denominacion": "Nuevo Tercero SA",
            "nombre_fantasia": "",
            "condicion_iva": self.catalogos["ri"].pk,
            "telefono": "3415550000",
            "email": "nuevo@example.com",
            "sitio_web": "",
            "fecha_alta": "2026-06-21",
            "es_cliente": "on",
            "observaciones": "",
        }
        datos.update(cambios)
        return datos

    def test_listado_requiere_login(self):
        respuesta = self.client.get(
            reverse("terceros:tercero_list")
        )
        self.assertEqual(respuesta.status_code, 302)

    def test_operador_puede_ver_listado(self):
        self._login_empresa(self.operador)
        respuesta = self.client.get(
            reverse("terceros:tercero_list")
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Cliente Visible SA")
        self.assertNotContains(respuesta, "Cliente Oculto SA")

    def test_operador_puede_crear(self):
        self._login_empresa(self.operador)
        respuesta = self.client.post(
            reverse("terceros:tercero_create"),
            self._datos_tercero(),
        )
        self.assertEqual(respuesta.status_code, 302)
        creado = Tercero.objects.get(
            empresa=self.empresa,
            denominacion="Nuevo Tercero SA",
        )
        self.assertEqual(creado.codigo, "T000002")
        self.assertTrue(creado.es_cliente)

    def test_lector_no_puede_crear(self):
        self._login_empresa(self.lector)
        respuesta = self.client.get(
            reverse("terceros:tercero_create")
        )
        self.assertEqual(respuesta.status_code, 403)

    def test_detalle_otra_empresa_devuelve_404(self):
        self._login_empresa(self.operador)
        respuesta = self.client.get(
            reverse(
                "terceros:tercero_detail",
                kwargs={"tercero_id": self.otro_tercero.pk},
            )
        )
        self.assertEqual(respuesta.status_code, 404)

    def test_operador_puede_editar(self):
        self._login_empresa(self.operador)
        respuesta = self.client.post(
            reverse(
                "terceros:tercero_edit",
                kwargs={"tercero_id": self.tercero.pk},
            ),
            self._datos_tercero(
                codigo=self.tercero.codigo,
                numero_documento=self.tercero.numero_documento,
                denominacion="Cliente Editado SA",
                es_proveedor="on",
            ),
        )
        self.assertEqual(respuesta.status_code, 302)
        self.tercero.refresh_from_db()
        self.assertEqual(
            self.tercero.denominacion,
            "Cliente Editado SA",
        )
        self.assertTrue(self.tercero.es_proveedor)

    def test_inactivar_solo_acepta_post(self):
        self._login_empresa(self.operador)
        respuesta = self.client.get(
            reverse(
                "terceros:tercero_deactivate",
                kwargs={"tercero_id": self.tercero.pk},
            )
        )
        self.assertEqual(respuesta.status_code, 405)


class RelacionesViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.empresa = crear_empresa()
        cls.usuario = crear_usuario(username="operador")
        asignar_rol(
            usuario=cls.usuario,
            empresa=cls.empresa,
            codigo_rol="OPERADOR",
        )
        cls.tercero = crear_tercero_prueba(
            empresa=cls.empresa,
        )

    def setUp(self):
        self.client.force_login(self.usuario)
        session = self.client.session
        session[SESSION_EMPRESA_ACTIVA_ID] = self.empresa.pk
        session.save()

    def test_crea_domicilio(self):
        respuesta = self.client.post(
            reverse(
                "terceros:domicilio_create",
                kwargs={"tercero_id": self.tercero.pk},
            ),
            {
                "tipo": DomicilioTercero.Tipo.FISCAL,
                "nombre": "Fiscal",
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
                "principal": "on",
                "fecha_alta": "2026-06-21",
                "observaciones": "",
            },
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(
            DomicilioTercero.objects.filter(
                tercero=self.tercero,
                activo=True,
                principal=True,
            ).exists()
        )

    def test_crea_contacto(self):
        respuesta = self.client.post(
            reverse(
                "terceros:contacto_create",
                kwargs={"tercero_id": self.tercero.pk},
            ),
            {
                "nombre": "Administración",
                "cargo": "",
                "area": "",
                "telefono": "3415550000",
                "email": "",
                "principal": "on",
                "fecha_alta": "2026-06-21",
                "observaciones": "",
            },
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(
            ContactoTercero.objects.filter(
                tercero=self.tercero,
                activo=True,
                principal=True,
            ).exists()
        )

    def test_detalle_muestra_relaciones(self):
        DomicilioTercero.objects.create(
            tercero=self.tercero,
            tipo=DomicilioTercero.Tipo.FISCAL,
            calle="Brasil",
            numero="151",
            localidad="Rosario",
            provincia="Santa Fe",
            pais="Argentina",
            principal=True,
            fecha_alta="2026-06-21",
        )
        ContactoTercero.objects.create(
            tercero=self.tercero,
            nombre="Administración",
            telefono="3415550000",
            principal=True,
            fecha_alta="2026-06-21",
        )
        respuesta = self.client.get(
            reverse(
                "terceros:tercero_detail",
                kwargs={"tercero_id": self.tercero.pk},
            )
        )
        self.assertContains(respuesta, "Brasil 151")
        self.assertContains(respuesta, "Administración")
