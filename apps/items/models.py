from decimal import Decimal
import unicodedata

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower
from django.utils import timezone

from apps.terceros.models import Tercero, TerceroRol

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

def normalizar_codigo_proveedor(valor):
    texto = unicodedata.normalize("NFKC", str(valor or ""))
    if any(unicodedata.category(caracter).startswith("C") for caracter in texto):
        raise ValidationError(
            {"codigo_proveedor": "El código no admite caracteres de control."}
        )
    return " ".join(texto.strip().split()).upper()


class ItemProveedor(models.Model):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="relaciones_items_proveedores",
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        related_name="relaciones_proveedores",
    )
    proveedor = models.ForeignKey(
        Tercero,
        on_delete=models.PROTECT,
        related_name="relaciones_items_proveedor",
    )
    codigo_proveedor = models.CharField(max_length=80, blank=True)
    observaciones = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    fecha_alta = models.DateField(default=timezone.localdate)
    fecha_baja = models.DateField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "items_itemproveedor"
        verbose_name = "proveedor de ítem"
        verbose_name_plural = "proveedores de ítems"
        ordering = [
            "empresa__razon_social",
            "item__nombre",
            "-activo",
            "proveedor__denominacion",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "item", "proveedor"],
                name="uniq_itemprov_emp_item_prov",
            ),
            models.UniqueConstraint(
                F("empresa"),
                F("proveedor"),
                Lower("codigo_proveedor"),
                condition=~Q(codigo_proveedor=""),
                name="uniq_itemprov_emp_prov_cod_ci",
            ),
            models.CheckConstraint(
                condition=(
                    Q(fecha_baja__isnull=True)
                    | Q(fecha_baja__gte=F("fecha_alta"))
                ),
                name="chk_itemprov_fechas",
            ),
            models.CheckConstraint(
                condition=Q(activo=False) | Q(fecha_baja__isnull=True),
                name="chk_itemprov_activo_sin_baja",
            ),
        ]
        indexes = [
            models.Index(
                fields=["empresa", "item", "activo"],
                name="idx_itemprov_emp_item_act",
            ),
            models.Index(
                fields=["empresa", "proveedor", "activo"],
                name="idx_itemprov_emp_prov_act",
            ),
        ]

    def _normalizar_campos(self):
        self.codigo_proveedor = normalizar_codigo_proveedor(
            self.codigo_proveedor
        )
        self.observaciones = self.observaciones.strip()

    def clean_fields(self, exclude=None):
        self._normalizar_campos()
        super().clean_fields(exclude=exclude)

    def clean(self):
        super().clean()
        self._normalizar_campos()
        errores = {}

        item = (
            Item.objects.filter(pk=self.item_id).first()
            if self.item_id
            else None
        )
        proveedor = (
            Tercero.objects.filter(pk=self.proveedor_id).first()
            if self.proveedor_id
            else None
        )

        if self.empresa_id and item and item.empresa_id != self.empresa_id:
            errores["item"] = "El ítem debe pertenecer a la misma empresa."
        if (
            self.empresa_id
            and proveedor
            and proveedor.empresa_id != self.empresa_id
        ):
            errores["proveedor"] = (
                "El proveedor debe pertenecer a la misma empresa."
            )

        if (
            self.fecha_baja is not None
            and self.fecha_alta is not None
            and self.fecha_baja < self.fecha_alta
        ):
            errores["fecha_baja"] = (
                "La fecha de baja no puede ser anterior a la fecha de alta."
            )
        if self.activo and self.fecha_baja is not None:
            errores["fecha_baja"] = (
                "Una relación activa no puede tener fecha de baja."
            )

        original = None
        if self.pk:
            original = (
                type(self)
                .objects.filter(pk=self.pk)
                .values("empresa_id", "item_id", "proveedor_id")
                .first()
            )
        if original:
            if original["empresa_id"] != self.empresa_id:
                errores["empresa"] = (
                    "La empresa de una relación existente no puede cambiar."
                )
            if original["item_id"] != self.item_id:
                errores["item"] = (
                    "El ítem de una relación existente no puede cambiar."
                )
            if original["proveedor_id"] != self.proveedor_id:
                errores["proveedor"] = (
                    "El proveedor de una relación existente no puede cambiar."
                )

        if self.empresa_id and self.item_id and self.proveedor_id:
            duplicada = type(self).objects.filter(
                empresa_id=self.empresa_id,
                item_id=self.item_id,
                proveedor_id=self.proveedor_id,
            )
            if self.pk:
                duplicada = duplicada.exclude(pk=self.pk)
            if duplicada.exists():
                errores["proveedor"] = (
                    "El proveedor ya posee una relación histórica con el ítem."
                )

        if self.empresa_id and self.proveedor_id and self.codigo_proveedor:
            codigo_duplicado = type(self).objects.filter(
                empresa_id=self.empresa_id,
                proveedor_id=self.proveedor_id,
                codigo_proveedor__iexact=self.codigo_proveedor,
            )
            if self.pk:
                codigo_duplicado = codigo_duplicado.exclude(pk=self.pk)
            if codigo_duplicado.exists():
                errores["codigo_proveedor"] = (
                    "El proveedor ya utiliza este código para otro ítem."
                )

        if self.activo:
            if self.empresa_id and not Empresa.objects.filter(
                pk=self.empresa_id,
                activa=True,
            ).exists():
                errores["empresa"] = "La empresa debe estar activa."

            if item:
                if not item.activo:
                    errores["item"] = "El ítem debe estar activo."
                elif not item.se_compra:
                    errores["item"] = "El ítem debe estar habilitado para compra."

            if proveedor:
                if not proveedor.activo:
                    errores["proveedor"] = "El proveedor debe estar activo."
                elif not TerceroRol.objects.filter(
                    tercero=proveedor,
                    rol=TerceroRol.Rol.PROVEEDOR,
                    activo=True,
                ).exists():
                    errores["proveedor"] = (
                        "El tercero debe tener un rol PROVEEDOR activo."
                    )

        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        self._normalizar_campos()
        super().save(*args, **kwargs)

    def _roles_proveedor_activos(self):
        precargados = getattr(
            self.proveedor,
            "roles_proveedor_activos_precargados",
            None,
        )
        if precargados is not None:
            return list(precargados)
        return list(
            self.proveedor.roles.filter(
                rol=TerceroRol.Rol.PROVEEDOR,
                activo=True,
            ).select_related("grupo")
        )

    @property
    def grupo_proveedor(self):
        roles = self._roles_proveedor_activos()
        return roles[0].grupo if roles else None

    @property
    def disponible_operativamente(self):
        return self.motivo_indisponibilidad == ""

    @property
    def motivo_indisponibilidad(self):
        if not self.activo:
            return "Relación inactiva"
        if not self.empresa.activa:
            return "Empresa inactiva"
        if not self.item.activo:
            return "Ítem inactivo"
        if not self.item.se_compra:
            return "Ítem no habilitado para compra"
        if not self.proveedor.activo:
            return "Proveedor inactivo"
        if not self._roles_proveedor_activos():
            return "Rol PROVEEDOR inactivo"
        return ""

    def __str__(self):
        return f"{self.item} — {self.proveedor}"
