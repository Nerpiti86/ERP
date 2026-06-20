from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import (
    ActividadEconomica,
    Auditoria,
    EmpresaActividad,
)


def _valor_json(valor):
    if hasattr(valor, "isoformat"):
        return valor.isoformat()
    return valor


def datos_empresa_actividad(relacion):
    return {
        "empresa_id": relacion.empresa_id,
        "actividad_id": relacion.actividad_id,
        "principal": relacion.principal,
        "activa": relacion.activa,
        "orden": relacion.orden,
        "vigencia_desde": _valor_json(relacion.vigencia_desde),
        "vigencia_hasta": _valor_json(relacion.vigencia_hasta),
        "observaciones": relacion.observaciones,
        "nomenclador_registrado": relacion.nomenclador_registrado,
        "codigo_registrado": relacion.codigo_registrado,
        "descripcion_registrada": relacion.descripcion_registrada,
        "fuente_sha256_registrada": (
            relacion.fuente_sha256_registrada
        ),
    }


def _datos_request(request):
    if request is None:
        return {
            "usuario": None,
            "ip": None,
            "user_agent": "",
        }

    usuario = getattr(request, "user", None)

    if usuario is not None and not usuario.is_authenticated:
        usuario = None

    ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()

    if not ip:
        ip = request.META.get("REMOTE_ADDR") or None

    return {
        "usuario": usuario,
        "ip": ip,
        "user_agent": request.META.get("HTTP_USER_AGENT", ""),
    }


def _registrar_auditoria(
    *,
    empresa,
    relacion,
    accion,
    anteriores,
    nuevos,
    request,
):
    datos_request = _datos_request(request)

    Auditoria.objects.create(
        empresa=empresa,
        usuario=datos_request["usuario"],
        accion=accion,
        tabla=EmpresaActividad._meta.db_table,
        registro_id=str(relacion.pk),
        datos_anteriores=anteriores,
        datos_nuevos=nuevos,
        ip=datos_request["ip"],
        user_agent=datos_request["user_agent"],
    )


def _desmarcar_principal_anterior(
    *,
    empresa,
    excluir_id=None,
    request=None,
):
    anteriores = (
        EmpresaActividad.objects.select_for_update()
        .filter(
            empresa=empresa,
            activa=True,
            principal=True,
        )
        .exclude(pk=excluir_id)
        .order_by("pk")
    )

    for relacion in anteriores:
        datos_anteriores = datos_empresa_actividad(relacion)
        relacion.principal = False
        relacion.full_clean()
        relacion.save(
            update_fields=[
                "principal",
                "actualizada_en",
            ]
        )
        _registrar_auditoria(
            empresa=empresa,
            relacion=relacion,
            accion=Auditoria.Accion.UPDATE,
            anteriores=datos_anteriores,
            nuevos=datos_empresa_actividad(relacion),
            request=request,
        )


@transaction.atomic
def crear_empresa_actividad(
    *,
    empresa,
    actividad,
    principal=False,
    orden=0,
    vigencia_desde=None,
    vigencia_hasta=None,
    observaciones="",
    request=None,
):
    actividad = ActividadEconomica.objects.select_for_update().filter(
        pk=actividad.pk,
        activa=True,
    ).first()

    if actividad is None:
        raise ValidationError(
            {
                "actividad": (
                    "La actividad seleccionada no existe o ya no está "
                    "activa en el catálogo oficial."
                )
            }
        )

    if EmpresaActividad.objects.select_for_update().filter(
        empresa=empresa,
        actividad=actividad,
        activa=True,
    ).exists():
        raise ValidationError(
            {
                "actividad": (
                    "La empresa ya tiene esta actividad activa."
                )
            }
        )

    if principal:
        _desmarcar_principal_anterior(
            empresa=empresa,
            request=request,
        )

    relacion = EmpresaActividad(
        empresa=empresa,
        actividad=actividad,
        principal=principal,
        activa=True,
        orden=orden,
        vigencia_desde=vigencia_desde,
        vigencia_hasta=vigencia_hasta,
        observaciones=(observaciones or "").strip(),
        nomenclador_registrado=actividad.nomenclador,
        codigo_registrado=actividad.codigo,
        descripcion_registrada=actividad.descripcion,
        fuente_sha256_registrada=actividad.fuente_sha256,
    )
    relacion.full_clean()
    relacion.save()

    _registrar_auditoria(
        empresa=empresa,
        relacion=relacion,
        accion=Auditoria.Accion.INSERT,
        anteriores=None,
        nuevos=datos_empresa_actividad(relacion),
        request=request,
    )

    return relacion


@transaction.atomic
def actualizar_empresa_actividad(
    *,
    empresa,
    empresa_actividad,
    principal,
    orden,
    vigencia_desde,
    vigencia_hasta,
    observaciones,
    request=None,
):
    relacion = (
        EmpresaActividad.objects.select_for_update()
        .select_related("actividad")
        .filter(
            pk=empresa_actividad.pk,
            empresa=empresa,
        )
        .first()
    )

    if relacion is None:
        raise ValidationError(
            "La actividad no pertenece a la empresa activa."
        )

    if not relacion.activa:
        raise ValidationError(
            "Una relación histórica inactiva no puede editarse."
        )

    datos_anteriores = datos_empresa_actividad(relacion)

    if principal:
        _desmarcar_principal_anterior(
            empresa=empresa,
            excluir_id=relacion.pk,
            request=request,
        )

    relacion.principal = principal
    relacion.orden = orden
    relacion.vigencia_desde = vigencia_desde
    relacion.vigencia_hasta = vigencia_hasta
    relacion.observaciones = (observaciones or "").strip()
    relacion.full_clean()
    relacion.save()

    datos_nuevos = datos_empresa_actividad(relacion)

    if datos_nuevos != datos_anteriores:
        _registrar_auditoria(
            empresa=empresa,
            relacion=relacion,
            accion=Auditoria.Accion.UPDATE,
            anteriores=datos_anteriores,
            nuevos=datos_nuevos,
            request=request,
        )

    return relacion


@transaction.atomic
def inactivar_empresa_actividad(
    *,
    empresa,
    empresa_actividad,
    request=None,
):
    relacion = (
        EmpresaActividad.objects.select_for_update()
        .select_related("actividad")
        .filter(
            pk=empresa_actividad.pk,
            empresa=empresa,
        )
        .first()
    )

    if relacion is None:
        raise ValidationError(
            "La actividad no pertenece a la empresa activa."
        )

    if not relacion.activa:
        return relacion

    datos_anteriores = datos_empresa_actividad(relacion)
    fecha_fin = timezone.localdate()

    if (
        relacion.vigencia_desde is not None
        and fecha_fin < relacion.vigencia_desde
    ):
        fecha_fin = relacion.vigencia_desde

    relacion.activa = False
    relacion.principal = False

    if relacion.vigencia_hasta is None:
        relacion.vigencia_hasta = fecha_fin

    relacion.full_clean()
    relacion.save()

    _registrar_auditoria(
        empresa=empresa,
        relacion=relacion,
        accion=Auditoria.Accion.UPDATE,
        anteriores=datos_anteriores,
        nuevos=datos_empresa_actividad(relacion),
        request=request,
    )

    return relacion
