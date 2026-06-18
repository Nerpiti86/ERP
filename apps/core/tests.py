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
