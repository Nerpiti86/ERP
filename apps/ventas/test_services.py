from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase

from apps.items.models import AlicuotaIVA, Item, UnidadMedida
from apps.nucleo.models import Auditoria, PuntoVenta, Sucursal
from apps.terceros.models import TerceroRol
from apps.terceros.tests_support import (
    crear_empresa,
    crear_tercero_prueba,
)

from .models import ComprobanteVenta, TipoComprobanteVenta
from .services import (
    anular_comprobante_venta,
    crear_borrador_venta,
    validar_comprobante_venta,
)


User = get_user_model()


class VentasServicesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.empresa = crear_empresa()
        cls.sucursal = Sucursal.objects.create(
            empresa=cls.empresa,
            codigo="CENTRAL",
            nombre="Casa central",
            es_casa_central=True,
        )
        cls.punto_venta = PuntoVenta.objects.create(
            empresa=cls.empresa,
            sucursal=cls.sucursal,
            numero=1,
            sistema_emision=PuntoVenta.SistemaEmision.MANUAL,
            predeterminado=True,
            activo=True,
        )
        cls.unidad = UnidadMedida.objects.get(codigo="UNIDAD")
        cls.alicuota = AlicuotaIVA.objects.get(codigo="IVA_21")
        cls.item = Item.objects.create(
            empresa=cls.empresa,
            codigo="SERV001",
            nombre="Servicio de prueba",
            tipo=Item.Tipo.SERVICIO,
            unidad_medida=cls.unidad,
            se_compra=False,
            se_vende=True,
            controla_stock=False,
            tratamiento_iva=Item.TratamientoIVA.GRAVADO,
            alicuota_iva=cls.alicuota,
            activo=True,
        )
        cls.item_no_vendible = Item.objects.create(
            empresa=cls.empresa,
            codigo="COMP001",
            nombre="Compra interna",
            tipo=Item.Tipo.PRODUCTO,
            unidad_medida=cls.unidad,
            se_compra=True,
            se_vende=False,
            controla_stock=False,
            tratamiento_iva=Item.TratamientoIVA.EXENTO,
            alicuota_iva=None,
            activo=True,
        )
        cls.factura_a = TipoComprobanteVenta.objects.get(codigo_arca=1)
        cls.nota_credito_a = TipoComprobanteVenta.objects.get(codigo_arca=3)
        cls.usuario = User.objects.create_user(
            username="ventas_operador",
            password="password-test",
        )

    def setUp(self):
        self.request = RequestFactory().post(
            "/ventas/",
            REMOTE_ADDR="127.0.0.1",
            HTTP_USER_AGENT="tests-ventas",
        )
        self.request.user = self.usuario
        self.cliente = crear_tercero_prueba(
            empresa=self.empresa,
            codigo="CLI001",
            numero_documento="30711915695",
            denominacion="Cliente Uno SA",
            request=self.request,
        )

    def _linea(self, **cambios):
        datos = {
            "item": self.item,
            "cantidad": Decimal("2"),
            "precio_unitario": Decimal("100.00"),
            "descuento_porcentaje": Decimal("0.00"),
        }
        datos.update(cambios)
        return datos

    def _crear_borrador(self, **cambios):
        datos = {
            "empresa": self.empresa,
            "sucursal": self.sucursal,
            "punto_venta": self.punto_venta,
            "tipo_comprobante": self.factura_a,
            "fecha": "2026-06-30",
            "fecha_vencimiento": None,
            "cliente": self.cliente,
            "lineas": [self._linea()],
            "observaciones": "",
            "request": self.request,
        }
        datos.update(cambios)
        return crear_borrador_venta(**datos)

    def test_crea_borrador_con_totales_y_auditoria(self):
        comprobante = self._crear_borrador()

        self.assertEqual(comprobante.estado, ComprobanteVenta.Estado.BORRADOR)
        self.assertEqual(comprobante.subtotal_gravado, Decimal("200.00"))
        self.assertEqual(comprobante.total_iva, Decimal("42.00"))
        self.assertEqual(comprobante.total, Decimal("242.00"))
        self.assertEqual(comprobante.totales_iva.count(), 1)
        self.assertEqual(
            comprobante.totales_iva.get().base_imponible,
            Decimal("200.00"),
        )

        auditoria = Auditoria.objects.get(
            tabla=ComprobanteVenta._meta.db_table,
            registro_id=str(comprobante.pk),
            accion=Auditoria.Accion.INSERT,
        )
        self.assertEqual(auditoria.empresa, self.empresa)
        self.assertEqual(auditoria.usuario, self.usuario)
        self.assertEqual(auditoria.datos_nuevos["total"], "242.00")

    def test_rechaza_tercero_sin_rol_cliente(self):
        proveedor = crear_tercero_prueba(
            empresa=self.empresa,
            codigo="PROV001",
            numero_documento="30714202959",
            denominacion="Proveedor Uno SA",
            roles={TerceroRol.Rol.PROVEEDOR},
            request=self.request,
        )

        with self.assertRaises(ValidationError):
            self._crear_borrador(cliente=proveedor)

    def test_rechaza_item_no_vendible(self):
        with self.assertRaises(ValidationError):
            self._crear_borrador(lineas=[self._linea(item=self.item_no_vendible)])

    def test_valida_borrador_sin_factura_electronica(self):
        comprobante = self._crear_borrador()

        validado = validar_comprobante_venta(
            empresa=self.empresa,
            comprobante=comprobante,
            request=self.request,
        )

        self.assertEqual(validado.estado, ComprobanteVenta.Estado.VALIDADO)

    def test_nota_credito_requiere_comprobante_asociado(self):
        comprobante = self._crear_borrador(
            tipo_comprobante=self.nota_credito_a,
        )

        with self.assertRaises(ValidationError):
            validar_comprobante_venta(
                empresa=self.empresa,
                comprobante=comprobante,
                request=self.request,
            )

    def test_anula_borrador_sin_borrar_historia(self):
        comprobante = self._crear_borrador()

        anulado = anular_comprobante_venta(
            empresa=self.empresa,
            comprobante=comprobante,
            request=self.request,
        )

        self.assertEqual(anulado.estado, ComprobanteVenta.Estado.ANULADO)
        self.assertTrue(anulado.lineas.exists())
