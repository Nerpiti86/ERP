from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.nucleo.empresa_activa import SESSION_EMPRESA_ACTIVA_ID
from apps.nucleo.models import Empresa, Sucursal, UsuarioEmpresa


class HomeTests(TestCase):
    def test_home_status_code(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)

    def test_home_muestra_metricas_del_nucleo(self):
        empresa = Empresa.objects.create(
            cuit="30712345678",
            razon_social="Empresa Demo SA",
        )
        Sucursal.objects.create(
            empresa=empresa,
            codigo="CASA",
            nombre="Casa central",
        )

        response = self.client.get(reverse("core:home"))

        self.assertContains(response, "Empresas")
        self.assertContains(response, "Sucursales")
        self.assertContains(response, "Sistema activo")
        self.assertContains(response, "Empresa")

    def test_home_muestra_accesos_al_admin_del_nucleo(self):
        response = self.client.get(reverse("core:home"))

        self.assertContains(response, "Panel admin")
        self.assertContains(response, "Ver empresas")
        self.assertContains(response, "Ver sucursales")
        self.assertContains(response, "Ver ejercicios")
        self.assertContains(response, "Ver períodos")
        self.assertContains(response, reverse("admin:nucleo_empresa_changelist"))
        self.assertContains(response, reverse("admin:nucleo_sucursal_changelist"))
        self.assertContains(response, reverse("admin:nucleo_ejerciciofiscal_changelist"))
        self.assertContains(response, reverse("admin:nucleo_periodocontable_changelist"))


class EmpresaActivaSesionTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.usuario = self.User.objects.create_user(
            username="operador_empresa",
            email="operador_empresa@example.com",
            password="password-test",
        )
        self.empresa_a = Empresa.objects.create(
            cuit="30711111118",
            razon_social="Empresa A SA",
        )
        self.empresa_b = Empresa.objects.create(
            cuit="30722222228",
            razon_social="Empresa B SA",
        )
        self.empresa_c = Empresa.objects.create(
            cuit="30733333338",
            razon_social="Empresa C SA",
        )
        self.empresa_inactiva = Empresa.objects.create(
            cuit="30744444448",
            razon_social="Empresa Inactiva SA",
            activa=False,
        )
        self.acceso_a = UsuarioEmpresa.objects.create(
            usuario=self.usuario,
            empresa=self.empresa_a,
        )

    def test_usuario_con_una_empresa_la_selecciona_automaticamente(self):
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("core:home"))

        self.assertEqual(
            self.client.session[SESSION_EMPRESA_ACTIVA_ID],
            self.empresa_a.pk,
        )
        self.assertEqual(response.context["empresa_activa"], self.empresa_a)

    def test_usuario_con_varias_empresas_debe_elegir(self):
        UsuarioEmpresa.objects.create(
            usuario=self.usuario,
            empresa=self.empresa_b,
        )
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("core:home"))

        self.assertNotIn(
            SESSION_EMPRESA_ACTIVA_ID,
            self.client.session,
        )
        self.assertIsNone(response.context["empresa_activa"])

    def test_selector_lista_solo_empresas_autorizadas_y_activas(self):
        UsuarioEmpresa.objects.create(
            usuario=self.usuario,
            empresa=self.empresa_b,
        )
        UsuarioEmpresa.objects.create(
            usuario=self.usuario,
            empresa=self.empresa_inactiva,
        )
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("core:seleccionar_empresa"))

        self.assertContains(response, "Empresa A SA")
        self.assertContains(response, "Empresa B SA")
        self.assertNotContains(response, "Empresa C SA")
        self.assertNotContains(response, "Empresa Inactiva SA")

    def test_post_selecciona_empresa_autorizada(self):
        UsuarioEmpresa.objects.create(
            usuario=self.usuario,
            empresa=self.empresa_b,
        )
        self.client.force_login(self.usuario)

        response = self.client.post(
            reverse("core:seleccionar_empresa"),
            {"empresa_id": self.empresa_b.pk},
        )

        self.assertRedirects(response, reverse("core:home"))
        self.assertEqual(
            self.client.session[SESSION_EMPRESA_ACTIVA_ID],
            self.empresa_b.pk,
        )

    def test_post_rechaza_empresa_no_autorizada(self):
        UsuarioEmpresa.objects.create(
            usuario=self.usuario,
            empresa=self.empresa_b,
        )
        self.client.force_login(self.usuario)

        response = self.client.post(
            reverse("core:seleccionar_empresa"),
            {"empresa_id": self.empresa_c.pk},
        )

        self.assertEqual(response.status_code, 403)
        self.assertNotEqual(
            self.client.session.get(SESSION_EMPRESA_ACTIVA_ID),
            self.empresa_c.pk,
        )

    def test_superusuario_puede_seleccionar_cualquier_empresa_activa(self):
        superusuario = self.User.objects.create_superuser(
            username="admin_empresa",
            email="admin_empresa@example.com",
            password="password-test",
        )
        self.client.force_login(superusuario)

        response = self.client.post(
            reverse("core:seleccionar_empresa"),
            {"empresa_id": self.empresa_b.pk},
        )

        self.assertRedirects(response, reverse("core:home"))
        self.assertEqual(
            self.client.session[SESSION_EMPRESA_ACTIVA_ID],
            self.empresa_b.pk,
        )

    def test_superusuario_no_puede_seleccionar_empresa_inactiva(self):
        superusuario = self.User.objects.create_superuser(
            username="admin_inactiva",
            email="admin_inactiva@example.com",
            password="password-test",
        )
        self.client.force_login(superusuario)

        response = self.client.post(
            reverse("core:seleccionar_empresa"),
            {"empresa_id": self.empresa_inactiva.pk},
        )

        self.assertEqual(response.status_code, 403)

    def test_sesion_invalida_se_limpia_si_usuario_pierde_acceso(self):
        self.client.force_login(self.usuario)
        self.client.get(reverse("core:home"))

        self.acceso_a.activo = False
        self.acceso_a.save()

        response = self.client.get(reverse("core:home"))

        self.assertNotIn(
            SESSION_EMPRESA_ACTIVA_ID,
            self.client.session,
        )
        self.assertIsNone(response.context["empresa_activa"])

    def test_navbar_muestra_empresa_activa(self):
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("core:home"))

        self.assertContains(response, "Empresa:")
        self.assertContains(response, "Empresa A SA")
        self.assertContains(response, "Cambiar empresa")

