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
    ConfiguracionIIBBEmpresaAdmin,
    EmpresaJurisdiccionIIBBAdmin,
    JurisdiccionFiscalAdmin,
)
from .forms import (
    ConfiguracionIIBBEmpresaForm,
    EmpresaJurisdiccionIIBBCrearForm,
)
from .models import (
    Auditoria,
    ConfiguracionIIBBEmpresa,
    Empresa,
    EmpresaJurisdiccionIIBB,
    JurisdiccionFiscal,
    PermisoFuncional,
    RolFuncional,
    RolPermiso,
    UsuarioEmpresa,
    UsuarioRolEmpresa,
)
from .roles_iniciales import PERMISOS_POR_ROL
from .servicios_iibb import (
    actualizar_configuracion_iibb,
    actualizar_jurisdiccion_iibb,
    crear_configuracion_iibb,
    crear_jurisdiccion_iibb,
    inactivar_configuracion_iibb,
    inactivar_jurisdiccion_iibb,
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


class BaseIIBBTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            cuit="30770000701",
            razon_social="Empresa IIBB SA",
            nombre_fantasia="Empresa IIBB",
        )
        self.otra_empresa = Empresa.objects.create(
            cuit="30770000702",
            razon_social="Otra Empresa IIBB SA",
            nombre_fantasia="Otra IIBB",
        )
        self.santa_fe = JurisdiccionFiscal.objects.get(codigo="921")
        self.cordoba = JurisdiccionFiscal.objects.get(codigo="904")
        self.usuario = User.objects.create_user(
            username="usuario_iibb_base",
            password="password-test",
        )
        self.request = RequestFactory().post("/nucleo/configuracion/")
        self.request.user = self.usuario
        self.request.META["REMOTE_ADDR"] = "127.0.0.1"

    def crear_configuracion(
        self,
        *,
        empresa=None,
        regimen=ConfiguracionIIBBEmpresa.Regimen.LOCAL,
    ):
        empresa = empresa or self.empresa
        numero = ""
        fecha_alta = None

        if regimen != ConfiguracionIIBBEmpresa.Regimen.NO_INSCRIPTO:
            numero = "30770000701"
            fecha_alta = date(2026, 1, 1)

        return crear_configuracion_iibb(
            empresa=empresa,
            regimen=regimen,
            tratamiento_general=(
                ConfiguracionIIBBEmpresa.TratamientoGeneral.GRAVADO
            ),
            numero_inscripcion=numero,
            fecha_alta=fecha_alta,
            observaciones="Configuración de prueba",
            request=self.request,
        )


class CatalogoJurisdiccionesTests(BaseIIBBTests):
    def test_migracion_carga_24_jurisdicciones(self):
        self.assertEqual(JurisdiccionFiscal.objects.count(), 24)
        self.assertEqual(
            JurisdiccionFiscal.objects.get(codigo="901").nombre,
            "Ciudad Autónoma de Buenos Aires",
        )
        self.assertEqual(
            JurisdiccionFiscal.objects.get(codigo="924").nombre,
            "Tucumán",
        )

    def test_catalogo_tiene_codigos_contiguos_901_924(self):
        codigos = list(
            JurisdiccionFiscal.objects.order_by("codigo").values_list(
                "codigo",
                flat=True,
            )
        )
        self.assertEqual(
            codigos,
            [str(codigo) for codigo in range(901, 925)],
        )


class ConfiguracionIIBBModelTests(BaseIIBBTests):
    def test_regimen_local_requiere_numero_y_fecha(self):
        configuracion = ConfiguracionIIBBEmpresa(
            empresa=self.empresa,
            regimen=ConfiguracionIIBBEmpresa.Regimen.LOCAL,
            tratamiento_general=(
                ConfiguracionIIBBEmpresa.TratamientoGeneral.GRAVADO
            ),
        )

        with self.assertRaises(ValidationError):
            configuracion.full_clean()

    def test_no_inscripto_rechaza_numero(self):
        configuracion = ConfiguracionIIBBEmpresa(
            empresa=self.empresa,
            regimen=ConfiguracionIIBBEmpresa.Regimen.NO_INSCRIPTO,
            tratamiento_general=(
                ConfiguracionIIBBEmpresa.TratamientoGeneral.NO_ALCANZADO
            ),
            numero_inscripcion="123",
        )

        with self.assertRaises(ValidationError):
            configuracion.full_clean()

    def test_unica_configuracion_activa_por_empresa(self):
        self.crear_configuracion()

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ConfiguracionIIBBEmpresa.objects.create(
                    empresa=self.empresa,
                    regimen=ConfiguracionIIBBEmpresa.Regimen.LOCAL,
                    tratamiento_general=(
                        ConfiguracionIIBBEmpresa.TratamientoGeneral.GRAVADO
                    ),
                    numero_inscripcion="OTRA",
                    fecha_alta=date(2026, 1, 1),
                )

    def test_no_inscripto_sin_jurisdicciones_esta_completo(self):
        configuracion = self.crear_configuracion(
            regimen=ConfiguracionIIBBEmpresa.Regimen.NO_INSCRIPTO,
        )
        self.assertTrue(configuracion.esta_completa)

    def test_local_sin_jurisdiccion_esta_incompleto(self):
        configuracion = self.crear_configuracion()
        self.assertFalse(configuracion.esta_completa)

    def test_fecha_baja_no_puede_ser_anterior(self):
        configuracion = ConfiguracionIIBBEmpresa(
            empresa=self.empresa,
            regimen=ConfiguracionIIBBEmpresa.Regimen.LOCAL,
            tratamiento_general=(
                ConfiguracionIIBBEmpresa.TratamientoGeneral.GRAVADO
            ),
            numero_inscripcion="123",
            fecha_alta=date(2026, 2, 1),
            fecha_baja=date(2026, 1, 1),
            activa=False,
        )

        with self.assertRaises(ValidationError):
            configuracion.full_clean()


class JurisdiccionIIBBModelTests(BaseIIBBTests):
    def setUp(self):
        super().setUp()
        self.configuracion = self.crear_configuracion(
            regimen=ConfiguracionIIBBEmpresa.Regimen.CONVENIO_MULTILATERAL,
        )

    def test_primera_jurisdiccion_con_servicio_es_sede(self):
        relacion = crear_jurisdiccion_iibb(
            empresa=self.empresa,
            configuracion=self.configuracion,
            jurisdiccion=self.santa_fe,
            fecha_alta=date(2026, 1, 1),
        )
        self.assertTrue(relacion.sede)
        self.assertTrue(self.configuracion.esta_completa)

    def test_snapshot_no_cambia_si_cambia_catalogo(self):
        relacion = crear_jurisdiccion_iibb(
            empresa=self.empresa,
            configuracion=self.configuracion,
            jurisdiccion=self.santa_fe,
            fecha_alta=date(2026, 1, 1),
        )
        nombre = relacion.nombre_registrado
        self.santa_fe.nombre = "Santa Fe actualizada"
        self.santa_fe.save(update_fields=["nombre"])

        relacion.refresh_from_db()
        self.assertEqual(relacion.nombre_registrado, nombre)

    def test_no_permite_dos_sedes_activas(self):
        crear_jurisdiccion_iibb(
            empresa=self.empresa,
            configuracion=self.configuracion,
            jurisdiccion=self.santa_fe,
            fecha_alta=date(2026, 1, 1),
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                EmpresaJurisdiccionIIBB.objects.create(
                    configuracion=self.configuracion,
                    jurisdiccion=self.cordoba,
                    sede=True,
                    fecha_alta=date(2026, 1, 1),
                    codigo_registrado="904",
                    nombre_registrado="Córdoba",
                )

    def test_jurisdiccion_activa_requiere_fecha_alta(self):
        relacion = EmpresaJurisdiccionIIBB(
            configuracion=self.configuracion,
            jurisdiccion=self.santa_fe,
            sede=True,
        )

        with self.assertRaises(ValidationError):
            relacion.full_clean()

    def test_regimen_local_rechaza_segunda_jurisdiccion(self):
        configuracion = self.configuracion
        configuracion.regimen = ConfiguracionIIBBEmpresa.Regimen.LOCAL
        configuracion.save(update_fields=["regimen"])
        crear_jurisdiccion_iibb(
            empresa=self.empresa,
            configuracion=configuracion,
            jurisdiccion=self.santa_fe,
            fecha_alta=date(2026, 1, 1),
        )

        with self.assertRaises(ValidationError):
            crear_jurisdiccion_iibb(
                empresa=self.empresa,
                configuracion=configuracion,
                jurisdiccion=self.cordoba,
                fecha_alta=date(2026, 1, 1),
            )


class ServiciosIIBBTests(BaseIIBBTests):
    def test_crear_configuracion_registra_auditoria(self):
        configuracion = self.crear_configuracion()

        auditoria = Auditoria.objects.get(
            tabla=ConfiguracionIIBBEmpresa._meta.db_table,
            registro_id=str(configuracion.pk),
        )
        self.assertEqual(auditoria.accion, Auditoria.Accion.INSERT)
        self.assertEqual(auditoria.usuario, self.usuario)

    def test_cambiar_sede_desmarca_anterior(self):
        configuracion = self.crear_configuracion(
            regimen=ConfiguracionIIBBEmpresa.Regimen.CONVENIO_MULTILATERAL,
        )
        primera = crear_jurisdiccion_iibb(
            empresa=self.empresa,
            configuracion=configuracion,
            jurisdiccion=self.santa_fe,
            fecha_alta=date(2026, 1, 1),
            request=self.request,
        )
        segunda = crear_jurisdiccion_iibb(
            empresa=self.empresa,
            configuracion=configuracion,
            jurisdiccion=self.cordoba,
            fecha_alta=date(2026, 1, 1),
            sede=True,
            request=self.request,
        )

        primera.refresh_from_db()
        segunda.refresh_from_db()
        self.assertFalse(primera.sede)
        self.assertTrue(segunda.sede)

    def test_inactivar_sede_promueve_otra(self):
        configuracion = self.crear_configuracion(
            regimen=ConfiguracionIIBBEmpresa.Regimen.CONVENIO_MULTILATERAL,
        )
        primera = crear_jurisdiccion_iibb(
            empresa=self.empresa,
            configuracion=configuracion,
            jurisdiccion=self.santa_fe,
            fecha_alta=date(2026, 1, 1),
        )
        segunda = crear_jurisdiccion_iibb(
            empresa=self.empresa,
            configuracion=configuracion,
            jurisdiccion=self.cordoba,
            fecha_alta=date(2026, 1, 1),
        )

        inactivar_jurisdiccion_iibb(
            empresa=self.empresa,
            relacion=primera,
            request=self.request,
        )

        primera.refresh_from_db()
        segunda.refresh_from_db()
        self.assertFalse(primera.activa)
        self.assertTrue(segunda.sede)

    def test_no_permite_quitar_sede_directamente(self):
        configuracion = self.crear_configuracion()
        relacion = crear_jurisdiccion_iibb(
            empresa=self.empresa,
            configuracion=configuracion,
            jurisdiccion=self.santa_fe,
            fecha_alta=date(2026, 1, 1),
        )

        with self.assertRaises(ValidationError):
            actualizar_jurisdiccion_iibb(
                empresa=self.empresa,
                relacion=relacion,
                numero_inscripcion="",
                sede=False,
                tratamiento=relacion.tratamiento,
                fecha_alta=relacion.fecha_alta,
                observaciones="",
            )

    def test_no_permite_no_inscripto_con_jurisdicciones(self):
        configuracion = self.crear_configuracion()
        crear_jurisdiccion_iibb(
            empresa=self.empresa,
            configuracion=configuracion,
            jurisdiccion=self.santa_fe,
            fecha_alta=date(2026, 1, 1),
        )

        with self.assertRaises(ValidationError):
            actualizar_configuracion_iibb(
                empresa=self.empresa,
                configuracion=configuracion,
                regimen=ConfiguracionIIBBEmpresa.Regimen.NO_INSCRIPTO,
                tratamiento_general=(
                    ConfiguracionIIBBEmpresa.TratamientoGeneral.NO_ALCANZADO
                ),
                numero_inscripcion="",
                fecha_alta=None,
                observaciones="",
            )

    def test_inactivar_configuracion_inactiva_jurisdicciones(self):
        configuracion = self.crear_configuracion()
        relacion = crear_jurisdiccion_iibb(
            empresa=self.empresa,
            configuracion=configuracion,
            jurisdiccion=self.santa_fe,
            fecha_alta=date(2026, 1, 1),
        )

        inactivar_configuracion_iibb(
            empresa=self.empresa,
            configuracion=configuracion,
            request=self.request,
        )

        configuracion.refresh_from_db()
        relacion.refresh_from_db()
        self.assertFalse(configuracion.activa)
        self.assertIsNotNone(configuracion.fecha_baja)
        self.assertFalse(relacion.activa)
        self.assertFalse(relacion.sede)

    def test_servicio_rechaza_configuracion_de_otra_empresa(self):
        configuracion = self.crear_configuracion(empresa=self.otra_empresa)

        with self.assertRaises(ValidationError):
            actualizar_configuracion_iibb(
                empresa=self.empresa,
                configuracion=configuracion,
                regimen=configuracion.regimen,
                tratamiento_general=configuracion.tratamiento_general,
                numero_inscripcion=configuracion.numero_inscripcion,
                fecha_alta=configuracion.fecha_alta,
                observaciones="",
            )


class FormulariosIIBBTests(BaseIIBBTests):
    def test_no_inscripto_limpia_numero_y_fecha(self):
        form = ConfiguracionIIBBEmpresaForm(
            {
                "regimen": ConfiguracionIIBBEmpresa.Regimen.NO_INSCRIPTO,
                "tratamiento_general": (
                    ConfiguracionIIBBEmpresa.TratamientoGeneral.NO_ALCANZADO
                ),
                "numero_inscripcion": "123",
                "fecha_alta": "2026-01-01",
                "observaciones": "",
            },
            empresa=self.empresa,
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["numero_inscripcion"], "")
        self.assertIsNone(form.cleaned_data["fecha_alta"])

    def test_local_requiere_numero_y_fecha(self):
        form = ConfiguracionIIBBEmpresaForm(
            {
                "regimen": ConfiguracionIIBBEmpresa.Regimen.LOCAL,
                "tratamiento_general": (
                    ConfiguracionIIBBEmpresa.TratamientoGeneral.GRAVADO
                ),
                "numero_inscripcion": "",
                "fecha_alta": "",
                "observaciones": "",
            },
            empresa=self.empresa,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("numero_inscripcion", form.errors)
        self.assertIn("fecha_alta", form.errors)

    def test_form_jurisdiccion_excluye_asignada(self):
        configuracion = self.crear_configuracion(
            regimen=ConfiguracionIIBBEmpresa.Regimen.CONVENIO_MULTILATERAL,
        )
        crear_jurisdiccion_iibb(
            empresa=self.empresa,
            configuracion=configuracion,
            jurisdiccion=self.santa_fe,
            fecha_alta=date(2026, 1, 1),
        )

        form = EmpresaJurisdiccionIIBBCrearForm(
            configuracion=configuracion,
        )
        self.assertNotIn(
            self.santa_fe,
            list(form.fields["jurisdiccion"].queryset),
        )
        self.assertIn(
            self.cordoba,
            list(form.fields["jurisdiccion"].queryset),
        )


class IIBBViewsTests(BaseIIBBTests):
    def setUp(self):
        super().setUp()
        self.editor = User.objects.create_user(
            username="editor_iibb",
            password="password-test",
        )
        self.lector = User.objects.create_user(
            username="lector_iibb",
            password="password-test",
        )
        self.sin_permiso = User.objects.create_user(
            username="sin_permiso_iibb",
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
            "iibb.ver",
            "IIBB_EDITOR_VER",
        )
        asignar_permiso(
            self.editor,
            self.empresa,
            "iibb.crear",
            "IIBB_EDITOR_CREAR",
        )
        asignar_permiso(
            self.editor,
            self.empresa,
            "iibb.editar",
            "IIBB_EDITOR_EDITAR",
        )
        asignar_permiso(
            self.lector,
            self.empresa,
            "iibb.ver",
            "IIBB_LECTOR",
        )

    def ingresar(self, usuario):
        self.client.force_login(usuario)
        session = self.client.session
        session[SESSION_EMPRESA_ACTIVA_ID] = self.empresa.pk
        session.save()

    def datos_configuracion(self):
        return {
            "regimen": ConfiguracionIIBBEmpresa.Regimen.LOCAL,
            "tratamiento_general": (
                ConfiguracionIIBBEmpresa.TratamientoGeneral.GRAVADO
            ),
            "numero_inscripcion": "921-123456-7",
            "fecha_alta": "2026-01-01",
            "observaciones": "Prueba de vista",
        }

    def test_portada_muestra_tarjeta_iibb(self):
        self.ingresar(self.lector)
        response = self.client.get(
            reverse("nucleo:configuracion_empresa")
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ingresos Brutos")
        self.assertContains(
            response,
            reverse("nucleo:ingresos_brutos"),
        )

    def test_editor_crea_configuracion(self):
        self.ingresar(self.editor)
        response = self.client.post(
            reverse("nucleo:configuracion_iibb_crear"),
            self.datos_configuracion(),
        )
        self.assertRedirects(
            response,
            reverse("nucleo:ingresos_brutos"),
        )
        self.assertTrue(
            ConfiguracionIIBBEmpresa.objects.filter(
                empresa=self.empresa,
                activa=True,
            ).exists()
        )

    def test_editor_agrega_jurisdiccion(self):
        configuracion = self.crear_configuracion()
        self.ingresar(self.editor)
        response = self.client.post(
            reverse(
                "nucleo:jurisdiccion_iibb_crear",
                args=[configuracion.pk],
            ),
            {
                "jurisdiccion": str(self.santa_fe.pk),
                "numero_inscripcion": "SF-123",
                "sede": "on",
                "tratamiento": (
                    EmpresaJurisdiccionIIBB.Tratamiento.SEGUN_CONFIGURACION
                ),
                "fecha_alta": "2026-01-01",
                "observaciones": "",
            },
        )
        self.assertRedirects(
            response,
            reverse("nucleo:ingresos_brutos"),
        )
        self.assertTrue(
            EmpresaJurisdiccionIIBB.objects.filter(
                configuracion=configuracion,
                jurisdiccion=self.santa_fe,
                activa=True,
                sede=True,
            ).exists()
        )

    def test_lector_no_puede_crear(self):
        self.ingresar(self.lector)
        response = self.client.post(
            reverse("nucleo:configuracion_iibb_crear"),
            self.datos_configuracion(),
        )
        self.assertEqual(response.status_code, 403)

    def test_usuario_sin_permiso_no_puede_listar(self):
        self.ingresar(self.sin_permiso)
        response = self.client.get(
            reverse("nucleo:ingresos_brutos")
        )
        self.assertEqual(response.status_code, 403)

    def test_edicion_rechaza_configuracion_de_otra_empresa(self):
        configuracion = self.crear_configuracion(empresa=self.otra_empresa)
        self.ingresar(self.editor)
        response = self.client.get(
            reverse(
                "nucleo:configuracion_iibb_editar",
                args=[configuracion.pk],
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_edicion_rechaza_jurisdiccion_de_otra_empresa(self):
        configuracion = self.crear_configuracion(empresa=self.otra_empresa)
        relacion = crear_jurisdiccion_iibb(
            empresa=self.otra_empresa,
            configuracion=configuracion,
            jurisdiccion=self.santa_fe,
            fecha_alta=date(2026, 1, 1),
        )
        self.ingresar(self.editor)
        response = self.client.get(
            reverse(
                "nucleo:jurisdiccion_iibb_editar",
                args=[relacion.pk],
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_listado_muestra_historial_de_jurisdicciones(self):
        configuracion = self.crear_configuracion()
        relacion = crear_jurisdiccion_iibb(
            empresa=self.empresa,
            configuracion=configuracion,
            jurisdiccion=self.santa_fe,
            fecha_alta=date(2026, 1, 1),
        )
        inactivar_jurisdiccion_iibb(
            empresa=self.empresa,
            relacion=relacion,
        )

        self.ingresar(self.editor)
        response = self.client.get(
            reverse("nucleo:ingresos_brutos")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Historial de jurisdicciones")
        self.assertContains(response, "Santa Fe")


class PermisosIIBBTests(TestCase):
    def test_matriz_inicial_asigna_permisos_correctos(self):
        salida = StringIO()
        call_command(
            "cargar_roles_permisos_iniciales",
            stdout=salida,
        )

        for permiso in ("iibb.ver", "iibb.crear", "iibb.editar"):
            self.assertIn(permiso, PERMISOS_POR_ROL["ADMIN"])
            self.assertIn(permiso, PERMISOS_POR_ROL["CONTADOR"])

        self.assertIn("iibb.ver", PERMISOS_POR_ROL["AUDITOR"])
        self.assertIn("iibb.ver", PERMISOS_POR_ROL["SOLO_LECTURA"])
        self.assertNotIn("iibb.ver", PERMISOS_POR_ROL["OPERADOR"])


class AdminIIBBTests(BaseIIBBTests):
    def setUp(self):
        super().setUp()
        self.superuser = User.objects.create_superuser(
            username="admin_iibb",
            password="password-test",
        )
        self.admin_request = RequestFactory().get("/admin/")
        self.admin_request.user = self.superuser

    def test_catalogo_jurisdicciones_es_solo_lectura(self):
        model_admin = JurisdiccionFiscalAdmin(
            JurisdiccionFiscal,
            admin.site,
        )
        self.assertFalse(
            model_admin.has_add_permission(self.admin_request)
        )
        self.assertFalse(
            model_admin.has_change_permission(
                self.admin_request,
                self.santa_fe,
            )
        )
        self.assertFalse(
            model_admin.has_delete_permission(
                self.admin_request,
                self.santa_fe,
            )
        )

    def test_configuracion_y_relaciones_son_solo_lectura(self):
        configuracion = self.crear_configuracion()
        relacion = crear_jurisdiccion_iibb(
            empresa=self.empresa,
            configuracion=configuracion,
            jurisdiccion=self.santa_fe,
            fecha_alta=date(2026, 1, 1),
        )

        config_admin = ConfiguracionIIBBEmpresaAdmin(
            ConfiguracionIIBBEmpresa,
            admin.site,
        )
        relacion_admin = EmpresaJurisdiccionIIBBAdmin(
            EmpresaJurisdiccionIIBB,
            admin.site,
        )

        self.assertFalse(
            config_admin.has_change_permission(
                self.admin_request,
                configuracion,
            )
        )
        self.assertFalse(
            relacion_admin.has_change_permission(
                self.admin_request,
                relacion,
            )
        )
