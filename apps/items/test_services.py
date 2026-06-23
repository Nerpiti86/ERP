from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import RequestFactory, TestCase

from apps.nucleo.models import Auditoria, Empresa, PermisoFuncional, RolPermiso
from apps.nucleo.roles_iniciales import PERMISOS_INICIALES, PERMISOS_POR_ROL

from .models import AlicuotaIVA, CategoriaItem, Item, Marca, UnidadMedida
from .services import actualizar_item, crear_item, inactivar_item


User = get_user_model()


class ItemServicesTests(TestCase):
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
            username="operador_items",
            password="password-test",
        )
        cls.unidad = UnidadMedida.objects.create(
            codigo="UNIDAD",
            nombre="Unidad",
            simbolo="u",
        )
        cls.otra_unidad = UnidadMedida.objects.create(
            codigo="HORA",
            nombre="Hora",
            simbolo="h",
        )
        cls.alicuota = AlicuotaIVA.objects.create(
            codigo="IVA_21",
            nombre="IVA 21%",
            porcentaje=Decimal("21.00"),
            codigo_arca=5,
        )
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
        cls.categoria_otra_empresa = CategoriaItem.objects.create(
            empresa=cls.otra_empresa,
            codigo="OTRA",
            nombre="Otra empresa",
        )

    def setUp(self):
        self.request = RequestFactory().post(
            "/items/",
            REMOTE_ADDR="127.0.0.1",
            HTTP_USER_AGENT="tests-items",
        )
        self.request.user = self.usuario

    def _crear(self, **cambios):
        datos = {
            "empresa": self.empresa,
            "codigo": "ITEM001",
            "nombre": "Producto de prueba",
            "descripcion": "Descripción",
            "tipo": Item.Tipo.PRODUCTO,
            "categoria": self.categoria,
            "marca": self.marca,
            "unidad_medida": self.unidad,
            "se_compra": True,
            "se_vende": True,
            "controla_stock": True,
            "tratamiento_iva": Item.TratamientoIVA.GRAVADO,
            "alicuota_iva": self.alicuota,
            "observaciones": "Observación",
            "request": self.request,
        }
        datos.update(cambios)
        return crear_item(**datos)

    def _actualizar(self, item, **cambios):
        datos = {
            "empresa": self.empresa,
            "item": item,
            "nombre": "Producto actualizado",
            "descripcion": "Descripción actualizada",
            "tipo": Item.Tipo.PRODUCTO,
            "categoria": self.categoria,
            "marca": self.marca,
            "unidad_medida": self.otra_unidad,
            "se_compra": False,
            "se_vende": True,
            "controla_stock": False,
            "tratamiento_iva": Item.TratamientoIVA.EXENTO,
            "alicuota_iva": None,
            "observaciones": "Actualizado",
            "request": self.request,
        }
        datos.update(cambios)
        return actualizar_item(**datos)

    def test_crea_item_y_audita_alta(self):
        item = self._crear(codigo=" item-001 ", nombre=" Producto ")
        self.assertEqual(item.codigo, "ITEM-001")
        self.assertEqual(item.nombre, "Producto")
        self.assertTrue(item.activo)

        auditoria = Auditoria.objects.get(
            tabla=Item._meta.db_table,
            registro_id=str(item.pk),
            accion=Auditoria.Accion.INSERT,
        )
        self.assertEqual(auditoria.empresa, self.empresa)
        self.assertEqual(auditoria.usuario, self.usuario)
        self.assertEqual(auditoria.ip, "127.0.0.1")
        self.assertIsNone(auditoria.datos_anteriores)
        self.assertEqual(auditoria.datos_nuevos["codigo"], "ITEM-001")

    def test_rechaza_empresa_inactiva(self):
        self.empresa.activa = False
        self.empresa.save(update_fields=["activa"])
        with self.assertRaises(ValidationError):
            self._crear()

    def test_rechaza_categoria_de_otra_empresa(self):
        with self.assertRaises(ValidationError):
            self._crear(categoria=self.categoria_otra_empresa)

    def test_rechaza_unidad_inactiva(self):
        self.unidad.activo = False
        self.unidad.save(update_fields=["activo"])
        with self.assertRaises(ValidationError):
            self._crear()

    def test_rechaza_servicio_con_stock(self):
        with self.assertRaises(ValidationError):
            self._crear(
                tipo=Item.Tipo.SERVICIO,
                controla_stock=True,
            )

    def test_rechaza_gravado_sin_alicuota(self):
        with self.assertRaises(ValidationError):
            self._crear(alicuota_iva=None)

    def test_rechaza_exento_con_alicuota(self):
        with self.assertRaises(ValidationError):
            self._crear(
                tratamiento_iva=Item.TratamientoIVA.EXENTO,
                alicuota_iva=self.alicuota,
            )

    def test_actualiza_item_con_snapshot_de_auditoria(self):
        item = self._crear()
        actualizado = self._actualizar(item)

        self.assertEqual(actualizado.codigo, "ITEM001")
        self.assertEqual(actualizado.nombre, "Producto actualizado")
        self.assertEqual(actualizado.unidad_medida, self.otra_unidad)
        self.assertEqual(actualizado.tratamiento_iva, Item.TratamientoIVA.EXENTO)

        auditoria = Auditoria.objects.get(
            tabla=Item._meta.db_table,
            registro_id=str(item.pk),
            accion=Auditoria.Accion.UPDATE,
        )
        self.assertEqual(
            auditoria.datos_anteriores["nombre"],
            "Producto de prueba",
        )
        self.assertEqual(
            auditoria.datos_nuevos["nombre"],
            "Producto actualizado",
        )
        self.assertEqual(auditoria.datos_anteriores["activo"], True)
        self.assertEqual(auditoria.datos_nuevos["activo"], True)

    def test_no_actualiza_item_de_otra_empresa(self):
        item = self._crear()
        with self.assertRaises(ValidationError):
            self._actualizar(item, empresa=self.otra_empresa)

    def test_no_actualiza_item_inactivo(self):
        item = self._crear()
        inactivar_item(
            empresa=self.empresa,
            item=item,
            request=self.request,
        )
        with self.assertRaises(ValidationError):
            self._actualizar(item)

    def test_inactiva_item_y_audita_cambio(self):
        item = self._crear()
        inactivado = inactivar_item(
            empresa=self.empresa,
            item=item,
            request=self.request,
        )

        self.assertFalse(inactivado.activo)
        auditoria = (
            Auditoria.objects.filter(
                tabla=Item._meta.db_table,
                registro_id=str(item.pk),
                accion=Auditoria.Accion.UPDATE,
            )
            .order_by("-pk")
            .first()
        )
        self.assertIsNotNone(auditoria)
        self.assertEqual(auditoria.datos_anteriores["activo"], True)
        self.assertEqual(auditoria.datos_nuevos["activo"], False)

    def test_no_inactiva_dos_veces(self):
        item = self._crear()
        inactivar_item(
            empresa=self.empresa,
            item=item,
            request=self.request,
        )
        with self.assertRaises(ValidationError):
            inactivar_item(
                empresa=self.empresa,
                item=item,
                request=self.request,
            )


class PermisosItemsTests(TestCase):
    def ejecutar_comando(self):
        salida = StringIO()
        call_command(
            "cargar_roles_permisos_iniciales",
            stdout=salida,
        )
        return salida.getvalue()

    def test_definiciones_incluyen_permisos_items(self):
        self.assertIn("items.ver", PERMISOS_INICIALES)
        self.assertIn("items.crear", PERMISOS_INICIALES)
        self.assertIn("items.editar", PERMISOS_INICIALES)

        for rol in ("ADMIN", "CONTADOR", "OPERADOR"):
            self.assertIn("items.ver", PERMISOS_POR_ROL[rol])
            self.assertIn("items.crear", PERMISOS_POR_ROL[rol])
            self.assertIn("items.editar", PERMISOS_POR_ROL[rol])

        for rol in ("AUDITOR", "SOLO_LECTURA"):
            self.assertIn("items.ver", PERMISOS_POR_ROL[rol])
            self.assertNotIn("items.crear", PERMISOS_POR_ROL[rol])
            self.assertNotIn("items.editar", PERMISOS_POR_ROL[rol])

    def test_comando_carga_permisos_items(self):
        salida = self.ejecutar_comando()

        self.assertIn("Roles y permisos iniciales cargados", salida)
        self.assertEqual(
            set(
                PermisoFuncional.objects.filter(
                    codigo__startswith="items.",
                    activo=True,
                ).values_list("codigo", flat=True)
            ),
            {"items.ver", "items.crear", "items.editar"},
        )
        self.assertTrue(
            RolPermiso.objects.filter(
                rol__codigo="OPERADOR",
                permiso__codigo="items.editar",
                activo=True,
            ).exists()
        )
        self.assertTrue(
            RolPermiso.objects.filter(
                rol__codigo="AUDITOR",
                permiso__codigo="items.ver",
                activo=True,
            ).exists()
        )
        self.assertFalse(
            RolPermiso.objects.filter(
                rol__codigo="AUDITOR",
                permiso__codigo="items.editar",
                activo=True,
            ).exists()
        )
