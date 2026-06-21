from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import (
    Auditoria,
    ConfiguracionIIBBEmpresa,
    EmpresaJurisdiccionIIBB,
    JurisdiccionFiscal,
)


def _valor_json(valor):
    if hasattr(valor, "isoformat"):
        return valor.isoformat()
    return valor


def datos_configuracion_iibb(configuracion):
    return {
        "empresa_id": configuracion.empresa_id,
        "regimen": configuracion.regimen,
        "tratamiento_general": configuracion.tratamiento_general,
        "numero_inscripcion": configuracion.numero_inscripcion,
        "fecha_alta": _valor_json(configuracion.fecha_alta),
        "fecha_baja": _valor_json(configuracion.fecha_baja),
        "activa": configuracion.activa,
        "observaciones": configuracion.observaciones,
    }


def datos_jurisdiccion_iibb(relacion):
    return {
        "configuracion_id": relacion.configuracion_id,
        "jurisdiccion_id": relacion.jurisdiccion_id,
        "numero_inscripcion": relacion.numero_inscripcion,
        "sede": relacion.sede,
        "tratamiento": relacion.tratamiento,
        "fecha_alta": _valor_json(relacion.fecha_alta),
        "fecha_baja": _valor_json(relacion.fecha_baja),
        "activa": relacion.activa,
        "observaciones": relacion.observaciones,
        "codigo_registrado": relacion.codigo_registrado,
        "nombre_registrado": relacion.nombre_registrado,
        "fuente_url_registrada": relacion.fuente_url_registrada,
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
    objeto,
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
        tabla=objeto._meta.db_table,
        registro_id=str(objeto.pk),
        datos_anteriores=anteriores,
        datos_nuevos=nuevos,
        ip=datos_request["ip"],
        user_agent=datos_request["user_agent"],
    )


def _fecha_baja_valida(fecha_alta):
    fecha = timezone.localdate()
    if fecha_alta is not None and fecha < fecha_alta:
        return fecha_alta
    return fecha


def _desmarcar_sede_anterior(
    *,
    configuracion,
    excluir_id=None,
    request=None,
):
    anteriores = (
        EmpresaJurisdiccionIIBB.objects.select_for_update()
        .filter(
            configuracion=configuracion,
            activa=True,
            sede=True,
        )
        .exclude(pk=excluir_id)
        .order_by("pk")
    )

    for relacion in anteriores:
        datos_anteriores = datos_jurisdiccion_iibb(relacion)
        relacion.sede = False
        relacion.full_clean()
        relacion.save(
            update_fields=[
                "sede",
                "actualizada_en",
            ]
        )
        _registrar_auditoria(
            empresa=configuracion.empresa,
            objeto=relacion,
            accion=Auditoria.Accion.UPDATE,
            anteriores=datos_anteriores,
            nuevos=datos_jurisdiccion_iibb(relacion),
            request=request,
        )


@transaction.atomic
def crear_configuracion_iibb(
    *,
    empresa,
    regimen,
    tratamiento_general,
    numero_inscripcion="",
    fecha_alta=None,
    observaciones="",
    request=None,
):
    if ConfiguracionIIBBEmpresa.objects.select_for_update().filter(
        empresa=empresa,
        activa=True,
    ).exists():
        raise ValidationError(
            "La empresa ya tiene una configuración de IIBB activa."
        )

    configuracion = ConfiguracionIIBBEmpresa(
        empresa=empresa,
        regimen=regimen,
        tratamiento_general=tratamiento_general,
        numero_inscripcion=(numero_inscripcion or "").strip(),
        fecha_alta=fecha_alta,
        fecha_baja=None,
        activa=True,
        observaciones=(observaciones or "").strip(),
    )
    configuracion.full_clean()
    configuracion.save()

    _registrar_auditoria(
        empresa=empresa,
        objeto=configuracion,
        accion=Auditoria.Accion.INSERT,
        anteriores=None,
        nuevos=datos_configuracion_iibb(configuracion),
        request=request,
    )

    return configuracion


@transaction.atomic
def actualizar_configuracion_iibb(
    *,
    empresa,
    configuracion,
    regimen,
    tratamiento_general,
    numero_inscripcion,
    fecha_alta,
    observaciones,
    request=None,
):
    configuracion = (
        ConfiguracionIIBBEmpresa.objects.select_for_update()
        .filter(
            pk=configuracion.pk,
            empresa=empresa,
            activa=True,
        )
        .first()
    )

    if configuracion is None:
        raise ValidationError(
            "La configuración de IIBB no pertenece a la empresa activa."
        )

    jurisdicciones = list(
        EmpresaJurisdiccionIIBB.objects.select_for_update()
        .filter(
            configuracion=configuracion,
            activa=True,
        )
        .order_by("pk")
    )

    if (
        regimen == ConfiguracionIIBBEmpresa.Regimen.NO_INSCRIPTO
        and jurisdicciones
    ):
        raise ValidationError(
            {
                "regimen": (
                    "Inactivá las jurisdicciones antes de marcar "
                    "la empresa como no inscripta."
                )
            }
        )

    if (
        regimen == ConfiguracionIIBBEmpresa.Regimen.LOCAL
        and len(jurisdicciones) > 1
    ):
        raise ValidationError(
            {
                "regimen": (
                    "El régimen local admite una sola jurisdicción activa."
                )
            }
        )

    datos_anteriores = datos_configuracion_iibb(configuracion)

    configuracion.regimen = regimen
    configuracion.tratamiento_general = tratamiento_general
    configuracion.numero_inscripcion = (numero_inscripcion or "").strip()
    configuracion.fecha_alta = fecha_alta
    configuracion.observaciones = (observaciones or "").strip()
    configuracion.full_clean()
    configuracion.save()

    if (
        regimen == ConfiguracionIIBBEmpresa.Regimen.LOCAL
        and len(jurisdicciones) == 1
        and not jurisdicciones[0].sede
    ):
        relacion = jurisdicciones[0]
        anteriores = datos_jurisdiccion_iibb(relacion)
        relacion.sede = True
        relacion.full_clean()
        relacion.save(
            update_fields=[
                "sede",
                "actualizada_en",
            ]
        )
        _registrar_auditoria(
            empresa=empresa,
            objeto=relacion,
            accion=Auditoria.Accion.UPDATE,
            anteriores=anteriores,
            nuevos=datos_jurisdiccion_iibb(relacion),
            request=request,
        )

    datos_nuevos = datos_configuracion_iibb(configuracion)

    if datos_nuevos != datos_anteriores:
        _registrar_auditoria(
            empresa=empresa,
            objeto=configuracion,
            accion=Auditoria.Accion.UPDATE,
            anteriores=datos_anteriores,
            nuevos=datos_nuevos,
            request=request,
        )

    return configuracion


@transaction.atomic
def inactivar_configuracion_iibb(
    *,
    empresa,
    configuracion,
    request=None,
):
    configuracion = (
        ConfiguracionIIBBEmpresa.objects.select_for_update()
        .filter(
            pk=configuracion.pk,
            empresa=empresa,
        )
        .first()
    )

    if configuracion is None:
        raise ValidationError(
            "La configuración de IIBB no pertenece a la empresa activa."
        )

    if not configuracion.activa:
        return configuracion

    relaciones = list(
        EmpresaJurisdiccionIIBB.objects.select_for_update()
        .filter(
            configuracion=configuracion,
            activa=True,
        )
        .order_by("pk")
    )

    for relacion in relaciones:
        anteriores = datos_jurisdiccion_iibb(relacion)
        relacion.activa = False
        relacion.sede = False
        if relacion.fecha_baja is None:
            relacion.fecha_baja = _fecha_baja_valida(
                relacion.fecha_alta
            )
        relacion.full_clean()
        relacion.save()
        _registrar_auditoria(
            empresa=empresa,
            objeto=relacion,
            accion=Auditoria.Accion.UPDATE,
            anteriores=anteriores,
            nuevos=datos_jurisdiccion_iibb(relacion),
            request=request,
        )

    datos_anteriores = datos_configuracion_iibb(configuracion)
    configuracion.activa = False
    if configuracion.fecha_baja is None:
        configuracion.fecha_baja = _fecha_baja_valida(
            configuracion.fecha_alta
        )
    configuracion.full_clean()
    configuracion.save()

    _registrar_auditoria(
        empresa=empresa,
        objeto=configuracion,
        accion=Auditoria.Accion.UPDATE,
        anteriores=datos_anteriores,
        nuevos=datos_configuracion_iibb(configuracion),
        request=request,
    )

    return configuracion


@transaction.atomic
def crear_jurisdiccion_iibb(
    *,
    empresa,
    configuracion,
    jurisdiccion,
    numero_inscripcion="",
    sede=False,
    tratamiento=(
        EmpresaJurisdiccionIIBB.Tratamiento.SEGUN_CONFIGURACION
    ),
    fecha_alta=None,
    observaciones="",
    request=None,
):
    configuracion = (
        ConfiguracionIIBBEmpresa.objects.select_for_update()
        .filter(
            pk=configuracion.pk,
            empresa=empresa,
            activa=True,
        )
        .first()
    )

    if configuracion is None:
        raise ValidationError(
            "La configuración de IIBB no pertenece a la empresa activa."
        )

    if (
        configuracion.regimen
        == ConfiguracionIIBBEmpresa.Regimen.NO_INSCRIPTO
    ):
        raise ValidationError(
            "Una empresa no inscripta no admite jurisdicciones."
        )

    jurisdiccion = JurisdiccionFiscal.objects.select_for_update().filter(
        pk=jurisdiccion.pk,
        activa=True,
    ).first()

    if jurisdiccion is None:
        raise ValidationError(
            {"jurisdiccion": "La jurisdicción seleccionada no está activa."}
        )

    activas = list(
        EmpresaJurisdiccionIIBB.objects.select_for_update()
        .filter(
            configuracion=configuracion,
            activa=True,
        )
        .order_by("pk")
    )

    if (
        configuracion.regimen
        == ConfiguracionIIBBEmpresa.Regimen.LOCAL
        and activas
    ):
        raise ValidationError(
            "El régimen local admite una sola jurisdicción activa."
        )

    if EmpresaJurisdiccionIIBB.objects.filter(
        configuracion=configuracion,
        jurisdiccion=jurisdiccion,
        activa=True,
    ).exists():
        raise ValidationError(
            {"jurisdiccion": "La jurisdicción ya está activa."}
        )

    if not activas:
        sede = True

    if (
        configuracion.regimen
        == ConfiguracionIIBBEmpresa.Regimen.LOCAL
    ):
        sede = True

    if sede:
        _desmarcar_sede_anterior(
            configuracion=configuracion,
            request=request,
        )

    relacion = EmpresaJurisdiccionIIBB(
        configuracion=configuracion,
        jurisdiccion=jurisdiccion,
        numero_inscripcion=(numero_inscripcion or "").strip(),
        sede=sede,
        tratamiento=tratamiento,
        fecha_alta=fecha_alta,
        fecha_baja=None,
        activa=True,
        observaciones=(observaciones or "").strip(),
        codigo_registrado=jurisdiccion.codigo,
        nombre_registrado=jurisdiccion.nombre,
        fuente_url_registrada=jurisdiccion.fuente_url,
    )
    relacion.full_clean()
    relacion.save()

    _registrar_auditoria(
        empresa=empresa,
        objeto=relacion,
        accion=Auditoria.Accion.INSERT,
        anteriores=None,
        nuevos=datos_jurisdiccion_iibb(relacion),
        request=request,
    )

    return relacion


@transaction.atomic
def actualizar_jurisdiccion_iibb(
    *,
    empresa,
    relacion,
    numero_inscripcion,
    sede,
    tratamiento,
    fecha_alta,
    observaciones,
    request=None,
):
    relacion = (
        EmpresaJurisdiccionIIBB.objects.select_for_update()
        .select_related("configuracion", "jurisdiccion")
        .filter(
            pk=relacion.pk,
            configuracion__empresa=empresa,
            activa=True,
        )
        .first()
    )

    if relacion is None:
        raise ValidationError(
            "La jurisdicción no pertenece a la empresa activa."
        )

    configuracion = relacion.configuracion

    if not configuracion.activa:
        raise ValidationError(
            "La configuración de IIBB ya no está activa."
        )

    if relacion.sede and not sede:
        raise ValidationError(
            {
                "sede": (
                    "No podés quitar la sede directamente. "
                    "Marcá otra jurisdicción como sede."
                )
            }
        )

    if (
        configuracion.regimen
        == ConfiguracionIIBBEmpresa.Regimen.LOCAL
    ):
        sede = True

    if sede:
        _desmarcar_sede_anterior(
            configuracion=configuracion,
            excluir_id=relacion.pk,
            request=request,
        )

    datos_anteriores = datos_jurisdiccion_iibb(relacion)
    relacion.numero_inscripcion = (numero_inscripcion or "").strip()
    relacion.sede = sede
    relacion.tratamiento = tratamiento
    relacion.fecha_alta = fecha_alta
    relacion.observaciones = (observaciones or "").strip()
    relacion.full_clean()
    relacion.save()

    datos_nuevos = datos_jurisdiccion_iibb(relacion)

    if datos_nuevos != datos_anteriores:
        _registrar_auditoria(
            empresa=empresa,
            objeto=relacion,
            accion=Auditoria.Accion.UPDATE,
            anteriores=datos_anteriores,
            nuevos=datos_nuevos,
            request=request,
        )

    return relacion


@transaction.atomic
def inactivar_jurisdiccion_iibb(
    *,
    empresa,
    relacion,
    request=None,
):
    relacion = (
        EmpresaJurisdiccionIIBB.objects.select_for_update()
        .select_related("configuracion", "jurisdiccion")
        .filter(
            pk=relacion.pk,
            configuracion__empresa=empresa,
        )
        .first()
    )

    if relacion is None:
        raise ValidationError(
            "La jurisdicción no pertenece a la empresa activa."
        )

    if not relacion.activa:
        return relacion

    configuracion = relacion.configuracion
    era_sede = relacion.sede
    datos_anteriores = datos_jurisdiccion_iibb(relacion)

    relacion.activa = False
    relacion.sede = False
    if relacion.fecha_baja is None:
        relacion.fecha_baja = _fecha_baja_valida(relacion.fecha_alta)
    relacion.full_clean()
    relacion.save()

    _registrar_auditoria(
        empresa=empresa,
        objeto=relacion,
        accion=Auditoria.Accion.UPDATE,
        anteriores=datos_anteriores,
        nuevos=datos_jurisdiccion_iibb(relacion),
        request=request,
    )

    if era_sede:
        siguiente = (
            EmpresaJurisdiccionIIBB.objects.select_for_update()
            .filter(
                configuracion=configuracion,
                activa=True,
            )
            .order_by(
                "jurisdiccion__orden",
                "pk",
            )
            .first()
        )

        if siguiente is not None:
            anteriores = datos_jurisdiccion_iibb(siguiente)
            siguiente.sede = True
            siguiente.full_clean()
            siguiente.save(
                update_fields=[
                    "sede",
                    "actualizada_en",
                ]
            )
            _registrar_auditoria(
                empresa=empresa,
                objeto=siguiente,
                accion=Auditoria.Accion.UPDATE,
                anteriores=anteriores,
                nuevos=datos_jurisdiccion_iibb(siguiente),
                request=request,
            )

    return relacion
