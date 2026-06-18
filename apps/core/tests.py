from django.test import TestCase
from django.urls import reverse

from apps.nucleo.models import Empresa, Sucursal


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
