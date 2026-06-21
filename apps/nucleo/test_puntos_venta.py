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

from .admin import PuntoVentaAdmin
from .forms import (
    PuntoVentaCrearForm,
    PuntoVentaEditarForm,
    SucursalForm,
)
from .models import (
    Auditoria,
    Empresa,
    ParametroSistema,
    PermisoFuncional,
    PuntoVenta,
    RolFuncional,
    RolPermiso,
    Sucursal,
    UsuarioEmpresa,
    UsuarioRolEmpresa,
)
from .roles_iniciales import PERMISOS_POR_ROL
from .servicios_puntos_venta import (
    actualizar_punto_venta,
    crear_punto_venta,
    inactivar_punto_venta,
    obtener_numero_punto_venta_legacy,
)
from .views import _resumen_puntos_venta


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


class BasePuntosVentaTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            cuit="30770000801",
            razon_social="Empresa Puntos SA",
            nombre_fantasia="Puntos",
        )
        self.otra_empresa = Empresa.objects.create(
            cuit="30770000802",
            razon_social="Empresa Ajena SA",
            nombre_fantasia="Ajena",
        )
        self.sucursal = Sucursal.objects.create(
            empresa=self.empresa,
            codigo="CENTRAL",
            nombre="Casa central",
            calle="Pasco",
            numero="240",
            localidad="Rosario",
            codigo_postal="2000",
            es_casa_central=True,
        )
        self.otra_sucursal = Sucursal.objects.create(
            empresa=self.empresa,
            codigo="NORTE",
            nombre="Sucursal norte",
            calle="Calle Norte",
            numero="100",
            localidad="Rosario",
            codigo_postal="2000",
        )
        self.sucursal_ajena = Sucursal.objects.create(
            empresa=self.otra_empresa,
            codigo="AJENA",
            nombre="Sucursal ajena",
            calle="Otra",
            numero="1",
            localidad="Rosario",
            codigo_postal="2000",
        )
        self.usuario = User.objects.create_user(
            username="usuario_puntos",
            password="password-test",
        )
        self.request = RequestFactory().post("/nucleo/configuracion/")
        self.request.user = self.usuario
        self.request.META["REMOTE_ADDR"] = "127.0.0.1"

    def crear_punto(
        self,
        *,
        empresa=None,
        sucursal=None,
        numero=1,
        predeterminado=False,
    ):
        return crear_punto_venta(
            empresa=empresa or self.empresa,
            sucursal=sucursal or self.sucursal,
            numero=numero,
            sistema_emision=PuntoVenta.SistemaEmision.WEB_SERVICE,
            nombre_fantasia="Ventas",
            predeterminado=predeterminado,
            fecha_alta=date(2026, 1, 1),
            request=self.request,
        )


class ResumenPuntosVentaTests(BasePuntosVentaTests):
    def test_sucursal_sin_puntos_no_invalida_configuracion(self):
        punto = self.crear_punto(numero=1)
        resumen = _resumen_puntos_venta(
            [punto],
            [self.sucursal, self.otra_sucursal],
        )
        self.assertTrue(resumen["completa"])
        self.assertEqual(resumen["sucursales_con_puntos"], 1)
        self.assertEqual(resumen["sucursales_sin_puntos"], 1)

    def test_sin_puntos_la_configuracion_es_incompleta(self):
        resumen = _resumen_puntos_venta(
            [],
            [self.sucursal, self.otra_sucursal],
        )
        self.assertFalse(resumen["completa"])


class PuntoVentaModelTests(BasePuntosVentaTests):
    def test_numero_se_muestra_con_cinco_posiciones(self):
        punto = self.crear_punto(numero=1)
        self.assertEqual(punto.numero_formateado, "00001")

    def test_numero_es_unico_por_empresa_incluso_inactivo(self):
        punto = self.crear_punto(numero=7)
        inactivar_punto_venta(
            empresa=self.empresa,
            punto_venta=punto,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PuntoVenta.objects.create(
                    empresa=self.empresa,
                    sucursal=self.sucursal,
                    numero=7,
                    sistema_emision=PuntoVenta.SistemaEmision.WEB_SERVICE,
                )

    def test_mismo_numero_se_admite_en_otra_empresa(self):
        self.crear_punto(numero=1)
        punto_ajeno = crear_punto_venta(
            empresa=self.otra_empresa,
            sucursal=self.sucursal_ajena,
            numero=1,
            sistema_emision=PuntoVenta.SistemaEmision.WEB_SERVICE,
        )
        self.assertEqual(punto_ajeno.numero, 1)

    def test_rechaza_sucursal_de_otra_empresa(self):
        punto = PuntoVenta(
            empresa=self.empresa,
            sucursal=self.sucursal_ajena,
            numero=10,
            sistema_emision=PuntoVenta.SistemaEmision.WEB_SERVICE,
        )
        with self.assertRaises(ValidationError):
            punto.full_clean()

    def test_rechaza_numero_fuera_de_rango(self):
        punto = PuntoVenta(
            empresa=self.empresa,
            sucursal=self.sucursal,
            numero=99999,
            sistema_emision=PuntoVenta.SistemaEmision.WEB_SERVICE,
        )
        with self.assertRaises(ValidationError):
            punto.full_clean()

    def test_no_permite_dos_predeterminados_activos_por_sucursal(self):
        self.crear_punto(numero=1, predeterminado=True)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PuntoVenta.objects.create(
                    empresa=self.empresa,
                    sucursal=self.sucursal,
                    numero=2,
                    sistema_emision=PuntoVenta.SistemaEmision.WEB_SERVICE,
                    predeterminado=True,
                )

    def test_numero_no_puede_cambiar(self):
        punto = self.crear_punto(numero=3)
        punto.numero = 4
        with self.assertRaises(ValidationError):
            punto.full_clean()


class ServiciosPuntosVentaTests(BasePuntosVentaTests):
    def test_primer_punto_es_predeterminado(self):
        punto = self.crear_punto(numero=1, predeterminado=False)
        self.assertTrue(punto.predeterminado)

    def test_cambiar_predeterminado_desmarca_anterior(self):
        primero = self.crear_punto(numero=1)
        segundo = self.crear_punto(
            numero=2,
            predeterminado=True,
        )
        primero.refresh_from_db()
        segundo.refresh_from_db()
        self.assertFalse(primero.predeterminado)
        self.assertTrue(segundo.predeterminado)

    def test_inactivar_predeterminado_promueve_otro(self):
        primero = self.crear_punto(numero=1)
        segundo = self.crear_punto(numero=2)

        inactivar_punto_venta(
            empresa=self.empresa,
            punto_venta=primero,
            request=self.request,
        )

        primero.refresh_from_db()
        segundo.refresh_from_db()
        self.assertFalse(primero.activo)
        self.assertFalse(primero.predeterminado)
        self.assertTrue(segundo.predeterminado)
        self.assertIsNotNone(primero.fecha_baja)

    def test_mover_predeterminado_deja_predeterminado_en_origen(self):
        primero = self.crear_punto(numero=1)
        segundo = self.crear_punto(numero=2)

        actualizar_punto_venta(
            empresa=self.empresa,
            punto_venta=primero,
            sucursal=self.otra_sucursal,
            sistema_emision=primero.sistema_emision,
            nombre_fantasia=primero.nombre_fantasia,
            descripcion_sistema_arca="",
            actividad_predeterminada=None,
            jurisdiccion_iibb_predeterminada=None,
            predeterminado=True,
            bloqueado=False,
            fecha_alta=primero.fecha_alta,
            observaciones="",
            request=self.request,
        )

        primero.refresh_from_db()
        segundo.refresh_from_db()
        self.assertEqual(primero.sucursal, self.otra_sucursal)
        self.assertTrue(primero.predeterminado)
        self.assertTrue(segundo.predeterminado)

    def test_creacion_registra_auditoria(self):
        punto = self.crear_punto(numero=5)
        auditoria = Auditoria.objects.get(
            tabla=PuntoVenta._meta.db_table,
            registro_id=str(punto.pk),
            accion=Auditoria.Accion.INSERT,
        )
        self.assertEqual(auditoria.usuario, self.usuario)

    def test_rechaza_creacion_en_sucursal_inactiva(self):
        self.sucursal.activa = False
        self.sucursal.save(update_fields=["activa"])
        with self.assertRaises(ValidationError):
            self.crear_punto(numero=8)



class DependenciasPuntoVentaTests(BasePuntosVentaTests):
    def test_no_permite_inactivar_actividad_usada_por_punto_activo(self):
        from .models import ActividadEconomica
        from .servicios_actividades import (
            crear_empresa_actividad,
            inactivar_empresa_actividad,
        )

        catalogo = ActividadEconomica.objects.create(
            codigo="620100",
            descripcion="Servicios de programación informática",
            fuente_sha256="a" * 64,
        )
        actividad = crear_empresa_actividad(
            empresa=self.empresa,
            actividad=catalogo,
            principal=True,
        )
        punto = self.crear_punto(numero=20)
        actualizar_punto_venta(
            empresa=self.empresa,
            punto_venta=punto,
            sucursal=self.sucursal,
            sistema_emision=punto.sistema_emision,
            nombre_fantasia=punto.nombre_fantasia,
            descripcion_sistema_arca="",
            actividad_predeterminada=actividad,
            jurisdiccion_iibb_predeterminada=None,
            predeterminado=True,
            bloqueado=False,
            fecha_alta=punto.fecha_alta,
            observaciones="",
        )

        with self.assertRaises(ValidationError):
            inactivar_empresa_actividad(
                empresa=self.empresa,
                empresa_actividad=actividad,
            )

    def test_no_permite_inactivar_jurisdiccion_usada_por_punto_activo(self):
        from .models import (
            ConfiguracionIIBBEmpresa,
            JurisdiccionFiscal,
        )
        from .servicios_iibb import (
            crear_configuracion_iibb,
            crear_jurisdiccion_iibb,
            inactivar_jurisdiccion_iibb,
        )

        jurisdiccion = JurisdiccionFiscal.objects.get(codigo="921")
        configuracion = crear_configuracion_iibb(
            empresa=self.empresa,
            regimen=ConfiguracionIIBBEmpresa.Regimen.LOCAL,
            tratamiento_general=(
                ConfiguracionIIBBEmpresa.TratamientoGeneral.GRAVADO
            ),
            numero_inscripcion=self.empresa.cuit,
            fecha_alta=date(2026, 1, 1),
        )
        relacion = crear_jurisdiccion_iibb(
            empresa=self.empresa,
            configuracion=configuracion,
            jurisdiccion=jurisdiccion,
            fecha_alta=date(2026, 1, 1),
        )
        punto = self.crear_punto(numero=21)
        actualizar_punto_venta(
            empresa=self.empresa,
            punto_venta=punto,
            sucursal=self.sucursal,
            sistema_emision=punto.sistema_emision,
            nombre_fantasia=punto.nombre_fantasia,
            descripcion_sistema_arca="",
            actividad_predeterminada=None,
            jurisdiccion_iibb_predeterminada=relacion,
            predeterminado=True,
            bloqueado=False,
            fecha_alta=punto.fecha_alta,
            observaciones="",
        )

        with self.assertRaises(ValidationError):
            inactivar_jurisdiccion_iibb(
                empresa=self.empresa,
                relacion=relacion,
            )


class ParametroLegacyPuntoVentaTests(BasePuntosVentaTests):
    def test_legacy_se_detecta_sin_crear_punto(self):
        ParametroSistema.objects.create(
            ambito=ParametroSistema.Ambito.EMPRESA,
            empresa=self.empresa,
            clave="punto_venta_default",
            valor="0007",
            tipo_valor=ParametroSistema.TipoValor.TEXTO,
        )
        self.assertEqual(
            obtener_numero_punto_venta_legacy(self.empresa),
            7,
        )
        self.assertFalse(
            PuntoVenta.objects.filter(empresa=self.empresa).exists()
        )

    def test_legacy_no_se_ofrece_si_ya_existen_puntos(self):
        ParametroSistema.objects.create(
            ambito=ParametroSistema.Ambito.EMPRESA,
            empresa=self.empresa,
            clave="punto_venta_default",
            valor="0007",
            tipo_valor=ParametroSistema.TipoValor.TEXTO,
        )
        self.crear_punto(numero=1)
        self.assertIsNone(
            obtener_numero_punto_venta_legacy(self.empresa)
        )


class PuntoVentaFormTests(BasePuntosVentaTests):
    def datos_validos(self):
        return {
            "numero": "7",
            "sucursal": str(self.sucursal.pk),
            "nombre_fantasia": "Ventas",
            "sistema_emision": PuntoVenta.SistemaEmision.WEB_SERVICE,
            "descripcion_sistema_arca": "",
            "actividad_predeterminada": "",
            "jurisdiccion_iibb_predeterminada": "",
            "predeterminado": "on",
            "bloqueado": "",
            "fecha_alta": "2026-01-01",
            "observaciones": "",
        }

    def test_formulario_filtra_sucursales_por_empresa(self):
        form = PuntoVentaCrearForm(
            empresa=self.empresa,
        )
        self.assertIn(
            self.sucursal,
            form.fields["sucursal"].queryset,
        )
        self.assertNotIn(
            self.sucursal_ajena,
            form.fields["sucursal"].queryset,
        )

    def test_formulario_rechaza_numero_fuera_de_rango(self):
        datos = self.datos_validos()
        datos["numero"] = "99999"
        form = PuntoVentaCrearForm(
            datos,
            empresa=self.empresa,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("numero", form.errors)

    def test_formulario_edicion_no_expone_numero(self):
        punto = self.crear_punto(numero=9)
        form = PuntoVentaEditarForm(
            empresa=self.empresa,
            punto_venta=punto,
        )
        self.assertNotIn("numero", form.fields)


class SucursalConPuntosTests(BasePuntosVentaTests):
    def test_no_permite_inactivar_sucursal_con_puntos_activos(self):
        self.crear_punto(numero=1)
        datos = {
            "codigo": self.sucursal.codigo,
            "nombre": self.sucursal.nombre,
            "calle": self.sucursal.calle,
            "numero": self.sucursal.numero,
            "sector": "",
            "torre": "",
            "piso": "",
            "departamento": "",
            "barrio": "",
            "localidad": self.sucursal.localidad,
            "codigo_postal": self.sucursal.codigo_postal,
            "partido_departamento": "",
            "provincia": self.sucursal.provincia,
            "pais": self.sucursal.pais,
            "es_casa_central": "on",
            "es_domicilio_fiscal_nacional": "",
            "es_domicilio_fiscal_provincial": "",
            "es_domicilio_legal": "",
            "es_principal_actividades": "",
            "es_deposito": "",
            "es_local_comercial": "",
            "es_oficina_administrativa": "",
            "otras_funciones": "",
            "activa": "",
        }
        form = SucursalForm(
            datos,
            instance=self.sucursal,
            empresa=self.empresa,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("activa", form.errors)


class PuntoVentaAdminTests(BasePuntosVentaTests):
    def test_admin_es_solo_lectura(self):
        model_admin = PuntoVentaAdmin(
            PuntoVenta,
            admin.site,
        )
        request = RequestFactory().get("/admin/")
        request.user = User.objects.create_superuser(
            username="admin_puntos",
            password="password-test",
        )
        self.assertFalse(model_admin.has_add_permission(request))
        self.assertFalse(model_admin.has_change_permission(request))
        self.assertFalse(model_admin.has_delete_permission(request))


class PuntoVentaPermisosInicialesTests(TestCase):
    def test_matriz_inicial_incluye_permisos(self):
        call_command(
            "cargar_roles_permisos_iniciales",
            stdout=StringIO(),
        )
        for codigo in (
            "puntos_venta.ver",
            "puntos_venta.crear",
            "puntos_venta.editar",
        ):
            self.assertTrue(
                PermisoFuncional.objects.filter(
                    codigo=codigo,
                    activo=True,
                ).exists()
            )
        self.assertIn(
            "puntos_venta.editar",
            PERMISOS_POR_ROL["ADMIN"],
        )
        self.assertIn(
            "puntos_venta.editar",
            PERMISOS_POR_ROL["CONTADOR"],
        )
        self.assertIn(
            "puntos_venta.ver",
            PERMISOS_POR_ROL["AUDITOR"],
        )
        self.assertIn(
            "puntos_venta.ver",
            PERMISOS_POR_ROL["SOLO_LECTURA"],
        )
        self.assertNotIn(
            "puntos_venta.ver",
            PERMISOS_POR_ROL["OPERADOR"],
        )


class PuntoVentaViewTests(BasePuntosVentaTests):
    def setUp(self):
        super().setUp()
        self.lector = User.objects.create_user(
            username="lector_puntos",
            password="password-test",
        )
        self.editor = User.objects.create_user(
            username="editor_puntos",
            password="password-test",
        )
        for usuario in (self.lector, self.editor):
            UsuarioEmpresa.objects.create(
                usuario=usuario,
                empresa=self.empresa,
            )
        asignar_permiso(
            self.lector,
            self.empresa,
            "puntos_venta.ver",
            "LECTOR_PUNTOS",
        )
        asignar_permiso(
            self.editor,
            self.empresa,
            "puntos_venta.crear",
            "CREADOR_PUNTOS",
        )
        asignar_permiso(
            self.editor,
            self.empresa,
            "puntos_venta.editar",
            "EDITOR_PUNTOS",
        )

    def ingresar(self, usuario):
        self.client.force_login(usuario)
        session = self.client.session
        session[SESSION_EMPRESA_ACTIVA_ID] = self.empresa.pk
        session.save()

    def datos_post(self):
        return {
            "numero": "11",
            "sucursal": str(self.sucursal.pk),
            "nombre_fantasia": "Ventas",
            "sistema_emision": PuntoVenta.SistemaEmision.WEB_SERVICE,
            "descripcion_sistema_arca": "",
            "actividad_predeterminada": "",
            "jurisdiccion_iibb_predeterminada": "",
            "predeterminado": "on",
            "bloqueado": "",
            "fecha_alta": "2026-01-01",
            "observaciones": "",
        }

    def test_listado_aisla_empresa_activa(self):
        self.crear_punto(numero=1)
        crear_punto_venta(
            empresa=self.otra_empresa,
            sucursal=self.sucursal_ajena,
            numero=2,
            sistema_emision=PuntoVenta.SistemaEmision.WEB_SERVICE,
        )
        self.ingresar(self.lector)
        response = self.client.get(
            reverse("nucleo:puntos_venta")
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "00001")
        self.assertNotContains(response, "00002")
        self.assertNotContains(response, self.otra_empresa.razon_social)

    def test_lector_no_puede_crear(self):
        self.ingresar(self.lector)
        response = self.client.get(
            reverse("nucleo:punto_venta_crear")
        )
        self.assertEqual(response.status_code, 403)

    def test_editor_puede_crear(self):
        self.ingresar(self.editor)
        response = self.client.post(
            reverse("nucleo:punto_venta_crear"),
            self.datos_post(),
        )
        self.assertRedirects(
            response,
            reverse("nucleo:puntos_venta"),
        )
        self.assertTrue(
            PuntoVenta.objects.filter(
                empresa=self.empresa,
                numero=11,
            ).exists()
        )

    def test_edicion_de_objeto_ajeno_devuelve_404(self):
        punto_ajeno = crear_punto_venta(
            empresa=self.otra_empresa,
            sucursal=self.sucursal_ajena,
            numero=2,
            sistema_emision=PuntoVenta.SistemaEmision.WEB_SERVICE,
        )
        self.ingresar(self.editor)
        response = self.client.get(
            reverse(
                "nucleo:punto_venta_editar",
                args=[punto_ajeno.pk],
            )
        )
        self.assertEqual(response.status_code, 404)
