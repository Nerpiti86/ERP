from datetime import date
from io import StringIO

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.nucleo.empresa_activa import SESSION_EMPRESA_ACTIVA_ID

from .admin import (
    ActividadEconomicaAdmin,
    EmpresaActividadAdmin,
)
from .models import (
    ActividadEconomica,
    Auditoria,
    Empresa,
    EmpresaActividad,
    PermisoFuncional,
    RolFuncional,
    RolPermiso,
    UsuarioEmpresa,
    UsuarioRolEmpresa,
)
from .roles_iniciales import PERMISOS_POR_ROL
from .servicios_actividades import (
    actualizar_empresa_actividad,
    crear_empresa_actividad,
    inactivar_empresa_actividad,
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


class BaseActividadesTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            cuit="30770000111",
            razon_social="Empresa Actividades SA",
            nombre_fantasia="Actividades",
        )
        self.otra_empresa = Empresa.objects.create(
            cuit="30770000112",
            razon_social="Empresa Ajena SA",
        )
        self.actividad_uno = ActividadEconomica.objects.create(
            codigo="259993",
            descripcion=(
                "Fabricación de productos metálicos "
                "de tornería y matricería"
            ),
            fuente_url="https://oficial.example/clae",
            fuente_sha256="a" * 64,
        )
        self.actividad_dos = ActividadEconomica.objects.create(
            codigo="259999",
            descripcion=(
                "Fabricación de productos elaborados "
                "de metal n.c.p."
            ),
            fuente_url="https://oficial.example/clae",
            fuente_sha256="b" * 64,
        )
        self.actividad_tres = ActividadEconomica.objects.create(
            codigo="620100",
            descripcion="Servicios de consultores en informática",
            fuente_url="https://oficial.example/clae",
            fuente_sha256="c" * 64,
        )


class EmpresaActividadModelTests(BaseActividadesTests):
    def test_captura_instantanea_al_crear(self):
        relacion = EmpresaActividad(
            empresa=self.empresa,
            actividad=self.actividad_uno,
            principal=True,
        )
        relacion.full_clean()
        relacion.save()

        self.assertEqual(
            relacion.codigo_registrado,
            self.actividad_uno.codigo,
        )
        self.assertEqual(
            relacion.descripcion_registrada,
            self.actividad_uno.descripcion,
        )
        self.assertEqual(
            relacion.fuente_sha256_registrada,
            self.actividad_uno.fuente_sha256,
        )

    def test_rechaza_vigencia_invertida(self):
        relacion = EmpresaActividad(
            empresa=self.empresa,
            actividad=self.actividad_uno,
            vigencia_desde=date(2026, 6, 20),
            vigencia_hasta=date(2026, 6, 19),
        )

        with self.assertRaises(ValidationError):
            relacion.full_clean()

    def test_rechaza_principal_inactiva(self):
        relacion = EmpresaActividad(
            empresa=self.empresa,
            actividad=self.actividad_uno,
            principal=True,
            activa=False,
        )

        with self.assertRaises(ValidationError):
            relacion.full_clean()

    def test_restriccion_impide_dos_principales_activas(self):
        EmpresaActividad.objects.create(
            empresa=self.empresa,
            actividad=self.actividad_uno,
            principal=True,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                EmpresaActividad.objects.create(
                    empresa=self.empresa,
                    actividad=self.actividad_dos,
                    principal=True,
                )

    def test_restriccion_impide_actividad_activa_duplicada(self):
        EmpresaActividad.objects.create(
            empresa=self.empresa,
            actividad=self.actividad_uno,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                EmpresaActividad.objects.create(
                    empresa=self.empresa,
                    actividad=self.actividad_uno,
                )

    def test_permite_historial_inactivo_de_la_misma_actividad(self):
        anterior = EmpresaActividad.objects.create(
            empresa=self.empresa,
            actividad=self.actividad_uno,
            activa=False,
        )
        actual = EmpresaActividad.objects.create(
            empresa=self.empresa,
            actividad=self.actividad_uno,
            activa=True,
        )

        self.assertNotEqual(anterior.pk, actual.pk)


class ServiciosEmpresaActividadTests(BaseActividadesTests):
    def setUp(self):
        super().setUp()
        self.usuario = User.objects.create_user(
            username="auditor_actividades",
            password="password-test",
        )
        self.request = RequestFactory().post("/")
        self.request.user = self.usuario
        self.request.META["REMOTE_ADDR"] = "127.0.0.1"
        self.request.META["HTTP_USER_AGENT"] = "Pruebas ERP"

    def test_crear_registra_auditoria(self):
        relacion = crear_empresa_actividad(
            empresa=self.empresa,
            actividad=self.actividad_uno,
            principal=True,
            orden=1,
            vigencia_desde=date(2026, 1, 1),
            observaciones="Principal declarada",
            request=self.request,
        )

        auditoria = Auditoria.objects.get(
            tabla=EmpresaActividad._meta.db_table,
            registro_id=str(relacion.pk),
            accion=Auditoria.Accion.INSERT,
        )

        self.assertEqual(auditoria.empresa, self.empresa)
        self.assertEqual(auditoria.usuario, self.usuario)
        self.assertEqual(
            auditoria.datos_nuevos["codigo_registrado"],
            "259993",
        )

    def test_nueva_principal_desmarca_anterior(self):
        anterior = crear_empresa_actividad(
            empresa=self.empresa,
            actividad=self.actividad_uno,
            principal=True,
            request=self.request,
        )
        nueva = crear_empresa_actividad(
            empresa=self.empresa,
            actividad=self.actividad_dos,
            principal=True,
            request=self.request,
        )

        anterior.refresh_from_db()

        self.assertFalse(anterior.principal)
        self.assertTrue(nueva.principal)
        self.assertEqual(
            EmpresaActividad.objects.filter(
                empresa=self.empresa,
                activa=True,
                principal=True,
            ).count(),
            1,
        )

    def test_edicion_conserva_instantanea_aunque_cambie_catalogo(self):
        relacion = crear_empresa_actividad(
            empresa=self.empresa,
            actividad=self.actividad_uno,
            principal=True,
            request=self.request,
        )
        descripcion_original = relacion.descripcion_registrada

        self.actividad_uno.descripcion = "Descripción oficial nueva"
        self.actividad_uno.save(update_fields=["descripcion"])

        actualizar_empresa_actividad(
            empresa=self.empresa,
            empresa_actividad=relacion,
            principal=True,
            orden=9,
            vigencia_desde=None,
            vigencia_hasta=None,
            observaciones="Se conserva el texto histórico",
            request=self.request,
        )

        relacion.refresh_from_db()

        self.assertEqual(
            relacion.descripcion_registrada,
            descripcion_original,
        )
        self.assertEqual(relacion.orden, 9)

    def test_inactivar_quita_principal_y_fija_fecha(self):
        relacion = crear_empresa_actividad(
            empresa=self.empresa,
            actividad=self.actividad_uno,
            principal=True,
            vigencia_desde=date(2026, 1, 1),
            request=self.request,
        )

        inactivar_empresa_actividad(
            empresa=self.empresa,
            empresa_actividad=relacion,
            request=self.request,
        )

        relacion.refresh_from_db()

        self.assertFalse(relacion.activa)
        self.assertFalse(relacion.principal)
        self.assertIsNotNone(relacion.vigencia_hasta)

    def test_no_permite_asignar_catalogo_inactivo(self):
        self.actividad_uno.activa = False
        self.actividad_uno.save(update_fields=["activa"])

        with self.assertRaises(ValidationError):
            crear_empresa_actividad(
                empresa=self.empresa,
                actividad=self.actividad_uno,
            )


class ActividadesEmpresaViewsTests(BaseActividadesTests):
    def setUp(self):
        super().setUp()
        self.editor = User.objects.create_user(
            username="editor_actividades",
            password="password-test",
        )
        self.lector = User.objects.create_user(
            username="lector_actividades",
            password="password-test",
        )
        self.sin_permiso = User.objects.create_user(
            username="sin_permiso_actividades",
            password="password-test",
        )

        for usuario in (
            self.editor,
            self.lector,
            self.sin_permiso,
        ):
            UsuarioEmpresa.objects.create(
                usuario=usuario,
                empresa=self.empresa,
            )

        asignar_permiso(
            self.editor,
            self.empresa,
            "actividades.ver",
            "ACTIVIDADES_EDITOR_VER",
        )
        asignar_permiso(
            self.editor,
            self.empresa,
            "actividades.crear",
            "ACTIVIDADES_EDITOR_CREAR",
        )
        asignar_permiso(
            self.editor,
            self.empresa,
            "actividades.editar",
            "ACTIVIDADES_EDITOR_EDITAR",
        )
        asignar_permiso(
            self.lector,
            self.empresa,
            "actividades.ver",
            "ACTIVIDADES_LECTOR",
        )

    def ingresar(self, usuario):
        self.client.force_login(usuario)
        session = self.client.session
        session[SESSION_EMPRESA_ACTIVA_ID] = self.empresa.pk
        session.save()

    def datos_post(self, actividad=None, principal=True):
        actividad = actividad or self.actividad_uno

        return {
            "actividad_id": str(actividad.pk),
            "actividad_texto": (
                f"{actividad.codigo} - {actividad.descripcion}"
            ),
            "principal": "on" if principal else "",
            "orden": "0",
            "vigencia_desde": "2026-01-01",
            "vigencia_hasta": "",
            "observaciones": "Carga de prueba",
        }

    def test_portada_muestra_tarjeta_actividades(self):
        self.ingresar(self.lector)

        response = self.client.get(
            reverse("nucleo:configuracion_empresa")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Actividades económicas")
        self.assertContains(
            response,
            reverse("nucleo:actividades_empresa"),
        )

    def test_editor_crea_actividad(self):
        self.ingresar(self.editor)

        response = self.client.post(
            reverse("nucleo:actividad_empresa_crear"),
            self.datos_post(),
        )

        self.assertRedirects(
            response,
            reverse("nucleo:actividades_empresa"),
        )
        relacion = EmpresaActividad.objects.get(
            empresa=self.empresa,
            actividad=self.actividad_uno,
        )
        self.assertTrue(relacion.principal)

    def test_lector_no_puede_crear(self):
        self.ingresar(self.lector)

        response = self.client.post(
            reverse("nucleo:actividad_empresa_crear"),
            self.datos_post(),
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            EmpresaActividad.objects.filter(
                empresa=self.empresa,
            ).exists()
        )

    def test_usuario_sin_permiso_no_puede_listar(self):
        self.ingresar(self.sin_permiso)

        response = self.client.get(
            reverse("nucleo:actividades_empresa")
        )

        self.assertEqual(response.status_code, 403)

    def test_edicion_rechaza_relacion_de_otra_empresa(self):
        relacion = crear_empresa_actividad(
            empresa=self.otra_empresa,
            actividad=self.actividad_uno,
            principal=True,
        )
        self.ingresar(self.editor)

        response = self.client.get(
            reverse(
                "nucleo:actividad_empresa_editar",
                args=[relacion.pk],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_busqueda_filtra_y_excluye_actividad_asignada(self):
        crear_empresa_actividad(
            empresa=self.empresa,
            actividad=self.actividad_uno,
            principal=True,
        )
        self.ingresar(self.editor)

        response = self.client.get(
            reverse("nucleo:catalogo_actividades_buscar"),
            {"q": "259"},
        )

        self.assertEqual(response.status_code, 200)
        codigos = {
            item["codigo"]
            for item in response.json()["results"]
        }
        self.assertNotIn("259993", codigos)
        self.assertIn("259999", codigos)

    def test_alta_bloqueada_si_catalogo_esta_vacio(self):
        ActividadEconomica.objects.all().delete()
        self.ingresar(self.editor)

        response = self.client.get(
            reverse("nucleo:actividad_empresa_crear")
        )

        self.assertRedirects(
            response,
            reverse("nucleo:actividades_empresa"),
        )


class PermisosActividadesTests(TestCase):
    def test_matriz_inicial_asigna_permisos_correctos(self):
        salida = StringIO()
        call_command(
            "cargar_roles_permisos_iniciales",
            stdout=salida,
        )

        self.assertIn(
            "actividades.ver",
            PERMISOS_POR_ROL["CONTADOR"],
        )
        self.assertIn(
            "actividades.crear",
            PERMISOS_POR_ROL["CONTADOR"],
        )
        self.assertIn(
            "actividades.editar",
            PERMISOS_POR_ROL["CONTADOR"],
        )
        self.assertIn(
            "actividades.ver",
            PERMISOS_POR_ROL["AUDITOR"],
        )
        self.assertIn(
            "actividades.ver",
            PERMISOS_POR_ROL["SOLO_LECTURA"],
        )
        self.assertNotIn(
            "actividades.ver",
            PERMISOS_POR_ROL["OPERADOR"],
        )


class AdminCatalogoActividadesTests(BaseActividadesTests):
    def setUp(self):
        super().setUp()
        self.superuser = User.objects.create_superuser(
            username="admin_catalogo",
            password="password-test",
        )
        self.request = RequestFactory().get("/admin/")
        self.request.user = self.superuser

    def test_catalogo_oficial_es_solo_lectura(self):
        model_admin = ActividadEconomicaAdmin(
            ActividadEconomica,
            admin.site,
        )

        self.assertFalse(model_admin.has_add_permission(self.request))
        self.assertFalse(
            model_admin.has_change_permission(
                self.request,
                self.actividad_uno,
            )
        )
        self.assertFalse(
            model_admin.has_delete_permission(
                self.request,
                self.actividad_uno,
            )
        )

    def test_relaciones_empresa_son_solo_lectura_en_admin(self):
        relacion = crear_empresa_actividad(
            empresa=self.empresa,
            actividad=self.actividad_uno,
            principal=True,
        )
        model_admin = EmpresaActividadAdmin(
            EmpresaActividad,
            admin.site,
        )

        self.assertFalse(model_admin.has_add_permission(self.request))
        self.assertFalse(
            model_admin.has_change_permission(
                self.request,
                relacion,
            )
        )
        self.assertFalse(
            model_admin.has_delete_permission(
                self.request,
                relacion,
            )
        )
