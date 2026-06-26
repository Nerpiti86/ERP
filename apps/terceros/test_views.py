from datetime import date

from django.test import TestCase
from django.urls import reverse

from apps.nucleo.empresa_activa import SESSION_EMPRESA_ACTIVA_ID

from .forms import TerceroForm
from .models import (
    ContactoTercero,
    DomicilioTercero,
    GrupoTercero,
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
from .services import (
    asegurar_grupos_generales,
    crear_grupo_tercero,
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
        cls.grupo_cliente = GrupoTercero.objects.get(
            empresa=cls.empresa,
            codigo="CLIENTES_GENERALES",
        )
        cls.grupo_proveedor = asegurar_grupos_generales(
            cls.empresa
        )[TerceroRol.Rol.PROVEEDOR]

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
            "grupo_cliente": self.grupo_cliente.pk,
            "grupo_proveedor": self.grupo_proveedor.pk,
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
        self.assertNotIn("resumen", respuesta.context)
        self.assertEqual(respuesta.context["cantidad_resultados"], 1)
        self.assertContains(respuesta, 'class="erp-list-filter-panel')
        self.assertContains(respuesta, 'type="search"')
        self.assertContains(respuesta, "1 resultado")

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

    def test_formulario_edicion_trata_none_como_no_vinculado(self):
        form = TerceroForm(
            None,
            empresa=self.empresa,
            tercero=self.tercero,
        )

        self.assertFalse(form.is_bound)
        self.assertEqual(
            form.initial["denominacion"],
            self.tercero.denominacion,
        )
        self.assertEqual(
            form.initial["numero_documento"],
            self.tercero.numero_documento,
        )
        self.assertTrue(form.initial["es_cliente"])

    def test_edicion_get_precarga_datos_actuales(self):
        self.tercero.nombre_fantasia = "Visible"
        self.tercero.telefono = "3415558877"
        self.tercero.email = "visible@example.com"
        self.tercero.sitio_web = "https://example.com"
        self.tercero.fecha_alta = date(2025, 4, 15)
        self.tercero.observaciones = "Datos existentes"
        self.tercero.save(
            update_fields=[
                "nombre_fantasia",
                "telefono",
                "email",
                "sitio_web",
                "fecha_alta",
                "observaciones",
                "actualizado_en",
            ]
        )
        TerceroRol.objects.get_or_create(
            tercero=self.tercero,
            rol=TerceroRol.Rol.PROVEEDOR,
            defaults={
                "grupo": self.grupo_proveedor,
                "fecha_alta": date(2025, 4, 15),
                "activo": True,
            },
        )
        self.tercero.refresh_from_db()

        self._login_empresa(self.operador)
        respuesta = self.client.get(
            reverse(
                "terceros:tercero_edit",
                kwargs={"tercero_id": self.tercero.pk},
            )
        )

        self.assertEqual(respuesta.status_code, 200)
        form = respuesta.context["form"]
        self.assertFalse(form.is_bound)
        self.assertEqual(
            form.initial["codigo"],
            self.tercero.codigo,
        )
        self.assertEqual(
            form.initial["tipo_persona"],
            self.tercero.tipo_persona,
        )
        self.assertEqual(
            form.initial["tipo_documento"],
            self.tercero.tipo_documento,
        )
        self.assertEqual(
            form.initial["numero_documento"],
            self.tercero.numero_documento,
        )
        self.assertEqual(
            form.initial["denominacion"],
            self.tercero.denominacion,
        )
        self.assertEqual(
            form.initial["nombre_fantasia"],
            "Visible",
        )
        self.assertEqual(
            form.initial["condicion_iva"],
            self.tercero.condicion_iva,
        )
        self.assertEqual(
            form.initial["telefono"],
            "3415558877",
        )
        self.assertEqual(
            form.initial["email"],
            "visible@example.com",
        )
        self.assertEqual(
            form.initial["sitio_web"],
            "https://example.com",
        )
        self.assertEqual(
            form.initial["fecha_alta"],
            date(2025, 4, 15),
        )
        self.assertTrue(form.initial["es_cliente"])
        self.assertTrue(form.initial["es_proveedor"])
        self.assertEqual(
            form.initial["observaciones"],
            "Datos existentes",
        )

    def test_edicion_get_se_distingue_visualmente_del_alta(self):
        self._login_empresa(self.operador)
        respuesta = self.client.get(
            reverse(
                "terceros:tercero_edit",
                kwargs={"tercero_id": self.tercero.pk},
            )
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Editar cliente/proveedor")
        self.assertContains(respuesta, "Modo edición")
        self.assertContains(
            respuesta,
            "Estás modificando un tercero existente.",
        )
        self.assertContains(respuesta, self.tercero.denominacion)
        self.assertContains(respuesta, self.tercero.codigo)
        self.assertContains(respuesta, self.tercero.identificacion)
        self.assertContains(respuesta, "Cancelar y volver")
        self.assertContains(respuesta, "Guardar cambios")

    def test_alta_no_muestra_modo_edicion(self):
        self._login_empresa(self.operador)
        respuesta = self.client.get(
            reverse("terceros:tercero_create")
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Nuevo cliente o proveedor")
        self.assertNotContains(respuesta, "Modo edición")
        self.assertNotContains(
            respuesta,
            "Estás modificando un tercero existente.",
        )

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

    def test_formulario_alta_muestra_grupos_por_rol(self):
        self._login_empresa(self.operador)
        respuesta = self.client.get(reverse("terceros:tercero_create"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Grupo de cliente", count=1)
        self.assertContains(respuesta, "Grupo de proveedor", count=1)
        self.assertContains(respuesta, self.grupo_cliente.nombre)
        self.assertContains(respuesta, self.grupo_proveedor.nombre)

    def test_listado_filtra_y_muestra_grupo(self):
        grupo = crear_grupo_tercero(
            empresa=self.empresa,
            tipo=GrupoTercero.Tipo.CLIENTE,
            codigo="ODONTOLOGOS",
            nombre="Odontólogos",
            observaciones="",
        )
        relacion = self.tercero.roles.get(
            rol=TerceroRol.Rol.CLIENTE,
            activo=True,
        )
        relacion.grupo = grupo
        relacion.full_clean()
        relacion.save()

        self._login_empresa(self.operador)
        respuesta = self.client.get(
            reverse("terceros:tercero_list"),
            {"grupo": grupo.pk},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Cliente Visible SA")
        self.assertContains(respuesta, "Odontólogos")
        self.assertNotContains(respuesta, "Cliente Oculto SA")


    def test_inactivar_solo_acepta_post(self):
        self._login_empresa(self.operador)
        respuesta = self.client.get(
            reverse(
                "terceros:tercero_deactivate",
                kwargs={"tercero_id": self.tercero.pk},
            )
        )
        self.assertEqual(respuesta.status_code, 405)


class GruposTerceroViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.empresa = crear_empresa()
        cls.otra_empresa = crear_empresa(
            cuit="30714202959",
            razon_social="Empresa Dos SA",
        )
        cls.operador = crear_usuario(username="operador_grupos")
        cls.lector = crear_usuario(username="lector_grupos")
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
        asegurar_grupos_generales(cls.empresa)
        asegurar_grupos_generales(cls.otra_empresa)

    def _login(self, usuario):
        self.client.force_login(usuario)
        session = self.client.session
        session[SESSION_EMPRESA_ACTIVA_ID] = self.empresa.pk
        session.save()

    def test_listado_clientes_aisla_tipo_y_empresa(self):
        cliente = crear_grupo_tercero(
            empresa=self.empresa,
            tipo=GrupoTercero.Tipo.CLIENTE,
            codigo="CLIENTES_TEST",
            nombre="Clientes test",
            observaciones="",
        )
        proveedor = crear_grupo_tercero(
            empresa=self.empresa,
            tipo=GrupoTercero.Tipo.PROVEEDOR,
            codigo="PROVEEDORES_TEST",
            nombre="Proveedores test",
            observaciones="",
        )
        oculto = crear_grupo_tercero(
            empresa=self.otra_empresa,
            tipo=GrupoTercero.Tipo.CLIENTE,
            codigo="OTRA_EMPRESA",
            nombre="Otra empresa",
            observaciones="",
        )
        self._login(self.operador)
        respuesta = self.client.get(
            reverse("terceros:grupo_cliente_list")
        )
        self.assertContains(respuesta, cliente.nombre)
        self.assertNotContains(respuesta, proveedor.nombre)
        self.assertNotContains(respuesta, oculto.nombre)

    def test_operador_crea_grupo_cliente(self):
        self._login(self.operador)
        respuesta = self.client.post(
            reverse("terceros:grupo_cliente_create"),
            {
                "codigo": "MAYORISTAS",
                "nombre": "Mayoristas",
                "observaciones": "",
            },
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(
            GrupoTercero.objects.filter(
                empresa=self.empresa,
                tipo=GrupoTercero.Tipo.CLIENTE,
                codigo="MAYORISTAS",
            ).exists()
        )

    def test_lector_no_puede_crear_grupo(self):
        self._login(self.lector)
        respuesta = self.client.get(
            reverse("terceros:grupo_cliente_create")
        )
        self.assertEqual(respuesta.status_code, 403)

    def test_edicion_grupo_otra_empresa_devuelve_404(self):
        grupo = GrupoTercero.objects.get(
            empresa=self.otra_empresa,
            tipo=GrupoTercero.Tipo.CLIENTE,
            codigo="CLIENTES_GENERALES",
        )
        self._login(self.operador)
        respuesta = self.client.get(
            reverse(
                "terceros:grupo_cliente_edit",
                kwargs={"grupo_id": grupo.pk},
            )
        )
        self.assertEqual(respuesta.status_code, 404)

    def test_no_inactiva_grupo_utilizado(self):
        grupo = crear_grupo_tercero(
            empresa=self.empresa,
            tipo=GrupoTercero.Tipo.CLIENTE,
            codigo="UTILIZADO",
            nombre="Utilizado",
            observaciones="",
        )
        crear_tercero_prueba(
            empresa=self.empresa,
            grupos_por_rol={TerceroRol.Rol.CLIENTE: grupo},
        )
        self._login(self.operador)
        respuesta = self.client.post(
            reverse(
                "terceros:grupo_cliente_deactivate",
                kwargs={"grupo_id": grupo.pk},
            )
        )
        self.assertEqual(respuesta.status_code, 302)
        grupo.refresh_from_db()
        self.assertTrue(grupo.activo)


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
