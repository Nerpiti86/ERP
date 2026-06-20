from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.contabilidad.models import CuentaContable
from apps.contabilidad.services import crear_cuenta_contable
from apps.nucleo.empresa_activa import SESSION_EMPRESA_ACTIVA_ID
from apps.nucleo.models import Empresa, Sucursal, UsuarioEmpresa
from apps.nucleo.sucursal_activa import SESSION_SUCURSAL_ACTIVA_ID


User = get_user_model()


class ShellVisualTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            cuit="30770000001",
            razon_social="Empresa Shell SA",
        )
        self.sucursal = Sucursal.objects.create(
            empresa=self.empresa,
            codigo="CENTRAL",
            nombre="Casa central",
        )
        self.superusuario = User.objects.create_superuser(
            username="admin_shell",
            password="password-test",
        )
        self.usuario_sin_permiso = User.objects.create_user(
            username="usuario_shell",
            password="password-test",
        )
        UsuarioEmpresa.objects.create(
            usuario=self.usuario_sin_permiso,
            empresa=self.empresa,
        )

    def ingresar(self, usuario, *, con_sucursal=True):
        self.client.force_login(usuario)
        session = self.client.session
        session[SESSION_EMPRESA_ACTIVA_ID] = self.empresa.pk
        if con_sucursal:
            session[SESSION_SUCURSAL_ACTIVA_ID] = self.sucursal.pk
        session.save()

    def test_shell_usa_css_global_y_ancho_completo(self):
        self.ingresar(self.superusuario)

        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/static/css/erp.css")
        self.assertContains(
            response,
            'class="container-fluid px-3 px-lg-4 erp-navbar-shell"',
        )
        self.assertContains(
            response,
            'class="container-fluid px-3 px-lg-4 py-4 erp-page-shell"',
        )
        self.assertNotContains(response, '<main class="container py-4">')

    def test_navbar_muestra_gestion_antes_de_contabilidad(self):
        self.ingresar(self.superusuario)

        response = self.client.get(reverse("core:home"))
        contenido = response.content.decode("utf-8")

        self.assertContains(response, "Gestión")
        self.assertContains(response, "Contabilidad")
        self.assertContains(response, "Plan de cuentas")
        self.assertContains(response, "erp-flow-indicator")
        self.assertLess(
            contenido.index("Gestión"),
            contenido.index("Contabilidad"),
        )

    def test_usuario_sin_permiso_no_ve_contabilidad(self):
        self.ingresar(self.usuario_sin_permiso)

        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gestión")
        self.assertNotContains(response, "Contabilidad")
        self.assertNotContains(response, "Plan de cuentas")

    def test_barra_contexto_muestra_empresa_y_sucursal(self):
        self.ingresar(self.superusuario)

        response = self.client.get(reverse("core:home"))

        self.assertContains(response, "erp-context-bar")
        self.assertContains(response, self.empresa.razon_social)
        self.assertContains(
            response,
            f"{self.sucursal.codigo} · {self.sucursal.nombre}",
        )
        self.assertContains(response, "Empresa")
        self.assertContains(response, "Sucursal")

    def test_barra_contexto_maneja_sucursal_no_seleccionada(self):
        Sucursal.objects.create(
            empresa=self.empresa,
            codigo="NORTE",
            nombre="Sucursal norte",
        )
        self.ingresar(self.superusuario, con_sucursal=False)

        response = self.client.get(reverse("core:home"))

        self.assertContains(response, self.empresa.razon_social)
        self.assertContains(response, "Sin seleccionar")
        self.assertContains(
            response,
            reverse("core:seleccionar_sucursal"),
        )

    def test_menu_usuario_conserva_config_admin_y_logout_post(self):
        self.ingresar(self.superusuario)

        response = self.client.get(reverse("core:home"))

        self.assertContains(response, "admin_shell")
        self.assertContains(response, "Configuración de empresa")
        self.assertContains(response, "Administración técnica")
        self.assertContains(
            response,
            f'action="{reverse("core:logout")}"',
        )
        self.assertContains(response, 'method="post"')
        self.assertContains(response, "Cerrar sesión")

    def test_plan_cuentas_usa_estilos_globales_sin_style_inline(self):
        crear_cuenta_contable(
            empresa=self.empresa,
            codigo="1.0.00.00.000",
            nombre="Activo",
            tipo_contable=CuentaContable.TipoContable.ACTIVO,
        )
        self.ingresar(self.superusuario)

        response = self.client.get(
            reverse("contabilidad:plan_cuentas")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "pc-nivel-1")
        self.assertNotContains(response, "<style>")
