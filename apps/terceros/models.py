import re

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from apps.nucleo.models import Empresa


DOCUMENTOS_NUMERICOS = {"CUIT", "CUIL", "CDI", "DNI", "LC", "LE"}


def normalizar_numero_documento(codigo_tipo, valor):
    codigo = str(codigo_tipo or "").strip().upper()
    texto = str(valor or "").strip()

    if codigo in DOCUMENTOS_NUMERICOS:
        return re.sub(r"\D", "", texto)

    return re.sub(r"\s+", " ", texto).upper()


def validar_cuit_cuil(valor):
    if not re.fullmatch(r"\d{11}", valor or ""):
        return False

    pesos = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)
    suma = sum(int(digito) * peso for digito, peso in zip(valor[:10], pesos))
    verificador = 11 - suma % 11

    if verificador == 11:
        verificador = 0
    elif verificador == 10:
        return False

    return verificador == int(valor[-1])


class TipoDocumento(models.Model):
    codigo = models.CharField(
        max_length=30,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^[A-Z0-9_]+$",
                message="El código debe usar mayúsculas, números y guion bajo.",
            )
        ],
    )
    nombre = models.CharField(max_length=120)
    codigo_arca = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        unique=True,
    )
    requiere_numero = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)
    sistema = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "terceros_tipodocumento"
        verbose_name = "tipo de documento"
        verbose_name_plural = "tipos de documento"
        ordering = ["codigo_arca", "nombre", "codigo"]

    def clean(self):
        super().clean()
        self.codigo = self.codigo.strip().upper()
        self.nombre = self.nombre.strip()

    def save(self, *args, **kwargs):
        self.codigo = self.codigo.strip().upper()
        self.nombre = self.nombre.strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class CondicionIVA(models.Model):
    codigo = models.CharField(
        max_length=40,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^[A-Z0-9_]+$",
                message="El código debe usar mayúsculas, números y guion bajo.",
            )
        ],
    )
    nombre = models.CharField(max_length=160)
    codigo_arca = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        unique=True,
    )
    activo = models.BooleanField(default=True)
    sistema = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "terceros_condicioniva"
        verbose_name = "condición frente al IVA"
        verbose_name_plural = "condiciones frente al IVA"
        ordering = ["codigo_arca", "nombre", "codigo"]

    def clean(self):
        super().clean()
        self.codigo = self.codigo.strip().upper()
        self.nombre = self.nombre.strip()

    def save(self, *args, **kwargs):
        self.codigo = self.codigo.strip().upper()
        self.nombre = self.nombre.strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class Tercero(models.Model):
    class TipoPersona(models.TextChoices):
        PERSONA_HUMANA = "PERSONA_HUMANA", "Persona humana"
        PERSONA_JURIDICA = "PERSONA_JURIDICA", "Persona jurídica"
        OTRA = "OTRA", "Otra"

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="terceros",
    )
    codigo = models.CharField(
        max_length=30,
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
    tipo_persona = models.CharField(
        max_length=30,
        choices=TipoPersona.choices,
    )
    tipo_documento = models.ForeignKey(
        TipoDocumento,
        on_delete=models.PROTECT,
        related_name="terceros",
    )
    numero_documento = models.CharField(max_length=30, blank=True)
    denominacion = models.CharField(max_length=200)
    nombre_fantasia = models.CharField(max_length=200, blank=True)
    condicion_iva = models.ForeignKey(
        CondicionIVA,
        on_delete=models.PROTECT,
        related_name="terceros",
    )
    telefono = models.CharField(max_length=60, blank=True)
    email = models.EmailField(max_length=180, blank=True)
    sitio_web = models.URLField(max_length=300, blank=True)
    observaciones = models.TextField(blank=True)
    fecha_alta = models.DateField(default=timezone.localdate)
    fecha_baja = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "terceros_tercero"
        verbose_name = "tercero"
        verbose_name_plural = "terceros"
        ordering = [
            "empresa__razon_social",
            "-activo",
            "denominacion",
            "codigo",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "codigo"],
                name="uniq_tercero_empresa_codigo",
            ),
            models.UniqueConstraint(
                fields=["empresa", "tipo_documento", "numero_documento"],
                condition=~Q(numero_documento=""),
                name="uniq_tercero_empresa_documento",
            ),
            models.CheckConstraint(
                condition=(
                    Q(fecha_baja__isnull=True)
                    | Q(fecha_baja__gte=F("fecha_alta"))
                ),
                name="chk_tercero_fechas",
            ),
            models.CheckConstraint(
                condition=Q(activo=False) | Q(fecha_baja__isnull=True),
                name="chk_tercero_activo_sin_baja",
            ),
        ]
        indexes = [
            models.Index(
                fields=["empresa", "activo", "denominacion"],
                name="idx_tercero_emp_act_den",
            ),
            models.Index(
                fields=["empresa", "tipo_documento", "numero_documento"],
                name="idx_tercero_emp_doc",
            ),
        ]

    def _normalizar_campos(self):
        self.codigo = self.codigo.strip().upper()
        self.denominacion = self.denominacion.strip()
        self.nombre_fantasia = self.nombre_fantasia.strip()
        self.telefono = self.telefono.strip()
        self.email = self.email.strip().lower()
        self.sitio_web = self.sitio_web.strip()
        self.observaciones = self.observaciones.strip()

    def clean_fields(self, exclude=None):
        self._normalizar_campos()
        super().clean_fields(exclude=exclude)

    def clean(self):
        super().clean()
        self._normalizar_campos()
        errores = {}

        if self.tipo_documento_id:
            tipo = self.tipo_documento
            self.numero_documento = normalizar_numero_documento(
                tipo.codigo,
                self.numero_documento,
            )

            if tipo.requiere_numero and not self.numero_documento:
                errores["numero_documento"] = (
                    "El tipo de documento seleccionado requiere número."
                )
            if not tipo.requiere_numero and self.numero_documento:
                errores["numero_documento"] = (
                    "Este tipo de documento no admite número."
                )
            if (
                tipo.codigo in {"CUIT", "CUIL"}
                and self.numero_documento
                and not validar_cuit_cuil(self.numero_documento)
            ):
                errores["numero_documento"] = (
                    f"El {tipo.codigo} informado no es válido."
                )
            if self.activo and not tipo.activo:
                errores["tipo_documento"] = (
                    "El tipo de documento debe estar activo."
                )

        if (
            self.condicion_iva_id
            and self.activo
            and not self.condicion_iva.activo
        ):
            errores["condicion_iva"] = (
                "La condición frente al IVA debe estar activa."
            )

        if self.empresa_id and self.activo and not self.empresa.activa:
            errores["empresa"] = (
                "Un tercero activo requiere una empresa activa."
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
                "Un tercero activo no puede tener fecha de baja."
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
                errores["empresa"] = (
                    "La empresa de un tercero existente no puede cambiar."
                )
            if original["codigo"] != self.codigo:
                errores["codigo"] = (
                    "El código de un tercero existente no puede cambiar."
                )

        if self.empresa_id and self.codigo:
            duplicado = type(self).objects.filter(
                empresa_id=self.empresa_id,
                codigo=self.codigo,
            )
            if self.pk:
                duplicado = duplicado.exclude(pk=self.pk)
            if duplicado.exists():
                errores["codigo"] = (
                    "Ya existe otro tercero con este código en la empresa."
                )

        if (
            self.empresa_id
            and self.tipo_documento_id
            and self.numero_documento
        ):
            duplicado = type(self).objects.filter(
                empresa_id=self.empresa_id,
                tipo_documento_id=self.tipo_documento_id,
                numero_documento=self.numero_documento,
            )
            if self.pk:
                duplicado = duplicado.exclude(pk=self.pk)
            if duplicado.exists():
                errores["numero_documento"] = (
                    "Ya existe otro tercero con este documento en la empresa."
                )

        if errores:
            raise ValidationError(errores)

    @property
    def identificacion(self):
        if self.numero_documento:
            return f"{self.tipo_documento.codigo} {self.numero_documento}"
        return self.tipo_documento.nombre

    @property
    def roles_activos(self):
        if hasattr(self, "roles_activos_precargados"):
            return self.roles_activos_precargados
        return list(self.roles.filter(activo=True).order_by("rol", "pk"))

    @property
    def es_cliente(self):
        return any(
            relacion.rol == TerceroRol.Rol.CLIENTE
            for relacion in self.roles_activos
        )

    @property
    def es_proveedor(self):
        return any(
            relacion.rol == TerceroRol.Rol.PROVEEDOR
            for relacion in self.roles_activos
        )

    def __str__(self):
        return f"{self.codigo} - {self.denominacion}"


class TerceroRol(models.Model):
    class Rol(models.TextChoices):
        CLIENTE = "CLIENTE", "Cliente"
        PROVEEDOR = "PROVEEDOR", "Proveedor"

    tercero = models.ForeignKey(
        Tercero,
        on_delete=models.PROTECT,
        related_name="roles",
    )
    rol = models.CharField(max_length=20, choices=Rol.choices)
    fecha_alta = models.DateField(default=timezone.localdate)
    fecha_baja = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "terceros_tercerorol"
        verbose_name = "rol de tercero"
        verbose_name_plural = "roles de terceros"
        ordering = [
            "tercero__empresa__razon_social",
            "tercero__denominacion",
            "-activo",
            "rol",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tercero", "rol"],
                condition=Q(activo=True),
                name="uniq_tercero_rol_activo",
            ),
            models.CheckConstraint(
                condition=(
                    Q(fecha_baja__isnull=True)
                    | Q(fecha_baja__gte=F("fecha_alta"))
                ),
                name="chk_tercero_rol_fechas",
            ),
            models.CheckConstraint(
                condition=Q(activo=False) | Q(fecha_baja__isnull=True),
                name="chk_tercero_rol_activo_sin_baja",
            ),
        ]

    def clean(self):
        super().clean()
        errores = {}

        if self.activo and self.fecha_baja is not None:
            errores["fecha_baja"] = (
                "Un rol activo no puede tener fecha de baja."
            )
        if (
            self.fecha_baja is not None
            and self.fecha_alta is not None
            and self.fecha_baja < self.fecha_alta
        ):
            errores["fecha_baja"] = (
                "La fecha de baja no puede ser anterior a la fecha de alta."
            )
        if self.tercero_id and self.activo and not self.tercero.activo:
            errores["tercero"] = (
                "No se puede activar un rol en un tercero inactivo."
            )

        original = None
        if self.pk:
            original = (
                type(self)
                .objects.filter(pk=self.pk)
                .values("tercero_id", "rol")
                .first()
            )

        if original:
            if original["tercero_id"] != self.tercero_id:
                errores["tercero"] = (
                    "El tercero de un rol existente no puede cambiar."
                )
            if original["rol"] != self.rol:
                errores["rol"] = (
                    "El tipo de rol existente no puede cambiar."
                )

        if self.tercero_id and self.rol and self.activo:
            duplicado = type(self).objects.filter(
                tercero_id=self.tercero_id,
                rol=self.rol,
                activo=True,
            )
            if self.pk:
                duplicado = duplicado.exclude(pk=self.pk)
            if duplicado.exists():
                errores["rol"] = "El tercero ya tiene este rol activo."

        if errores:
            raise ValidationError(errores)

    def __str__(self):
        return f"{self.tercero} - {self.get_rol_display()}"


class DomicilioTercero(models.Model):
    class Tipo(models.TextChoices):
        FISCAL = "FISCAL", "Fiscal"
        COMERCIAL = "COMERCIAL", "Comercial"
        ENTREGA = "ENTREGA", "Entrega"
        COBRANZA = "COBRANZA", "Cobranza"
        OTRO = "OTRO", "Otro"

    tercero = models.ForeignKey(
        Tercero,
        on_delete=models.PROTECT,
        related_name="domicilios",
    )
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    nombre = models.CharField(max_length=120, blank=True)
    calle = models.CharField(max_length=160)
    numero = models.CharField(max_length=30, blank=True)
    sector = models.CharField(max_length=80, blank=True)
    torre = models.CharField(max_length=50, blank=True)
    piso = models.CharField(max_length=30, blank=True)
    departamento = models.CharField(max_length=30, blank=True)
    barrio = models.CharField(max_length=120, blank=True)
    localidad = models.CharField(max_length=120)
    codigo_postal = models.CharField(max_length=20, blank=True)
    partido_departamento = models.CharField(max_length=120, blank=True)
    provincia = models.CharField(max_length=120, default="Santa Fe")
    pais = models.CharField(max_length=120, default="Argentina")
    principal = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    fecha_alta = models.DateField(default=timezone.localdate)
    fecha_baja = models.DateField(null=True, blank=True)
    observaciones = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "terceros_domiciliotercero"
        verbose_name = "domicilio de tercero"
        verbose_name_plural = "domicilios de terceros"
        ordering = [
            "tercero__denominacion",
            "-activo",
            "tipo",
            "-principal",
            "pk",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tercero", "tipo"],
                condition=Q(activo=True, principal=True),
                name="uniq_dom_tercero_tipo_principal",
            ),
            models.CheckConstraint(
                condition=Q(principal=False) | Q(activo=True),
                name="chk_dom_principal_activo",
            ),
            models.CheckConstraint(
                condition=(
                    Q(fecha_baja__isnull=True)
                    | Q(fecha_baja__gte=F("fecha_alta"))
                ),
                name="chk_dom_tercero_fechas",
            ),
            models.CheckConstraint(
                condition=Q(activo=False) | Q(fecha_baja__isnull=True),
                name="chk_dom_tercero_activo_sin_baja",
            ),
        ]
        indexes = [
            models.Index(
                fields=["tercero", "activo", "tipo"],
                name="idx_dom_tercero_act_tipo",
            )
        ]

    def clean(self):
        super().clean()

        for campo in (
            "nombre",
            "calle",
            "numero",
            "sector",
            "torre",
            "piso",
            "departamento",
            "barrio",
            "localidad",
            "codigo_postal",
            "partido_departamento",
            "provincia",
            "pais",
            "observaciones",
        ):
            setattr(self, campo, getattr(self, campo).strip())

        errores = {}

        if self.activo and self.tercero_id and not self.tercero.activo:
            errores["tercero"] = (
                "No se puede activar un domicilio en un tercero inactivo."
            )
        if self.principal and not self.activo:
            errores["principal"] = (
                "Un domicilio principal debe estar activo."
            )
        if self.activo and self.fecha_baja is not None:
            errores["fecha_baja"] = (
                "Un domicilio activo no puede tener fecha de baja."
            )
        if (
            self.fecha_baja is not None
            and self.fecha_alta is not None
            and self.fecha_baja < self.fecha_alta
        ):
            errores["fecha_baja"] = (
                "La fecha de baja no puede ser anterior a la fecha de alta."
            )

        original = None
        if self.pk:
            original = (
                type(self)
                .objects.filter(pk=self.pk)
                .values("tercero_id")
                .first()
            )
        if original and original["tercero_id"] != self.tercero_id:
            errores["tercero"] = (
                "El tercero de un domicilio existente no puede cambiar."
            )

        if self.tercero_id and self.activo and self.principal:
            otro = type(self).objects.filter(
                tercero_id=self.tercero_id,
                tipo=self.tipo,
                activo=True,
                principal=True,
            )
            if self.pk:
                otro = otro.exclude(pk=self.pk)
            if otro.exists():
                errores["principal"] = (
                    "Ya existe otro domicilio principal activo de este tipo."
                )

        if errores:
            raise ValidationError(errores)

    @property
    def domicilio_formateado(self):
        linea = " ".join(
            parte
            for parte in (self.calle.strip(), self.numero.strip())
            if parte
        )
        complementos = []
        for etiqueta, valor in (
            ("Sector", self.sector),
            ("Torre", self.torre),
            ("Piso", self.piso),
            ("Depto.", self.departamento),
        ):
            if valor.strip():
                complementos.append(f"{etiqueta} {valor.strip()}")

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
        bloques = [valor for valor in (linea, ", ".join(complementos), ", ".join(ubicacion)) if valor]
        return " · ".join(bloques) or "Sin domicilio informado"

    def __str__(self):
        return (
            f"{self.tercero} - {self.get_tipo_display()} - "
            f"{self.domicilio_formateado}"
        )


class ContactoTercero(models.Model):
    tercero = models.ForeignKey(
        Tercero,
        on_delete=models.PROTECT,
        related_name="contactos",
    )
    nombre = models.CharField(max_length=150)
    cargo = models.CharField(max_length=120, blank=True)
    area = models.CharField(max_length=120, blank=True)
    telefono = models.CharField(max_length=60, blank=True)
    email = models.EmailField(max_length=180, blank=True)
    principal = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    fecha_alta = models.DateField(default=timezone.localdate)
    fecha_baja = models.DateField(null=True, blank=True)
    observaciones = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "terceros_contactotercero"
        verbose_name = "contacto de tercero"
        verbose_name_plural = "contactos de terceros"
        ordering = [
            "tercero__denominacion",
            "-activo",
            "-principal",
            "nombre",
            "pk",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tercero"],
                condition=Q(activo=True, principal=True),
                name="uniq_contacto_tercero_principal",
            ),
            models.CheckConstraint(
                condition=Q(principal=False) | Q(activo=True),
                name="chk_contacto_principal_activo",
            ),
            models.CheckConstraint(
                condition=(
                    Q(fecha_baja__isnull=True)
                    | Q(fecha_baja__gte=F("fecha_alta"))
                ),
                name="chk_contacto_tercero_fechas",
            ),
            models.CheckConstraint(
                condition=Q(activo=False) | Q(fecha_baja__isnull=True),
                name="chk_contacto_activo_sin_baja",
            ),
        ]
        indexes = [
            models.Index(
                fields=["tercero", "activo", "principal"],
                name="idx_contacto_tercero_act",
            )
        ]

    def clean(self):
        super().clean()
        self.nombre = self.nombre.strip()
        self.cargo = self.cargo.strip()
        self.area = self.area.strip()
        self.telefono = self.telefono.strip()
        self.email = self.email.strip().lower()
        self.observaciones = self.observaciones.strip()
        errores = {}

        if not self.telefono and not self.email:
            mensaje = "Informá al menos un teléfono o un correo electrónico."
            errores["telefono"] = mensaje
            errores["email"] = mensaje
        if self.activo and self.tercero_id and not self.tercero.activo:
            errores["tercero"] = (
                "No se puede activar un contacto en un tercero inactivo."
            )
        if self.principal and not self.activo:
            errores["principal"] = (
                "Un contacto principal debe estar activo."
            )
        if self.activo and self.fecha_baja is not None:
            errores["fecha_baja"] = (
                "Un contacto activo no puede tener fecha de baja."
            )
        if (
            self.fecha_baja is not None
            and self.fecha_alta is not None
            and self.fecha_baja < self.fecha_alta
        ):
            errores["fecha_baja"] = (
                "La fecha de baja no puede ser anterior a la fecha de alta."
            )

        original = None
        if self.pk:
            original = (
                type(self)
                .objects.filter(pk=self.pk)
                .values("tercero_id")
                .first()
            )
        if original and original["tercero_id"] != self.tercero_id:
            errores["tercero"] = (
                "El tercero de un contacto existente no puede cambiar."
            )

        if self.tercero_id and self.activo and self.principal:
            otro = type(self).objects.filter(
                tercero_id=self.tercero_id,
                activo=True,
                principal=True,
            )
            if self.pk:
                otro = otro.exclude(pk=self.pk)
            if otro.exists():
                errores["principal"] = (
                    "Ya existe otro contacto principal activo."
                )

        if errores:
            raise ValidationError(errores)

    def __str__(self):
        return f"{self.tercero} - {self.nombre}"
