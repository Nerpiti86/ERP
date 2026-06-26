import importlib
import json
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase, override_settings
from django.urls import NoReverseMatch, clear_url_caches, reverse

from apps.core.context_processors import modo_aplicacion
from apps.core.estado_aplicacion import estado_aplicacion
from apps.nucleo.empresa_activa import SESSION_EMPRESA_ACTIVA_ID
from apps.nucleo.models import Empresa, UsuarioEmpresa


User = get_user_model()


class ModosAplicacionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.empresa = Empresa.objects.create(
            cuit="30780000001",
            razon_social="Empresa Modos SA",
        )
        cls.usuario = User.objects.create_superuser(
            username="admin_modos",
            password="password-test",
        )
        UsuarioEmpresa.objects.create(
            usuario=cls.usuario,
            empresa=cls.empresa,
        )

    def tearDown(self):
        clear_url_caches()
        super().tearDown()

    def _contexto(self):
        request = RequestFactory().get("/")
        return modo_aplicacion(request)["erp_aplicacion"]

    def _ingresar(self):
        self.client.force_login(self.usuario)
        session = self.client.session
        session[SESSION_EMPRESA_ACTIVA_ID] = self.empresa.pk
        session.save()

    def test_contexto_integrado_habilita_ambos_dominios(self):
        contexto = self._contexto()
        self.assertEqual(contexto["modo"], "integrado")
        self.assertTrue(contexto["gestion"])
        self.assertTrue(contexto["contabilidad"])

    @override_settings(ERP_APP_MODE="gestion")
    def test_contexto_gestion_habilita_solo_gestion(self):
        contexto = self._contexto()
        self.assertTrue(contexto["gestion"])
        self.assertFalse(contexto["contabilidad"])

    @override_settings(ERP_APP_MODE="contabilidad")
    def test_contexto_contabilidad_habilita_solo_contabilidad(self):
        contexto = self._contexto()
        self.assertFalse(contexto["gestion"])
        self.assertTrue(contexto["contabilidad"])

    @override_settings(
        ROOT_URLCONF="config.urls_gestion",
        ERP_APP_MODE="gestion",
    )
    def test_urlconf_gestion_publica_solo_gestion(self):
        clear_url_caches()
        self.assertTrue(reverse("items:item_list").startswith("/items/"))
        self.assertTrue(
            reverse("terceros:tercero_list").startswith("/terceros/")
        )
        with self.assertRaises(NoReverseMatch):
            reverse("contabilidad:plan_cuentas")

    @override_settings(
        ROOT_URLCONF="config.urls_contabilidad",
        ERP_APP_MODE="contabilidad",
    )
    def test_urlconf_contabilidad_publica_solo_contabilidad(self):
        clear_url_caches()
        self.assertEqual(
            reverse("contabilidad:plan_cuentas"),
            "/contabilidad/plan-de-cuentas/",
        )
        with self.assertRaises(NoReverseMatch):
            reverse("items:item_list")
        with self.assertRaises(NoReverseMatch):
            reverse("terceros:tercero_list")

    @override_settings(ERP_APP_MODE="gestion")
    def test_endpoint_estado_identifica_gestion(self):
        response = estado_aplicacion(RequestFactory().get("/_estado/"))
        self.assertEqual(
            json.loads(response.content),
            {"estado": "ok", "aplicacion": "gestion"},
        )

    @override_settings(ERP_APP_MODE="contabilidad")
    def test_endpoint_estado_identifica_contabilidad(self):
        response = estado_aplicacion(RequestFactory().get("/_estado/"))
        self.assertEqual(
            json.loads(response.content),
            {"estado": "ok", "aplicacion": "contabilidad"},
        )

    def test_settings_cookies_y_lanzadores_son_independientes(self):
        gestion = importlib.import_module("config.settings_gestion")
        contabilidad = importlib.import_module(
            "config.settings_contabilidad"
        )
        self.assertNotEqual(
            gestion.SESSION_COOKIE_NAME,
            contabilidad.SESSION_COOKIE_NAME,
        )
        self.assertNotEqual(
            gestion.CSRF_COOKIE_NAME,
            contabilidad.CSRF_COOKIE_NAME,
        )

        for nombre in (
            "launcher_erp.py",
            "ERP_GESTION.pyw",
            "ERP_CONTABILIDAD.pyw",
        ):
            ruta = Path(settings.BASE_DIR) / nombre
            compile(
                ruta.read_text(encoding="utf-8"),
                str(ruta),
                "exec",
            )

    def test_lanzador_contable_abre_plan_de_cuentas(self):
        contenido = (
            Path(settings.BASE_DIR) / "ERP_CONTABILIDAD.pyw"
        ).read_text(encoding="utf-8")
        self.assertIn(
            'ruta_inicial="/contabilidad/plan-de-cuentas/"',
            contenido,
        )
        self.assertNotIn(
            'ruta_inicial="/contabilidad/"',
            contenido,
        )

    @override_settings(
        ROOT_URLCONF="config.urls_gestion",
        ERP_APP_MODE="gestion",
    )
    def test_shell_gestion_no_intenta_resolver_contabilidad(self):
        clear_url_caches()
        self._ingresar()
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gestión")
        self.assertNotContains(response, "Plan de cuentas")

    @override_settings(
        ROOT_URLCONF="config.urls_contabilidad",
        ERP_APP_MODE="contabilidad",
    )
    def test_shell_contabilidad_no_intenta_resolver_gestion(self):
        clear_url_caches()
        self._ingresar()
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Plan de cuentas")
        self.assertNotContains(response, "Clientes y proveedores")
        self.assertNotContains(response, "Productos y servicios")
