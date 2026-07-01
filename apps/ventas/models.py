from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from apps.items.models import AlicuotaIVA, Item, UnidadMedida
from apps.nucleo.models import Empresa, PuntoVenta, Sucursal
from apps.terceros.models import Tercero


class TipoComprobanteVenta(models.Model):
    class Clase(models.TextChoices):
        A = "A", "A"
        B = "B", "B"
        C = "C", "C"
        E = "E", "E"
        M = "M", "M"
        X = "X", "Interno"

    class Especie(models.TextChoices):
        FACTURA = "FACTURA", "Factura"
        NOTA_DEBITO = "NOTA_DEBITO", "Nota de debito"
        NOTA_CREDITO = "NOTA_CREDITO", "Nota de credito"
        RECIBO = "RECIBO", "Recibo"
        REMITO = "REMITO", "Remito"
        OTRO = "OTRO", "Otro"

    class Signo(models.IntegerChoices):
        POSITIVO = 1, "Positivo"
        NEGATIVO = -1, "Negativo"
        NEUTRO = 0, "Neutro"

    codigo_arca = models.PositiveSmallIntegerField(unique=True)
    nombre = models.CharField(max_length=160)
    abreviatura = models.CharField(max_length=20)
    clase = models.CharField(max_length=1, choices=Clase.choices)
    especie = models.CharField(max_length=20, choices=Especie.choices)
    signo = models.SmallIntegerField(
        choices=Signo.choices,
        default=Signo.POSITIVO,
    )
    mueve_iva = models.BooleanField(default=True)
    requiere_comprobante_asociado = models.BooleanField(default=False)
    electronico = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)
    sistema = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ventas_tipocomprobanteventa"
        verbose_name = "tipo de comprobante de venta"
        verbose_name_plural = "tipos de comprobante de venta"
        ordering = ["codigo_arca", "nombre"]

    def _normalizar_campos(self):
        self.nombre = self.nombre.strip()
        self.abreviatura = self.abreviatura.strip().upper()

    def clean(self):
        super().clean()
        self._normalizar_campos()

    def save(self, *args, **kwargs):
        self._normalizar_campos()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo_arca} - {self.nombre}"


class ComprobanteVenta(models.Model):
    class Estado(models.TextChoices):
        BORRADOR = "BORRADOR", "Borrador"
        VALIDADO = "VALIDADO", "Validado"
        EMITIDO = "EMITIDO", "Emitido"
        ANULADO = "ANULADO", "Anulado"

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="comprobantes_venta",
    )
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.PROTECT,
        related_name="comprobantes_venta",
    )
    punto_venta = models.ForeignKey(
        PuntoVenta,
        on_delete=models.PROTECT,
        related_name="comprobantes_venta",
        null=True,
        blank=True,
    )
    tipo_comprobante = models.ForeignKey(
        TipoComprobanteVenta,
        on_delete=models.PROTECT,
        related_name="comprobantes_venta",
    )
    numero = models.PositiveIntegerField(null=True, blank=True)
    fecha = models.DateField(default=timezone.localdate)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    cliente = models.ForeignKey(
        Tercero,
        on_delete=models.PROTECT,
        related_name="comprobantes_venta",
    )
    cliente_denominacion = models.CharField(max_length=200)
    cliente_tipo_documento_codigo = models.CharField(max_length=30, blank=True)
    cliente_numero_documento = models.CharField(max_length=30, blank=True)
    cliente_condicion_iva_codigo = models.CharField(max_length=40, blank=True)
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.BORRADOR,
    )
    subtotal_gravado = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    subtotal_no_gravado = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    subtotal_exento = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    total_iva = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    total_tributos = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    total = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    observaciones = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ventas_comprobanteventa"
        verbose_name = "comprobante de venta"
        verbose_name_plural = "comprobantes de venta"
        ordering = ["empresa__razon_social", "-fecha", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "empresa",
                    "tipo_comprobante",
                    "punto_venta",
                    "numero",
                ],
                condition=Q(numero__isnull=False),
                name="uniq_cv_emp_tipo_pv_num",
            ),
            models.CheckConstraint(
                condition=(
                    Q(fecha_vencimiento__isnull=True)
                    | Q(fecha_vencimiento__gte=F("fecha"))
                ),
                name="chk_cv_fechas",
            ),
            models.CheckConstraint(
                condition=Q(numero__isnull=True) | Q(punto_venta__isnull=False),
                name="chk_cv_numero_requiere_pv",
            ),
        ]
        indexes = [
            models.Index(fields=["empresa", "fecha"], name="idx_cv_emp_fecha"),
            models.Index(fields=["empresa", "estado", "fecha"], name="idx_cv_emp_est_fecha"),
            models.Index(fields=["empresa", "cliente"], name="idx_cv_emp_cliente"),
        ]

    def _normalizar_campos(self):
        self.cliente_denominacion = self.cliente_denominacion.strip()
        self.cliente_tipo_documento_codigo = (
            self.cliente_tipo_documento_codigo.strip().upper()
        )
        self.cliente_numero_documento = self.cliente_numero_documento.strip()
        self.cliente_condicion_iva_codigo = (
            self.cliente_condicion_iva_codigo.strip().upper()
        )
        self.observaciones = self.observaciones.strip()

    def clean(self):
        super().clean()
        self._normalizar_campos()
        errores = {}

        if self.sucursal_id and self.empresa_id:
            if self.sucursal.empresa_id != self.empresa_id:
                errores["sucursal"] = "La sucursal no pertenece a la empresa."

        if self.punto_venta_id:
            if self.punto_venta.empresa_id != self.empresa_id:
                errores["punto_venta"] = (
                    "El punto de venta no pertenece a la empresa."
                )
            if self.sucursal_id and self.punto_venta.sucursal_id != self.sucursal_id:
                errores["punto_venta"] = (
                    "El punto de venta no pertenece a la sucursal."
                )

        if self.cliente_id and self.empresa_id:
            if self.cliente.empresa_id != self.empresa_id:
                errores["cliente"] = "El cliente no pertenece a la empresa."

        if (
            self.fecha_vencimiento is not None
            and self.fecha is not None
            and self.fecha_vencimiento < self.fecha
        ):
            errores["fecha_vencimiento"] = (
                "La fecha de vencimiento no puede ser anterior a la fecha."
            )

        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        self._normalizar_campos()
        super().save(*args, **kwargs)

    @property
    def identificacion(self):
        if self.numero and self.punto_venta_id:
            return (
                f"{self.tipo_comprobante.abreviatura} "
                f"{self.punto_venta.numero:05d}-{self.numero:08d}"
            )
        return f"{self.tipo_comprobante.abreviatura} borrador #{self.pk or '-'}"

    def __str__(self):
        return self.identificacion


class ComprobanteVentaLinea(models.Model):
    comprobante = models.ForeignKey(
        ComprobanteVenta,
        on_delete=models.CASCADE,
        related_name="lineas",
    )
    numero_linea = models.PositiveSmallIntegerField()
    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        related_name="lineas_venta",
        null=True,
        blank=True,
    )
    descripcion = models.CharField(max_length=300)
    unidad_medida = models.ForeignKey(
        UnidadMedida,
        on_delete=models.PROTECT,
        related_name="lineas_venta",
    )
    cantidad = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0.0001"))],
    )
    precio_unitario = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0.0000"))],
    )
    descuento_porcentaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
        ],
    )
    tratamiento_iva = models.CharField(
        max_length=20,
        choices=Item.TratamientoIVA.choices,
        default=Item.TratamientoIVA.GRAVADO,
    )
    alicuota_iva = models.ForeignKey(
        AlicuotaIVA,
        on_delete=models.PROTECT,
        related_name="lineas_venta",
        null=True,
        blank=True,
    )
    subtotal_gravado = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    subtotal_no_gravado = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    subtotal_exento = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    iva_importe = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    total_linea = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    class Meta:
        db_table = "ventas_comprobanteventalinea"
        verbose_name = "linea de comprobante de venta"
        verbose_name_plural = "lineas de comprobante de venta"
        ordering = ["comprobante_id", "numero_linea"]
        constraints = [
            models.UniqueConstraint(
                fields=["comprobante", "numero_linea"],
                name="uniq_cvl_comprobante_linea",
            ),
            models.CheckConstraint(
                condition=Q(descuento_porcentaje__gte=0)
                & Q(descuento_porcentaje__lte=100),
                name="chk_cvl_descuento_rango",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        tratamiento_iva=Item.TratamientoIVA.GRAVADO,
                        alicuota_iva__isnull=False,
                    )
                    | (
                        ~Q(tratamiento_iva=Item.TratamientoIVA.GRAVADO)
                        & Q(alicuota_iva__isnull=True)
                    )
                ),
                name="chk_cvl_tratamiento_iva",
            ),
        ]

    def _normalizar_campos(self):
        self.descripcion = self.descripcion.strip()

    def clean(self):
        super().clean()
        self._normalizar_campos()
        errores = {}

        if self.item_id:
            if self.item.empresa_id != self.comprobante.empresa_id:
                errores["item"] = "El item no pertenece a la empresa."
            if not self.item.activo or not self.item.se_vende:
                errores["item"] = "El item no esta habilitado para venta."

        if (
            self.tratamiento_iva == Item.TratamientoIVA.GRAVADO
            and self.alicuota_iva_id is None
        ):
            errores["alicuota_iva"] = "Una linea gravada requiere alicuota."
        if (
            self.tratamiento_iva != Item.TratamientoIVA.GRAVADO
            and self.alicuota_iva_id is not None
        ):
            errores["alicuota_iva"] = (
                "Una linea exenta o no gravada no debe informar alicuota."
            )

        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        self._normalizar_campos()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.comprobante} - linea {self.numero_linea}"


class ComprobanteVentaIVA(models.Model):
    comprobante = models.ForeignKey(
        ComprobanteVenta,
        on_delete=models.CASCADE,
        related_name="totales_iva",
    )
    alicuota_iva = models.ForeignKey(
        AlicuotaIVA,
        on_delete=models.PROTECT,
        related_name="totales_iva_venta",
    )
    base_imponible = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    importe_iva = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    class Meta:
        db_table = "ventas_comprobanteventaiva"
        verbose_name = "IVA de comprobante de venta"
        verbose_name_plural = "IVA de comprobantes de venta"
        ordering = ["comprobante_id", "alicuota_iva__porcentaje"]
        constraints = [
            models.UniqueConstraint(
                fields=["comprobante", "alicuota_iva"],
                name="uniq_cvi_comprobante_alicuota",
            )
        ]


class ComprobanteVentaTributo(models.Model):
    comprobante = models.ForeignKey(
        ComprobanteVenta,
        on_delete=models.CASCADE,
        related_name="tributos",
    )
    codigo = models.CharField(max_length=40)
    nombre = models.CharField(max_length=160)
    base_imponible = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    porcentaje = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.0000"))],
    )
    importe = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    class Meta:
        db_table = "ventas_comprobanteventatributo"
        verbose_name = "tributo de comprobante de venta"
        verbose_name_plural = "tributos de comprobante de venta"
        ordering = ["comprobante_id", "codigo", "id"]

    def _normalizar_campos(self):
        self.codigo = self.codigo.strip().upper()
        self.nombre = self.nombre.strip()

    def clean(self):
        super().clean()
        self._normalizar_campos()

    def save(self, *args, **kwargs):
        self._normalizar_campos()
        super().save(*args, **kwargs)


class ComprobanteVentaAsociado(models.Model):
    class TipoAsociacion(models.TextChoices):
        AJUSTE = "AJUSTE", "Ajuste"
        REFERENCIA = "REFERENCIA", "Referencia"

    comprobante = models.ForeignKey(
        ComprobanteVenta,
        on_delete=models.CASCADE,
        related_name="asociaciones",
    )
    comprobante_asociado = models.ForeignKey(
        ComprobanteVenta,
        on_delete=models.PROTECT,
        related_name="comprobantes_que_lo_asocian",
    )
    tipo = models.CharField(
        max_length=20,
        choices=TipoAsociacion.choices,
        default=TipoAsociacion.AJUSTE,
    )
    observaciones = models.TextField(blank=True)

    class Meta:
        db_table = "ventas_comprobanteventaasociado"
        verbose_name = "comprobante de venta asociado"
        verbose_name_plural = "comprobantes de venta asociados"
        ordering = ["comprobante_id", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["comprobante", "comprobante_asociado"],
                name="uniq_cva_comprobante_asociado",
            ),
            models.CheckConstraint(
                condition=~Q(comprobante=F("comprobante_asociado")),
                name="chk_cva_no_autoasociado",
            ),
        ]

    def clean(self):
        super().clean()
        errores = {}
        if self.comprobante_id == self.comprobante_asociado_id:
            errores["comprobante_asociado"] = (
                "Un comprobante no puede asociarse a si mismo."
            )
        if (
            self.comprobante_id
            and self.comprobante_asociado_id
            and self.comprobante.empresa_id
            != self.comprobante_asociado.empresa_id
        ):
            errores["comprobante_asociado"] = (
                "El comprobante asociado debe pertenecer a la misma empresa."
            )
        if errores:
            raise ValidationError(errores)
