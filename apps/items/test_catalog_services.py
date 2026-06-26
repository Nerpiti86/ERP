from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase

from apps.nucleo.models import Auditoria, Empresa

from .models import AlicuotaIVA, CategoriaItem, Item, Marca, UnidadMedida
from .services import (
    actualizar_categoria,
    actualizar_marca,
    crear_categoria,
    crear_marca,
    inactivar_categoria,
    inactivar_marca,
)


User = get_user_model()


class CatalogosEmpresaServicesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.empresa = Empresa.objects.create(
            cuit="30711915695",
            razon_social="Empresa Uno SA",
        )
        cls.otra_empresa = Empresa.objects.create(
            cuit="30714202959",
            razon_social="Empresa Dos SA",
        )
        cls.usuario = User.objects.create_user(
            username="catalogos_items",
            password="password-test",
        )
        cls.unidad = UnidadMedida.objects.get(codigo="UNIDAD")
        cls.iva_21 = AlicuotaIVA.objects.get(codigo="IVA_21")

    def setUp(self):
        self.request = RequestFactory().post(
            "/items/",
            REMOTE_ADDR="127.0.0.1",
            HTTP_USER_AGENT="tests-catalogos-items",
        )
        self.request.user = self.usuario

    def test_crea_categoria_y_audita(self):
        categoria = crear_categoria(
            empresa=self.empresa,
            codigo=" insumos ",
            nombre=" Insumos ",
            descripcion=" Materiales ",
            request=self.request,
        )
        self.assertEqual(categoria.codigo, "INSUMOS")
        self.assertEqual(categoria.nombre, "Insumos")
        auditoria = Auditoria.objects.get(
            tabla=CategoriaItem._meta.db_table,
            registro_id=str(categoria.pk),
            accion=Auditoria.Accion.INSERT,
        )
        self.assertEqual(auditoria.datos_nuevos["codigo"], "INSUMOS")

    def test_actualiza_categoria_sin_cambiar_codigo(self):
        categoria = crear_categoria(
            empresa=self.empresa,
            codigo="INSUMOS",
            nombre="Insumos",
            descripcion="",
        )
        actualizada = actualizar_categoria(
            empresa=self.empresa,
            categoria=categoria,
            nombre="Insumos odontológicos",
            descripcion="Descripción",
            request=self.request,
        )
        self.assertEqual(actualizada.codigo, "INSUMOS")
        self.assertEqual(actualizada.nombre, "Insumos odontológicos")

    def test_no_actualiza_categoria_de_otra_empresa(self):
        categoria = crear_categoria(
            empresa=self.otra_empresa,
            codigo="OTRA",
            nombre="Otra",
            descripcion="",
        )
        with self.assertRaises(ValidationError):
            actualizar_categoria(
                empresa=self.empresa,
                categoria=categoria,
                nombre="Cambio",
                descripcion="",
            )

    def test_inactiva_categoria_sin_items_activos(self):
        categoria = crear_categoria(
            empresa=self.empresa,
            codigo="LIBRE",
            nombre="Libre",
            descripcion="",
        )
        inactivar_categoria(
            empresa=self.empresa,
            categoria=categoria,
            request=self.request,
        )
        categoria.refresh_from_db()
        self.assertFalse(categoria.activo)

    def test_no_inactiva_categoria_usada_por_item_activo(self):
        categoria = crear_categoria(
            empresa=self.empresa,
            codigo="USADA",
            nombre="Usada",
            descripcion="",
        )
        Item.objects.create(
            empresa=self.empresa,
            codigo="ITEMCAT",
            nombre="Ítem con categoría",
            tipo=Item.Tipo.PRODUCTO,
            categoria=categoria,
            unidad_medida=self.unidad,
            se_vende=True,
            tratamiento_iva=Item.TratamientoIVA.GRAVADO,
            alicuota_iva=self.iva_21,
        )
        with self.assertRaises(ValidationError):
            inactivar_categoria(
                empresa=self.empresa,
                categoria=categoria,
            )

    def test_crea_actualiza_e_inactiva_marca(self):
        marca = crear_marca(
            empresa=self.empresa,
            codigo="MARCA1",
            nombre="Marca uno",
            request=self.request,
        )
        marca = actualizar_marca(
            empresa=self.empresa,
            marca=marca,
            nombre="Marca actualizada",
            request=self.request,
        )
        self.assertEqual(marca.nombre, "Marca actualizada")
        inactivar_marca(
            empresa=self.empresa,
            marca=marca,
            request=self.request,
        )
        marca.refresh_from_db()
        self.assertFalse(marca.activo)

    def test_no_inactiva_marca_usada_por_item_activo(self):
        marca = crear_marca(
            empresa=self.empresa,
            codigo="USADA",
            nombre="Usada",
        )
        Item.objects.create(
            empresa=self.empresa,
            codigo="ITEMMARCA",
            nombre="Ítem con marca",
            tipo=Item.Tipo.PRODUCTO,
            marca=marca,
            unidad_medida=self.unidad,
            se_vende=True,
            tratamiento_iva=Item.TratamientoIVA.GRAVADO,
            alicuota_iva=self.iva_21,
        )
        with self.assertRaises(ValidationError):
            inactivar_marca(
                empresa=self.empresa,
                marca=marca,
            )
