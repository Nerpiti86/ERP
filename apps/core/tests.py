from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.nucleo.empresa_activa import SESSION_EMPRESA_ACTIVA_ID
from apps.nucleo.sucursal_activa import SESSION_SUCURSAL_ACTIVA_ID
from apps.nucleo.models import (
    Empresa,
    Sucursal,
    UsuarioEmpresa,
    UsuarioSucursal,
)


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


class SucursalActivaSesionTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.usuario = self.User.objects.create_user(
            username="operador_sucursal",
            email="operador_sucursal@example.com",
            password="password-test",
        )
        self.empresa_a = Empresa.objects.create(
            cuit="30755555558",
            razon_social="Empresa Sucursales A SA",
        )
        self.empresa_b = Empresa.objects.create(
            cuit="30766666668",
            razon_social="Empresa Sucursales B SA",
        )
        self.sucursal_a1 = Sucursal.objects.create(
            empresa=self.empresa_a,
            codigo="A1",
            nombre="Sucursal A1",
            localidad="Rosario",
        )
        self.sucursal_a2 = Sucursal.objects.create(
            empresa=self.empresa_a,
            codigo="A2",
            nombre="Sucursal A2",
            localidad="Rosario",
        )
        self.sucursal_a_inactiva = Sucursal.objects.create(
            empresa=self.empresa_a,
            codigo="A0",
            nombre="Sucursal A inactiva",
            activa=False,
        )
        self.sucursal_b1 = Sucursal.objects.create(
            empresa=self.empresa_b,
            codigo="B1",
            nombre="Sucursal B1",
            localidad="Santa Fe",
        )
        self.acceso_empresa_a = UsuarioEmpresa.objects.create(
            usuario=self.usuario,
            empresa=self.empresa_a,
        )
        self.acceso_sucursal_a1 = UsuarioSucursal.objects.create(
            usuario=self.usuario,
            sucursal=self.sucursal_a1,
        )

    def test_usuario_con_una_sucursal_la_selecciona_automaticamente(self):
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("core:home"))

        self.assertEqual(
            self.client.session[SESSION_EMPRESA_ACTIVA_ID],
            self.empresa_a.pk,
        )
        self.assertEqual(
            self.client.session[SESSION_SUCURSAL_ACTIVA_ID],
            self.sucursal_a1.pk,
        )
        self.assertEqual(response.context["sucursal_activa"], self.sucursal_a1)

    def test_usuario_con_varias_sucursales_debe_elegir(self):
        UsuarioSucursal.objects.create(
            usuario=self.usuario,
            sucursal=self.sucursal_a2,
        )
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("core:home"))

        self.assertNotIn(
            SESSION_SUCURSAL_ACTIVA_ID,
            self.client.session,
        )
        self.assertIsNone(response.context["sucursal_activa"])

    def test_selector_lista_solo_sucursales_autorizadas_activas_de_empresa(self):
        UsuarioSucursal.objects.create(
            usuario=self.usuario,
            sucursal=self.sucursal_a2,
        )
        UsuarioSucursal.objects.create(
            usuario=self.usuario,
            sucursal=self.sucursal_a_inactiva,
        )
        UsuarioSucursal.objects.create(
            usuario=self.usuario,
            sucursal=self.sucursal_b1,
        )
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("core:seleccionar_sucursal"))

        self.assertContains(response, "Sucursal A1")
        self.assertContains(response, "Sucursal A2")
        self.assertNotContains(response, "Sucursal A inactiva")
        self.assertNotContains(response, "Sucursal B1")

    def test_post_selecciona_sucursal_autorizada(self):
        UsuarioSucursal.objects.create(
            usuario=self.usuario,
            sucursal=self.sucursal_a2,
        )
        self.client.force_login(self.usuario)

        response = self.client.post(
            reverse("core:seleccionar_sucursal"),
            {"sucursal_id": self.sucursal_a2.pk},
        )

        self.assertRedirects(response, reverse("core:home"))
        self.assertEqual(
            self.client.session[SESSION_SUCURSAL_ACTIVA_ID],
            self.sucursal_a2.pk,
        )

    def test_post_rechaza_sucursal_no_autorizada(self):
        self.client.force_login(self.usuario)

        response = self.client.post(
            reverse("core:seleccionar_sucursal"),
            {"sucursal_id": self.sucursal_a2.pk},
        )

        self.assertEqual(response.status_code, 403)
        self.assertNotEqual(
            self.client.session.get(SESSION_SUCURSAL_ACTIVA_ID),
            self.sucursal_a2.pk,
        )

    def test_post_rechaza_sucursal_de_otra_empresa(self):
        UsuarioEmpresa.objects.create(
            usuario=self.usuario,
            empresa=self.empresa_b,
        )
        UsuarioSucursal.objects.create(
            usuario=self.usuario,
            sucursal=self.sucursal_b1,
        )
        self.client.force_login(self.usuario)
        session = self.client.session
        session[SESSION_EMPRESA_ACTIVA_ID] = self.empresa_a.pk
        session.save()

        response = self.client.post(
            reverse("core:seleccionar_sucursal"),
            {"sucursal_id": self.sucursal_b1.pk},
        )

        self.assertEqual(response.status_code, 403)

    def test_superusuario_puede_seleccionar_sucursal_activa_de_empresa(self):
        superusuario = self.User.objects.create_superuser(
            username="admin_sucursal",
            email="admin_sucursal@example.com",
            password="password-test",
        )
        self.client.force_login(superusuario)
        session = self.client.session
        session[SESSION_EMPRESA_ACTIVA_ID] = self.empresa_a.pk
        session.save()

        response = self.client.post(
            reverse("core:seleccionar_sucursal"),
            {"sucursal_id": self.sucursal_a2.pk},
        )

        self.assertRedirects(response, reverse("core:home"))
        self.assertEqual(
            self.client.session[SESSION_SUCURSAL_ACTIVA_ID],
            self.sucursal_a2.pk,
        )

    def test_superusuario_no_puede_seleccionar_sucursal_inactiva(self):
        superusuario = self.User.objects.create_superuser(
            username="admin_sucursal_inactiva",
            email="admin_sucursal_inactiva@example.com",
            password="password-test",
        )
        self.client.force_login(superusuario)
        session = self.client.session
        session[SESSION_EMPRESA_ACTIVA_ID] = self.empresa_a.pk
        session.save()

        response = self.client.post(
            reverse("core:seleccionar_sucursal"),
            {"sucursal_id": self.sucursal_a_inactiva.pk},
        )

        self.assertEqual(response.status_code, 403)

    def test_sesion_se_limpia_si_usuario_pierde_acceso_sucursal(self):
        self.client.force_login(self.usuario)
        self.client.get(reverse("core:home"))

        self.acceso_sucursal_a1.activo = False
        self.acceso_sucursal_a1.save()

        response = self.client.get(reverse("core:home"))

        self.assertNotIn(
            SESSION_SUCURSAL_ACTIVA_ID,
            self.client.session,
        )
        self.assertIsNone(response.context["sucursal_activa"])

    def test_cambiar_empresa_limpia_sucursal_anterior(self):
        UsuarioEmpresa.objects.create(
            usuario=self.usuario,
            empresa=self.empresa_b,
        )
        UsuarioSucursal.objects.create(
            usuario=self.usuario,
            sucursal=self.sucursal_b1,
        )
        self.client.force_login(self.usuario)

        session = self.client.session
        session[SESSION_EMPRESA_ACTIVA_ID] = self.empresa_a.pk
        session[SESSION_SUCURSAL_ACTIVA_ID] = self.sucursal_a1.pk
        session.save()

        response = self.client.post(
            reverse("core:seleccionar_empresa"),
            {"empresa_id": self.empresa_b.pk},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("core:home"))
        self.assertNotIn(
            SESSION_SUCURSAL_ACTIVA_ID,
            self.client.session,
        )

    def test_navbar_muestra_sucursal_activa(self):
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("core:home"))

        self.assertContains(response, "Sucursal:")
        self.assertContains(response, "A1")
        self.assertContains(response, "Sucursal A1")
        self.assertContains(response, "Cambiar sucursal")

    def test_selector_sucursal_sin_empresa_redirige_a_selector_empresa(self):
        UsuarioEmpresa.objects.create(
            usuario=self.usuario,
            empresa=self.empresa_b,
        )
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("core:seleccionar_sucursal"))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            response.url.startswith(reverse("core:seleccionar_empresa"))
        )
        self.assertIn("next=", response.url)

