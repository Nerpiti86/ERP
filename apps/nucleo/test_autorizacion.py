from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.nucleo.empresa_activa import SESSION_EMPRESA_ACTIVA_ID

from .models import (
    Empresa,
    ParametroSistema,
    PermisoFuncional,
    RolFuncional,
    RolPermiso,
    UsuarioEmpresa,
    UsuarioRolEmpresa,
)
from .parametros_empresa import inicializar_parametros_empresa
from .permisos import usuario_tiene_alguno_de_permisos


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


class PermisosFuncionalesHelperTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            cuit="30712345678",
            razon_social="Empresa Autorizada SA",
        )
        self.usuario = User.objects.create_user(
            username="lector",
            password="password-test",
        )
        self.superusuario = User.objects.create_superuser(
            username="admin_autorizacion",
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
            "LECTOR_PARAMETROS",
        )

    def test_alguno_devuelve_true_si_posee_un_permiso(self):
        self.assertTrue(
            usuario_tiene_alguno_de_permisos(
                self.usuario,
                self.empresa,
                ("parametros.editar", "parametros.ver"),
            )
        )

    def test_alguno_devuelve_false_si_no_posee_permisos(self):
        self.assertFalse(
            usuario_tiene_alguno_de_permisos(
                self.usuario,
                self.empresa,
                ("usuarios.editar", "empresas.editar"),
            )
        )

    def test_alguno_normaliza_codigos(self):
        self.assertTrue(
            usuario_tiene_alguno_de_permisos(
                self.usuario,
                self.empresa,
                (" PARAMETROS.VER ",),
            )
        )

    def test_usuario_inactivo_no_conserva_permiso(self):
        self.usuario.is_active = False
        self.usuario.save(update_fields=["is_active"])

        self.assertFalse(
            usuario_tiene_alguno_de_permisos(
                self.usuario,
                self.empresa,
                ("parametros.ver",),
            )
        )

    def test_superusuario_activo_supera_autorizacion_funcional(self):
        self.assertTrue(
            usuario_tiene_alguno_de_permisos(
                self.superusuario,
                self.empresa,
                ("permiso.aun_no_definido",),
            )
        )


class AutorizacionConfiguracionEmpresaTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            cuit="30712345678",
            razon_social="Empresa Autorizada SA",
        )
        self.otra_empresa = Empresa.objects.create(
            cuit="30712345679",
            razon_social="Otra Empresa Autorizada SA",
        )

        self.lector = User.objects.create_user(
            username="lector_parametros",
            password="password-test",
        )
        self.editor = User.objects.create_user(
            username="editor_parametros",
            password="password-test",
        )
        self.staff_sin_permiso = User.objects.create_user(
            username="staff_sin_permiso",
            password="password-test",
            is_staff=True,
        )
        self.usuario_sin_permiso = User.objects.create_user(
            username="usuario_sin_permiso",
            password="password-test",
        )

        for usuario in (
            self.lector,
            self.editor,
            self.staff_sin_permiso,
            self.usuario_sin_permiso,
        ):
            UsuarioEmpresa.objects.create(
                usuario=usuario,
                empresa=self.empresa,
            )

        UsuarioEmpresa.objects.create(
            usuario=self.lector,
            empresa=self.otra_empresa,
        )

        asignar_permiso(
            self.lector,
            self.empresa,
            "parametros.ver",
            "LECTOR_CONFIGURACION",
        )
        asignar_permiso(
            self.editor,
            self.empresa,
            "parametros.editar",
            "EDITOR_CONFIGURACION",
        )

    def seleccionar_empresa(self, empresa=None):
        session = self.client.session
        session[SESSION_EMPRESA_ACTIVA_ID] = (
            empresa or self.empresa
        ).pk
        session.save()

    def ingresar(self, usuario, empresa=None):
        self.client.force_login(usuario)
        self.seleccionar_empresa(empresa)

    def datos_post(self):
        return {
            "moneda_funcional": "USD",
            "punto_venta_default": "0007",
            "modo_numeracion_comprobantes": "manual",
            "permite_stock_negativo": "on",
            "usa_centros_costo": "",
            "usa_proyectos": "on",
            "requiere_aprobacion_compras": "on",
            "requiere_aprobacion_pagos": "",
        }

    def test_lector_accede_en_modo_solo_lectura(self):
        inicializar_parametros_empresa(self.empresa)
        self.ingresar(self.lector)

        response = self.client.get(
            reverse("nucleo:configuracion_empresa")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Modo solo lectura")
        self.assertNotContains(response, "Guardar configuración")
        self.assertTrue(
            all(
                campo.disabled
                for campo in response.context["form"].fields.values()
            )
        )

    def test_lector_no_puede_guardar(self):
        inicializar_parametros_empresa(self.empresa)
        self.ingresar(self.lector)

        response = self.client.post(
            reverse("nucleo:configuracion_empresa"),
            self.datos_post(),
        )

        self.assertEqual(response.status_code, 403)
        moneda = ParametroSistema.objects.get(
            empresa=self.empresa,
            clave="moneda_funcional",
        )
        self.assertEqual(moneda.valor, "ARS")

    def test_lector_no_puede_inicializar(self):
        self.ingresar(self.lector)

        response = self.client.post(
            reverse("nucleo:inicializar_configuracion_empresa")
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            ParametroSistema.objects.filter(
                empresa=self.empresa
            ).exists()
        )

    def test_editor_sin_permiso_ver_puede_abrir_para_editar(self):
        self.ingresar(self.editor)

        response = self.client.get(
            reverse("nucleo:configuracion_empresa")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Inicializar configuración")

    def test_editor_puede_inicializar(self):
        self.ingresar(self.editor)

        response = self.client.post(
            reverse("nucleo:inicializar_configuracion_empresa")
        )

        self.assertRedirects(
            response,
            reverse("nucleo:configuracion_empresa"),
        )
        self.assertEqual(
            ParametroSistema.objects.filter(
                empresa=self.empresa
            ).count(),
            8,
        )

    def test_editor_puede_guardar(self):
        inicializar_parametros_empresa(self.empresa)
        self.ingresar(self.editor)

        response = self.client.post(
            reverse("nucleo:configuracion_empresa"),
            self.datos_post(),
        )

        self.assertRedirects(
            response,
            reverse("nucleo:configuracion_empresa"),
        )
        moneda = ParametroSistema.objects.get(
            empresa=self.empresa,
            clave="moneda_funcional",
        )
        self.assertEqual(moneda.valor, "USD")

    def test_staff_sin_permiso_recibe_403_personalizado(self):
        self.ingresar(self.staff_sin_permiso)

        response = self.client.get(
            reverse("nucleo:configuracion_empresa")
        )

        self.assertEqual(response.status_code, 403)
        self.assertContains(
            response,
            "No tenés permiso para realizar esta operación",
            status_code=403,
        )

    def test_navegacion_muestra_configuracion_a_lector(self):
        self.ingresar(self.lector)

        response = self.client.get(reverse("core:home"))

        self.assertContains(
            response,
            reverse("nucleo:configuracion_empresa"),
        )

    def test_navegacion_oculta_configuracion_sin_permiso(self):
        self.ingresar(self.usuario_sin_permiso)

        response = self.client.get(reverse("core:home"))

        self.assertNotContains(
            response,
            reverse("nucleo:configuracion_empresa"),
        )

    def test_sin_empresa_activa_redirige_al_selector(self):
        self.client.force_login(self.lector)
        session = self.client.session
        session.pop(SESSION_EMPRESA_ACTIVA_ID, None)
        session.save()

        response = self.client.get(
            reverse("nucleo:configuracion_empresa")
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            response.url.startswith(
                reverse("core:seleccionar_empresa")
            )
        )
        self.assertIn("next=", response.url)
