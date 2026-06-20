from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.nucleo.models import Empresa

from .admin import CuentaContableAdmin
from .models import CuentaContable
from .services import crear_cuenta_contable


User = get_user_model()


class CuentaContableAdminTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_superuser(
            username="admin_contabilidad",
            password="password-test",
            email="admin@example.com",
        )
        self.empresa = Empresa.objects.create(
            cuit="30777777778",
            razon_social="Empresa Backoffice SA",
        )
        self.client.force_login(self.usuario)

    @property
    def add_url(self):
        return reverse("admin:contabilidad_cuentacontable_add")

    def datos_cuenta(
        self,
        *,
        codigo,
        nombre,
        tipo_contable,
        parent="",
        naturaleza="",
    ):
        return {
            "empresa": str(self.empresa.pk),
            "parent": str(parent) if parent else "",
            "codigo": codigo,
            "nombre": nombre,
            "descripcion": "",
            "tipo_contable": tipo_contable,
            "naturaleza": naturaleza,
            "habilitada": "on",
            "_save": "Guardar",
        }

    def test_modelo_esta_registrado_con_admin_especifico(self):
        model_admin = admin.site._registry[CuentaContable]

        self.assertIsInstance(model_admin, CuentaContableAdmin)
        self.assertFalse(model_admin.has_delete_permission(None))

    def test_admin_crea_raiz_y_cuenta_hija(self):
        response_raiz = self.client.post(
            self.add_url,
            self.datos_cuenta(
                codigo="1.0.00.00.000",
                nombre="Activo",
                tipo_contable=CuentaContable.TipoContable.ACTIVO,
            ),
        )

        self.assertEqual(response_raiz.status_code, 302)
        raiz = CuentaContable.objects.get(
            empresa=self.empresa,
            codigo="1.0.00.00.000",
        )

        response_hija = self.client.post(
            self.add_url,
            self.datos_cuenta(
                codigo="1.1.00.00.000",
                nombre="Activo corriente",
                tipo_contable=CuentaContable.TipoContable.ACTIVO,
                parent=raiz.pk,
            ),
        )

        self.assertEqual(response_hija.status_code, 302)
        hija = CuentaContable.objects.get(
            empresa=self.empresa,
            codigo="1.1.00.00.000",
        )
        self.assertEqual(hija.parent, raiz)
        self.assertEqual(list(raiz.get_children()), [hija])

    def test_admin_rechaza_superior_incompatible_con_codigo(self):
        activo = crear_cuenta_contable(
            empresa=self.empresa,
            codigo="1.0.00.00.000",
            nombre="Activo",
            tipo_contable=CuentaContable.TipoContable.ACTIVO,
        )
        pasivo = crear_cuenta_contable(
            empresa=self.empresa,
            codigo="2.0.00.00.000",
            nombre="Pasivo",
            tipo_contable=CuentaContable.TipoContable.PASIVO,
        )

        response = self.client.post(
            self.add_url,
            self.datos_cuenta(
                codigo="1.1.00.00.000",
                nombre="Activo corriente",
                tipo_contable=CuentaContable.TipoContable.ACTIVO,
                parent=pasivo.pk,
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "La cuenta superior no coincide con el codigo de la cuenta.",
        )
        self.assertFalse(
            CuentaContable.objects.filter(
                empresa=self.empresa,
                codigo="1.1.00.00.000",
            ).exists()
        )
        self.assertEqual(activo.codigo, "1.0.00.00.000")

    def test_listado_muestra_cuenta_y_datos_derivados(self):
        raiz = crear_cuenta_contable(
            empresa=self.empresa,
            codigo="1.0.00.00.000",
            nombre="Activo",
            tipo_contable=CuentaContable.TipoContable.ACTIVO,
        )
        nivel_2 = crear_cuenta_contable(
            empresa=self.empresa,
            codigo="1.1.00.00.000",
            nombre="Activo corriente",
            tipo_contable=CuentaContable.TipoContable.ACTIVO,
        )

        url = reverse("admin:contabilidad_cuentacontable_changelist")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, raiz.codigo)
        self.assertContains(response, nivel_2.nombre)
        self.assertContains(response, self.empresa.razon_social)

        model_admin = admin.site._registry[CuentaContable]
        self.assertEqual(model_admin.nivel_admin(nivel_2), 2)
        self.assertFalse(model_admin.imputable_admin(nivel_2))

    def test_admin_no_permite_eliminacion_fisica(self):
        raiz = crear_cuenta_contable(
            empresa=self.empresa,
            codigo="1.0.00.00.000",
            nombre="Activo",
            tipo_contable=CuentaContable.TipoContable.ACTIVO,
        )
        url = reverse(
            "admin:contabilidad_cuentacontable_delete",
            args=[raiz.pk],
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            CuentaContable.objects.filter(pk=raiz.pk).exists()
        )
