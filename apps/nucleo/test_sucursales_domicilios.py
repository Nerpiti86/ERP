from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.nucleo.empresa_activa import SESSION_EMPRESA_ACTIVA_ID

from .forms import SucursalForm
from .models import (
    Empresa,
    PermisoFuncional,
    RolFuncional,
    RolPermiso,
    Sucursal,
    UsuarioEmpresa,
    UsuarioRolEmpresa,
)


User = get_user_model()


def asignar_permiso(usuario, empresa, codigo_permiso, codigo_rol):
    permiso, _ = PermisoFuncional.objects.get_or_create(
        codigo=codigo_permiso,
    )
    rol = RolFuncional.objects.create(
        codigo=codigo_rol,
        nombre=codigo_rol.replace("_", " ").title(),
    )
    RolPermiso.objects.create(
        rol=rol,
        permiso=permiso,
    )
    UsuarioRolEmpresa.objects.create(
        usuario=usuario,
        empresa=empresa,
        rol=rol,
    )


def datos_sucursal(**cambios):
    datos = {
        "codigo": "CENTRAL",
        "nombre": "Casa central",
        "calle": "Santa Fe",
        "numero": "3011",
        "sector": "",
        "torre": "",
        "piso": "",
        "departamento": "",
        "barrio": "Centro",
        "localidad": "Rosario",
        "codigo_postal": "2000",
        "partido_departamento": "Rosario",
        "provincia": "Santa Fe",
        "pais": "Argentina",
        "es_casa_central": "on",
        "es_domicilio_fiscal_nacional": "on",
        "es_domicilio_fiscal_provincial": "on",
        "es_domicilio_legal": "on",
        "es_principal_actividades": "on",
        "es_deposito": "",
        "es_local_comercial": "on",
        "es_oficina_administrativa": "on",
        "otras_funciones": "",
        "activa": "on",
    }
    datos.update(cambios)
    return datos


class SucursalDomicilioModelTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            cuit="30770001001",
            razon_social="Empresa Sucursales SA",
        )

    def test_domicilio_formateado_y_funciones(self):
        sucursal = Sucursal.objects.create(
            empresa=self.empresa,
            codigo="CENTRAL",
            nombre="Casa central",
            calle="Santa Fe",
            numero="3011",
            piso="1",
            localidad="Rosario",
            codigo_postal="2000",
            provincia="Santa Fe",
            pais="Argentina",
            es_casa_central=True,
            es_local_comercial=True,
        )

        self.assertTrue(sucursal.domicilio_estructurado_completo)
        self.assertIn("Santa Fe 3011", sucursal.domicilio_formateado)
        self.assertIn("Rosario", sucursal.domicilio_formateado)
        self.assertEqual(
            sucursal.funciones,
            ["Casa central", "Local comercial"],
        )

    def test_domicilio_anterior_se_conserva_como_respaldo(self):
        sucursal = Sucursal.objects.create(
            empresa=self.empresa,
            codigo="ANTERIOR",
            nombre="Sucursal anterior",
            domicilio="Dirección histórica 123",
            localidad="Rosario",
        )

        self.assertFalse(sucursal.domicilio_estructurado_completo)
        self.assertIn(
            "Dirección histórica 123",
            sucursal.domicilio_formateado,
        )

    def test_funcion_exclusiva_no_se_duplica_en_sucursales_activas(self):
        Sucursal.objects.create(
            empresa=self.empresa,
            codigo="CENTRAL",
            nombre="Casa central",
            es_casa_central=True,
        )
        duplicada = Sucursal(
            empresa=self.empresa,
            codigo="OTRA",
            nombre="Otra central",
            es_casa_central=True,
        )

        with self.assertRaises(ValidationError):
            duplicada.full_clean()

    def test_funcion_exclusiva_puede_quedar_en_sucursal_inactiva(self):
        Sucursal.objects.create(
            empresa=self.empresa,
            codigo="ANTERIOR",
            nombre="Central anterior",
            es_casa_central=True,
            activa=False,
        )
        actual = Sucursal(
            empresa=self.empresa,
            codigo="ACTUAL",
            nombre="Central actual",
            es_casa_central=True,
        )

        actual.full_clean()


class SucursalFormTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            cuit="30770001002",
            razon_social="Empresa Formularios SA",
        )

    def test_formulario_normaliza_codigo_y_guarda_empresa(self):
        form = SucursalForm(
            datos_sucursal(codigo="central"),
            empresa=self.empresa,
        )

        self.assertTrue(form.is_valid(), form.errors)
        sucursal = form.save()

        self.assertEqual(sucursal.codigo, "CENTRAL")
        self.assertEqual(sucursal.empresa, self.empresa)
        self.assertTrue(sucursal.es_casa_central)

    def test_formulario_requiere_domicilio_estructurado(self):
        datos = datos_sucursal(calle="", codigo_postal="")
        form = SucursalForm(datos, empresa=self.empresa)

        self.assertFalse(form.is_valid())
        self.assertIn("calle", form.errors)
        self.assertIn("codigo_postal", form.errors)


class SucursalesViewTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            cuit="30770001003",
            razon_social="Empresa Operativa SA",
        )
        self.otra_empresa = Empresa.objects.create(
            cuit="30770001004",
            razon_social="Empresa Ajena SA",
        )
        self.sucursal = Sucursal.objects.create(
            empresa=self.empresa,
            codigo="CENTRAL",
            nombre="Casa central",
            calle="Santa Fe",
            numero="3011",
            localidad="Rosario",
            codigo_postal="2000",
            provincia="Santa Fe",
            pais="Argentina",
            es_casa_central=True,
        )
        self.sucursal_ajena = Sucursal.objects.create(
            empresa=self.otra_empresa,
            codigo="AJENA",
            nombre="Sucursal ajena",
        )

        self.lector = User.objects.create_user(
            username="lector_sucursales",
            password="password-test",
        )
        self.creador = User.objects.create_user(
            username="creador_sucursales",
            password="password-test",
        )
        self.editor = User.objects.create_user(
            username="editor_sucursales",
            password="password-test",
        )
        self.sin_permiso = User.objects.create_user(
            username="sin_permiso_sucursales",
            password="password-test",
        )

        for usuario in (
            self.lector,
            self.creador,
            self.editor,
            self.sin_permiso,
        ):
            UsuarioEmpresa.objects.create(
                usuario=usuario,
                empresa=self.empresa,
            )

        asignar_permiso(
            self.lector,
            self.empresa,
            "sucursales.ver",
            "LECTOR_SUCURSALES",
        )
        asignar_permiso(
            self.creador,
            self.empresa,
            "sucursales.crear",
            "CREADOR_SUCURSALES",
        )
        asignar_permiso(
            self.editor,
            self.empresa,
            "sucursales.editar",
            "EDITOR_SUCURSALES",
        )

    def ingresar(self, usuario):
        self.client.force_login(usuario)
        session = self.client.session
        session[SESSION_EMPRESA_ACTIVA_ID] = self.empresa.pk
        session.save()

    def test_listado_muestra_solo_empresa_activa(self):
        self.ingresar(self.lector)

        response = self.client.get(reverse("nucleo:sucursales"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CENTRAL · Casa central")
        self.assertContains(response, "Santa Fe 3011")
        self.assertContains(response, "Casa central")
        self.assertNotContains(response, "Sucursal ajena")

    def test_creador_puede_alta_sucursal(self):
        self.ingresar(self.creador)
        datos = datos_sucursal(
            codigo="DEPOSITO",
            nombre="Depósito principal",
            es_casa_central="",
            es_domicilio_fiscal_nacional="",
            es_domicilio_fiscal_provincial="",
            es_domicilio_legal="",
            es_principal_actividades="",
            es_deposito="on",
            es_local_comercial="",
            es_oficina_administrativa="",
        )

        response = self.client.post(
            reverse("nucleo:sucursal_crear"),
            datos,
        )

        self.assertRedirects(response, reverse("nucleo:sucursales"))
        creada = Sucursal.objects.get(
            empresa=self.empresa,
            codigo="DEPOSITO",
        )
        self.assertTrue(creada.es_deposito)
        self.assertFalse(creada.es_casa_central)

    def test_editor_no_puede_editar_sucursal_ajena(self):
        self.ingresar(self.editor)

        response = self.client.get(
            reverse(
                "nucleo:sucursal_editar",
                args=[self.sucursal_ajena.pk],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_funcion_exclusiva_duplicada_muestra_error(self):
        segunda = Sucursal.objects.create(
            empresa=self.empresa,
            codigo="SEGUNDA",
            nombre="Segunda sucursal",
        )
        self.ingresar(self.editor)

        response = self.client.post(
            reverse(
                "nucleo:sucursal_editar",
                args=[segunda.pk],
            ),
            datos_sucursal(
                codigo="SEGUNDA",
                nombre="Segunda sucursal",
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Ya existe otra sucursal activa marcada como casa central.",
        )

    def test_usuario_sin_permiso_recibe_403(self):
        self.ingresar(self.sin_permiso)

        response = self.client.get(reverse("nucleo:sucursales"))

        self.assertEqual(response.status_code, 403)

    def test_navbar_y_portada_admiten_permiso_de_sucursales(self):
        self.ingresar(self.lector)

        home = self.client.get(reverse("core:home"))
        portada = self.client.get(
            reverse("nucleo:configuracion_empresa")
        )

        self.assertContains(
            home,
            reverse("nucleo:configuracion_empresa"),
        )
        self.assertEqual(portada.status_code, 200)
        self.assertContains(portada, "Sucursales y domicilios")
        self.assertContains(
            portada,
            reverse("nucleo:sucursales"),
        )
