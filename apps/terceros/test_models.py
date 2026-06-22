from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import (
    CondicionIVA,
    ContactoTercero,
    DomicilioTercero,
    Tercero,
    TerceroRol,
    TipoDocumento,
    normalizar_numero_documento,
    validar_cuit_cuil,
)
from .tests_support import crear_empresa, obtener_catalogos


class CatalogosTercerosTests(TestCase):
    def test_catalogo_tipos_documento_inicial(self):
        self.assertEqual(TipoDocumento.objects.count(), 8)
        self.assertEqual(
            TipoDocumento.objects.get(codigo="CUIT").codigo_arca,
            80,
        )
        self.assertEqual(
            TipoDocumento.objects.get(codigo="DNI").codigo_arca,
            96,
        )
        self.assertFalse(
            TipoDocumento.objects.get(
                codigo="SIN_IDENTIFICAR"
            ).requiere_numero
        )

    def test_catalogo_condiciones_iva_inicial(self):
        self.assertEqual(CondicionIVA.objects.count(), 11)
        self.assertEqual(
            CondicionIVA.objects.get(
                codigo="IVA_RESPONSABLE_INSCRIPTO"
            ).codigo_arca,
            1,
        )
        self.assertEqual(
            CondicionIVA.objects.get(
                codigo="MONOTRIBUTO_PROMOVIDO"
            ).codigo_arca,
            16,
        )


class NormalizacionDocumentoTests(TestCase):
    def test_normaliza_documento_numerico(self):
        self.assertEqual(
            normalizar_numero_documento("CUIT", "30-71191569-5"),
            "30711915695",
        )

    def test_normaliza_documento_alfanumerico(self):
        self.assertEqual(
            normalizar_numero_documento(
                "PASAPORTE",
                "  aa 123  ",
            ),
            "AA 123",
        )

    def test_valida_cuit_correcto(self):
        self.assertTrue(validar_cuit_cuil("30711915695"))

    def test_rechaza_cuit_incorrecto(self):
        self.assertFalse(validar_cuit_cuil("30711915694"))


class TerceroModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.empresa = crear_empresa()
        cls.otra_empresa = crear_empresa(
            cuit="30714202959",
            razon_social="Empresa Dos SA",
        )
        cls.catalogos = obtener_catalogos()

    def _tercero(self, **cambios):
        datos = {
            "empresa": self.empresa,
            "codigo": "CLI001",
            "tipo_persona": Tercero.TipoPersona.PERSONA_JURIDICA,
            "tipo_documento": self.catalogos["cuit"],
            "numero_documento": "30-71191569-5",
            "denominacion": "  Cliente Uno SA  ",
            "nombre_fantasia": " Cliente Uno ",
            "condicion_iva": self.catalogos["ri"],
            "telefono": " 3415550000 ",
            "email": " ADMIN@EXAMPLE.COM ",
            "sitio_web": "",
            "observaciones": " Nota ",
            "fecha_alta": "2026-06-21",
            "activo": True,
        }
        datos.update(cambios)
        return Tercero(**datos)

    def test_normaliza_campos_al_validar(self):
        tercero = self._tercero(codigo=" cli-001 ")
        tercero.full_clean()
        self.assertEqual(tercero.codigo, "CLI-001")
        self.assertEqual(tercero.numero_documento, "30711915695")
        self.assertEqual(tercero.denominacion, "Cliente Uno SA")
        self.assertEqual(tercero.email, "admin@example.com")

    def test_requiere_numero_segun_tipo(self):
        tercero = self._tercero(numero_documento="")
        with self.assertRaises(ValidationError):
            tercero.full_clean()

    def test_sin_identificar_no_admite_numero(self):
        tercero = self._tercero(
            tipo_documento=self.catalogos["sin_documento"],
            numero_documento="123",
        )
        with self.assertRaises(ValidationError):
            tercero.full_clean()

    def test_rechaza_cuit_invalido(self):
        tercero = self._tercero(numero_documento="30711915694")
        with self.assertRaises(ValidationError):
            tercero.full_clean()

    def test_codigo_unico_por_empresa(self):
        primero = self._tercero()
        primero.full_clean()
        primero.save()

        segundo = self._tercero(numero_documento="30714202959")
        with self.assertRaises(ValidationError):
            segundo.full_clean()

    def test_mismo_codigo_permitido_en_otra_empresa(self):
        primero = self._tercero()
        primero.full_clean()
        primero.save()

        segundo = self._tercero(empresa=self.otra_empresa)
        segundo.full_clean()
        segundo.save()
        self.assertNotEqual(primero.pk, segundo.pk)

    def test_documento_unico_por_empresa(self):
        primero = self._tercero()
        primero.full_clean()
        primero.save()

        segundo = self._tercero(codigo="CLI002")
        with self.assertRaises(ValidationError):
            segundo.full_clean()

    def test_mismo_documento_permitido_en_otra_empresa(self):
        primero = self._tercero()
        primero.full_clean()
        primero.save()

        segundo = self._tercero(empresa=self.otra_empresa)
        segundo.full_clean()
        segundo.save()
        self.assertNotEqual(primero.pk, segundo.pk)

    def test_empresa_y_codigo_son_inmutables(self):
        tercero = self._tercero()
        tercero.full_clean()
        tercero.save()
        tercero.codigo = "OTRO"
        with self.assertRaises(ValidationError):
            tercero.full_clean()

    def test_base_impide_duplicado_documental(self):
        primero = self._tercero()
        primero.full_clean()
        primero.save()

        segundo = self._tercero(codigo="CLI002")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Tercero.objects.create(
                    empresa=segundo.empresa,
                    codigo=segundo.codigo,
                    tipo_persona=segundo.tipo_persona,
                    tipo_documento=segundo.tipo_documento,
                    numero_documento="30711915695",
                    denominacion=segundo.denominacion,
                    condicion_iva=segundo.condicion_iva,
                    fecha_alta=segundo.fecha_alta,
                )


class RelacionesTerceroModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        empresa = crear_empresa()
        catalogos = obtener_catalogos()
        cls.tercero = Tercero.objects.create(
            empresa=empresa,
            codigo="T000001",
            tipo_persona=Tercero.TipoPersona.PERSONA_JURIDICA,
            tipo_documento=catalogos["cuit"],
            numero_documento="30711915695",
            denominacion="Tercero SA",
            condicion_iva=catalogos["ri"],
            fecha_alta="2026-06-21",
        )

    def test_un_solo_rol_activo_del_mismo_tipo(self):
        TerceroRol.objects.create(
            tercero=self.tercero,
            rol=TerceroRol.Rol.CLIENTE,
            fecha_alta="2026-06-21",
        )
        duplicado = TerceroRol(
            tercero=self.tercero,
            rol=TerceroRol.Rol.CLIENTE,
            fecha_alta="2026-06-21",
        )
        with self.assertRaises(ValidationError):
            duplicado.full_clean()

    def test_un_principal_por_tipo_domicilio(self):
        DomicilioTercero.objects.create(
            tercero=self.tercero,
            tipo=DomicilioTercero.Tipo.FISCAL,
            calle="Brasil",
            numero="151",
            localidad="Rosario",
            provincia="Santa Fe",
            pais="Argentina",
            principal=True,
            fecha_alta="2026-06-21",
        )
        duplicado = DomicilioTercero(
            tercero=self.tercero,
            tipo=DomicilioTercero.Tipo.FISCAL,
            calle="Córdoba",
            numero="1000",
            localidad="Rosario",
            provincia="Santa Fe",
            pais="Argentina",
            principal=True,
            fecha_alta="2026-06-21",
        )
        with self.assertRaises(ValidationError):
            duplicado.full_clean()

    def test_domicilio_formateado(self):
        domicilio = DomicilioTercero(
            tercero=self.tercero,
            tipo=DomicilioTercero.Tipo.COMERCIAL,
            calle="Brasil",
            numero="151",
            piso="2",
            departamento="A",
            localidad="Rosario",
            codigo_postal="2000",
            provincia="Santa Fe",
            pais="Argentina",
            fecha_alta="2026-06-21",
        )
        self.assertIn("Brasil 151", domicilio.domicilio_formateado)
        self.assertIn("Piso 2", domicilio.domicilio_formateado)
        self.assertIn("Rosario", domicilio.domicilio_formateado)

    def test_contacto_requiere_medio(self):
        contacto = ContactoTercero(
            tercero=self.tercero,
            nombre="Administración",
            fecha_alta="2026-06-21",
        )
        with self.assertRaises(ValidationError):
            contacto.full_clean()

    def test_un_solo_contacto_principal_activo(self):
        ContactoTercero.objects.create(
            tercero=self.tercero,
            nombre="Uno",
            telefono="3415550001",
            principal=True,
            fecha_alta="2026-06-21",
        )
        duplicado = ContactoTercero(
            tercero=self.tercero,
            nombre="Dos",
            telefono="3415550002",
            principal=True,
            fecha_alta="2026-06-21",
        )
        with self.assertRaises(ValidationError):
            duplicado.full_clean()
