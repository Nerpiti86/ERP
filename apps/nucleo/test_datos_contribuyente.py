from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.nucleo.empresa_activa import SESSION_EMPRESA_ACTIVA_ID

from .models import (
    Empresa,
    PerfilFiscalEmpresa,
    PermisoFuncional,
    RolFuncional,
    RolPermiso,
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


class PerfilFiscalEmpresaTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            cuit="30770000111",
            razon_social="Contribuyente de Prueba SA",
        )

    def test_persona_humana_requiere_apellido_y_nombres(self):
        perfil = PerfilFiscalEmpresa(
            empresa=self.empresa,
            naturaleza=(
                PerfilFiscalEmpresa.NaturalezaContribuyente.PERSONA_HUMANA
            ),
            fecha_inicio_actividades=date(2020, 1, 1),
            mes_cierre_ejercicio_predeterminado=12,
        )

        with self.assertRaises(ValidationError):
            perfil.full_clean()

    def test_persona_juridica_rechaza_datos_personales(self):
        perfil = PerfilFiscalEmpresa(
            empresa=self.empresa,
            naturaleza=(
                PerfilFiscalEmpresa.NaturalezaContribuyente.PERSONA_JURIDICA
            ),
            fecha_inicio_actividades=date(2020, 1, 1),
            mes_cierre_ejercicio_predeterminado=12,
            apellido="No corresponde",
        )

        with self.assertRaises(ValidationError):
            perfil.full_clean()


class DatosContribuyenteViewTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            cuit="30770000222",
            razon_social="Empresa Editable SA",
            nombre_fantasia="Editable",
        )
        self.otra_empresa = Empresa.objects.create(
            cuit="30770000333",
            razon_social="Otra Empresa SA",
            nombre_fantasia="Otra",
        )

        self.lector = User.objects.create_user(
            username="lector_empresa",
            password="password-test",
        )
        self.editor = User.objects.create_user(
            username="editor_empresa",
            password="password-test",
        )
        self.sin_permiso = User.objects.create_user(
            username="sin_permiso_empresa",
            password="password-test",
        )

        for usuario in (
            self.lector,
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
            "empresas.ver",
            "LECTOR_DATOS_EMPRESA",
        )
        asignar_permiso(
            self.editor,
            self.empresa,
            "empresas.editar",
            "EDITOR_DATOS_EMPRESA",
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

    def datos_persona_humana(self):
        return {
            "cuit": "27123456789",
            "razon_social": "Pérez Ana",
            "nombre_corto": "AP - Ana",
            "naturaleza": "PERSONA_HUMANA",
            "condicion_iva": "MONOTRIBUTO",
            "fecha_inicio_actividades": "2009-01-01",
            "mes_cierre_ejercicio_predeterminado": "12",
            "activa": "on",
            "apellido": "Pérez",
            "apellido_materno": "Gómez",
            "nombres": "Ana",
            "fecha_nacimiento": "1981-05-18",
        }

    def test_lector_accede_en_modo_solo_lectura(self):
        self.ingresar(self.lector)

        response = self.client.get(
            reverse("nucleo:datos_contribuyente")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Modo solo lectura")
        self.assertNotContains(
            response,
            "Guardar datos del contribuyente",
        )
        self.assertTrue(
            all(
                campo.disabled
                for campo in response.context["form"].fields.values()
            )
        )

    def test_editor_guarda_persona_humana(self):
        self.ingresar(self.editor)

        response = self.client.post(
            reverse("nucleo:datos_contribuyente"),
            self.datos_persona_humana(),
        )

        self.assertRedirects(
            response,
            reverse("nucleo:datos_contribuyente"),
        )

        self.empresa.refresh_from_db()
        perfil = self.empresa.perfil_fiscal

        self.assertEqual(self.empresa.cuit, "27123456789")
        self.assertEqual(self.empresa.razon_social, "Pérez Ana")
        self.assertEqual(self.empresa.nombre_fantasia, "AP - Ana")
        self.assertEqual(
            self.empresa.condicion_iva,
            Empresa.CondicionIVA.MONOTRIBUTO,
        )
        self.assertEqual(
            perfil.naturaleza,
            PerfilFiscalEmpresa.NaturalezaContribuyente.PERSONA_HUMANA,
        )
        self.assertEqual(
            perfil.fecha_inicio_actividades,
            date(2009, 1, 1),
        )
        self.assertEqual(
            perfil.mes_cierre_ejercicio_predeterminado,
            12,
        )
        self.assertEqual(perfil.apellido, "Pérez")
        self.assertEqual(perfil.nombres, "Ana")
        self.assertEqual(
            perfil.fecha_nacimiento,
            date(1981, 5, 18),
        )
        self.assertTrue(perfil.esta_completo)

    def test_persona_juridica_limpia_datos_personales(self):
        PerfilFiscalEmpresa.objects.create(
            empresa=self.empresa,
            naturaleza="PERSONA_HUMANA",
            fecha_inicio_actividades=date(2009, 1, 1),
            mes_cierre_ejercicio_predeterminado=12,
            apellido="Anterior",
            apellido_materno="Dato",
            nombres="Personal",
            fecha_nacimiento=date(1980, 1, 1),
        )
        self.ingresar(self.editor)

        datos = self.datos_persona_humana()
        datos.update(
            {
                "naturaleza": "PERSONA_JURIDICA",
                "condicion_iva": "RESPONSABLE_INSCRIPTO",
                "apellido": "Debe borrarse",
                "apellido_materno": "Debe borrarse",
                "nombres": "Debe borrarse",
                "fecha_nacimiento": "1981-05-18",
            }
        )

        response = self.client.post(
            reverse("nucleo:datos_contribuyente"),
            datos,
        )

        self.assertEqual(response.status_code, 302)

        perfil = PerfilFiscalEmpresa.objects.get(
            empresa=self.empresa
        )
        self.assertEqual(perfil.apellido, "")
        self.assertEqual(perfil.apellido_materno, "")
        self.assertEqual(perfil.nombres, "")
        self.assertIsNone(perfil.fecha_nacimiento)

    def test_guardado_no_afecta_otra_empresa(self):
        PerfilFiscalEmpresa.objects.create(
            empresa=self.otra_empresa,
            naturaleza="PERSONA_JURIDICA",
            fecha_inicio_actividades=date(2015, 3, 1),
            mes_cierre_ejercicio_predeterminado=6,
        )
        self.ingresar(self.editor)

        self.client.post(
            reverse("nucleo:datos_contribuyente"),
            self.datos_persona_humana(),
        )

        self.otra_empresa.refresh_from_db()
        otro_perfil = self.otra_empresa.perfil_fiscal

        self.assertEqual(
            self.otra_empresa.razon_social,
            "Otra Empresa SA",
        )
        self.assertEqual(
            otro_perfil.mes_cierre_ejercicio_predeterminado,
            6,
        )

    def test_portada_muestra_estado_y_enlace(self):
        PerfilFiscalEmpresa.objects.create(
            empresa=self.empresa,
            naturaleza="PERSONA_JURIDICA",
            fecha_inicio_actividades=date(2011, 5, 15),
            mes_cierre_ejercicio_predeterminado=5,
        )
        self.ingresar(self.lector)

        response = self.client.get(
            reverse("nucleo:configuracion_empresa")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Datos del contribuyente")
        self.assertContains(response, "Completo")
        self.assertContains(
            response,
            reverse("nucleo:datos_contribuyente"),
        )
        self.assertContains(response, "Consultar datos")

    def test_usuario_sin_permiso_recibe_403(self):
        self.ingresar(self.sin_permiso)

        response = self.client.get(
            reverse("nucleo:datos_contribuyente")
        )

        self.assertEqual(response.status_code, 403)

    def test_navbar_se_muestra_con_empresas_ver(self):
        self.ingresar(self.lector)

        response = self.client.get(reverse("core:home"))

        self.assertContains(
            response,
            reverse("nucleo:configuracion_empresa"),
        )
