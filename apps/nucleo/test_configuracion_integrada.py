from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.nucleo.empresa_activa import SESSION_EMPRESA_ACTIVA_ID

from .models import (
    Empresa,
    PermisoFuncional,
    RolFuncional,
    RolPermiso,
    Sucursal,
    UsuarioEmpresa,
    UsuarioRolEmpresa,
)
from .parametros_empresa import inicializar_parametros_empresa


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


class ConfiguracionEmpresaIntegradaTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            cuit="30770000011",
            razon_social="Empresa Integrada SA",
            nombre_fantasia="Integrada",
            condicion_iva=Empresa.CondicionIVA.RESPONSABLE_INSCRIPTO,
        )
        self.otra_empresa = Empresa.objects.create(
            cuit="30770000012",
            razon_social="Empresa Ajena SA",
        )
        self.sucursal_activa = Sucursal.objects.create(
            empresa=self.empresa,
            codigo="CENTRAL",
            nombre="Casa central",
            localidad="Rosario",
        )
        Sucursal.objects.create(
            empresa=self.empresa,
            codigo="DEPOSITO",
            nombre="Depósito",
            localidad="Rosario",
            activa=False,
        )
        Sucursal.objects.create(
            empresa=self.otra_empresa,
            codigo="AJENA",
            nombre="Sucursal ajena",
        )

        self.usuario = User.objects.create_user(
            username="config_integrada",
            password="password-test",
        )
        UsuarioEmpresa.objects.create(
            usuario=self.usuario,
            empresa=self.empresa,
        )
        asignar_permiso(
            self.usuario,
            self.empresa,
            "parametros.ver",
            "LECTOR_CONFIG_INTEGRADA",
        )
        inicializar_parametros_empresa(self.empresa)

    def ingresar(self):
        self.client.force_login(self.usuario)
        session = self.client.session
        session[SESSION_EMPRESA_ACTIVA_ID] = self.empresa.pk
        session.save()

    def test_portada_integra_estado_real_de_la_empresa(self):
        self.ingresar()

        response = self.client.get(
            reverse("nucleo:configuracion_empresa")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "nucleo/configuracion_empresa.html",
        )
        self.assertContains(response, "Datos del contribuyente")
        self.assertContains(response, "Sucursales")
        self.assertContains(response, "Ingresos Brutos")
        self.assertContains(response, "Parámetros operativos")
        self.assertContains(response, "Usuarios y accesos")
        self.assertContains(response, self.empresa.razon_social)
        self.assertContains(response, self.empresa.nombre_fantasia)
        self.assertContains(response, self.empresa.cuit)
        self.assertEqual(
            response.context["resumen"]["sucursales_activas"],
            1,
        )
        self.assertEqual(
            response.context["resumen"]["sucursales_total"],
            2,
        )
        self.assertEqual(
            response.context["estado_parametros"]["configurados"],
            8,
        )
        self.assertEqual(
            response.context["estado_parametros"]["total"],
            8,
        )
        self.assertTrue(
            response.context["estado_parametros"]["completa"]
        )
        self.assertContains(response, "activas")
        self.assertContains(response, "parámetros activos")
        self.assertContains(response, "CENTRAL · Casa central")
        self.assertContains(
            response,
            reverse("nucleo:parametros_operativos"),
        )
        self.assertNotContains(response, self.otra_empresa.razon_social)
        self.assertNotContains(response, "Sucursal ajena")
        self.assertNotContains(response, "/admin/")

    def test_portada_no_incluye_el_formulario_de_parametros(self):
        self.ingresar()

        response = self.client.get(
            reverse("nucleo:configuracion_empresa")
        )

        self.assertNotIn("form", response.context)
        self.assertNotContains(response, "Guardar configuración")
        self.assertContains(
            response,
            "Abrir parámetros operativos",
        )

    def test_portada_es_solo_lectura_http(self):
        self.ingresar()

        response = self.client.post(
            reverse("nucleo:configuracion_empresa"),
            {},
        )

        self.assertEqual(response.status_code, 405)

    def test_parametros_conservan_formulario_existente(self):
        self.ingresar()

        response = self.client.get(
            reverse("nucleo:parametros_operativos")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "nucleo/parametros_operativos.html",
        )
        self.assertContains(response, "Parámetros operativos")
        self.assertContains(response, "Modo solo lectura")
        self.assertIn("form", response.context)
        self.assertTrue(
            all(
                campo.disabled
                for campo in response.context["form"].fields.values()
            )
        )
