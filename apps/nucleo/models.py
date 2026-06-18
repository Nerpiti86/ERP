import json
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
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
