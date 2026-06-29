from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.nucleo.empresa_activa import SESSION_EMPRESA_ACTIVA_ID
from apps.nucleo.models import Auditoria
from apps.terceros.models import TerceroRol
from apps.terceros.tests_support import (
    asignar_rol,
    crear_empresa,
    crear_tercero_prueba,
    crear_usuario,
)

from .forms import ItemProveedorForm
from .models import AlicuotaIVA, Item, ItemProveedor, UnidadMedida
from .services import (
    actualizar_item,
    actualizar_item_proveedor,
    crear_item_proveedor,
    inactivar_item,
    inactivar_item_proveedor,
    reactivar_item_proveedor,
)


def cuit_valido(seed):
    while True:
        base = f"30{seed:08d}"
        pesos = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)
        suma = sum(int(digito) * peso for digito, peso in zip(base, pesos))
        verificador = 11 - suma % 11
        if verificador == 11:
            verificador = 0
        elif verificador == 10:
            seed += 1
            continue
        return f"{base}{verificador}"


class ItemProveedorBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.empresa = crear_empresa()
        cls.otra_empresa = crear_empresa(
            cuit="30714202959",
            razon_social="Empresa Dos SA",
        )
        cls.operador = crear_usuario(username="operador_item_proveedor")
        cls.lector = crear_usuario(username="lector_item_proveedor")
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
        cls.iva = AlicuotaIVA.objects.get(codigo="IVA_21")
        cls.item = Item.objects.create(
            empresa=cls.empresa,
            codigo="COMPRA",
            nombre="Ítem comprable",
            tipo=Item.Tipo.PRODUCTO,
            unidad_medida=cls.unidad,
            se_compra=True,
            se_vende=True,
            tratamiento_iva=Item.TratamientoIVA.GRAVADO,
            alicuota_iva=cls.iva,
        )
        cls.otro_item = Item.objects.create(
            empresa=cls.empresa,
            codigo="OTRO",
            nombre="Otro ítem",
            tipo=Item.Tipo.PRODUCTO,
            unidad_medida=cls.unidad,
            se_compra=True,
            se_vende=False,
            tratamiento_iva=Item.TratamientoIVA.GRAVADO,
            alicuota_iva=cls.iva,
        )
        cls.item_solo_venta = Item.objects.create(
            empresa=cls.empresa,
            codigo="VENTA",
            nombre="Solo venta",
            tipo=Item.Tipo.PRODUCTO,
            unidad_medida=cls.unidad,
            se_compra=False,
            se_vende=True,
            tratamiento_iva=Item.TratamientoIVA.GRAVADO,
            alicuota_iva=cls.iva,
        )
        cls.item_otra_empresa = Item.objects.create(
            empresa=cls.otra_empresa,
            codigo="AJENO",
            nombre="Ítem ajeno",
            tipo=Item.Tipo.PRODUCTO,
            unidad_medida=cls.unidad,
            se_compra=True,
            se_vende=False,
            tratamiento_iva=Item.TratamientoIVA.GRAVADO,
            alicuota_iva=cls.iva,
        )

        cls.proveedor = crear_tercero_prueba(
            empresa=cls.empresa,
            numero_documento=cuit_valido(1),
            denominacion="Proveedor Uno SA",
            roles={TerceroRol.Rol.PROVEEDOR},
        )
        cls.otro_proveedor = crear_tercero_prueba(
            empresa=cls.empresa,
            numero_documento=cuit_valido(2),
            denominacion="Proveedor Dos SA",
            roles={TerceroRol.Rol.PROVEEDOR},
        )
        cls.solo_cliente = crear_tercero_prueba(
            empresa=cls.empresa,
            numero_documento=cuit_valido(3),
            denominacion="Cliente sin rol proveedor",
            roles={TerceroRol.Rol.CLIENTE},
        )
        cls.proveedor_otra_empresa = crear_tercero_prueba(
            empresa=cls.otra_empresa,
            numero_documento=cuit_valido(4),
            denominacion="Proveedor Ajeno SA",
            roles={TerceroRol.Rol.PROVEEDOR},
        )

    def setUp(self):
        self.request = RequestFactory().post(
            "/items/",
            REMOTE_ADDR="127.0.0.1",
            HTTP_USER_AGENT="tests-item-proveedor",
        )
        self.request.user = self.operador

    def relacion_directa(self, **cambios):
        datos = {
            "empresa": self.empresa,
            "item": self.item,
            "proveedor": self.proveedor,
            "codigo_proveedor": "COD-1",
            "observaciones": "",
            "activo": True,
        }
        datos.update(cambios)
        relacion = ItemProveedor(**datos)
        relacion.full_clean()
        relacion.save()
        return relacion

    def relacion_servicio(self, **cambios):
        datos = {
            "empresa": self.empresa,
            "item": self.item,
            "proveedor": self.proveedor,
            "codigo_proveedor": "COD-1",
            "observaciones": "",
            "request": self.request,
        }
        datos.update(cambios)
        return crear_item_proveedor(**datos)

    def login_empresa(self, usuario):
        self.client.force_login(usuario)
        session = self.client.session
        session[SESSION_EMPRESA_ACTIVA_ID] = self.empresa.pk
        session.save()


class ItemProveedorModelTests(ItemProveedorBase):
    def test_normaliza_codigo_y_observaciones(self):
        relacion = ItemProveedor(
            empresa=self.empresa,
            item=self.item,
            proveedor=self.proveedor,
            codigo_proveedor="  ab-12 / x  ",
            observaciones=" Nota ",
        )
        relacion.full_clean()
        self.assertEqual(relacion.codigo_proveedor, "AB-12 / X")
        self.assertEqual(relacion.observaciones, "Nota")

    def test_rechaza_relacion_historica_duplicada(self):
        self.relacion_directa()
        duplicada = ItemProveedor(
            empresa=self.empresa,
            item=self.item,
            proveedor=self.proveedor,
        )
        with self.assertRaises(ValidationError):
            duplicada.full_clean()

    def test_base_impide_relacion_duplicada(self):
        self.relacion_directa()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ItemProveedor.objects.create(
                    empresa=self.empresa,
                    item=self.item,
                    proveedor=self.proveedor,
                )

    def test_base_impide_codigo_duplicado_sin_importar_mayusculas(self):
        self.relacion_directa(codigo_proveedor="ABC-1")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ItemProveedor.objects.create(
                    empresa=self.empresa,
                    item=self.otro_item,
                    proveedor=self.proveedor,
                    codigo_proveedor="abc-1",
                )

    def test_mismo_codigo_permitido_en_proveedores_diferentes(self):
        self.relacion_directa(codigo_proveedor="ABC-1")
        segunda = ItemProveedor(
            empresa=self.empresa,
            item=self.item,
            proveedor=self.otro_proveedor,
            codigo_proveedor="ABC-1",
        )
        segunda.full_clean()
        segunda.save()
        self.assertTrue(segunda.pk)

    def test_empresa_item_y_proveedor_son_inmutables(self):
        relacion = self.relacion_directa()

        relacion.item = self.otro_item
        with self.assertRaises(ValidationError):
            relacion.full_clean()

        relacion.refresh_from_db()
        relacion.proveedor = self.otro_proveedor
        with self.assertRaises(ValidationError):
            relacion.full_clean()

        relacion.refresh_from_db()
        relacion.empresa = self.otra_empresa
        with self.assertRaises(ValidationError):
            relacion.full_clean()

    def test_rechaza_entidades_de_otra_empresa(self):
        relacion = ItemProveedor(
            empresa=self.empresa,
            item=self.item_otra_empresa,
            proveedor=self.proveedor,
        )
        with self.assertRaises(ValidationError):
            relacion.full_clean()

    def test_disponibilidad_refleja_estado_del_rol(self):
        relacion = self.relacion_directa()
        self.assertTrue(relacion.disponible_operativamente)

        TerceroRol.objects.filter(
            tercero=self.proveedor,
            rol=TerceroRol.Rol.PROVEEDOR,
            activo=True,
        ).update(activo=False)

        relacion.proveedor.refresh_from_db()
        self.assertFalse(relacion.disponible_operativamente)
        self.assertEqual(
            relacion.motivo_indisponibilidad,
            "Rol PROVEEDOR inactivo",
        )


class ItemProveedorServicesTests(ItemProveedorBase):
    def test_crea_relacion_y_audita(self):
        relacion = self.relacion_servicio(codigo_proveedor=" cod-1 ")
        self.assertEqual(relacion.codigo_proveedor, "COD-1")
        auditoria = Auditoria.objects.get(
            tabla=ItemProveedor._meta.db_table,
            registro_id=str(relacion.pk),
            accion=Auditoria.Accion.INSERT,
        )
        self.assertEqual(auditoria.usuario, self.operador)
        self.assertTrue(
            auditoria.datos_nuevos["disponible_operativamente"]
        )

    def test_rechaza_item_no_comprable(self):
        with self.assertRaises(ValidationError):
            self.relacion_servicio(item=self.item_solo_venta)

    def test_rechaza_tercero_sin_rol_proveedor(self):
        with self.assertRaises(ValidationError):
            self.relacion_servicio(proveedor=self.solo_cliente)

    def test_rechaza_proveedor_de_otra_empresa(self):
        with self.assertRaises(ValidationError):
            self.relacion_servicio(proveedor=self.proveedor_otra_empresa)

    def test_actualiza_codigo_y_observaciones(self):
        relacion = self.relacion_servicio()
        actualizada = actualizar_item_proveedor(
            empresa=self.empresa,
            relacion=relacion,
            codigo_proveedor=" nuevo ",
            observaciones=" Observación ",
            request=self.request,
        )
        self.assertEqual(actualizada.codigo_proveedor, "NUEVO")
        self.assertEqual(actualizada.observaciones, "Observación")
        auditoria = Auditoria.objects.filter(
            tabla=ItemProveedor._meta.db_table,
            registro_id=str(relacion.pk),
            accion=Auditoria.Accion.UPDATE,
        ).latest("pk")
        self.assertEqual(
            auditoria.datos_anteriores["codigo_proveedor"],
            "COD-1",
        )
        self.assertEqual(
            auditoria.datos_nuevos["codigo_proveedor"],
            "NUEVO",
        )

    def test_inactiva_y_reactiva_la_misma_fila(self):
        relacion = self.relacion_servicio()
        pk = relacion.pk
        inactivar_item_proveedor(
            empresa=self.empresa,
            relacion=relacion,
            request=self.request,
        )
        relacion.refresh_from_db()
        self.assertFalse(relacion.activo)
        self.assertIsNotNone(relacion.fecha_baja)

        reactivar_item_proveedor(
            empresa=self.empresa,
            relacion=relacion,
            request=self.request,
        )
        relacion.refresh_from_db()
        self.assertEqual(relacion.pk, pk)
        self.assertTrue(relacion.activo)
        self.assertIsNone(relacion.fecha_baja)

    def test_reactivacion_requiere_rol_proveedor_activo(self):
        relacion = self.relacion_servicio()
        inactivar_item_proveedor(
            empresa=self.empresa,
            relacion=relacion,
            request=self.request,
        )
        TerceroRol.objects.filter(
            tercero=self.proveedor,
            rol=TerceroRol.Rol.PROVEEDOR,
            activo=True,
        ).update(activo=False)

        with self.assertRaises(ValidationError):
            reactivar_item_proveedor(
                empresa=self.empresa,
                relacion=relacion,
                request=self.request,
            )

    def test_bloquea_quitar_capacidad_de_compra(self):
        self.relacion_servicio()
        with self.assertRaises(ValidationError):
            actualizar_item(
                empresa=self.empresa,
                item=self.item,
                nombre=self.item.nombre,
                descripcion=self.item.descripcion,
                tipo=self.item.tipo,
                categoria=self.item.categoria,
                marca=self.item.marca,
                unidad_medida=self.item.unidad_medida,
                se_compra=False,
                se_vende=True,
                controla_stock=self.item.controla_stock,
                tratamiento_iva=self.item.tratamiento_iva,
                alicuota_iva=self.item.alicuota_iva,
                observaciones=self.item.observaciones,
                request=self.request,
            )

    def test_inactivar_item_conserva_relacion(self):
        relacion = self.relacion_servicio()
        inactivar_item(
            empresa=self.empresa,
            item=self.item,
            request=self.request,
        )
        relacion.refresh_from_db()
        self.assertTrue(relacion.activo)
        self.assertFalse(relacion.disponible_operativamente)
        self.assertEqual(relacion.motivo_indisponibilidad, "Ítem inactivo")

    def test_alta_duplicada_indica_editar_o_reactivar(self):
        relacion = self.relacion_servicio()
        inactivar_item_proveedor(
            empresa=self.empresa,
            relacion=relacion,
            request=self.request,
        )
        with self.assertRaises(ValidationError) as contexto:
            self.relacion_servicio()
        self.assertIn("reactivarla", str(contexto.exception))


class ItemProveedorFormsTests(ItemProveedorBase):
    def test_selector_limita_proveedores_y_excluye_historial(self):
        form = ItemProveedorForm(
            empresa=self.empresa,
            item=self.item,
        )
        self.assertIn(
            self.proveedor,
            form.fields["proveedor"].queryset,
        )
        self.assertNotIn(
            self.solo_cliente,
            form.fields["proveedor"].queryset,
        )
        self.assertNotIn(
            self.proveedor_otra_empresa,
            form.fields["proveedor"].queryset,
        )

        self.relacion_directa()
        form = ItemProveedorForm(
            empresa=self.empresa,
            item=self.item,
        )
        self.assertNotIn(
            self.proveedor,
            form.fields["proveedor"].queryset,
        )

    def test_edicion_deshabilita_proveedor(self):
        relacion = self.relacion_directa()
        form = ItemProveedorForm(
            empresa=self.empresa,
            item=self.item,
            relacion=relacion,
        )
        self.assertTrue(form.fields["proveedor"].disabled)
        self.assertEqual(form.initial["proveedor"], self.proveedor)


class ItemProveedorViewsTests(ItemProveedorBase):
    def test_detalle_muestra_proveedor(self):
        self.relacion_directa()
        self.login_empresa(self.operador)
        respuesta = self.client.get(
            reverse("items:item_detail", kwargs={"item_id": self.item.pk})
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Proveedor Uno SA")
        self.assertContains(respuesta, "COD-1")
        self.assertContains(respuesta, "Disponible")

    def test_lector_consulta_sin_acciones(self):
        self.relacion_directa()
        self.login_empresa(self.lector)
        respuesta = self.client.get(
            reverse("items:item_detail", kwargs={"item_id": self.item.pk})
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Proveedor Uno SA")
        self.assertNotContains(respuesta, "Agregar proveedor")
        self.assertNotContains(respuesta, ">Inactivar<")

    def test_operador_puede_asociar_proveedor(self):
        self.login_empresa(self.operador)
        respuesta = self.client.post(
            reverse(
                "items:item_proveedor_create",
                kwargs={"item_id": self.item.pk},
            ),
            {
                "proveedor": self.proveedor.pk,
                "codigo_proveedor": " codigo-web ",
                "observaciones": "",
            },
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(
            ItemProveedor.objects.filter(
                empresa=self.empresa,
                item=self.item,
                proveedor=self.proveedor,
                codigo_proveedor="CODIGO-WEB",
            ).exists()
        )

    def test_lector_no_puede_asociar_proveedor(self):
        self.login_empresa(self.lector)
        respuesta = self.client.get(
            reverse(
                "items:item_proveedor_create",
                kwargs={"item_id": self.item.pk},
            )
        )
        self.assertEqual(respuesta.status_code, 403)

    def test_formulario_rechaza_proveedor_de_otra_empresa(self):
        self.login_empresa(self.operador)
        respuesta = self.client.post(
            reverse(
                "items:item_proveedor_create",
                kwargs={"item_id": self.item.pk},
            ),
            {
                "proveedor": self.proveedor_otra_empresa.pk,
                "codigo_proveedor": "",
                "observaciones": "",
            },
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(
            ItemProveedor.objects.filter(
                empresa=self.empresa,
                item=self.item,
            ).exists()
        )

    def test_inactivacion_solo_post_y_funciona(self):
        relacion = self.relacion_directa()
        self.login_empresa(self.operador)
        url = reverse(
            "items:item_proveedor_deactivate",
            kwargs={"item_id": self.item.pk, "relacion_id": relacion.pk},
        )
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url).status_code, 302)
        relacion.refresh_from_db()
        self.assertFalse(relacion.activo)

    def test_reactivacion_funciona(self):
        relacion = self.relacion_servicio()
        inactivar_item_proveedor(
            empresa=self.empresa,
            relacion=relacion,
            request=self.request,
        )
        self.login_empresa(self.operador)
        respuesta = self.client.post(
            reverse(
                "items:item_proveedor_reactivate",
                kwargs={
                    "item_id": self.item.pk,
                    "relacion_id": relacion.pk,
                },
            )
        )
        self.assertEqual(respuesta.status_code, 302)
        relacion.refresh_from_db()
        self.assertTrue(relacion.activo)

    def test_relacion_de_otra_empresa_devuelve_404(self):
        relacion = ItemProveedor.objects.create(
            empresa=self.otra_empresa,
            item=self.item_otra_empresa,
            proveedor=self.proveedor_otra_empresa,
        )
        self.login_empresa(self.operador)
        respuesta = self.client.get(
            reverse(
                "items:item_proveedor_edit",
                kwargs={
                    "item_id": self.item.pk,
                    "relacion_id": relacion.pk,
                },
            )
        )
        self.assertEqual(respuesta.status_code, 404)
