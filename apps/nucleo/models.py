import json
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
    RegexValidator,
)
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


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


class PerfilFiscalEmpresa(models.Model):
    class NaturalezaContribuyente(models.TextChoices):
        PERSONA_HUMANA = "PERSONA_HUMANA", "Persona humana"
        PERSONA_JURIDICA = "PERSONA_JURIDICA", "Persona jurídica"
        SUCESION_INDIVISA = "SUCESION_INDIVISA", "Sucesión indivisa"
        OTRA = "OTRA", "Otra"

    MESES_CIERRE = (
        (1, "Enero"),
        (2, "Febrero"),
        (3, "Marzo"),
        (4, "Abril"),
        (5, "Mayo"),
        (6, "Junio"),
        (7, "Julio"),
        (8, "Agosto"),
        (9, "Septiembre"),
        (10, "Octubre"),
        (11, "Noviembre"),
        (12, "Diciembre"),
    )

    empresa = models.OneToOneField(
        Empresa,
        on_delete=models.PROTECT,
        related_name="perfil_fiscal",
    )
    naturaleza = models.CharField(
        max_length=30,
        choices=NaturalezaContribuyente.choices,
        blank=True,
        default="",
    )
    fecha_inicio_actividades = models.DateField(
        null=True,
        blank=True,
    )
    mes_cierre_ejercicio_predeterminado = models.PositiveSmallIntegerField(
        choices=MESES_CIERRE,
        null=True,
        blank=True,
    )
    apellido = models.CharField(max_length=120, blank=True)
    apellido_materno = models.CharField(max_length=120, blank=True)
    nombres = models.CharField(max_length=160, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "nucleo_perfilfiscalempresa"
        verbose_name = "perfil fiscal de empresa"
        verbose_name_plural = "perfiles fiscales de empresa"
        ordering = ["empresa__razon_social"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(mes_cierre_ejercicio_predeterminado__isnull=True)
                    | Q(
                        mes_cierre_ejercicio_predeterminado__gte=1,
                        mes_cierre_ejercicio_predeterminado__lte=12,
                    )
                ),
                name="chk_perfil_fiscal_mes_cierre",
            )
        ]

    def clean(self):
        super().clean()

        naturaleza_personal = {
            self.NaturalezaContribuyente.PERSONA_HUMANA,
            self.NaturalezaContribuyente.SUCESION_INDIVISA,
        }

        if self.naturaleza in naturaleza_personal:
            errores = {}

            if not self.apellido.strip():
                errores["apellido"] = (
                    "El apellido es obligatorio para esta naturaleza."
                )

            if not self.nombres.strip():
                errores["nombres"] = (
                    "Los nombres son obligatorios para esta naturaleza."
                )

            if errores:
                raise ValidationError(errores)

        elif self.naturaleza:
            campos_personales = (
                self.apellido,
                self.apellido_materno,
                self.nombres,
                self.fecha_nacimiento,
            )

            if any(campos_personales):
                raise ValidationError(
                    "Los datos personales corresponden únicamente a "
                    "personas humanas o sucesiones indivisas."
                )

    @property
    def esta_completo(self):
        basicos = (
            bool(self.naturaleza)
            and self.fecha_inicio_actividades is not None
            and self.mes_cierre_ejercicio_predeterminado is not None
        )

        if not basicos:
            return False

        if self.naturaleza in {
            self.NaturalezaContribuyente.PERSONA_HUMANA,
            self.NaturalezaContribuyente.SUCESION_INDIVISA,
        }:
            return bool(
                self.apellido.strip()
                and self.nombres.strip()
                and self.fecha_nacimiento
            )

        return True

    def __str__(self):
        return f"Perfil fiscal de {self.empresa}"


class ActividadEconomica(models.Model):
    class Nomenclador(models.TextChoices):
        ARCA_CLAE = "ARCA_CLAE", "ARCA - CLAE F. 883"

    nomenclador = models.CharField(
        max_length=30,
        choices=Nomenclador.choices,
        default=Nomenclador.ARCA_CLAE,
    )
    codigo = models.CharField(
        max_length=6,
        validators=[
            RegexValidator(
                regex=r"^\d{6}$",
                message=(
                    "El codigo de actividad debe contener "
                    "exactamente 6 digitos."
                ),
            )
        ],
    )
    descripcion = models.TextField()
    activa = models.BooleanField(default=True)
    fuente_url = models.URLField(max_length=500, blank=True)
    fuente_sha256 = models.CharField(max_length=64, blank=True)
    primera_importacion_en = models.DateTimeField(auto_now_add=True)
    ultima_sincronizacion_en = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "nucleo_actividadeconomica"
        verbose_name = "actividad economica"
        verbose_name_plural = "actividades economicas"
        ordering = ["nomenclador", "codigo"]
        constraints = [
            models.UniqueConstraint(
                fields=["nomenclador", "codigo"],
                name="uniq_actividad_nomenclador_codigo",
            )
        ]
        indexes = [
            models.Index(
                fields=["nomenclador", "activa", "codigo"],
                name="idx_actividad_nom_act_cod",
            )
        ]

    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"


class ImportacionCatalogoActividad(models.Model):
    nomenclador = models.CharField(
        max_length=30,
        choices=ActividadEconomica.Nomenclador.choices,
        default=ActividadEconomica.Nomenclador.ARCA_CLAE,
    )
    fuente_url = models.URLField(max_length=500)
    archivo_nombre = models.CharField(max_length=255)
    sha256 = models.CharField(max_length=64, db_index=True)
    total_registros = models.PositiveIntegerField()
    creados = models.PositiveIntegerField(default=0)
    actualizados = models.PositiveIntegerField(default=0)
    reactivados = models.PositiveIntegerField(default=0)
    desactivados = models.PositiveIntegerField(default=0)
    importada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "nucleo_importacioncatalogoactividad"
        verbose_name = "importacion de catalogo de actividades"
        verbose_name_plural = "importaciones de catalogos de actividades"
        ordering = ["-importada_en", "-id"]

    def __str__(self):
        return (
            f"{self.get_nomenclador_display()} - "
            f"{self.importada_en:%Y-%m-%d %H:%M:%S}"
        )


class EmpresaActividad(models.Model):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="actividades_economicas",
    )
    actividad = models.ForeignKey(
        ActividadEconomica,
        on_delete=models.PROTECT,
        related_name="asignaciones_empresa",
    )
    principal = models.BooleanField(default=False)
    activa = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0)
    vigencia_desde = models.DateField(null=True, blank=True)
    vigencia_hasta = models.DateField(null=True, blank=True)
    observaciones = models.TextField(blank=True)
    nomenclador_registrado = models.CharField(
        max_length=30,
        blank=True,
        default="",
        editable=False,
    )
    codigo_registrado = models.CharField(
        max_length=6,
        blank=True,
        default="",
        editable=False,
    )
    descripcion_registrada = models.TextField(
        blank=True,
        default="",
        editable=False,
    )
    fuente_sha256_registrada = models.CharField(
        max_length=64,
        blank=True,
        default="",
        editable=False,
    )
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "nucleo_empresaactividad"
        verbose_name = "actividad económica de empresa"
        verbose_name_plural = "actividades económicas de empresa"
        ordering = [
            "empresa__razon_social",
            "-activa",
            "-principal",
            "orden",
            "codigo_registrado",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "actividad"],
                condition=Q(activa=True),
                name="uniq_emp_actividad_activa",
            ),
            models.UniqueConstraint(
                fields=["empresa"],
                condition=Q(
                    activa=True,
                    principal=True,
                ),
                name="uniq_emp_actividad_principal",
            ),
            models.CheckConstraint(
                condition=Q(principal=False) | Q(activa=True),
                name="chk_emp_act_principal_activa",
            ),
            models.CheckConstraint(
                condition=(
                    Q(vigencia_hasta__isnull=True)
                    | (
                        Q(vigencia_desde__isnull=False)
                        & Q(vigencia_hasta__gte=F("vigencia_desde"))
                    )
                ),
                name="chk_emp_act_vigencia",
            ),
        ]
        indexes = [
            models.Index(
                fields=[
                    "empresa",
                    "activa",
                    "principal",
                    "orden",
                ],
                name="idx_emp_act_estado",
            )
        ]

    CAMPOS_INSTANTANEA = (
        "nomenclador_registrado",
        "codigo_registrado",
        "descripcion_registrada",
        "fuente_sha256_registrada",
    )

    def _capturar_instantanea(self):
        if not self.actividad_id:
            return

        actividad = ActividadEconomica.objects.only(
            "nomenclador",
            "codigo",
            "descripcion",
            "fuente_sha256",
        ).get(pk=self.actividad_id)

        self.nomenclador_registrado = actividad.nomenclador
        self.codigo_registrado = actividad.codigo
        self.descripcion_registrada = actividad.descripcion
        self.fuente_sha256_registrada = actividad.fuente_sha256

    def clean(self):
        super().clean()

        errores = {}

        if self.principal and not self.activa:
            errores["principal"] = (
                "Una actividad principal debe permanecer activa."
            )

        if self.vigencia_hasta is not None:
            if self.vigencia_desde is None:
                errores["vigencia_desde"] = (
                    "Informá la vigencia desde cuando existe "
                    "una vigencia hasta."
                )
            elif self.vigencia_hasta < self.vigencia_desde:
                errores["vigencia_hasta"] = (
                    "La vigencia hasta no puede ser anterior "
                    "a la vigencia desde."
                )

        original = None

        if self.pk:
            original = (
                type(self)
                .objects.filter(pk=self.pk)
                .values(
                    "empresa_id",
                    "actividad_id",
                    *self.CAMPOS_INSTANTANEA,
                )
                .first()
            )

        if original is not None:
            if original["empresa_id"] != self.empresa_id:
                errores["empresa"] = (
                    "La empresa de una relación existente no puede cambiar."
                )

            if original["actividad_id"] != self.actividad_id:
                errores["actividad"] = (
                    "La actividad de una relación existente no puede cambiar."
                )

            for campo in self.CAMPOS_INSTANTANEA:
                if original[campo] != getattr(self, campo):
                    errores[campo] = (
                        "La instantánea histórica no puede modificarse."
                    )
        elif self.actividad_id and self.activa:
            actividad_activa = ActividadEconomica.objects.filter(
                pk=self.actividad_id,
                activa=True,
            ).exists()

            if not actividad_activa:
                errores["actividad"] = (
                    "Solo se pueden asignar actividades activas "
                    "del catálogo oficial."
                )

        if self.empresa_id and self.actividad_id and self.activa:
            duplicada = type(self).objects.filter(
                empresa_id=self.empresa_id,
                actividad_id=self.actividad_id,
                activa=True,
            )

            if self.pk:
                duplicada = duplicada.exclude(pk=self.pk)

            if duplicada.exists():
                errores["actividad"] = (
                    "La empresa ya tiene esta actividad activa."
                )

        if self.empresa_id and self.activa and self.principal:
            principal_existente = type(self).objects.filter(
                empresa_id=self.empresa_id,
                activa=True,
                principal=True,
            )

            if self.pk:
                principal_existente = principal_existente.exclude(pk=self.pk)

            if principal_existente.exists():
                errores["principal"] = (
                    "La empresa ya tiene otra actividad principal activa."
                )

        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        if not self.pk and self.actividad_id:
            self._capturar_instantanea()

        super().save(*args, **kwargs)

    def __str__(self):
        tipo = "Principal" if self.principal else "Secundaria"
        estado = "activa" if self.activa else "inactiva"
        return (
            f"{self.empresa} - {self.codigo_registrado} "
            f"({tipo}, {estado})"
        )


class JurisdiccionFiscal(models.Model):
    codigo = models.CharField(
        max_length=3,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^9\d{2}$",
                message="El código COMARB debe contener tres dígitos.",
            )
        ],
    )
    nombre = models.CharField(max_length=120)
    activa = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0)
    fuente_url = models.URLField(max_length=500, blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "nucleo_jurisdiccionfiscal"
        verbose_name = "jurisdicción fiscal"
        verbose_name_plural = "jurisdicciones fiscales"
        ordering = ["orden", "codigo"]
        indexes = [
            models.Index(
                fields=["activa", "orden", "codigo"],
                name="idx_jur_fiscal_act_ord",
            )
        ]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class ConfiguracionIIBBEmpresa(models.Model):
    class Regimen(models.TextChoices):
        NO_INSCRIPTO = "NO_INSCRIPTO", "No inscripto"
        LOCAL = "LOCAL", "Contribuyente local"
        CONVENIO_MULTILATERAL = (
            "CONVENIO_MULTILATERAL",
            "Convenio Multilateral",
        )

    class TratamientoGeneral(models.TextChoices):
        GRAVADO = "GRAVADO", "Gravado"
        EXENTO = "EXENTO", "Exento"
        NO_ALCANZADO = "NO_ALCANZADO", "No alcanzado"
        MIXTO = "MIXTO", "Mixto"

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="configuraciones_iibb",
    )
    regimen = models.CharField(
        max_length=30,
        choices=Regimen.choices,
    )
    tratamiento_general = models.CharField(
        max_length=20,
        choices=TratamientoGeneral.choices,
        default=TratamientoGeneral.GRAVADO,
    )
    numero_inscripcion = models.CharField(max_length=50, blank=True)
    fecha_alta = models.DateField(null=True, blank=True)
    fecha_baja = models.DateField(null=True, blank=True)
    activa = models.BooleanField(default=True)
    observaciones = models.TextField(blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "nucleo_configuracionesiibbempresa"
        verbose_name = "configuración de Ingresos Brutos"
        verbose_name_plural = "configuraciones de Ingresos Brutos"
        ordering = ["empresa__razon_social", "-activa", "-creada_en"]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa"],
                condition=Q(activa=True),
                name="uniq_emp_config_iibb_activa",
            ),
            models.CheckConstraint(
                condition=(
                    Q(fecha_baja__isnull=True)
                    | (
                        Q(fecha_alta__isnull=False)
                        & Q(fecha_baja__gte=F("fecha_alta"))
                    )
                ),
                name="chk_config_iibb_fechas",
            ),
            models.CheckConstraint(
                condition=Q(activa=False) | Q(fecha_baja__isnull=True),
                name="chk_config_iibb_activa_sin_baja",
            ),
        ]
        indexes = [
            models.Index(
                fields=["empresa", "activa", "regimen"],
                name="idx_config_iibb_emp_est",
            )
        ]

    def clean(self):
        super().clean()
        self.numero_inscripcion = self.numero_inscripcion.strip()
        self.observaciones = self.observaciones.strip()
        errores = {}

        if self.fecha_baja is not None:
            if self.fecha_alta is None:
                errores["fecha_alta"] = (
                    "Informá la fecha de alta cuando existe fecha de baja."
                )
            elif self.fecha_baja < self.fecha_alta:
                errores["fecha_baja"] = (
                    "La fecha de baja no puede ser anterior a la fecha de alta."
                )

        if self.activa and self.fecha_baja is not None:
            errores["fecha_baja"] = (
                "Una configuración activa no puede tener fecha de baja."
            )

        if self.regimen == self.Regimen.NO_INSCRIPTO:
            if self.numero_inscripcion:
                errores["numero_inscripcion"] = (
                    "Una empresa no inscripta no debe tener número de inscripción."
                )
            if self.fecha_alta is not None:
                errores["fecha_alta"] = (
                    "Una empresa no inscripta no debe tener fecha de alta."
                )
        elif self.activa:
            if not self.numero_inscripcion:
                errores["numero_inscripcion"] = (
                    "El número de inscripción es obligatorio."
                )
            if self.fecha_alta is None:
                errores["fecha_alta"] = "La fecha de alta es obligatoria."

        original = None
        if self.pk:
            original = (
                type(self)
                .objects.filter(pk=self.pk)
                .values("empresa_id")
                .first()
            )

        if original and original["empresa_id"] != self.empresa_id:
            errores["empresa"] = (
                "La empresa de una configuración existente no puede cambiar."
            )

        if self.empresa_id and self.activa:
            duplicada = type(self).objects.filter(
                empresa_id=self.empresa_id,
                activa=True,
            )
            if self.pk:
                duplicada = duplicada.exclude(pk=self.pk)
            if duplicada.exists():
                errores["empresa"] = (
                    "La empresa ya tiene una configuración de IIBB activa."
                )

        if self.pk and self.activa:
            activas = self.jurisdicciones.filter(activa=True)
            if self.regimen == self.Regimen.NO_INSCRIPTO and activas.exists():
                errores["regimen"] = (
                    "Inactivá las jurisdicciones antes de marcar no inscripto."
                )
            if self.regimen == self.Regimen.LOCAL and activas.count() > 1:
                errores["regimen"] = (
                    "El régimen local admite una sola jurisdicción activa."
                )

        if errores:
            raise ValidationError(errores)

    @property
    def esta_completa(self):
        if not self.activa:
            return False

        activas = self.jurisdicciones.filter(activa=True)
        sedes = activas.filter(sede=True).count()

        if self.regimen == self.Regimen.NO_INSCRIPTO:
            return not activas.exists()

        if not self.numero_inscripcion or self.fecha_alta is None:
            return False

        if self.regimen == self.Regimen.LOCAL:
            return activas.count() == 1 and sedes == 1

        return activas.exists() and sedes == 1

    def __str__(self):
        return f"{self.empresa} - {self.get_regimen_display()}"


class EmpresaJurisdiccionIIBB(models.Model):
    class Tratamiento(models.TextChoices):
        SEGUN_CONFIGURACION = (
            "SEGUN_CONFIGURACION",
            "Según configuración general",
        )
        GRAVADO = "GRAVADO", "Gravado"
        EXENTO = "EXENTO", "Exento"
        NO_ALCANZADO = "NO_ALCANZADO", "No alcanzado"
        MIXTO = "MIXTO", "Mixto"

    configuracion = models.ForeignKey(
        ConfiguracionIIBBEmpresa,
        on_delete=models.PROTECT,
        related_name="jurisdicciones",
    )
    jurisdiccion = models.ForeignKey(
        JurisdiccionFiscal,
        on_delete=models.PROTECT,
        related_name="inscripciones_empresa",
    )
    numero_inscripcion = models.CharField(max_length=50, blank=True)
    sede = models.BooleanField(default=False)
    tratamiento = models.CharField(
        max_length=25,
        choices=Tratamiento.choices,
        default=Tratamiento.SEGUN_CONFIGURACION,
    )
    fecha_alta = models.DateField(null=True, blank=True)
    fecha_baja = models.DateField(null=True, blank=True)
    activa = models.BooleanField(default=True)
    observaciones = models.TextField(blank=True)
    codigo_registrado = models.CharField(
        max_length=3,
        blank=True,
        default="",
        editable=False,
    )
    nombre_registrado = models.CharField(
        max_length=120,
        blank=True,
        default="",
        editable=False,
    )
    fuente_url_registrada = models.URLField(
        max_length=500,
        blank=True,
        default="",
        editable=False,
    )
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    CAMPOS_INSTANTANEA = (
        "codigo_registrado",
        "nombre_registrado",
        "fuente_url_registrada",
    )

    class Meta:
        db_table = "nucleo_empresajurisdicioniibb"
        verbose_name = "jurisdicción de Ingresos Brutos"
        verbose_name_plural = "jurisdicciones de Ingresos Brutos"
        ordering = [
            "configuracion__empresa__razon_social",
            "-activa",
            "-sede",
            "jurisdiccion__orden",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["configuracion", "jurisdiccion"],
                condition=Q(activa=True),
                name="uniq_config_jur_iibb_activa",
            ),
            models.UniqueConstraint(
                fields=["configuracion"],
                condition=Q(activa=True, sede=True),
                name="uniq_config_jur_iibb_sede",
            ),
            models.CheckConstraint(
                condition=Q(sede=False) | Q(activa=True),
                name="chk_jur_iibb_sede_activa",
            ),
            models.CheckConstraint(
                condition=(
                    Q(fecha_baja__isnull=True)
                    | (
                        Q(fecha_alta__isnull=False)
                        & Q(fecha_baja__gte=F("fecha_alta"))
                    )
                ),
                name="chk_jur_iibb_fechas",
            ),
            models.CheckConstraint(
                condition=Q(activa=False) | Q(fecha_baja__isnull=True),
                name="chk_jur_iibb_activa_sin_baja",
            ),
        ]
        indexes = [
            models.Index(
                fields=["configuracion", "activa", "sede"],
                name="idx_jur_iibb_config_est",
            )
        ]

    def _capturar_instantanea(self):
        if not self.jurisdiccion_id:
            return
        jurisdiccion = JurisdiccionFiscal.objects.only(
            "codigo",
            "nombre",
            "fuente_url",
        ).get(pk=self.jurisdiccion_id)
        self.codigo_registrado = jurisdiccion.codigo
        self.nombre_registrado = jurisdiccion.nombre
        self.fuente_url_registrada = jurisdiccion.fuente_url

    def clean(self):
        super().clean()
        self.numero_inscripcion = self.numero_inscripcion.strip()
        self.observaciones = self.observaciones.strip()
        errores = {}

        if self.sede and not self.activa:
            errores["sede"] = "Una jurisdicción sede debe estar activa."

        if self.fecha_baja is not None:
            if self.fecha_alta is None:
                errores["fecha_alta"] = (
                    "Informá la fecha de alta cuando existe fecha de baja."
                )
            elif self.fecha_baja < self.fecha_alta:
                errores["fecha_baja"] = (
                    "La fecha de baja no puede ser anterior a la fecha de alta."
                )

        if self.activa and self.fecha_baja is not None:
            errores["fecha_baja"] = (
                "Una jurisdicción activa no puede tener fecha de baja."
            )

        if self.activa and self.fecha_alta is None:
            errores["fecha_alta"] = (
                "La fecha de alta jurisdiccional es obligatoria."
            )

        original = None
        if self.pk:
            original = (
                type(self)
                .objects.filter(pk=self.pk)
                .values(
                    "configuracion_id",
                    "jurisdiccion_id",
                    *self.CAMPOS_INSTANTANEA,
                )
                .first()
            )

        if original:
            if original["configuracion_id"] != self.configuracion_id:
                errores["configuracion"] = (
                    "La configuración de una relación existente no puede cambiar."
                )
            if original["jurisdiccion_id"] != self.jurisdiccion_id:
                errores["jurisdiccion"] = (
                    "La jurisdicción de una relación existente no puede cambiar."
                )
            for campo in self.CAMPOS_INSTANTANEA:
                if original[campo] != getattr(self, campo):
                    errores[campo] = (
                        "La instantánea histórica no puede modificarse."
                    )
        elif self.jurisdiccion_id and self.activa:
            if not JurisdiccionFiscal.objects.filter(
                pk=self.jurisdiccion_id,
                activa=True,
            ).exists():
                errores["jurisdiccion"] = (
                    "Solo se pueden asignar jurisdicciones activas."
                )

        if self.configuracion_id and self.activa:
            if not self.configuracion.activa:
                errores["configuracion"] = (
                    "La configuración de IIBB no está activa."
                )
            if (
                self.configuracion.regimen
                == ConfiguracionIIBBEmpresa.Regimen.NO_INSCRIPTO
            ):
                errores["configuracion"] = (
                    "Una empresa no inscripta no admite jurisdicciones activas."
                )

            duplicada = type(self).objects.filter(
                configuracion_id=self.configuracion_id,
                jurisdiccion_id=self.jurisdiccion_id,
                activa=True,
            )
            if self.pk:
                duplicada = duplicada.exclude(pk=self.pk)
            if duplicada.exists():
                errores["jurisdiccion"] = (
                    "La jurisdicción ya está activa en esta configuración."
                )

            if (
                self.configuracion.regimen
                == ConfiguracionIIBBEmpresa.Regimen.LOCAL
            ):
                otra = type(self).objects.filter(
                    configuracion_id=self.configuracion_id,
                    activa=True,
                )
                if self.pk:
                    otra = otra.exclude(pk=self.pk)
                if otra.exists():
                    errores["jurisdiccion"] = (
                        "El régimen local admite una sola jurisdicción activa."
                    )

            if self.sede:
                sede_existente = type(self).objects.filter(
                    configuracion_id=self.configuracion_id,
                    activa=True,
                    sede=True,
                )
                if self.pk:
                    sede_existente = sede_existente.exclude(pk=self.pk)
                if sede_existente.exists():
                    errores["sede"] = (
                        "La configuración ya tiene otra jurisdicción sede."
                    )

        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        if not self.pk and self.jurisdiccion_id:
            self._capturar_instantanea()
        super().save(*args, **kwargs)

    def __str__(self):
        sede = " - Sede" if self.sede else ""
        return (
            f"{self.configuracion.empresa} - "
            f"{self.codigo_registrado} {self.nombre_registrado}{sede}"
        )

class Sucursal(models.Model):
    FUNCIONES_EXCLUSIVAS = (
        ("es_casa_central", "Casa central"),
        (
            "es_domicilio_fiscal_nacional",
            "Domicilio fiscal nacional",
        ),
        (
            "es_domicilio_fiscal_provincial",
            "Domicilio fiscal provincial",
        ),
        ("es_domicilio_legal", "Domicilio legal"),
        (
            "es_principal_actividades",
            "Principal lugar de actividades",
        ),
    )

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="sucursales",
    )
    codigo = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r"^[A-Z0-9_-]+$",
                message=(
                    "El código debe usar mayúsculas, números, "
                    "guion o guion bajo."
                ),
            )
        ],
    )
    nombre = models.CharField(max_length=120)
    domicilio = models.CharField(
        max_length=255,
        blank=True,
        help_text=(
            "Dirección anterior conservada durante la transición "
            "al domicilio estructurado."
        ),
    )
    calle = models.CharField(max_length=160, blank=True)
    numero = models.CharField(max_length=30, blank=True)
    sector = models.CharField(max_length=80, blank=True)
    torre = models.CharField(max_length=50, blank=True)
    piso = models.CharField(max_length=30, blank=True)
    departamento = models.CharField(max_length=30, blank=True)
    barrio = models.CharField(max_length=120, blank=True)
    localidad = models.CharField(max_length=120, blank=True)
    codigo_postal = models.CharField(max_length=20, blank=True)
    partido_departamento = models.CharField(max_length=120, blank=True)
    provincia = models.CharField(max_length=120, default="Santa Fe")
    pais = models.CharField(max_length=120, default="Argentina")
    es_casa_central = models.BooleanField(default=False)
    es_domicilio_fiscal_nacional = models.BooleanField(default=False)
    es_domicilio_fiscal_provincial = models.BooleanField(default=False)
    es_domicilio_legal = models.BooleanField(default=False)
    es_principal_actividades = models.BooleanField(default=False)
    es_deposito = models.BooleanField(default=False)
    es_local_comercial = models.BooleanField(default=False)
    es_oficina_administrativa = models.BooleanField(default=False)
    otras_funciones = models.CharField(max_length=255, blank=True)
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
            ),
            models.UniqueConstraint(
                fields=["empresa"],
                condition=Q(
                    activa=True,
                    es_casa_central=True,
                ),
                name="uniq_suc_emp_casa_central",
            ),
            models.UniqueConstraint(
                fields=["empresa"],
                condition=Q(
                    activa=True,
                    es_domicilio_fiscal_nacional=True,
                ),
                name="uniq_suc_emp_fiscal_nac",
            ),
            models.UniqueConstraint(
                fields=["empresa"],
                condition=Q(
                    activa=True,
                    es_domicilio_fiscal_provincial=True,
                ),
                name="uniq_suc_emp_fiscal_prov",
            ),
            models.UniqueConstraint(
                fields=["empresa"],
                condition=Q(
                    activa=True,
                    es_domicilio_legal=True,
                ),
                name="uniq_suc_emp_legal",
            ),
            models.UniqueConstraint(
                fields=["empresa"],
                condition=Q(
                    activa=True,
                    es_principal_actividades=True,
                ),
                name="uniq_suc_emp_principal_act",
            ),
        ]

    def clean(self):
        super().clean()

        self.codigo = self.codigo.strip().upper()
        errores = {}

        if self.empresa_id and self.activa:
            for campo, etiqueta in self.FUNCIONES_EXCLUSIVAS:
                if not getattr(self, campo):
                    continue

                duplicada = Sucursal.objects.filter(
                    empresa_id=self.empresa_id,
                    activa=True,
                    **{campo: True},
                )

                if self.pk:
                    duplicada = duplicada.exclude(pk=self.pk)

                if duplicada.exists():
                    errores[campo] = (
                        f"Ya existe otra sucursal activa marcada como "
                        f"{etiqueta.lower()}."
                    )

        if (
            self.pk
            and not self.activa
            and self.puntos_venta.filter(activo=True).exists()
        ):
            errores["activa"] = (
                "Inactivá o reasigná los puntos de venta activos "
                "antes de inactivar la sucursal."
            )

        if errores:
            raise ValidationError(errores)

    @property
    def domicilio_estructurado_completo(self):
        return all(
            (
                self.calle.strip(),
                self.numero.strip(),
                self.localidad.strip(),
                self.codigo_postal.strip(),
                self.provincia.strip(),
                self.pais.strip(),
            )
        )

    @property
    def domicilio_formateado(self):
        linea_principal = " ".join(
            parte
            for parte in (
                self.calle.strip(),
                self.numero.strip(),
            )
            if parte
        )

        if not linea_principal:
            linea_principal = self.domicilio.strip()

        complementos = []

        for etiqueta, valor in (
            ("Sector", self.sector),
            ("Torre", self.torre),
            ("Piso", self.piso),
            ("Depto.", self.departamento),
        ):
            valor = valor.strip()
            if valor:
                complementos.append(f"{etiqueta} {valor}")

        if self.barrio.strip():
            complementos.append(self.barrio.strip())

        ubicacion = [
            valor.strip()
            for valor in (
                self.localidad,
                self.partido_departamento,
                self.provincia,
                self.codigo_postal,
                self.pais,
            )
            if valor.strip()
        ]

        bloques = []

        if linea_principal:
            bloques.append(linea_principal)
        if complementos:
            bloques.append(", ".join(complementos))
        if ubicacion:
            bloques.append(", ".join(ubicacion))

        return " · ".join(bloques) or "Sin domicilio informado"

    @property
    def funciones(self):
        funciones = []

        for campo, etiqueta in self.FUNCIONES_EXCLUSIVAS:
            if getattr(self, campo):
                funciones.append(etiqueta)

        for campo, etiqueta in (
            ("es_deposito", "Depósito"),
            ("es_local_comercial", "Local comercial"),
            (
                "es_oficina_administrativa",
                "Oficina administrativa",
            ),
        ):
            if getattr(self, campo):
                funciones.append(etiqueta)

        if self.otras_funciones.strip():
            funciones.append(self.otras_funciones.strip())

        return funciones

    def __str__(self):
        return f"{self.empresa} - {self.nombre}"


class PuntoVenta(models.Model):
    class SistemaEmision(models.TextChoices):
        WEB_SERVICE = (
            "WEB_SERVICE",
            "Factura electrónica - Web Services",
        )
        COMPROBANTES_EN_LINEA = (
            "COMPROBANTES_EN_LINEA",
            "Comprobantes en línea",
        )
        CONTROLADOR_FISCAL = (
            "CONTROLADOR_FISCAL",
            "Controlador fiscal",
        )
        FACTURADOR = (
            "FACTURADOR",
            "Facturador",
        )
        MANUAL = (
            "MANUAL",
            "Comprobantes manuales",
        )
        OTRO = (
            "OTRO",
            "Otro sistema",
        )

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="puntos_venta",
    )
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.PROTECT,
        related_name="puntos_venta",
    )
    numero = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(99998),
        ],
    )
    nombre_fantasia = models.CharField(max_length=200, blank=True)
    sistema_emision = models.CharField(
        max_length=30,
        choices=SistemaEmision.choices,
    )
    descripcion_sistema_arca = models.CharField(
        max_length=200,
        blank=True,
        help_text=(
            "Descripción exacta observada en ARCA, cuando sea necesario "
            "conservarla."
        ),
    )
    actividad_predeterminada = models.ForeignKey(
        EmpresaActividad,
        on_delete=models.PROTECT,
        related_name="puntos_venta_predeterminados",
        null=True,
        blank=True,
    )
    jurisdiccion_iibb_predeterminada = models.ForeignKey(
        EmpresaJurisdiccionIIBB,
        on_delete=models.PROTECT,
        related_name="puntos_venta_predeterminados",
        null=True,
        blank=True,
    )
    predeterminado = models.BooleanField(default=False)
    bloqueado = models.BooleanField(default=False)
    fecha_alta = models.DateField(null=True, blank=True)
    fecha_baja = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    observaciones = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "nucleo_puntoventa"
        verbose_name = "punto de venta"
        verbose_name_plural = "puntos de venta"
        ordering = [
            "empresa__razon_social",
            "-activo",
            "sucursal__codigo",
            "numero",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "numero"],
                name="uniq_pv_empresa_numero",
            ),
            models.UniqueConstraint(
                fields=["sucursal"],
                condition=Q(
                    activo=True,
                    predeterminado=True,
                ),
                name="uniq_pv_suc_default_activo",
            ),
            models.CheckConstraint(
                condition=Q(
                    numero__gte=1,
                    numero__lte=99998,
                ),
                name="chk_pv_numero_rango",
            ),
            models.CheckConstraint(
                condition=(
                    Q(fecha_baja__isnull=True)
                    | Q(fecha_alta__isnull=True)
                    | Q(fecha_baja__gte=F("fecha_alta"))
                ),
                name="chk_pv_fechas",
            ),
            models.CheckConstraint(
                condition=Q(activo=False) | Q(fecha_baja__isnull=True),
                name="chk_pv_activo_sin_baja",
            ),
            models.CheckConstraint(
                condition=Q(predeterminado=False) | Q(activo=True),
                name="chk_pv_default_activo",
            ),
        ]
        indexes = [
            models.Index(
                fields=["empresa", "activo", "numero"],
                name="idx_pv_emp_act_num",
            ),
            models.Index(
                fields=["sucursal", "activo", "predeterminado"],
                name="idx_pv_suc_act_def",
            ),
        ]

    def clean(self):
        super().clean()

        self.nombre_fantasia = self.nombre_fantasia.strip()
        self.descripcion_sistema_arca = (
            self.descripcion_sistema_arca.strip()
        )
        self.observaciones = self.observaciones.strip()
        errores = {}

        if (
            self.numero is not None
            and not 1 <= self.numero <= 99998
        ):
            errores["numero"] = (
                "El punto de venta debe estar comprendido entre 1 y 99998."
            )

        if self.sucursal_id:
            if self.sucursal.empresa_id != self.empresa_id:
                errores["sucursal"] = (
                    "La sucursal no pertenece a la empresa del punto de venta."
                )
            elif self.activo and not self.sucursal.activa:
                errores["sucursal"] = (
                    "Un punto de venta activo requiere una sucursal activa."
                )

        if self.actividad_predeterminada_id:
            actividad = self.actividad_predeterminada

            if actividad.empresa_id != self.empresa_id:
                errores["actividad_predeterminada"] = (
                    "La actividad predeterminada no pertenece a la empresa."
                )
            elif self.activo and not actividad.activa:
                errores["actividad_predeterminada"] = (
                    "La actividad predeterminada debe estar activa."
                )

        if self.jurisdiccion_iibb_predeterminada_id:
            relacion = self.jurisdiccion_iibb_predeterminada

            if relacion.configuracion.empresa_id != self.empresa_id:
                errores["jurisdiccion_iibb_predeterminada"] = (
                    "La jurisdicción de IIBB no pertenece a la empresa."
                )
            elif self.activo and (
                not relacion.activa
                or not relacion.configuracion.activa
            ):
                errores["jurisdiccion_iibb_predeterminada"] = (
                    "La jurisdicción predeterminada debe estar activa."
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
                "Un punto de venta activo no puede tener fecha de baja."
            )

        if self.predeterminado and not self.activo:
            errores["predeterminado"] = (
                "Un punto de venta inactivo no puede ser predeterminado."
            )

        original = None

        if self.pk:
            original = (
                type(self)
                .objects.filter(pk=self.pk)
                .values(
                    "empresa_id",
                    "numero",
                )
                .first()
            )

        if original:
            if original["empresa_id"] != self.empresa_id:
                errores["empresa"] = (
                    "La empresa de un punto de venta existente no puede cambiar."
                )
            if original["numero"] != self.numero:
                errores["numero"] = (
                    "El número de un punto de venta existente no puede cambiar."
                )

        if self.empresa_id:
            duplicado = type(self).objects.filter(
                empresa_id=self.empresa_id,
                numero=self.numero,
            )

            if self.pk:
                duplicado = duplicado.exclude(pk=self.pk)

            if duplicado.exists():
                errores["numero"] = (
                    "Este número de punto de venta ya fue utilizado por la "
                    "empresa y no puede reutilizarse."
                )

        if self.sucursal_id and self.activo and self.predeterminado:
            otro_predeterminado = type(self).objects.filter(
                sucursal_id=self.sucursal_id,
                activo=True,
                predeterminado=True,
            )

            if self.pk:
                otro_predeterminado = otro_predeterminado.exclude(pk=self.pk)

            if otro_predeterminado.exists():
                errores["predeterminado"] = (
                    "La sucursal ya tiene otro punto de venta predeterminado."
                )

        if errores:
            raise ValidationError(errores)

    @property
    def numero_formateado(self):
        return f"{self.numero:05d}"

    def __str__(self):
        return (
            f"{self.empresa} - {self.numero_formateado} - "
            f"{self.sucursal.nombre}"
        )


class EjercicioFiscal(models.Model):
    class Estado(models.TextChoices):
        ABIERTO = "ABIERTO", "Abierto"
        CERRADO = "CERRADO", "Cerrado"
        BLOQUEADO = "BLOQUEADO", "Bloqueado"

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="ejercicios_fiscales",
    )
    codigo = models.CharField(max_length=20)
    nombre = models.CharField(max_length=120)
    fecha_inicio = models.DateField()
    fecha_cierre = models.DateField()
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.ABIERTO,
    )
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "ejercicio fiscal"
        verbose_name_plural = "ejercicios fiscales"
        ordering = ["empresa__razon_social", "-fecha_inicio"]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "codigo"],
                name="uniq_ejercicio_empresa_codigo",
            ),
            models.CheckConstraint(
                condition=Q(fecha_cierre__gte=F("fecha_inicio")),
                name="chk_ejercicio_fecha_cierre_gte_inicio",
            ),
        ]

    def clean(self):
        super().clean()

        if (
            self.fecha_inicio
            and self.fecha_cierre
            and self.fecha_cierre < self.fecha_inicio
        ):
            raise ValidationError(
                {
                    "fecha_cierre": (
                        "La fecha de cierre no puede ser anterior "
                        "a la fecha de inicio."
                    )
                }
            )

    def __str__(self):
        return f"{self.empresa} - {self.codigo}"


class PeriodoContable(models.Model):
    class Estado(models.TextChoices):
        ABIERTO = "ABIERTO", "Abierto"
        CERRADO = "CERRADO", "Cerrado"
        BLOQUEADO = "BLOQUEADO", "Bloqueado"

    ejercicio = models.ForeignKey(
        EjercicioFiscal,
        on_delete=models.PROTECT,
        related_name="periodos",
    )
    codigo = models.CharField(max_length=20)
    nombre = models.CharField(max_length=120)
    fecha_inicio = models.DateField()
    fecha_cierre = models.DateField()
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.ABIERTO,
    )
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "periodo contable"
        verbose_name_plural = "periodos contables"
        ordering = [
            "ejercicio__empresa__razon_social",
            "ejercicio__fecha_inicio",
            "fecha_inicio",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["ejercicio", "codigo"],
                name="uniq_periodo_ejercicio_codigo",
            ),
            models.CheckConstraint(
                condition=Q(fecha_cierre__gte=F("fecha_inicio")),
                name="chk_periodo_fecha_cierre_gte_inicio",
            ),
        ]

    @property
    def empresa(self):
        return self.ejercicio.empresa

    def clean(self):
        super().clean()

        if (
            self.fecha_inicio
            and self.fecha_cierre
            and self.fecha_cierre < self.fecha_inicio
        ):
            raise ValidationError(
                {
                    "fecha_cierre": (
                        "La fecha de cierre no puede ser anterior "
                        "a la fecha de inicio."
                    )
                }
            )

        try:
            ejercicio = self.ejercicio
        except EjercicioFiscal.DoesNotExist:
            return

        if not ejercicio or not self.fecha_inicio or not self.fecha_cierre:
            return

        if self.fecha_inicio < ejercicio.fecha_inicio:
            raise ValidationError(
                {
                    "fecha_inicio": (
                        "La fecha de inicio del periodo no puede ser anterior "
                        "al inicio del ejercicio fiscal."
                    )
                }
            )

        if self.fecha_cierre > ejercicio.fecha_cierre:
            raise ValidationError(
                {
                    "fecha_cierre": (
                        "La fecha de cierre del periodo no puede ser posterior "
                        "al cierre del ejercicio fiscal."
                    )
                }
            )

    def __str__(self):
        return f"{self.ejercicio} - {self.codigo}"



class ParametroSistema(models.Model):
    class Ambito(models.TextChoices):
        GLOBAL = "GLOBAL", "Global"
        EMPRESA = "EMPRESA", "Empresa"

    class TipoValor(models.TextChoices):
        TEXTO = "TEXTO", "Texto"
        ENTERO = "ENTERO", "Entero"
        DECIMAL = "DECIMAL", "Decimal"
        BOOLEANO = "BOOLEANO", "Booleano"
        JSON = "JSON", "JSON"

    ambito = models.CharField(
        max_length=20,
        choices=Ambito.choices,
        default=Ambito.EMPRESA,
    )
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="parametros_sistema",
        null=True,
        blank=True,
    )
    clave = models.CharField(
        max_length=100,
        db_index=True,
        validators=[
            RegexValidator(
                regex=r"^[a-z0-9_.-]+$",
                message=(
                    "La clave debe usar minúsculas, números, punto, "
                    "guion o guion bajo."
                ),
            )
        ],
    )
    valor = models.TextField(blank=True)
    tipo_valor = models.CharField(
        max_length=20,
        choices=TipoValor.choices,
        default=TipoValor.TEXTO,
    )
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "parámetro del sistema"
        verbose_name_plural = "parámetros del sistema"
        ordering = ["ambito", "empresa__razon_social", "clave"]
        constraints = [
            models.UniqueConstraint(
                fields=["clave"],
                condition=Q(empresa__isnull=True),
                name="uniq_parametro_global_clave",
            ),
            models.UniqueConstraint(
                fields=["empresa", "clave"],
                condition=Q(empresa__isnull=False),
                name="uniq_parametro_empresa_clave",
            ),
            models.CheckConstraint(
                condition=(
                    Q(ambito="GLOBAL", empresa__isnull=True)
                    | Q(ambito="EMPRESA", empresa__isnull=False)
                ),
                name="chk_parametro_ambito_empresa",
            ),
        ]

    def _normalizar_clave(self):
        if self.clave:
            self.clave = self.clave.strip().lower()

    def clean_fields(self, exclude=None):
        self._normalizar_clave()
        super().clean_fields(exclude=exclude)

    def clean(self):
        super().clean()

        self._normalizar_clave()

        if self.ambito == self.Ambito.GLOBAL and self.empresa_id:
            raise ValidationError(
                {"empresa": "Un parámetro global no debe tener empresa."}
            )

        if self.ambito == self.Ambito.EMPRESA and not self.empresa_id:
            raise ValidationError(
                {"empresa": "Un parámetro por empresa debe tener empresa."}
            )

        self._validar_valor_segun_tipo()

    def _validar_valor_segun_tipo(self):
        if self.valor == "":
            return

        if self.tipo_valor == self.TipoValor.ENTERO:
            try:
                int(self.valor)
            except ValueError as exc:
                raise ValidationError(
                    {"valor": "El valor debe ser un número entero."}
                ) from exc

        if self.tipo_valor == self.TipoValor.DECIMAL:
            try:
                Decimal(self.valor.replace(",", "."))
            except (InvalidOperation, AttributeError) as exc:
                raise ValidationError(
                    {"valor": "El valor debe ser un número decimal válido."}
                ) from exc

        if self.tipo_valor == self.TipoValor.BOOLEANO:
            valores_validos = {
                "1",
                "0",
                "true",
                "false",
                "si",
                "sí",
                "no",
                "s",
                "n",
            }
            if self.valor.strip().lower() not in valores_validos:
                raise ValidationError(
                    {
                        "valor": (
                            "El valor booleano debe ser true/false, "
                            "1/0 o sí/no."
                        )
                    }
                )

        if self.tipo_valor == self.TipoValor.JSON:
            try:
                json.loads(self.valor)
            except json.JSONDecodeError as exc:
                raise ValidationError(
                    {"valor": "El valor debe contener JSON válido."}
                ) from exc

    def save(self, *args, **kwargs):
        self._normalizar_clave()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.empresa_id:
            return f"{self.empresa} - {self.clave}"
        return f"GLOBAL - {self.clave}"


class Auditoria(models.Model):
    class Accion(models.TextChoices):
        INSERT = "INSERT", "Insertar"
        UPDATE = "UPDATE", "Actualizar"
        DELETE = "DELETE", "Eliminar"
        LOGIN = "LOGIN", "Login"
        LOGOUT = "LOGOUT", "Logout"
        ANULAR = "ANULAR", "Anular"
        CONFIRMAR = "CONFIRMAR", "Confirmar"
        CERRAR_PERIODO = "CERRAR_PERIODO", "Cerrar periodo"
        ABRIR_PERIODO = "ABRIR_PERIODO", "Abrir periodo"

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="auditorias",
        null=True,
        blank=True,
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="auditorias",
        null=True,
        blank=True,
    )
    accion = models.CharField(
        max_length=30,
        choices=Accion.choices,
        db_index=True,
    )
    tabla = models.CharField(max_length=120, db_index=True)
    registro_id = models.CharField(max_length=80, blank=True)
    datos_anteriores = models.JSONField(null=True, blank=True)
    datos_nuevos = models.JSONField(null=True, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "nucleo_auditoria"
        verbose_name = "auditoría"
        verbose_name_plural = "auditoría"
        ordering = ["-creado_en"]
        indexes = [
            models.Index(
                fields=["empresa", "-creado_en"],
                name="idx_auditoria_empresa_fecha",
            ),
            models.Index(
                fields=["accion", "-creado_en"],
                name="idx_auditoria_accion_fecha",
            ),
            models.Index(
                fields=["tabla", "registro_id"],
                name="idx_auditoria_tabla_registro",
            ),
        ]

    def __str__(self):
        registro = f" #{self.registro_id}" if self.registro_id else ""
        return f"{self.accion} {self.tabla}{registro}"


class EventoNegocio(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        PROCESADO = "PROCESADO", "Procesado"
        ERROR = "ERROR", "Error"
        IGNORADO = "IGNORADO", "Ignorado"

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="eventos_negocio",
        null=True,
        blank=True,
    )
    tipo_evento = models.CharField(
        max_length=80,
        db_index=True,
        validators=[
            RegexValidator(
                regex=r"^[A-Z0-9_]+$",
                message=(
                    "El tipo de evento debe usar mayúsculas, números "
                    "y guion bajo."
                ),
            )
        ],
    )
    entidad_tipo = models.CharField(max_length=120, db_index=True)
    entidad_id = models.CharField(max_length=80, blank=True)
    fecha_evento = models.DateTimeField(default=timezone.now, db_index=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="eventos_negocio",
        null=True,
        blank=True,
    )
    payload_json = models.JSONField(default=dict, blank=True)
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
        db_index=True,
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "nucleo_eventonegocio"
        verbose_name = "evento de negocio"
        verbose_name_plural = "eventos de negocio"
        ordering = ["-fecha_evento", "-creado_en"]
        indexes = [
            models.Index(
                fields=["empresa", "-fecha_evento"],
                name="idx_evento_empresa_fecha",
            ),
            models.Index(
                fields=["tipo_evento", "-fecha_evento"],
                name="idx_evento_tipo_fecha",
            ),
            models.Index(
                fields=["entidad_tipo", "entidad_id"],
                name="idx_evento_entidad",
            ),
        ]

    def _normalizar_tipo_evento(self):
        if self.tipo_evento:
            self.tipo_evento = self.tipo_evento.strip().upper()

    def clean_fields(self, exclude=None):
        self._normalizar_tipo_evento()
        super().clean_fields(exclude=exclude)

    def clean(self):
        super().clean()
        self._normalizar_tipo_evento()

    def save(self, *args, **kwargs):
        self._normalizar_tipo_evento()
        super().save(*args, **kwargs)

    def __str__(self):
        registro = f" #{self.entidad_id}" if self.entidad_id else ""
        return f"{self.tipo_evento} {self.entidad_tipo}{registro}"


class DocumentoAdjunto(models.Model):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="documentos_adjuntos",
    )
    entidad_tipo = models.CharField(max_length=120, db_index=True)
    entidad_id = models.CharField(max_length=80, db_index=True)
    nombre_original = models.CharField(max_length=255)
    nombre_archivo = models.CharField(max_length=255)
    tipo_mime = models.CharField(max_length=120)
    ruta = models.CharField(
        max_length=500,
        help_text="Ruta relativa dentro del almacenamiento local media/.",
    )
    tamanio_bytes = models.PositiveBigIntegerField()
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="documentos_adjuntos",
        null=True,
        blank=True,
    )
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "nucleo_documentoadjunto"
        verbose_name = "documento adjunto"
        verbose_name_plural = "documentos adjuntos"
        ordering = ["-creado_en"]
        indexes = [
            models.Index(
                fields=["empresa", "-creado_en"],
                name="idx_documento_empresa_fecha",
            ),
            models.Index(
                fields=["entidad_tipo", "entidad_id"],
                name="idx_documento_entidad",
            ),
            models.Index(
                fields=["activo", "-creado_en"],
                name="idx_documento_activo_fecha",
            ),
        ]

    def _normalizar_textos(self):
        for campo in (
            "entidad_tipo",
            "entidad_id",
            "nombre_original",
            "nombre_archivo",
            "tipo_mime",
            "ruta",
        ):
            valor = getattr(self, campo, None)
            if isinstance(valor, str):
                setattr(self, campo, valor.strip())

    def clean_fields(self, exclude=None):
        self._normalizar_textos()
        super().clean_fields(exclude=exclude)

    def clean(self):
        super().clean()
        self._normalizar_textos()

        if self.tamanio_bytes is not None and self.tamanio_bytes <= 0:
            raise ValidationError(
                {"tamanio_bytes": "El tamaño del documento debe ser mayor a cero."}
            )

    def save(self, *args, **kwargs):
        self._normalizar_textos()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre_original} ({self.entidad_tipo} #{self.entidad_id})"


class RolFuncional(models.Model):
    codigo = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        validators=[
            RegexValidator(
                regex=r"^[A-Z0-9_]+$",
                message=(
                    "El código del rol debe usar mayúsculas, números "
                    "y guion bajo."
                ),
            )
        ],
    )
    nombre = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    sistema = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "nucleo_rolfuncional"
        verbose_name = "rol funcional"
        verbose_name_plural = "roles funcionales"
        ordering = ["codigo"]

    def _normalizar_codigo(self):
        if self.codigo:
            self.codigo = self.codigo.strip().upper()

    def clean_fields(self, exclude=None):
        self._normalizar_codigo()
        super().clean_fields(exclude=exclude)

    def clean(self):
        super().clean()
        self._normalizar_codigo()

    def save(self, *args, **kwargs):
        self._normalizar_codigo()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.codigo


class PermisoFuncional(models.Model):
    codigo = models.CharField(
        max_length=120,
        unique=True,
        db_index=True,
        validators=[
            RegexValidator(
                regex=r"^[a-z0-9_]+\.[a-z0-9_]+$",
                message=(
                    "El código del permiso debe usar el formato "
                    "modulo.accion en minúsculas."
                ),
            )
        ],
    )
    modulo = models.CharField(
        max_length=60,
        db_index=True,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^[a-z0-9_]+$",
                message="El módulo debe usar minúsculas, números y guion bajo.",
            )
        ],
    )
    accion = models.CharField(
        max_length=60,
        db_index=True,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^[a-z0-9_]+$",
                message="La acción debe usar minúsculas, números y guion bajo.",
            )
        ],
    )
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "nucleo_permisofuncional"
        verbose_name = "permiso funcional"
        verbose_name_plural = "permisos funcionales"
        ordering = ["modulo", "accion", "codigo"]

    def _normalizar_codigo_modulo_accion(self):
        if self.codigo:
            self.codigo = self.codigo.strip().lower()

        if self.modulo:
            self.modulo = self.modulo.strip().lower()

        if self.accion:
            self.accion = self.accion.strip().lower()

        if self.codigo and "." in self.codigo:
            modulo, accion = self.codigo.split(".", 1)
            if not self.modulo:
                self.modulo = modulo
            if not self.accion:
                self.accion = accion

        if self.modulo and self.accion and not self.codigo:
            self.codigo = f"{self.modulo}.{self.accion}"

    def clean_fields(self, exclude=None):
        self._normalizar_codigo_modulo_accion()
        super().clean_fields(exclude=exclude)

    def clean(self):
        super().clean()
        self._normalizar_codigo_modulo_accion()

        if self.modulo and self.accion:
            codigo_esperado = f"{self.modulo}.{self.accion}"
            if self.codigo != codigo_esperado:
                raise ValidationError(
                    {"codigo": f"El código debe ser {codigo_esperado}."}
                )

    def save(self, *args, **kwargs):
        self._normalizar_codigo_modulo_accion()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.codigo


class RolPermiso(models.Model):
    rol = models.ForeignKey(
        RolFuncional,
        on_delete=models.PROTECT,
        related_name="permisos_asignados",
    )
    permiso = models.ForeignKey(
        PermisoFuncional,
        on_delete=models.PROTECT,
        related_name="roles_asignados",
    )
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "nucleo_rolpermiso"
        verbose_name = "permiso por rol"
        verbose_name_plural = "permisos por rol"
        ordering = ["rol__codigo", "permiso__codigo"]
        constraints = [
            models.UniqueConstraint(
                fields=["rol", "permiso"],
                name="uniq_rol_permiso",
            )
        ]

    def clean(self):
        super().clean()

        try:
            rol = self.rol
            permiso = self.permiso
        except (RolFuncional.DoesNotExist, PermisoFuncional.DoesNotExist):
            return

        if rol and not rol.activo:
            raise ValidationError({"rol": "No se puede asignar un rol inactivo."})

        if permiso and not permiso.activo:
            raise ValidationError(
                {"permiso": "No se puede asignar un permiso inactivo."}
            )

    def __str__(self):
        return f"{self.rol.codigo} -> {self.permiso.codigo}"


class UsuarioRolEmpresa(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="roles_empresas",
    )
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="usuarios_roles",
    )
    rol = models.ForeignKey(
        RolFuncional,
        on_delete=models.PROTECT,
        related_name="usuarios_empresa",
    )
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "nucleo_usuariorolempresa"
        verbose_name = "rol de usuario por empresa"
        verbose_name_plural = "roles de usuario por empresa"
        ordering = ["usuario__username", "empresa__razon_social", "rol__codigo"]
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "empresa", "rol"],
                name="uniq_usuario_rol_empresa",
            )
        ]

    def clean(self):
        super().clean()

        try:
            usuario = self.usuario
            empresa = self.empresa
            rol = self.rol
        except (Empresa.DoesNotExist, RolFuncional.DoesNotExist):
            return

        if not usuario or not empresa or not rol:
            return

        if not rol.activo:
            raise ValidationError({"rol": "No se puede asignar un rol inactivo."})

        if usuario.is_superuser:
            return

        existe_acceso_empresa = UsuarioEmpresa.objects.filter(
            usuario=usuario,
            empresa=empresa,
            activo=True,
        ).exists()

        if not existe_acceso_empresa:
            raise ValidationError(
                {
                    "empresa": (
                        "El usuario debe tener acceso activo a la empresa "
                        "antes de recibir un rol funcional."
                    )
                }
            )

    def __str__(self):
        return f"{self.usuario} - {self.empresa} - {self.rol.codigo}"


class UsuarioEmpresa(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="empresas_asignadas",
    )
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="usuarios_asignados",
    )
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "usuario por empresa"
        verbose_name_plural = "usuarios por empresa"
        ordering = ["usuario__username", "empresa__razon_social"]
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "empresa"],
                name="uniq_usuario_empresa",
            )
        ]

    def __str__(self):
        return f"{self.usuario} - {self.empresa}"


class UsuarioSucursal(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sucursales_asignadas",
    )
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.PROTECT,
        related_name="usuarios_asignados",
    )
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "usuario por sucursal"
        verbose_name_plural = "usuarios por sucursal"
        ordering = [
            "usuario__username",
            "sucursal__empresa__razon_social",
            "sucursal__codigo",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "sucursal"],
                name="uniq_usuario_sucursal",
            )
        ]

    @property
    def empresa(self):
        return self.sucursal.empresa

    def clean(self):
        super().clean()

        try:
            usuario = self.usuario
            sucursal = self.sucursal
        except Sucursal.DoesNotExist:
            return

        if not usuario or not sucursal:
            return

        if usuario.is_superuser:
            return

        existe_acceso_empresa = UsuarioEmpresa.objects.filter(
            usuario=usuario,
            empresa=sucursal.empresa,
            activo=True,
        ).exists()

        if not existe_acceso_empresa:
            raise ValidationError(
                {
                    "sucursal": (
                        "El usuario debe tener acceso activo a la empresa "
                        "de la sucursal antes de ser asignado a la sucursal."
                    )
                }
            )

    def __str__(self):
        return f"{self.usuario} - {self.sucursal}"
