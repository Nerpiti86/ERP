from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.nucleo.empresa_activa import SESSION_EMPRESA_ACTIVA_ID

from .forms import ConfiguracionEmpresaForm
from .models import (
    Empresa,
    ParametroSistema,
    UsuarioEmpresa,
)
from .parametros_empresa import (
    CLAVES_PARAMETROS_EMPRESA,
    PARAMETROS_EMPRESA_ESTANDAR,
    guardar_configuracion_empresa,
    inicializar_parametros_empresa,
    obtener_datos_configuracion_empresa,
    obtener_estado_parametros_empresa,
)


User = get_user_model()


class ParametrosEmpresaServiceTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            cuit="30712345678",
            razon_social="Empresa Configurable SA",
        )

    def datos_validos(self):
        return {
            "moneda_funcional": "USD",
            "modo_numeracion_comprobantes": "manual",
            "permite_stock_negativo": True,
            "usa_centros_costo": False,
            "usa_proyectos": True,
            "requiere_aprobacion_compras": True,
            "requiere_aprobacion_pagos": False,
        }

    def test_inicializacion_crea_siete_parametros_predeterminados(self):
        resultado = inicializar_parametros_empresa(self.empresa)

        self.assertEqual(len(resultado["creados"]), 7)
        self.assertEqual(resultado["reactivados"], ())
        self.assertEqual(resultado["existentes"], ())
        self.assertEqual(
            ParametroSistema.objects.filter(empresa=self.empresa).count(),
            7,
        )

        valores = dict(
            ParametroSistema.objects.filter(
                empresa=self.empresa,
            ).values_list("clave", "valor")
        )
        self.assertEqual(valores["moneda_funcional"], "ARS")
        self.assertEqual(
            valores["modo_numeracion_comprobantes"],
            "automatico",
        )
        self.assertEqual(valores["usa_centros_costo"], "si")

    def test_inicializacion_es_idempotente(self):
        inicializar_parametros_empresa(self.empresa)

        resultado = inicializar_parametros_empresa(self.empresa)

        self.assertEqual(resultado["creados"], ())
        self.assertEqual(resultado["reactivados"], ())
        self.assertEqual(len(resultado["existentes"]), 7)
        self.assertEqual(
            ParametroSistema.objects.filter(empresa=self.empresa).count(),
            7,
        )

    def test_inicializacion_preserva_valor_existente(self):
        ParametroSistema.objects.create(
            ambito=ParametroSistema.Ambito.EMPRESA,
            empresa=self.empresa,
            clave="moneda_funcional",
            valor="USD",
            tipo_valor=ParametroSistema.TipoValor.TEXTO,
        )

        resultado = inicializar_parametros_empresa(self.empresa)

        parametro = ParametroSistema.objects.get(
            empresa=self.empresa,
            clave="moneda_funcional",
        )
        self.assertEqual(parametro.valor, "USD")
        self.assertIn("moneda_funcional", resultado["existentes"])

    def test_inicializacion_reactiva_sin_pisar_valor(self):
        ParametroSistema.objects.create(
            ambito=ParametroSistema.Ambito.EMPRESA,
            empresa=self.empresa,
            clave="moneda_funcional",
            valor="USD",
            tipo_valor=ParametroSistema.TipoValor.TEXTO,
            activo=False,
        )

        resultado = inicializar_parametros_empresa(self.empresa)

        parametro = ParametroSistema.objects.get(
            empresa=self.empresa,
            clave="moneda_funcional",
        )
        self.assertTrue(parametro.activo)
        self.assertEqual(parametro.valor, "USD")
        self.assertIn("moneda_funcional", resultado["reactivados"])

    def test_estado_distingue_faltantes_e_inactivos(self):
        ParametroSistema.objects.create(
            ambito=ParametroSistema.Ambito.EMPRESA,
            empresa=self.empresa,
            clave="moneda_funcional",
            valor="ARS",
            tipo_valor=ParametroSistema.TipoValor.TEXTO,
        )
        ParametroSistema.objects.create(
            ambito=ParametroSistema.Ambito.EMPRESA,
            empresa=self.empresa,
            clave="modo_numeracion_comprobantes",
            valor="automatico",
            tipo_valor=ParametroSistema.TipoValor.TEXTO,
            activo=False,
        )

        estado = obtener_estado_parametros_empresa(self.empresa)

        self.assertFalse(estado["completa"])
        self.assertEqual(estado["configurados"], 1)
        self.assertEqual(len(estado["faltantes"]), 5)
        self.assertEqual(len(estado["inactivos"]), 1)

    def test_lectura_convierte_booleanos_para_formulario(self):
        inicializar_parametros_empresa(self.empresa)

        datos, advertencias = obtener_datos_configuracion_empresa(
            self.empresa
        )

        self.assertEqual(advertencias, ())
        self.assertEqual(datos["moneda_funcional"], "ARS")
        self.assertFalse(datos["permite_stock_negativo"])
        self.assertTrue(datos["usa_centros_costo"])

    def test_guardado_actualiza_y_crea_configuracion_completa(self):
        resultado = guardar_configuracion_empresa(
            self.empresa,
            self.datos_validos(),
        )

        self.assertEqual(len(resultado["creados"]), 7)
        self.assertEqual(resultado["actualizados"], ())
        self.assertTrue(
            obtener_estado_parametros_empresa(self.empresa)["completa"]
        )

        valores = dict(
            ParametroSistema.objects.filter(
                empresa=self.empresa,
            ).values_list("clave", "valor")
        )
        self.assertEqual(valores["moneda_funcional"], "USD")
        self.assertEqual(
            valores["modo_numeracion_comprobantes"],
            "manual",
        )
        self.assertEqual(valores["permite_stock_negativo"], "si")
        self.assertEqual(valores["usa_centros_costo"], "no")
        self.assertEqual(valores["usa_proyectos"], "si")

    def test_guardado_no_toca_parametros_personalizados(self):
        personalizado = ParametroSistema.objects.create(
            ambito=ParametroSistema.Ambito.EMPRESA,
            empresa=self.empresa,
            clave="integracion_personalizada",
            valor="conservar",
            tipo_valor=ParametroSistema.TipoValor.TEXTO,
        )

        guardar_configuracion_empresa(
            self.empresa,
            self.datos_validos(),
        )

        personalizado.refresh_from_db()
        self.assertEqual(personalizado.valor, "conservar")
        self.assertTrue(personalizado.activo)
        self.assertEqual(
            ParametroSistema.objects.filter(
                empresa=self.empresa,
            ).count(),
            len(CLAVES_PARAMETROS_EMPRESA) + 1,
        )


    def test_configuracion_estandar_preserva_parametro_legacy(self):
        legacy = ParametroSistema.objects.create(
            ambito=ParametroSistema.Ambito.EMPRESA,
            empresa=self.empresa,
            clave="punto_venta_default",
            valor="0001",
            tipo_valor=ParametroSistema.TipoValor.TEXTO,
        )

        inicializar_parametros_empresa(self.empresa)
        guardar_configuracion_empresa(
            self.empresa,
            self.datos_validos(),
        )

        legacy.refresh_from_db()
        self.assertEqual(legacy.valor, "0001")
        self.assertTrue(legacy.activo)
        self.assertNotIn(
            "punto_venta_default",
            CLAVES_PARAMETROS_EMPRESA,
        )


class ConfiguracionEmpresaFormTests(TestCase):
    def datos_validos(self):
        return {
            "moneda_funcional": "ars",
            "modo_numeracion_comprobantes": "automatico",
            "permite_stock_negativo": "",
            "usa_centros_costo": "on",
            "usa_proyectos": "",
            "requiere_aprobacion_compras": "",
            "requiere_aprobacion_pagos": "",
        }

    def test_formulario_valido_normaliza_moneda(self):
        form = ConfiguracionEmpresaForm(self.datos_validos())

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["moneda_funcional"], "ARS")
        self.assertTrue(form.cleaned_data["usa_centros_costo"])
        self.assertFalse(form.cleaned_data["usa_proyectos"])

    def test_formulario_rechaza_moneda_invalida(self):
        datos = self.datos_validos()
        datos["moneda_funcional"] = "PESOS"

        form = ConfiguracionEmpresaForm(datos)

        self.assertFalse(form.is_valid())
        self.assertIn("moneda_funcional", form.errors)

    def test_formulario_rechaza_modo_desconocido(self):
        datos = self.datos_validos()
        datos["modo_numeracion_comprobantes"] = "mixto"

        form = ConfiguracionEmpresaForm(datos)

        self.assertFalse(form.is_valid())
        self.assertIn("modo_numeracion_comprobantes", form.errors)


class ConfiguracionEmpresaViewTests(TestCase):
    def setUp(self):
        self.superusuario = User.objects.create_superuser(
            username="admin_configuracion",
            email="admin_configuracion@example.com",
            password="password-test",
        )
        self.empresa = Empresa.objects.create(
            cuit="30712345678",
            razon_social="Empresa Configurable SA",
        )
        self.otra_empresa = Empresa.objects.create(
            cuit="30712345679",
            razon_social="Otra Empresa SA",
        )
        self.client.force_login(self.superusuario)
        self.seleccionar_empresa(self.empresa)

    def seleccionar_empresa(self, empresa):
        session = self.client.session
        session[SESSION_EMPRESA_ACTIVA_ID] = empresa.pk
        session.save()

    def datos_post(self):
        return {
            "moneda_funcional": "USD",
            "modo_numeracion_comprobantes": "manual",
            "permite_stock_negativo": "on",
            "usa_centros_costo": "",
            "usa_proyectos": "on",
            "requiere_aprobacion_compras": "on",
            "requiere_aprobacion_pagos": "",
        }

    def test_anonimo_redirige_al_login(self):
        self.client.logout()

        response = self.client.get(
            reverse("nucleo:configuracion_empresa")
        )

        self.assertRedirects(
            response,
            (
                f"{reverse('core:login')}?next="
                f"{reverse('nucleo:configuracion_empresa')}"
            ),
        )

    def test_usuario_sin_permiso_recibe_403(self):
        usuario = User.objects.create_user(
            username="operador_configuracion",
            email="operador_configuracion@example.com",
            password="password-test",
        )
        UsuarioEmpresa.objects.create(
            usuario=usuario,
            empresa=self.empresa,
        )
        self.client.force_login(usuario)
        self.seleccionar_empresa(self.empresa)

        response = self.client.get(
            reverse("nucleo:configuracion_empresa")
        )

        self.assertEqual(response.status_code, 403)

    def test_sin_empresa_activa_redirige_al_selector(self):
        session = self.client.session
        session.pop(SESSION_EMPRESA_ACTIVA_ID, None)
        session.save()

        response = self.client.get(
            reverse("nucleo:configuracion_empresa")
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            response.url.startswith(reverse("core:seleccionar_empresa"))
        )
        self.assertIn("next=", response.url)

    def test_empresa_incompleta_muestra_inicializacion(self):
        response = self.client.get(
            reverse("nucleo:parametros_operativos")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Configuración incompleta")
        self.assertContains(response, "0 de 7 parámetros activos")
        self.assertContains(response, "Inicializar configuración")
        self.assertContains(response, "Valores predeterminados propuestos")

    def test_post_inicializar_crea_parametros_faltantes(self):
        response = self.client.post(
            reverse("nucleo:inicializar_configuracion_empresa")
        )

        self.assertRedirects(
            response,
            reverse("nucleo:parametros_operativos"),
        )
        self.assertEqual(
            ParametroSistema.objects.filter(
                empresa=self.empresa,
            ).count(),
            7,
        )

    def test_empresa_completa_muestra_formulario_amigable(self):
        inicializar_parametros_empresa(self.empresa)

        response = self.client.get(
            reverse("nucleo:parametros_operativos")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Configuración completa")
        self.assertContains(response, "Moneda funcional")
        self.assertContains(response, "Permitir stock negativo")
        self.assertContains(response, "Guardar configuración")
        self.assertNotContains(response, "Ámbito")
        self.assertNotContains(response, "Tipo de valor")

    def test_post_guardar_persiste_valores(self):
        inicializar_parametros_empresa(self.empresa)

        response = self.client.post(
            reverse("nucleo:parametros_operativos"),
            self.datos_post(),
        )

        self.assertRedirects(
            response,
            reverse("nucleo:parametros_operativos"),
        )
        valores = dict(
            ParametroSistema.objects.filter(
                empresa=self.empresa,
            ).values_list("clave", "valor")
        )
        self.assertEqual(valores["moneda_funcional"], "USD")
        self.assertEqual(
            valores["modo_numeracion_comprobantes"],
            "manual",
        )
        self.assertEqual(valores["permite_stock_negativo"], "si")
        self.assertEqual(valores["usa_centros_costo"], "no")

    def test_guardado_afecta_solo_empresa_activa(self):
        inicializar_parametros_empresa(self.empresa)
        inicializar_parametros_empresa(self.otra_empresa)

        self.client.post(
            reverse("nucleo:parametros_operativos"),
            self.datos_post(),
        )

        moneda_activa = ParametroSistema.objects.get(
            empresa=self.empresa,
            clave="moneda_funcional",
        )
        moneda_otra = ParametroSistema.objects.get(
            empresa=self.otra_empresa,
            clave="moneda_funcional",
        )
        self.assertEqual(moneda_activa.valor, "USD")
        self.assertEqual(moneda_otra.valor, "ARS")

    def test_navbar_muestra_configuracion_segun_autorizacion(self):
        response_staff = self.client.get(reverse("core:home"))
        self.assertContains(
            response_staff,
            reverse("nucleo:configuracion_empresa"),
        )

        usuario = User.objects.create_user(
            username="operador_sin_configuracion",
            email="operador_sin_configuracion@example.com",
            password="password-test",
        )
        UsuarioEmpresa.objects.create(
            usuario=usuario,
            empresa=self.empresa,
        )
        self.client.force_login(usuario)
        self.seleccionar_empresa(self.empresa)

        response_usuario = self.client.get(reverse("core:home"))
        self.assertNotContains(
            response_usuario,
            reverse("nucleo:configuracion_empresa"),
        )

    def test_inicializacion_get_no_esta_permitida(self):
        response = self.client.get(
            reverse("nucleo:inicializar_configuracion_empresa")
        )

        self.assertEqual(response.status_code, 405)
