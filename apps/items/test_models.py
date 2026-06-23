from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.nucleo.models import Empresa

from .models import AlicuotaIVA, CategoriaItem, Item, Marca, UnidadMedida


class ItemModelTests(TestCase):
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
        cls.unidad = UnidadMedida.objects.get(codigo="UNIDAD")
        cls.alicuota = AlicuotaIVA.objects.get(codigo="IVA_21")
        cls.categoria = CategoriaItem.objects.create(
            empresa=cls.empresa,
            codigo="GENERAL",
            nombre="General",
        )
        cls.marca = Marca.objects.create(
            empresa=cls.empresa,
            codigo="SIN_MARCA",
            nombre="Sin marca",
        )

    def _item(self, **cambios):
        datos = {
            "empresa": self.empresa,
            "codigo": "ITEM001",
            "nombre": "  Ítem de prueba  ",
            "descripcion": " Descripción ",
            "tipo": Item.Tipo.PRODUCTO,
            "categoria": self.categoria,
            "marca": self.marca,
            "unidad_medida": self.unidad,
            "se_compra": False,
            "se_vende": True,
            "controla_stock": False,
            "tratamiento_iva": Item.TratamientoIVA.GRAVADO,
            "alicuota_iva": self.alicuota,
            "activo": True,
            "observaciones": " Observación ",
        }
        datos.update(cambios)
        return Item(**datos)

    def test_normaliza_codigo_y_textos(self):
        item = self._item(codigo=" item-001 ")
        item.full_clean()
        self.assertEqual(item.codigo, "ITEM-001")
        self.assertEqual(item.nombre, "Ítem de prueba")
        self.assertEqual(item.descripcion, "Descripción")
        self.assertEqual(item.observaciones, "Observación")

    def test_codigo_unico_por_empresa(self):
        primero = self._item()
        primero.full_clean()
        primero.save()

        segundo = self._item()
        with self.assertRaises(ValidationError):
            segundo.full_clean()

    def test_mismo_codigo_permitido_en_otra_empresa(self):
        primero = self._item()
        primero.full_clean()
        primero.save()

        categoria = CategoriaItem.objects.create(
            empresa=self.otra_empresa,
            codigo="GENERAL",
            nombre="General",
        )
        marca = Marca.objects.create(
            empresa=self.otra_empresa,
            codigo="SIN_MARCA",
            nombre="Sin marca",
        )
        segundo = self._item(
            empresa=self.otra_empresa,
            categoria=categoria,
            marca=marca,
        )
        segundo.full_clean()
        segundo.save()
        self.assertNotEqual(primero.pk, segundo.pk)

    def test_base_impide_codigo_duplicado(self):
        Item.objects.create(
            empresa=self.empresa,
            codigo="ITEM001",
            nombre="Primero",
            tipo=Item.Tipo.PRODUCTO,
            unidad_medida=self.unidad,
            se_vende=True,
            tratamiento_iva=Item.TratamientoIVA.GRAVADO,
            alicuota_iva=self.alicuota,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Item.objects.create(
                    empresa=self.empresa,
                    codigo="ITEM001",
                    nombre="Segundo",
                    tipo=Item.Tipo.PRODUCTO,
                    unidad_medida=self.unidad,
                    se_vende=True,
                    tratamiento_iva=Item.TratamientoIVA.GRAVADO,
                    alicuota_iva=self.alicuota,
                )

    def test_empresa_y_codigo_son_inmutables(self):
        item = self._item()
        item.full_clean()
        item.save()

        item.codigo = "OTRO"
        with self.assertRaises(ValidationError):
            item.full_clean()

        item.refresh_from_db()
        item.empresa = self.otra_empresa
        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_servicio_no_puede_controlar_stock(self):
        item = self._item(
            tipo=Item.Tipo.SERVICIO,
            controla_stock=True,
        )
        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_base_impide_stock_en_servicio(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Item.objects.create(
                    empresa=self.empresa,
                    codigo="SERV001",
                    nombre="Servicio",
                    tipo=Item.Tipo.SERVICIO,
                    unidad_medida=self.unidad,
                    se_vende=True,
                    controla_stock=True,
                    tratamiento_iva=Item.TratamientoIVA.GRAVADO,
                    alicuota_iva=self.alicuota,
                )

    def test_producto_puede_controlar_stock(self):
        item = self._item(controla_stock=True)
        item.full_clean()
        item.save()
        self.assertTrue(item.controla_stock)

    def test_requiere_compra_o_venta(self):
        item = self._item(se_compra=False, se_vende=False)
        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_base_impide_item_sin_capacidad_operativa(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Item.objects.create(
                    empresa=self.empresa,
                    codigo="SINOPER",
                    nombre="Sin operación",
                    tipo=Item.Tipo.PRODUCTO,
                    unidad_medida=self.unidad,
                    se_compra=False,
                    se_vende=False,
                    tratamiento_iva=Item.TratamientoIVA.GRAVADO,
                    alicuota_iva=self.alicuota,
                )

    def test_compra_y_venta_son_independientes(self):
        solo_compra = self._item(
            codigo="COMPRA",
            se_compra=True,
            se_vende=False,
        )
        solo_compra.full_clean()

        solo_venta = self._item(
            codigo="VENTA",
            se_compra=False,
            se_vende=True,
        )
        solo_venta.full_clean()

    def test_rechaza_catalogos_de_otra_empresa(self):
        categoria_ajena = CategoriaItem.objects.create(
            empresa=self.otra_empresa,
            codigo="AJENA",
            nombre="Ajena",
        )
        item = self._item(categoria=categoria_ajena)
        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_gravado_requiere_alicuota(self):
        item = self._item(alicuota_iva=None)
        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_exento_no_admite_alicuota(self):
        item = self._item(
            tratamiento_iva=Item.TratamientoIVA.EXENTO,
            alicuota_iva=self.alicuota,
        )
        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_exento_sin_alicuota_es_valido(self):
        item = self._item(
            tratamiento_iva=Item.TratamientoIVA.EXENTO,
            alicuota_iva=None,
        )
        item.full_clean()


class CatalogosItemTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.empresa = Empresa.objects.create(
            cuit="30711915695",
            razon_social="Empresa Uno SA",
        )

    def test_categoria_normaliza_codigo_y_nombre(self):
        categoria = CategoriaItem(
            empresa=self.empresa,
            codigo=" herramientas ",
            nombre=" Herramientas ",
        )
        categoria.full_clean()
        self.assertEqual(categoria.codigo, "HERRAMIENTAS")
        self.assertEqual(categoria.nombre, "Herramientas")

    def test_codigo_catalogo_es_inmutable(self):
        marca = Marca.objects.create(
            empresa=self.empresa,
            codigo="MARCA1",
            nombre="Marca Uno",
        )
        marca.codigo = "MARCA2"
        with self.assertRaises(ValidationError):
            marca.full_clean()
