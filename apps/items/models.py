from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q

from apps.nucleo.models import Empresa


VALIDADOR_CODIGO = RegexValidator(
    regex=r"^[A-Z0-9_-]+$",
    message="El código debe usar mayúsculas, números, guion o guion bajo.",
)


class CatalogoEmpresaBase(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT)
    codigo = models.CharField(max_length=30, validators=[VALIDADOR_CODIGO])
    nombre = models.CharField(max_length=160)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def _normalizar_campos(self):
        self.codigo = self.codigo.strip().upper()
        self.nombre = self.nombre.strip()

    def clean_fields(self, exclude=None):
        self._normalizar_campos()
        super().clean_fields(exclude=exclude)

    def clean(self):
        super().clean()
        self._normalizar_campos()
        errores = {}

        if self.empresa_id and self.activo:
            if not Empresa.objects.filter(pk=self.empresa_id, activa=True).exists():
                errores["empresa"] = "Un catálogo activo requiere una empresa activa."

        original = None
        if self.pk:
            original = (
                type(self)
                .objects.filter(pk=self.pk)
                .values("empresa_id", "codigo")
                .first()
            )

        if original:
            if original["empresa_id"] != self.empresa_id:
                errores["empresa"] = "La empresa de un registro existente no puede cambiar."
            if original["codigo"] != self.codigo:
                errores["codigo"] = "El código de un registro existente no puede cambiar."

        if self.empresa_id and self.codigo:
            duplicado = type(self).objects.filter(
                empresa_id=self.empresa_id,
                codigo=self.codigo,
            )
            if self.pk:
                duplicado = duplicado.exclude(pk=self.pk)
            if duplicado.exists():
                errores["codigo"] = "Ya existe este código en la empresa."

        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        self._normalizar_campos()
        super().save(*args, **kwargs)


class CategoriaItem(CatalogoEmpresaBase):
    descripcion = models.TextField(blank=True)

    class Meta:
        db_table = "items_categoriaitem"
        verbose_name = "categoría de ítem"
        verbose_name_plural = "categorías de ítems"
        ordering = ["empresa__razon_social", "-activo", "nombre", "codigo"]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "codigo"],
                name="uniq_categoria_item_empresa_codigo",
            )
        ]
        indexes = [
            models.Index(
                fields=["empresa", "activo", "nombre"],
                name="idx_categoria_item_emp_act",
            )
        ]

    def _normalizar_campos(self):
        super()._normalizar_campos()
        self.descripcion = self.descripcion.strip()

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Marca(CatalogoEmpresaBase):
    class Meta:
        db_table = "items_marca"
        verbose_name = "marca"
        verbose_name_plural = "marcas"
        ordering = ["empresa__razon_social", "-activo", "nombre", "codigo"]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "codigo"],
                name="uniq_marca_empresa_codigo",
            )
        ]
        indexes = [
            models.Index(
                fields=["empresa", "activo", "nombre"],
                name="idx_marca_emp_act_nombre",
            )
        ]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class CatalogoGlobalBase(models.Model):
    codigo = models.CharField(max_length=30, unique=True, validators=[VALIDADOR_CODIGO])
    nombre = models.CharField(max_length=160)
    activo = models.BooleanField(default=True)
    sistema = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def _normalizar_campos(self):
        self.codigo = self.codigo.strip().upper()
        self.nombre = self.nombre.strip()

    def clean_fields(self, exclude=None):
        self._normalizar_campos()
        super().clean_fields(exclude=exclude)

    def clean(self):
        super().clean()
        self._normalizar_campos()
        errores = {}

        if self.pk:
            original = (
                type(self).objects.filter(pk=self.pk).values("codigo").first()
            )
            if original and original["codigo"] != self.codigo:
                errores["codigo"] = "El código de un catálogo existente no puede cambiar."

        duplicado = type(self).objects.filter(codigo=self.codigo)
        if self.pk:
            duplicado = duplicado.exclude(pk=self.pk)
        if self.codigo and duplicado.exists():
            errores["codigo"] = "Ya existe un catálogo con este código."

        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        self._normalizar_campos()
        super().save(*args, **kwargs)


class UnidadMedida(CatalogoGlobalBase):
    simbolo = models.CharField(max_length=20, blank=True)
    codigo_arca = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        unique=True,
    )

    class Meta:
        db_table = "items_unidadmedida"
        verbose_name = "unidad de medida"
        verbose_name_plural = "unidades de medida"
        ordering = ["nombre", "codigo"]

    def _normalizar_campos(self):
        super()._normalizar_campos()
        self.simbolo = self.simbolo.strip()

    def __str__(self):
        if self.simbolo:
            return f"{self.nombre} ({self.simbolo})"
        return self.nombre


class AlicuotaIVA(CatalogoGlobalBase):
    porcentaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.00")),
            MaxValueValidator(Decimal("100.00")),
        ],
    )
    codigo_arca = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        unique=True,
    )

    class Meta:
        db_table = "items_alicuotaiva"
        verbose_name = "alícuota de IVA"
        verbose_name_plural = "alícuotas de IVA"
        ordering = ["porcentaje", "nombre", "codigo"]

    def __str__(self):
        return f"{self.nombre} ({self.porcentaje} %)"


class Item(models.Model):
    class Tipo(models.TextChoices):
        PRODUCTO = "PRODUCTO", "Producto"
        SERVICIO = "SERVICIO", "Servicio"

    class TratamientoIVA(models.TextChoices):
        GRAVADO = "GRAVADO", "Gravado"
        EXENTO = "EXENTO", "Exento"
        NO_GRAVADO = "NO_GRAVADO", "No gravado"

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="items",
    )
    codigo = models.CharField(max_length=30, validators=[VALIDADOR_CODIGO])
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    categoria = models.ForeignKey(
        CategoriaItem,
        on_delete=models.PROTECT,
        related_name="items",
        null=True,
        blank=True,
    )
    marca = models.ForeignKey(
        Marca,
        on_delete=models.PROTECT,
        related_name="items",
        null=True,
        blank=True,
    )
    unidad_medida = models.ForeignKey(
        UnidadMedida,
        on_delete=models.PROTECT,
        related_name="items",
    )
    se_compra = models.BooleanField(default=False)
    se_vende = models.BooleanField(default=False)
    controla_stock = models.BooleanField(default=False)
    tratamiento_iva = models.CharField(
        max_length=20,
        choices=TratamientoIVA.choices,
        default=TratamientoIVA.GRAVADO,
    )
    alicuota_iva = models.ForeignKey(
        AlicuotaIVA,
        on_delete=models.PROTECT,
        related_name="items",
        null=True,
        blank=True,
    )
    activo = models.BooleanField(default=True)
    observaciones = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "items_item"
        verbose_name = "ítem"
        verbose_name_plural = "ítems"
        ordering = ["empresa__razon_social", "-activo", "nombre", "codigo"]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "codigo"],
                name="uniq_item_empresa_codigo",
            ),
            models.CheckConstraint(
                condition=Q(se_compra=True) | Q(se_vende=True),
                name="chk_item_capacidad_operativa",
            ),
            models.CheckConstraint(
                condition=Q(tipo="PRODUCTO") | Q(controla_stock=False),
                name="chk_item_servicio_sin_stock",
            ),
            models.CheckConstraint(
                condition=(
                    Q(tratamiento_iva="GRAVADO", alicuota_iva__isnull=False)
                    | (
                        ~Q(tratamiento_iva="GRAVADO")
                        & Q(alicuota_iva__isnull=True)
                    )
                ),
                name="chk_item_tratamiento_iva",
            ),
        ]
        indexes = [
            models.Index(
                fields=["empresa", "activo", "nombre"],
                name="idx_item_emp_act_nombre",
            ),
            models.Index(
                fields=["empresa", "tipo", "activo"],
                name="idx_item_emp_tipo_activo",
            ),
        ]

    def _normalizar_campos(self):
        self.codigo = self.codigo.strip().upper()
        self.nombre = self.nombre.strip()
        self.descripcion = self.descripcion.strip()
        self.observaciones = self.observaciones.strip()

    def clean_fields(self, exclude=None):
        self._normalizar_campos()
        super().clean_fields(exclude=exclude)

    def clean(self):
        super().clean()
        self._normalizar_campos()
        errores = {}

        if self.empresa_id and self.activo:
            if not Empresa.objects.filter(pk=self.empresa_id, activa=True).exists():
                errores["empresa"] = "Un ítem activo requiere una empresa activa."

        if not self.se_compra and not self.se_vende:
            errores["se_compra"] = "El ítem debe poder comprarse, venderse o ambas cosas."

        if self.tipo == self.Tipo.SERVICIO and self.controla_stock:
            errores["controla_stock"] = "Un servicio no puede controlar stock."

        if self.categoria_id:
            categoria = CategoriaItem.objects.filter(pk=self.categoria_id).first()
            if categoria is not None:
                if self.empresa_id and categoria.empresa_id != self.empresa_id:
                    errores["categoria"] = "La categoría debe pertenecer a la misma empresa."
                elif self.activo and not categoria.activo:
                    errores["categoria"] = "La categoría debe estar activa."

        if self.marca_id:
            marca = Marca.objects.filter(pk=self.marca_id).first()
            if marca is not None:
                if self.empresa_id and marca.empresa_id != self.empresa_id:
                    errores["marca"] = "La marca debe pertenecer a la misma empresa."
                elif self.activo and not marca.activo:
                    errores["marca"] = "La marca debe estar activa."

        if self.unidad_medida_id and self.activo:
            unidad_activa = UnidadMedida.objects.filter(
                pk=self.unidad_medida_id,
                activo=True,
            ).exists()
            if not unidad_activa:
                errores["unidad_medida"] = "La unidad de medida debe estar activa."

        if self.tratamiento_iva == self.TratamientoIVA.GRAVADO:
            if not self.alicuota_iva_id:
                errores["alicuota_iva"] = "Un ítem gravado requiere alícuota de IVA."
            elif self.activo and not AlicuotaIVA.objects.filter(
                pk=self.alicuota_iva_id,
                activo=True,
            ).exists():
                errores["alicuota_iva"] = "La alícuota de IVA debe estar activa."
        elif self.alicuota_iva_id:
            errores["alicuota_iva"] = (
                "Los ítems exentos o no gravados no deben informar alícuota de IVA."
            )

        original = None
        if self.pk:
            original = (
                type(self)
                .objects.filter(pk=self.pk)
                .values("empresa_id", "codigo")
                .first()
            )

        if original:
            if original["empresa_id"] != self.empresa_id:
                errores["empresa"] = "La empresa de un ítem existente no puede cambiar."
            if original["codigo"] != self.codigo:
                errores["codigo"] = "El código de un ítem existente no puede cambiar."

        if self.empresa_id and self.codigo:
            duplicado = type(self).objects.filter(
                empresa_id=self.empresa_id,
                codigo=self.codigo,
            )
            if self.pk:
                duplicado = duplicado.exclude(pk=self.pk)
            if duplicado.exists():
                errores["codigo"] = "Ya existe otro ítem con este código en la empresa."

        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        self._normalizar_campos()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
