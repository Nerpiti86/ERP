from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.nucleo.empresa_activa import SESSION_EMPRESA_ACTIVA_ID
from apps.nucleo.models import (
    Empresa,
    PermisoFuncional,
    RolFuncional,
    RolPermiso,
    UsuarioEmpresa,
    UsuarioRolEmpresa,
)

from .models import CuentaContable
from .services import crear_cuenta_contable


User = get_user_model()


def asignar_permiso(usuario, empresa, codigo_permiso, codigo_rol):
    permiso, _ = PermisoFuncional.objects.get_or_create(
        codigo=codigo_permiso,
    )
    rol = RolFuncional.objects.create(
        codigo=codigo_rol,
        nombre=codigo_rol.replace("_", " ").title(),
    )
    RolPermiso.objects.create(rol=rol, permiso=permiso)
    UsuarioRolEmpresa.objects.create(
        usuario=usuario,
        empresa=empresa,
        rol=rol,
    )


class PantallasPlanCuentasTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            cuit="30760000001",
            razon_social="Empresa Plan SA",
        )
        self.otra_empresa = Empresa.objects.create(
            cuit="30760000002",
            razon_social="Otra Empresa Plan SA",
        )
        self.superusuario = User.objects.create_superuser(
            username="admin_plan",
            password="password-test",
        )
        self.lector = User.objects.create_user(
            username="lector_plan",
            password="password-test",
        )
        self.editor = User.objects.create_user(
            username="editor_plan",
            password="password-test",
        )
        self.sin_permiso = User.objects.create_user(
            username="sin_permiso_plan",
            password="password-test",
        )

        for usuario in (self.lector, self.editor, self.sin_permiso):
            UsuarioEmpresa.objects.create(
                usuario=usuario,
                empresa=self.empresa,
            )

        asignar_permiso(
            self.lector,
            self.empresa,
            "contabilidad.ver",
            "LECTOR_PLAN",
        )
        asignar_permiso(
            self.editor,
            self.empresa,
            "contabilidad.editar",
            "EDITOR_PLAN",
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

    def crear_jerarquia_activo_nivel_4(self):
        cuentas = []
        for codigo, nombre in (
            ("1.0.00.00.000", "Activo"),
            ("1.1.00.00.000", "Activo corriente"),
            ("1.1.01.00.000", "Cajas y bancos"),
            ("1.1.01.01.000", "Cajas en moneda nacional"),
        ):
            cuentas.append(
                crear_cuenta_contable(
                    empresa=self.empresa,
                    codigo=codigo,
                    nombre=nombre,
                    tipo_contable=CuentaContable.TipoContable.ACTIVO,
                )
            )
        return cuentas

    def datos_post(
        self,
        *,
        codigo,
        nombre,
        tipo_contable=CuentaContable.TipoContable.ACTIVO,
        naturaleza="",
        habilitada="on",
    ):
        return {
            "codigo": codigo,
            "nombre": nombre,
            "descripcion": "",
            "tipo_contable": tipo_contable,
            "naturaleza": naturaleza,
            "habilitada": habilitada,
        }

    def test_plan_requiere_autenticacion(self):
        response = self.client.get(reverse("contabilidad:plan_cuentas"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("core:login"), response.url)

    def test_plan_requiere_empresa_activa(self):
        self.client.force_login(self.superusuario)
        response = self.client.get(reverse("contabilidad:plan_cuentas"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("core:seleccionar_empresa"), response.url)

    def test_plan_aisla_cuentas_por_empresa(self):
        crear_cuenta_contable(
            empresa=self.empresa,
            codigo="1.0.00.00.000",
            nombre="Activo empresa principal",
            tipo_contable=CuentaContable.TipoContable.ACTIVO,
        )
        crear_cuenta_contable(
            empresa=self.otra_empresa,
            codigo="1.0.00.00.000",
            nombre="Activo empresa ajena",
            tipo_contable=CuentaContable.TipoContable.ACTIVO,
        )
        self.ingresar(self.superusuario)

        response = self.client.get(reverse("contabilidad:plan_cuentas"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Activo empresa principal")
        self.assertNotContains(response, "Activo empresa ajena")
        self.assertEqual(response.context["resumen"]["total"], 1)

    def test_lector_consulta_pero_no_puede_crear(self):
        crear_cuenta_contable(
            empresa=self.empresa,
            codigo="1.0.00.00.000",
            nombre="Activo",
            tipo_contable=CuentaContable.TipoContable.ACTIVO,
        )
        self.ingresar(self.lector)

        listado = self.client.get(reverse("contabilidad:plan_cuentas"))
        alta = self.client.get(reverse("contabilidad:crear_cuenta"))

        self.assertEqual(listado.status_code, 200)
        self.assertContains(listado, "Solo lectura")
        self.assertNotContains(listado, "Nueva cuenta")
        self.assertEqual(alta.status_code, 403)

    def test_editor_accede_al_listado_y_al_formulario(self):
        self.ingresar(self.editor)

        listado = self.client.get(reverse("contabilidad:plan_cuentas"))
        alta = self.client.get(reverse("contabilidad:crear_cuenta"))

        self.assertEqual(listado.status_code, 200)
        self.assertContains(listado, "Nueva cuenta")
        self.assertEqual(alta.status_code, 200)
        self.assertContains(alta, "Nueva cuenta contable")

    def test_editor_crea_imputable_con_superior_derivado(self):
        jerarquia = self.crear_jerarquia_activo_nivel_4()
        self.ingresar(self.editor)

        response = self.client.post(
            reverse("contabilidad:crear_cuenta"),
            self.datos_post(
                codigo="1.1.01.01.009",
                nombre="Caja prueba",
                naturaleza=CuentaContable.Naturaleza.DEUDORA,
            ),
        )

        self.assertEqual(response.status_code, 302)
        cuenta = CuentaContable.objects.get(
            empresa=self.empresa,
            codigo="1.1.01.01.009",
        )
        self.assertEqual(cuenta.parent, jerarquia[-1])
        self.assertTrue(cuenta.imputable)
        self.assertEqual(
            cuenta.naturaleza,
            CuentaContable.Naturaleza.DEUDORA,
        )

    def test_alta_rechaza_superior_inexistente(self):
        self.ingresar(self.editor)
        response = self.client.post(
            reverse("contabilidad:crear_cuenta"),
            self.datos_post(
                codigo="1.9.00.00.000",
                nombre="Activo sin superior",
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "No existe la cuenta superior esperada 1.0.00.00.000",
        )
        self.assertFalse(
            CuentaContable.objects.filter(
                empresa=self.empresa,
                codigo="1.9.00.00.000",
            ).exists()
        )

    def test_alta_rechaza_naturaleza_en_agrupadora(self):
        self.ingresar(self.editor)
        response = self.client.post(
            reverse("contabilidad:crear_cuenta"),
            self.datos_post(
                codigo="1.0.00.00.000",
                nombre="Activo",
                naturaleza=CuentaContable.Naturaleza.DEUDORA,
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Las cuentas agrupadoras no deben tener naturaleza.",
        )

    def test_alta_exige_naturaleza_en_imputable(self):
        self.crear_jerarquia_activo_nivel_4()
        self.ingresar(self.editor)
        response = self.client.post(
            reverse("contabilidad:crear_cuenta"),
            self.datos_post(
                codigo="1.1.01.01.010",
                nombre="Caja sin naturaleza",
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "La naturaleza es obligatoria para una cuenta imputable.",
        )

    def test_alta_rechaza_raiz_incompatible_con_tipo(self):
        self.ingresar(self.editor)
        response = self.client.post(
            reverse("contabilidad:crear_cuenta"),
            self.datos_post(
                codigo="1.0.00.00.000",
                nombre="Pasivo mal codificado",
                tipo_contable=CuentaContable.TipoContable.PASIVO,
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "El codigo raiz no corresponde al tipo contable seleccionado.",
        )

    def test_alta_rechaza_codigo_duplicado(self):
        crear_cuenta_contable(
            empresa=self.empresa,
            codigo="1.0.00.00.000",
            nombre="Activo",
            tipo_contable=CuentaContable.TipoContable.ACTIVO,
        )
        self.ingresar(self.editor)

        response = self.client.post(
            reverse("contabilidad:crear_cuenta"),
            self.datos_post(
                codigo="1.0.00.00.000",
                nombre="Activo duplicado",
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ya existe")
        self.assertEqual(
            CuentaContable.objects.filter(
                empresa=self.empresa,
                codigo="1.0.00.00.000",
            ).count(),
            1,
        )

    def test_busqueda_y_filtros_reducen_resultados(self):
        self.crear_jerarquia_activo_nivel_4()
        crear_cuenta_contable(
            empresa=self.empresa,
            codigo="2.0.00.00.000",
            nombre="Pasivo",
            tipo_contable=CuentaContable.TipoContable.PASIVO,
        )
        self.ingresar(self.editor)

        response = self.client.get(
            reverse("contabilidad:plan_cuentas"),
            {
                "q": "cajas",
                "tipo": CuentaContable.TipoContable.ACTIVO,
                "clase": "agrupadoras",
                "estado": "habilitadas",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cajas y bancos")
        self.assertNotContains(response, ">Pasivo<")
        self.assertEqual(len(response.context["cuentas"]), 2)

    def test_menu_respeta_permiso_contable(self):
        self.ingresar(self.lector)
        con_permiso = self.client.get(reverse("core:home"))

        self.client.logout()
        self.ingresar(self.sin_permiso)
        sin_permiso = self.client.get(reverse("core:home"))

        self.assertContains(con_permiso, "Plan de cuentas")
        self.assertNotContains(sin_permiso, "Plan de cuentas")
