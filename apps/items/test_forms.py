from django.test import TestCase

from apps.nucleo.models import Empresa

from .forms import CategoriaItemForm, ItemForm, MarcaForm
from .models import AlicuotaIVA, CategoriaItem, Item, Marca, UnidadMedida


class ItemFormsTests(TestCase):
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
        cls.iva_21 = AlicuotaIVA.objects.get(codigo="IVA_21")
        cls.categoria = CategoriaItem.objects.create(
            empresa=cls.empresa,
            codigo="GENERAL",
            nombre="General",
        )
        cls.categoria_otra = CategoriaItem.objects.create(
            empresa=cls.otra_empresa,
            codigo="OTRA",
            nombre="Otra",
        )
        cls.marca = Marca.objects.create(
            empresa=cls.empresa,
            codigo="MARCA",
            nombre="Marca",
        )

    def datos_item(self, **cambios):
        datos = {
            "codigo": "ITEM001",
            "nombre": "Ítem",
            "descripcion": "",
            "tipo": Item.Tipo.PRODUCTO,
            "categoria": self.categoria.pk,
            "marca": self.marca.pk,
            "unidad_medida": self.unidad.pk,
            "se_vende": "on",
            "tratamiento_iva": Item.TratamientoIVA.GRAVADO,
            "alicuota_iva": self.iva_21.pk,
            "observaciones": "",
        }
        datos.update(cambios)
        return datos

    def test_form_item_valido(self):
        form = ItemForm(
            self.datos_item(),
            empresa=self.empresa,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_rechaza_item_sin_compra_ni_venta(self):
        form = ItemForm(
            self.datos_item(se_vende=""),
            empresa=self.empresa,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("se_vende", form.errors)

    def test_form_rechaza_servicio_con_stock(self):
        form = ItemForm(
            self.datos_item(
                tipo=Item.Tipo.SERVICIO,
                controla_stock="on",
            ),
            empresa=self.empresa,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("controla_stock", form.errors)

    def test_form_no_ofrece_categoria_de_otra_empresa(self):
        form = ItemForm(empresa=self.empresa)
        self.assertIn(self.categoria, form.fields["categoria"].queryset)
        self.assertNotIn(
            self.categoria_otra,
            form.fields["categoria"].queryset,
        )

    def test_edicion_deshabilita_codigo(self):
        item = Item.objects.create(
            empresa=self.empresa,
            codigo="EDITAR",
            nombre="Editar",
            tipo=Item.Tipo.PRODUCTO,
            unidad_medida=self.unidad,
            se_vende=True,
            tratamiento_iva=Item.TratamientoIVA.GRAVADO,
            alicuota_iva=self.iva_21,
        )
        form = ItemForm(
            empresa=self.empresa,
            item=item,
        )
        self.assertTrue(form.fields["codigo"].disabled)
        self.assertEqual(form.initial["codigo"], "EDITAR")

    def test_formularios_catalogo_deshabilitan_codigo_en_edicion(self):
        categoria_form = CategoriaItemForm(categoria=self.categoria)
        marca_form = MarcaForm(marca=self.marca)
        self.assertTrue(categoria_form.fields["codigo"].disabled)
        self.assertTrue(marca_form.fields["codigo"].disabled)


    def test_item_ligado_en_edicion_conserva_codigo_inmutable(self):
        item = Item.objects.create(
            empresa=self.empresa,
            codigo="LIGADO",
            nombre="Ítem ligado",
            tipo=Item.Tipo.PRODUCTO,
            unidad_medida=self.unidad,
            se_vende=True,
            tratamiento_iva=Item.TratamientoIVA.GRAVADO,
            alicuota_iva=self.iva_21,
        )
        form = ItemForm(
            self.datos_item(
                codigo="CODIGO_IGNORADO",
                nombre="Ítem editado",
            ),
            empresa=self.empresa,
            item=item,
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["codigo"], "LIGADO")

    def test_catalogos_ligados_en_edicion_conservan_codigo_inmutable(self):
        categoria_form = CategoriaItemForm(
            {
                "codigo": "OTRO",
                "nombre": "Categoría editada",
                "descripcion": "Descripción",
            },
            categoria=self.categoria,
        )
        marca_form = MarcaForm(
            {
                "codigo": "OTRA",
                "nombre": "Marca editada",
            },
            marca=self.marca,
        )

        self.assertTrue(categoria_form.is_valid(), categoria_form.errors)
        self.assertTrue(marca_form.is_valid(), marca_form.errors)
        self.assertEqual(
            categoria_form.cleaned_data["codigo"],
            self.categoria.codigo,
        )
        self.assertEqual(
            marca_form.cleaned_data["codigo"],
            self.marca.codigo,
        )
