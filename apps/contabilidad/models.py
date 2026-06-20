from django.core.validators import RegexValidator
from django.db import models
from treebeard.al_tree import AL_Node

from apps.nucleo.models import Empresa

from .codigo_cuentas import (
    CODIGO_CUENTA_ESTRUCTURAL_REGEX,
    CODIGO_CUENTA_REGEX,
    codigo_padre_desde_codigo,
    nivel_desde_codigo,
)
from .validaciones import normalizar_campos, validar_cuenta


class CuentaContable(AL_Node):
    class TipoContable(models.TextChoices):
        ACTIVO = "ACTIVO", "Activo"
        PASIVO = "PASIVO", "Pasivo"
        PATRIMONIO_NETO = "PATRIMONIO_NETO", "Patrimonio Neto"
        RESULTADO_POSITIVO = "RESULTADO_POSITIVO", "Ingresos"
        RESULTADO_NEGATIVO = "RESULTADO_NEGATIVO", "Gastos y perdidas"
        ORDEN = "ORDEN", "Cuentas de orden"

    class Naturaleza(models.TextChoices):
        DEUDORA = "DEUDORA", "Deudora"
        ACREEDORA = "ACREEDORA", "Acreedora"

    CODIGOS_RAIZ_POR_TIPO = {
        TipoContable.ACTIVO: "1.0.00.00.000",
        TipoContable.PASIVO: "2.0.00.00.000",
        TipoContable.PATRIMONIO_NETO: "3.0.00.00.000",
        TipoContable.RESULTADO_POSITIVO: "4.0.00.00.000",
        TipoContable.RESULTADO_NEGATIVO: "5.0.00.00.000",
    }

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="cuentas_contables",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        related_name="cuentas_hijas",
        null=True,
        blank=True,
        db_index=True,
        db_column="cuenta_padre_id",
        verbose_name="Cuenta superior",
    )
    codigo = models.CharField(
        max_length=13,
        validators=[
            RegexValidator(
                regex=CODIGO_CUENTA_REGEX,
                message="El codigo debe respetar la mascara 9.9.99.99.999.",
            )
        ],
    )
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    tipo_contable = models.CharField(
        max_length=20,
        choices=TipoContable.choices,
    )
    naturaleza = models.CharField(
        max_length=10,
        choices=Naturaleza.choices,
        null=True,
        blank=True,
    )
    habilitada = models.BooleanField(default=True)
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    node_order_by = ["codigo"]

    class Meta:
        verbose_name = "cuenta contable"
        verbose_name_plural = "cuentas contables"
        ordering = ["empresa_id", "codigo"]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "codigo"],
                name="uniq_cuenta_empresa_codigo",
            ),
            models.UniqueConstraint(
                fields=["empresa", "tipo_contable"],
                condition=models.Q(parent__isnull=True),
                name="uniq_cuenta_raiz_empresa_tipo",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    codigo__regex=CODIGO_CUENTA_ESTRUCTURAL_REGEX
                ),
                name="chk_cuenta_codigo_estructura",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(codigo__endswith=".000", naturaleza__isnull=True)
                    | (
                        ~models.Q(codigo__endswith=".000")
                        & models.Q(naturaleza__isnull=False)
                        & models.Q(
                            naturaleza__in=[
                                "DEUDORA",
                                "ACREEDORA",
                            ]
                        )
                    )
                ),
                name="chk_cuenta_naturaleza_imputabilidad",
            ),
        ]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    @classmethod
    def nivel_desde_codigo(cls, codigo):
        return nivel_desde_codigo(codigo)

    @classmethod
    def codigo_padre_desde_codigo(cls, codigo):
        return codigo_padre_desde_codigo(codigo)

    @property
    def nivel(self):
        return self.nivel_desde_codigo(self.codigo)

    @property
    def imputable(self):
        return self.nivel == 5

    @property
    def es_raiz(self):
        return self.nivel == 1

    @property
    def codigo_padre_esperado(self):
        return self.codigo_padre_desde_codigo(self.codigo)

    def clean_fields(self, exclude=None):
        normalizar_campos(self)
        return super().clean_fields(exclude=exclude)

    def clean(self):
        super().clean()
        validar_cuenta(self)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
