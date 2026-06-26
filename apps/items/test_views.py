from django.test import TestCase
from django.urls import reverse

from apps.nucleo.empresa_activa import SESSION_EMPRESA_ACTIVA_ID
from apps.terceros.tests_support import (
    asignar_rol,
    crear_empresa,
    crear_usuario,
)

from .models import AlicuotaIVA, CategoriaItem, Item, Marca, UnidadMedida


class ItemsViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.empresa = crear_empresa()
        cls.otra_empresa = crear_empresa(
            cuit="30714202959",
            razon_social="Empresa Dos SA",
        )
        cls.operador = crear_usuario(username="operador_items_ui")
        cls.lector = crear_usuario(username="lector_items_ui")
        asignar_rol(
            usuario=cls.operador,
            empresa=cls.empresa,
            codigo_rol="OPERADOR",
        )
        asignar_rol(
            usuario=cls.lector,
            empresa=cls.empresa,
            codigo_rol="SOLO_LECTURA",
        )
        cls.unidad = UnidadMedida.objects.get(codigo="UNIDAD")
        cls.iva_21 = AlicuotaIVA.objects.get(codigo="IVA_21")
        cls.categoria = CategoriaItem.objects.create(
            empresa=cls.empresa,
            codigo="GENERAL",
            nombre="General",
        )
        cls.marca = Marca.objects.create(
            empresa=cls.empresa,
            codigo="MARCA",
            nombre="Marca",
        )
        cls.item = Item.objects.create(
            empresa=cls.empresa,
            codigo="VISIBLE",
            nombre="Ítem visible",
            tipo=Item.Tipo.PRODUCTO,
            categoria=cls.categoria,
            marca=cls.marca,
            unidad_medida=cls.unidad,
            se_vende=True,
            tratamiento_iva=Item.TratamientoIVA.GRAVADO,
            alicuota_iva=cls.iva_21,
        )
        cls.item_otra_empresa = Item.objects.create(
            empresa=cls.otra_empresa,
            codigo="OCULTO",
            nombre="Ítem oculto",
            tipo=Item.Tipo.PRODUCTO,
            unidad_medida=cls.unidad,
            se_vende=True,
            tratamiento_iva=Item.TratamientoIVA.GRAVADO,
            alicuota_iva=cls.iva_21,
        )

    def _login_empresa(self, usuario):
        self.client.force_login(usuario)
        session = self.client.session
        session[SESSION_EMPRESA_ACTIVA_ID] = self.empresa.pk
        session.save()

    def datos_item(self, **cambios):
        datos = {
            "codigo": "NUEVO",
            "nombre": "Ítem nuevo",
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

    def test_listado_requiere_login(self):
        respuesta = self.client.get(reverse("items:item_list"))
        self.assertEqual(respuesta.status_code, 302)

    def test_operador_ve_solo_items_de_empresa_activa(self):
        self._login_empresa(self.operador)
        respuesta = self.client.get(reverse("items:item_list"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Ítem visible")
        self.assertNotContains(respuesta, "Ítem oculto")
        self.assertNotIn("resumen", respuesta.context)
        self.assertEqual(respuesta.context["cantidad_resultados"], 1)
        self.assertContains(respuesta, 'class="erp-list-filter-panel')
        self.assertContains(respuesta, 'type="search"')
        self.assertContains(respuesta, "1 resultado")

    def test_navegacion_muestra_items_categorias_y_marcas(self):
        self._login_empresa(self.operador)
        respuesta = self.client.get(reverse("items:item_list"))
        self.assertContains(respuesta, "Productos y servicios")
        self.assertContains(respuesta, "Categorías de ítems")
        self.assertContains(respuesta, "Marcas")

    def test_operador_puede_crear_item(self):
        self._login_empresa(self.operador)
        respuesta = self.client.post(
            reverse("items:item_create"),
            self.datos_item(),
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(
            Item.objects.filter(
                empresa=self.empresa,
                codigo="NUEVO",
            ).exists()
        )

    def test_lector_no_puede_crear_item(self):
        self._login_empresa(self.lector)
        respuesta = self.client.get(reverse("items:item_create"))
        self.assertEqual(respuesta.status_code, 403)

    def test_detalle_de_otra_empresa_devuelve_404(self):
        self._login_empresa(self.operador)
        respuesta = self.client.get(
            reverse(
                "items:item_detail",
                kwargs={"item_id": self.item_otra_empresa.pk},
            )
        )
        self.assertEqual(respuesta.status_code, 404)

    def test_edicion_precarga_y_deshabilita_codigo(self):
        self._login_empresa(self.operador)
        respuesta = self.client.get(
            reverse(
                "items:item_edit",
                kwargs={"item_id": self.item.pk},
            )
        )
        self.assertEqual(respuesta.status_code, 200)
        form = respuesta.context["form"]
        self.assertTrue(form.fields["codigo"].disabled)
        self.assertEqual(form.initial["codigo"], "VISIBLE")
        self.assertContains(respuesta, "Modo edición")

    def test_operador_puede_editar_item(self):
        self._login_empresa(self.operador)
        respuesta = self.client.post(
            reverse(
                "items:item_edit",
                kwargs={"item_id": self.item.pk},
            ),
            self.datos_item(
                codigo=self.item.codigo,
                nombre="Ítem editado",
            ),
        )
        self.assertEqual(respuesta.status_code, 302)
        self.item.refresh_from_db()
        self.assertEqual(self.item.nombre, "Ítem editado")

    def test_inactivar_item_solo_acepta_post(self):
        self._login_empresa(self.operador)
        respuesta = self.client.get(
            reverse(
                "items:item_deactivate",
                kwargs={"item_id": self.item.pk},
            )
        )
        self.assertEqual(respuesta.status_code, 405)

    def test_operador_puede_crear_categoria(self):
        self._login_empresa(self.operador)
        respuesta = self.client.post(
            reverse("items:categoria_create"),
            {
                "codigo": "NUEVA",
                "nombre": "Nueva categoría",
                "descripcion": "",
            },
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(
            CategoriaItem.objects.filter(
                empresa=self.empresa,
                codigo="NUEVA",
            ).exists()
        )

    def test_operador_puede_editar_categoria(self):
        self._login_empresa(self.operador)
        respuesta = self.client.post(
            reverse(
                "items:categoria_edit",
                kwargs={"categoria_id": self.categoria.pk},
            ),
            {
                "codigo": self.categoria.codigo,
                "nombre": "Categoría editada",
                "descripcion": "",
            },
        )
        self.assertEqual(respuesta.status_code, 302)
        self.categoria.refresh_from_db()
        self.assertEqual(self.categoria.nombre, "Categoría editada")

    def test_no_inactiva_categoria_utilizada(self):
        self._login_empresa(self.operador)
        respuesta = self.client.post(
            reverse(
                "items:categoria_deactivate",
                kwargs={"categoria_id": self.categoria.pk},
            )
        )
        self.assertEqual(respuesta.status_code, 302)
        self.categoria.refresh_from_db()
        self.assertTrue(self.categoria.activo)

    def test_operador_puede_crear_editar_e_inactivar_marca_libre(self):
        self._login_empresa(self.operador)
        respuesta = self.client.post(
            reverse("items:marca_create"),
            {"codigo": "LIBRE", "nombre": "Marca libre"},
        )
        self.assertEqual(respuesta.status_code, 302)
        marca = Marca.objects.get(
            empresa=self.empresa,
            codigo="LIBRE",
        )

        respuesta = self.client.post(
            reverse(
                "items:marca_edit",
                kwargs={"marca_id": marca.pk},
            ),
            {"codigo": marca.codigo, "nombre": "Marca editada"},
        )
        self.assertEqual(respuesta.status_code, 302)
        marca.refresh_from_db()
        self.assertEqual(marca.nombre, "Marca editada")

        respuesta = self.client.post(
            reverse(
                "items:marca_deactivate",
                kwargs={"marca_id": marca.pk},
            )
        )
        self.assertEqual(respuesta.status_code, 302)
        marca.refresh_from_db()
        self.assertFalse(marca.activo)

    def test_lector_ve_catalogos_pero_no_puede_crearlos(self):
        self._login_empresa(self.lector)
        categorias = self.client.get(reverse("items:categoria_list"))
        marcas = self.client.get(reverse("items:marca_list"))

        self.assertEqual(categorias.status_code, 200)
        self.assertEqual(marcas.status_code, 200)
        for respuesta in (categorias, marcas):
            self.assertNotIn("resumen", respuesta.context)
            self.assertEqual(respuesta.context["cantidad_resultados"], 1)
            self.assertContains(respuesta, 'class="erp-list-filter-panel')
            self.assertContains(respuesta, 'type="search"')
            self.assertContains(respuesta, "1 resultado")

        self.assertEqual(
            self.client.get(reverse("items:categoria_create")).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(reverse("items:marca_create")).status_code,
            403,
        )
