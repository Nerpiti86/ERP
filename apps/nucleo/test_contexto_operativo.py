from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import TestCase, override_settings
from django.urls import include, path, reverse

from .autorizacion import (
    contexto_operativo_requerido,
    sucursal_activa_requerida,
)
from .contexto_operativo import (
    filtrar_queryset_por_contexto_operativo,
    filtrar_queryset_por_empresa_activa,
    validar_objeto_en_contexto_operativo,
    validar_objeto_en_empresa_activa,
)
from .empresa_activa import SESSION_EMPRESA_ACTIVA_ID
from .models import (
    Empresa,
    ParametroSistema,
    Sucursal,
    UsuarioEmpresa,
    UsuarioSucursal,
)
from .sucursal_activa import SESSION_SUCURSAL_ACTIVA_ID


User = get_user_model()


@login_required
@contexto_operativo_requerido
def vista_operativa_prueba(request):
    return HttpResponse("contexto operativo ok")


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
def vista_empresa_prueba(request):
    return HttpResponse("contexto empresa ok")


@login_required
@sucursal_activa_requerida
def vista_sucursal_prueba(request):
    return HttpResponse("contexto sucursal ok")


urlpatterns = [
    path("", include("apps.core.urls")),
    path(
        "prueba/contexto/operativo/",
        vista_operativa_prueba,
        name="prueba_contexto_operativo",
    ),
    path(
        "prueba/contexto/empresa/",
        vista_empresa_prueba,
        name="prueba_contexto_empresa",
    ),
    path(
        "prueba/contexto/sucursal/",
        vista_sucursal_prueba,
        name="prueba_contexto_sucursal",
    ),
]


@override_settings(ROOT_URLCONF=__name__)
class ContextoOperativoDecoradoresTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username="operador_contexto",
            password="password-test",
        )
        self.empresa_a = Empresa.objects.create(
            cuit="30711111118",
            razon_social="Empresa Contexto A SA",
        )
        self.empresa_b = Empresa.objects.create(
            cuit="30722222228",
            razon_social="Empresa Contexto B SA",
        )
        self.sucursal_a1 = Sucursal.objects.create(
            empresa=self.empresa_a,
            codigo="A1",
            nombre="Sucursal A1",
        )
        self.sucursal_a2 = Sucursal.objects.create(
            empresa=self.empresa_a,
            codigo="A2",
            nombre="Sucursal A2",
        )
        self.sucursal_b1 = Sucursal.objects.create(
            empresa=self.empresa_b,
            codigo="B1",
            nombre="Sucursal B1",
        )
        UsuarioEmpresa.objects.create(
            usuario=self.usuario,
            empresa=self.empresa_a,
        )
        UsuarioEmpresa.objects.create(
            usuario=self.usuario,
            empresa=self.empresa_b,
        )
        for sucursal in (
            self.sucursal_a1,
            self.sucursal_a2,
            self.sucursal_b1,
        ):
            UsuarioSucursal.objects.create(
                usuario=self.usuario,
                sucursal=sucursal,
            )

    def seleccionar_contexto(self, empresa=None, sucursal=None):
        session = self.client.session
        session.pop(SESSION_EMPRESA_ACTIVA_ID, None)
        session.pop(SESSION_SUCURSAL_ACTIVA_ID, None)

        if empresa is not None:
            session[SESSION_EMPRESA_ACTIVA_ID] = empresa.pk
        if sucursal is not None:
            session[SESSION_SUCURSAL_ACTIVA_ID] = sucursal.pk

        session.save()

    def test_anonimo_redirige_al_login(self):
        response = self.client.get(
            reverse("prueba_contexto_operativo")
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("core:login")))

    def test_operativa_sin_empresa_redirige_a_selector_empresa(self):
        self.client.force_login(self.usuario)

        response = self.client.get(
            reverse("prueba_contexto_operativo")
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            response.url.startswith(reverse("core:seleccionar_empresa"))
        )

    def test_operativa_preserva_next_al_pedir_empresa(self):
        self.client.force_login(self.usuario)
        destino = reverse("prueba_contexto_operativo")

        response = self.client.get(destino)

        self.assertIn("next=", response.url)
        self.assertIn("prueba%2Fcontexto%2Foperativo", response.url)

    def test_operativa_sin_sucursal_redirige_a_selector_sucursal(self):
        self.client.force_login(self.usuario)
        self.seleccionar_contexto(empresa=self.empresa_a)

        response = self.client.get(
            reverse("prueba_contexto_operativo")
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            response.url.startswith(reverse("core:seleccionar_sucursal"))
        )

    def test_operativa_preserva_next_al_pedir_sucursal(self):
        self.client.force_login(self.usuario)
        self.seleccionar_contexto(empresa=self.empresa_a)
        destino = reverse("prueba_contexto_operativo")

        response = self.client.get(destino)

        self.assertIn("next=", response.url)
        self.assertIn("prueba%2Fcontexto%2Foperativo", response.url)

    def test_operativa_con_contexto_completo_responde(self):
        self.client.force_login(self.usuario)
        self.seleccionar_contexto(
            empresa=self.empresa_a,
            sucursal=self.sucursal_a1,
        )

        response = self.client.get(
            reverse("prueba_contexto_operativo")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "contexto operativo ok")

    def test_vista_empresa_no_requiere_sucursal(self):
        self.client.force_login(self.usuario)
        self.seleccionar_contexto(empresa=self.empresa_a)

        response = self.client.get(
            reverse("prueba_contexto_empresa")
        )

        self.assertEqual(response.status_code, 200)

    def test_vista_empresa_sin_empresa_redirige(self):
        self.client.force_login(self.usuario)

        response = self.client.get(
            reverse("prueba_contexto_empresa")
        )

        self.assertTrue(
            response.url.startswith(reverse("core:seleccionar_empresa"))
        )

    def test_decorador_sucursal_sin_empresa_pide_empresa(self):
        self.client.force_login(self.usuario)

        response = self.client.get(
            reverse("prueba_contexto_sucursal")
        )

        self.assertTrue(
            response.url.startswith(reverse("core:seleccionar_empresa"))
        )

    def test_decorador_sucursal_sin_sucursal_pide_sucursal(self):
        self.client.force_login(self.usuario)
        self.seleccionar_contexto(empresa=self.empresa_a)

        response = self.client.get(
            reverse("prueba_contexto_sucursal")
        )

        self.assertTrue(
            response.url.startswith(reverse("core:seleccionar_sucursal"))
        )

    def test_sucursal_de_otra_empresa_se_limpia_y_redirige(self):
        self.client.force_login(self.usuario)
        self.seleccionar_contexto(
            empresa=self.empresa_a,
            sucursal=self.sucursal_b1,
        )

        response = self.client.get(
            reverse("prueba_contexto_operativo")
        )

        self.assertTrue(
            response.url.startswith(reverse("core:seleccionar_sucursal"))
        )
        self.assertNotIn(
            SESSION_SUCURSAL_ACTIVA_ID,
            self.client.session,
        )


class ContextoOperativoDatosTests(TestCase):
    def setUp(self):
        self.empresa_a = Empresa.objects.create(
            cuit="30733333338",
            razon_social="Empresa Datos A SA",
        )
        self.empresa_b = Empresa.objects.create(
            cuit="30744444448",
            razon_social="Empresa Datos B SA",
        )
        self.sucursal_a1 = Sucursal.objects.create(
            empresa=self.empresa_a,
            codigo="A1",
            nombre="Sucursal Datos A1",
        )
        self.sucursal_a2 = Sucursal.objects.create(
            empresa=self.empresa_a,
            codigo="A2",
            nombre="Sucursal Datos A2",
        )
        self.sucursal_b1 = Sucursal.objects.create(
            empresa=self.empresa_b,
            codigo="B1",
            nombre="Sucursal Datos B1",
        )
        self.parametro_a = ParametroSistema.objects.create(
            ambito=ParametroSistema.Ambito.EMPRESA,
            empresa=self.empresa_a,
            clave="contexto_prueba",
            valor="A",
        )
        self.parametro_b = ParametroSistema.objects.create(
            ambito=ParametroSistema.Ambito.EMPRESA,
            empresa=self.empresa_b,
            clave="contexto_prueba",
            valor="B",
        )

    def request_contexto(self, empresa=None, sucursal=None):
        return SimpleNamespace(
            empresa_activa=empresa,
            sucursal_activa=sucursal,
        )

    def test_filtrar_queryset_por_empresa_aisla_datos(self):
        request = self.request_contexto(empresa=self.empresa_a)

        queryset = filtrar_queryset_por_empresa_activa(
            request,
            ParametroSistema.objects.all(),
        )

        self.assertQuerySetEqual(
            queryset.order_by("pk"),
            [self.parametro_a],
        )

    def test_filtrar_queryset_sin_empresa_falla_cerrado(self):
        request = self.request_contexto()

        with self.assertRaises(PermissionDenied):
            filtrar_queryset_por_empresa_activa(
                request,
                ParametroSistema.objects.all(),
            )

    def test_filtrar_queryset_con_empresa_inactiva_falla_cerrado(self):
        self.empresa_a.activa = False
        self.empresa_a.save(update_fields=["activa"])
        request = self.request_contexto(empresa=self.empresa_a)

        with self.assertRaises(PermissionDenied):
            filtrar_queryset_por_empresa_activa(
                request,
                ParametroSistema.objects.all(),
            )

    def test_filtrar_queryset_por_contexto_aisla_sucursal(self):
        request = self.request_contexto(
            empresa=self.empresa_a,
            sucursal=self.sucursal_a1,
        )

        queryset = filtrar_queryset_por_contexto_operativo(
            request,
            Sucursal.objects.all(),
            campo_empresa="empresa_id",
            campo_sucursal="id",
        )

        self.assertQuerySetEqual(queryset, [self.sucursal_a1])

    def test_filtrar_contexto_sin_sucursal_falla_cerrado(self):
        request = self.request_contexto(empresa=self.empresa_a)

        with self.assertRaises(PermissionDenied):
            filtrar_queryset_por_contexto_operativo(
                request,
                Sucursal.objects.all(),
                campo_empresa="empresa_id",
                campo_sucursal="id",
            )

    def test_validar_objeto_de_empresa_activa_devuelve_objeto(self):
        request = self.request_contexto(empresa=self.empresa_a)

        resultado = validar_objeto_en_empresa_activa(
            request,
            self.parametro_a,
        )

        self.assertIs(resultado, self.parametro_a)

    def test_validar_objeto_de_otra_empresa_rechaza(self):
        request = self.request_contexto(empresa=self.empresa_a)

        with self.assertRaises(PermissionDenied):
            validar_objeto_en_empresa_activa(
                request,
                self.parametro_b,
            )

    def test_validar_objeto_de_sucursal_activa_devuelve_objeto(self):
        request = self.request_contexto(
            empresa=self.empresa_a,
            sucursal=self.sucursal_a1,
        )
        objeto = SimpleNamespace(
            empresa=self.empresa_a,
            sucursal=self.sucursal_a1,
        )

        resultado = validar_objeto_en_contexto_operativo(
            request,
            objeto,
            atributo_empresa="empresa",
            atributo_sucursal="sucursal",
        )

        self.assertIs(resultado, objeto)

    def test_validar_objeto_de_otra_sucursal_rechaza(self):
        request = self.request_contexto(
            empresa=self.empresa_a,
            sucursal=self.sucursal_a1,
        )
        objeto = SimpleNamespace(
            empresa=self.empresa_a,
            sucursal=self.sucursal_a2,
        )

        with self.assertRaises(PermissionDenied):
            validar_objeto_en_contexto_operativo(
                request,
                objeto,
                atributo_empresa="empresa",
                atributo_sucursal="sucursal",
            )
