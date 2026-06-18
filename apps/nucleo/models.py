from django.core.validators import RegexValidator
from django.db import models


class Empresa(models.Model):
    class CondicionIVA(models.TextChoices):
        RESPONSABLE_INSCRIPTO = "RESPONSABLE_INSCRIPTO", "Responsable inscripto"
        MONOTRIBUTO = "MONOTRIBUTO", "Monotributo"
        EXENTO = "EXENTO", "Exento"
        CONSUMIDOR_FINAL = "CONSUMIDOR_FINAL", "Consumidor final"
        NO_CATEGORIZADO = "NO_CATEGORIZADO", "No categorizado"

    cuit = models.CharField(
        max_length=11,
        unique=True,
        db_index=True,
        validators=[
            RegexValidator(
                regex=r"^\d{11}$",
                message="El CUIT debe contener 11 dígitos sin guiones.",
            )
        ],
    )
    razon_social = models.CharField(max_length=200)
    nombre_fantasia = models.CharField(max_length=200, blank=True)
    condicion_iva = models.CharField(
        max_length=30,
        choices=CondicionIVA.choices,
        default=CondicionIVA.RESPONSABLE_INSCRIPTO,
    )
    activa = models.BooleanField(default=True)
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "empresa"
        verbose_name_plural = "empresas"
        ordering = ["razon_social"]

    def __str__(self):
        return self.razon_social


class Sucursal(models.Model):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="sucursales",
    )
    codigo = models.CharField(max_length=20)
    nombre = models.CharField(max_length=120)
    domicilio = models.CharField(max_length=255, blank=True)
    localidad = models.CharField(max_length=120, blank=True)
    provincia = models.CharField(max_length=120, default="Santa Fe")
    pais = models.CharField(max_length=120, default="Argentina")
    activa = models.BooleanField(default=True)
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "sucursal"
        verbose_name_plural = "sucursales"
        ordering = ["empresa__razon_social", "codigo"]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "codigo"],
                name="uniq_sucursal_empresa_codigo",
            )
        ]

    def __str__(self):
        return f"{self.empresa} - {self.nombre}"
