from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import (
    Auditoria,
    EmpresaActividad,
    EmpresaJurisdiccionIIBB,
    ParametroSistema,
    PuntoVenta,
    Sucursal,
)


CLAVE_PUNTO_VENTA_LEGACY = "punto_venta_default"


def _valor_json(valor):
    if hasattr(valor, "isoformat"):
        return valor.isoformat()
    return valor


def datos_punto_venta(punto_venta):
    return {
        "empresa_id": punto_venta.empresa_id,
        "sucursal_id": punto_venta.sucursal_id,
        "numero": punto_venta.numero,
        "nombre_fantasia": punto_venta.nombre_fantasia,
        "sistema_emision": punto_venta.sistema_emision,
        "descripcion_sistema_arca": (
            punto_venta.descripcion_sistema_arca
        ),
        "actividad_predeterminada_id": (
            punto_venta.actividad_predeterminada_id
        ),
        "jurisdiccion_iibb_predeterminada_id": (
            punto_venta.jurisdiccion_iibb_predeterminada_id
        ),
        "predeterminado": punto_venta.predeterminado,
        "bloqueado": punto_venta.bloqueado,
        "fecha_alta": _valor_json(punto_venta.fecha_alta),
        "fecha_baja": _valor_json(punto_venta.fecha_baja),
        "activo": punto_venta.activo,
        "observaciones": punto_venta.observaciones,
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
    punto_venta,
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
        tabla=PuntoVenta._meta.db_table,
        registro_id=str(punto_venta.pk),
        datos_anteriores=anteriores,
        datos_nuevos=nuevos,
        ip=datos_request["ip"],
        user_agent=datos_request["user_agent"],
    )


def obtener_numero_punto_venta_legacy(empresa):
    if PuntoVenta.objects.filter(empresa=empresa).exists():
        return None

    parametro = ParametroSistema.objects.filter(
        ambito=ParametroSistema.Ambito.EMPRESA,
        empresa=empresa,
        clave=CLAVE_PUNTO_VENTA_LEGACY,
    ).first()

    if parametro is None:
        return None

    texto = str(parametro.valor or "").strip()

    if not texto.isdigit():
        return None

    numero = int(texto)

    if not 1 <= numero <= 99998:
        return None

    return numero


def _obtener_sucursal_activa(*, empresa, sucursal):
    sucursal_bloqueada = (
        Sucursal.objects.select_for_update()
        .filter(
            pk=sucursal.pk,
            empresa=empresa,
            activa=True,
        )
        .first()
    )

    if sucursal_bloqueada is None:
        raise ValidationError(
            {
                "sucursal": (
                    "La sucursal no pertenece a la empresa activa "
                    "o está inactiva."
                )
            }
        )

    return sucursal_bloqueada


def _obtener_actividad_activa(*, empresa, actividad):
    if actividad is None:
        return None

    actividad_bloqueada = (
        EmpresaActividad.objects.select_for_update()
        .filter(
            pk=actividad.pk,
            empresa=empresa,
            activa=True,
        )
        .first()
    )

    if actividad_bloqueada is None:
        raise ValidationError(
            {
                "actividad_predeterminada": (
                    "La actividad no pertenece a la empresa "
                    "o está inactiva."
                )
            }
        )

    return actividad_bloqueada


def _obtener_jurisdiccion_activa(*, empresa, relacion):
    if relacion is None:
        return None

    relacion_bloqueada = (
        EmpresaJurisdiccionIIBB.objects.select_for_update()
        .select_related("configuracion")
        .filter(
            pk=relacion.pk,
            configuracion__empresa=empresa,
            configuracion__activa=True,
            activa=True,
        )
        .first()
    )

    if relacion_bloqueada is None:
        raise ValidationError(
            {
                "jurisdiccion_iibb_predeterminada": (
                    "La jurisdicción de IIBB no pertenece a la empresa "
                    "o está inactiva."
                )
            }
        )

    return relacion_bloqueada


def _desmarcar_predeterminado_anterior(
    *,
    empresa,
    sucursal,
    excluir_id=None,
    request=None,
):
    anteriores = (
        PuntoVenta.objects.select_for_update()
        .filter(
            empresa=empresa,
            sucursal=sucursal,
            activo=True,
            predeterminado=True,
        )
        .exclude(pk=excluir_id)
        .order_by("pk")
    )

    for punto_venta in anteriores:
        datos_anteriores = datos_punto_venta(punto_venta)
        punto_venta.predeterminado = False
        punto_venta.full_clean()
        punto_venta.save(
            update_fields=[
                "predeterminado",
                "actualizado_en",
            ]
        )
        _registrar_auditoria(
            empresa=empresa,
            punto_venta=punto_venta,
            accion=Auditoria.Accion.UPDATE,
            anteriores=datos_anteriores,
            nuevos=datos_punto_venta(punto_venta),
            request=request,
        )


def _asegurar_predeterminado_sucursal(
    *,
    empresa,
    sucursal,
    request=None,
):
    puntos_activos = list(
        PuntoVenta.objects.select_for_update()
        .filter(
            empresa=empresa,
            sucursal=sucursal,
            activo=True,
        )
        .order_by("numero", "pk")
    )

    if not puntos_activos:
        return None

    if any(punto.predeterminado for punto in puntos_activos):
        return next(
            punto
            for punto in puntos_activos
            if punto.predeterminado
        )

    punto_venta = puntos_activos[0]
    datos_anteriores = datos_punto_venta(punto_venta)
    punto_venta.predeterminado = True
    punto_venta.full_clean()
    punto_venta.save(
        update_fields=[
            "predeterminado",
            "actualizado_en",
        ]
    )
    _registrar_auditoria(
        empresa=empresa,
        punto_venta=punto_venta,
        accion=Auditoria.Accion.UPDATE,
        anteriores=datos_anteriores,
        nuevos=datos_punto_venta(punto_venta),
        request=request,
    )
    return punto_venta


def _fecha_baja_valida(fecha_alta):
    fecha = timezone.localdate()

    if fecha_alta is not None and fecha < fecha_alta:
        return fecha_alta

    return fecha


@transaction.atomic
def crear_punto_venta(
    *,
    empresa,
    sucursal,
    numero,
    sistema_emision,
    nombre_fantasia="",
    descripcion_sistema_arca="",
    actividad_predeterminada=None,
    jurisdiccion_iibb_predeterminada=None,
    predeterminado=False,
    bloqueado=False,
    fecha_alta=None,
    observaciones="",
    request=None,
):
    sucursal = _obtener_sucursal_activa(
        empresa=empresa,
        sucursal=sucursal,
    )
    actividad_predeterminada = _obtener_actividad_activa(
        empresa=empresa,
        actividad=actividad_predeterminada,
    )
    jurisdiccion_iibb_predeterminada = _obtener_jurisdiccion_activa(
        empresa=empresa,
        relacion=jurisdiccion_iibb_predeterminada,
    )

    if PuntoVenta.objects.select_for_update().filter(
        empresa=empresa,
        numero=numero,
    ).exists():
        raise ValidationError(
            {
                "numero": (
                    "Este número de punto de venta ya fue utilizado "
                    "por la empresa y no puede reutilizarse."
                )
            }
        )

    activos_sucursal = list(
        PuntoVenta.objects.select_for_update()
        .filter(
            empresa=empresa,
            sucursal=sucursal,
            activo=True,
        )
        .order_by("numero", "pk")
    )

    if not activos_sucursal:
        predeterminado = True

    if predeterminado:
        _desmarcar_predeterminado_anterior(
            empresa=empresa,
            sucursal=sucursal,
            request=request,
        )

    punto_venta = PuntoVenta(
        empresa=empresa,
        sucursal=sucursal,
        numero=numero,
        nombre_fantasia=(nombre_fantasia or "").strip(),
        sistema_emision=sistema_emision,
        descripcion_sistema_arca=(
            descripcion_sistema_arca or ""
        ).strip(),
        actividad_predeterminada=actividad_predeterminada,
        jurisdiccion_iibb_predeterminada=(
            jurisdiccion_iibb_predeterminada
        ),
        predeterminado=predeterminado,
        bloqueado=bloqueado,
        fecha_alta=fecha_alta,
        fecha_baja=None,
        activo=True,
        observaciones=(observaciones or "").strip(),
    )
    punto_venta.full_clean()
    punto_venta.save()

    _registrar_auditoria(
        empresa=empresa,
        punto_venta=punto_venta,
        accion=Auditoria.Accion.INSERT,
        anteriores=None,
        nuevos=datos_punto_venta(punto_venta),
        request=request,
    )

    return punto_venta


@transaction.atomic
def actualizar_punto_venta(
    *,
    empresa,
    punto_venta,
    sucursal,
    sistema_emision,
    nombre_fantasia,
    descripcion_sistema_arca,
    actividad_predeterminada,
    jurisdiccion_iibb_predeterminada,
    predeterminado,
    bloqueado,
    fecha_alta,
    observaciones,
    request=None,
):
    punto_venta = (
        PuntoVenta.objects.select_for_update()
        .filter(
            pk=punto_venta.pk,
            empresa=empresa,
            activo=True,
        )
        .first()
    )

    if punto_venta is None:
        raise ValidationError(
            "El punto de venta no pertenece a la empresa activa "
            "o está inactivo."
        )

    sucursal_anterior = punto_venta.sucursal
    era_predeterminado = punto_venta.predeterminado

    sucursal = _obtener_sucursal_activa(
        empresa=empresa,
        sucursal=sucursal,
    )
    actividad_predeterminada = _obtener_actividad_activa(
        empresa=empresa,
        actividad=actividad_predeterminada,
    )
    jurisdiccion_iibb_predeterminada = _obtener_jurisdiccion_activa(
        empresa=empresa,
        relacion=jurisdiccion_iibb_predeterminada,
    )

    otros_en_destino = list(
        PuntoVenta.objects.select_for_update()
        .filter(
            empresa=empresa,
            sucursal=sucursal,
            activo=True,
        )
        .exclude(pk=punto_venta.pk)
        .order_by("numero", "pk")
    )

    if predeterminado or not otros_en_destino:
        predeterminado = True
        _desmarcar_predeterminado_anterior(
            empresa=empresa,
            sucursal=sucursal,
            excluir_id=punto_venta.pk,
            request=request,
        )
    elif not any(
        otro.predeterminado
        for otro in otros_en_destino
    ):
        predeterminado = True

    datos_anteriores = datos_punto_venta(punto_venta)

    punto_venta.sucursal = sucursal
    punto_venta.nombre_fantasia = (nombre_fantasia or "").strip()
    punto_venta.sistema_emision = sistema_emision
    punto_venta.descripcion_sistema_arca = (
        descripcion_sistema_arca or ""
    ).strip()
    punto_venta.actividad_predeterminada = actividad_predeterminada
    punto_venta.jurisdiccion_iibb_predeterminada = (
        jurisdiccion_iibb_predeterminada
    )
    punto_venta.predeterminado = predeterminado
    punto_venta.bloqueado = bloqueado
    punto_venta.fecha_alta = fecha_alta
    punto_venta.observaciones = (observaciones or "").strip()
    punto_venta.full_clean()
    punto_venta.save()

    if (
        sucursal_anterior.pk != sucursal.pk
        and era_predeterminado
    ):
        _asegurar_predeterminado_sucursal(
            empresa=empresa,
            sucursal=sucursal_anterior,
            request=request,
        )

    datos_nuevos = datos_punto_venta(punto_venta)

    if datos_nuevos != datos_anteriores:
        _registrar_auditoria(
            empresa=empresa,
            punto_venta=punto_venta,
            accion=Auditoria.Accion.UPDATE,
            anteriores=datos_anteriores,
            nuevos=datos_nuevos,
            request=request,
        )

    return punto_venta


@transaction.atomic
def inactivar_punto_venta(
    *,
    empresa,
    punto_venta,
    request=None,
):
    punto_venta = (
        PuntoVenta.objects.select_for_update()
        .select_related("sucursal")
        .filter(
            pk=punto_venta.pk,
            empresa=empresa,
        )
        .first()
    )

    if punto_venta is None:
        raise ValidationError(
            "El punto de venta no pertenece a la empresa activa."
        )

    if not punto_venta.activo:
        return punto_venta

    sucursal = punto_venta.sucursal
    era_predeterminado = punto_venta.predeterminado
    datos_anteriores = datos_punto_venta(punto_venta)

    punto_venta.activo = False
    punto_venta.predeterminado = False
    punto_venta.fecha_baja = _fecha_baja_valida(
        punto_venta.fecha_alta
    )
    punto_venta.full_clean()
    punto_venta.save()

    _registrar_auditoria(
        empresa=empresa,
        punto_venta=punto_venta,
        accion=Auditoria.Accion.UPDATE,
        anteriores=datos_anteriores,
        nuevos=datos_punto_venta(punto_venta),
        request=request,
    )

    if era_predeterminado:
        _asegurar_predeterminado_sucursal(
            empresa=empresa,
            sucursal=sucursal,
            request=request,
        )

    return punto_venta
