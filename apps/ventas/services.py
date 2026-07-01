from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.items.models import AlicuotaIVA, Item, UnidadMedida
from apps.nucleo.models import Auditoria, Empresa, PuntoVenta, Sucursal
from apps.terceros.models import Tercero, TerceroRol

from .models import (
    ComprobanteVenta,
    ComprobanteVentaIVA,
    ComprobanteVentaLinea,
    TipoComprobanteVenta,
)


MONTO = Decimal("0.01")


def _dinero(valor):
    return Decimal(valor or "0").quantize(MONTO, rounding=ROUND_HALF_UP)


def _decimal(valor):
    return Decimal(str(valor or "0"))


def _datos_request(request):
    if request is None:
        return {"usuario": None, "ip": None, "user_agent": ""}

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


def _auditar(*, empresa, objeto, accion, anteriores, nuevos, request):
    datos = _datos_request(request)
    Auditoria.objects.create(
        empresa=empresa,
        usuario=datos["usuario"],
        accion=accion,
        tabla=objeto._meta.db_table,
        registro_id=str(objeto.pk),
        datos_anteriores=anteriores,
        datos_nuevos=nuevos,
        ip=datos["ip"],
        user_agent=datos["user_agent"],
    )


def datos_comprobante_venta(comprobante):
    return {
        "empresa_id": comprobante.empresa_id,
        "sucursal_id": comprobante.sucursal_id,
        "punto_venta_id": comprobante.punto_venta_id,
        "tipo_comprobante_id": comprobante.tipo_comprobante_id,
        "numero": comprobante.numero,
        "fecha": comprobante.fecha.isoformat() if comprobante.fecha else None,
        "fecha_vencimiento": (
            comprobante.fecha_vencimiento.isoformat()
            if comprobante.fecha_vencimiento
            else None
        ),
        "cliente_id": comprobante.cliente_id,
        "cliente_denominacion": comprobante.cliente_denominacion,
        "cliente_tipo_documento_codigo": (
            comprobante.cliente_tipo_documento_codigo
        ),
        "cliente_numero_documento": comprobante.cliente_numero_documento,
        "cliente_condicion_iva_codigo": (
            comprobante.cliente_condicion_iva_codigo
        ),
        "estado": comprobante.estado,
        "subtotal_gravado": str(comprobante.subtotal_gravado),
        "subtotal_no_gravado": str(comprobante.subtotal_no_gravado),
        "subtotal_exento": str(comprobante.subtotal_exento),
        "total_iva": str(comprobante.total_iva),
        "total_tributos": str(comprobante.total_tributos),
        "total": str(comprobante.total),
        "observaciones": comprobante.observaciones,
    }


def _empresa_activa(empresa):
    encontrada = (
        Empresa.objects.select_for_update()
        .filter(pk=getattr(empresa, "pk", None), activa=True)
        .first()
    )
    if encontrada is None:
        raise ValidationError("La empresa no existe o esta inactiva.")
    return encontrada


def _sucursal_activa(*, empresa, sucursal):
    encontrada = (
        Sucursal.objects.select_for_update()
        .filter(
            pk=getattr(sucursal, "pk", None),
            empresa=empresa,
            activa=True,
        )
        .first()
    )
    if encontrada is None:
        raise ValidationError(
            {"sucursal": "La sucursal no pertenece a la empresa activa."}
        )
    return encontrada


def _punto_venta_activo(*, empresa, sucursal, punto_venta):
    if punto_venta is None:
        return None

    encontrado = (
        PuntoVenta.objects.select_for_update()
        .filter(
            pk=getattr(punto_venta, "pk", None),
            empresa=empresa,
            sucursal=sucursal,
            activo=True,
            bloqueado=False,
        )
        .first()
    )
    if encontrado is None:
        raise ValidationError(
            {
                "punto_venta": (
                    "El punto de venta no pertenece a la sucursal activa "
                    "o esta bloqueado."
                )
            }
        )
    return encontrado


def _tipo_comprobante_activo(tipo_comprobante):
    encontrado = (
        TipoComprobanteVenta.objects.select_for_update()
        .filter(pk=getattr(tipo_comprobante, "pk", None), activo=True)
        .first()
    )
    if encontrado is None:
        raise ValidationError(
            {"tipo_comprobante": "El tipo de comprobante no esta activo."}
        )
    return encontrado


def _cliente_activo(*, empresa, cliente):
    encontrado = (
        Tercero.objects.select_for_update()
        .select_related("tipo_documento", "condicion_iva")
        .filter(
            pk=getattr(cliente, "pk", None),
            empresa=empresa,
            activo=True,
        )
        .first()
    )
    if encontrado is None:
        raise ValidationError(
            {"cliente": "El cliente no pertenece a la empresa activa."}
        )

    tiene_rol = TerceroRol.objects.select_for_update().filter(
        tercero=encontrado,
        rol=TerceroRol.Rol.CLIENTE,
        activo=True,
    ).exists()
    if not tiene_rol:
        raise ValidationError(
            {"cliente": "El tercero no tiene un rol CLIENTE activo."}
        )
    return encontrado


def _item_vendible(*, empresa, item):
    encontrado = (
        Item.objects.select_for_update()
        .filter(
            pk=getattr(item, "pk", None),
            empresa=empresa,
            activo=True,
            se_vende=True,
        )
        .first()
    )
    if encontrado is None:
        raise ValidationError(
            {"item": "El item no pertenece a la empresa o no se vende."}
        )
    return encontrado


def _unidad_activa(unidad_medida):
    encontrada = (
        UnidadMedida.objects.select_for_update()
        .filter(pk=getattr(unidad_medida, "pk", None), activo=True)
        .first()
    )
    if encontrada is None:
        raise ValidationError(
            {"unidad_medida": "La unidad de medida no esta activa."}
        )
    return encontrada


def _alicuota_activa(alicuota_iva):
    if alicuota_iva is None:
        return None

    encontrada = (
        AlicuotaIVA.objects.select_for_update()
        .filter(pk=getattr(alicuota_iva, "pk", None), activo=True)
        .first()
    )
    if encontrada is None:
        raise ValidationError({"alicuota_iva": "La alicuota no esta activa."})
    return encontrada


def _snapshot_cliente(cliente):
    return {
        "cliente_denominacion": cliente.denominacion,
        "cliente_tipo_documento_codigo": cliente.tipo_documento.codigo,
        "cliente_numero_documento": cliente.numero_documento,
        "cliente_condicion_iva_codigo": cliente.condicion_iva.codigo,
    }


def _datos_linea_desde_item(*, empresa, datos):
    item = datos.get("item")
    if item is None:
        unidad_medida = _unidad_activa(datos.get("unidad_medida"))
        alicuota_iva = _alicuota_activa(datos.get("alicuota_iva"))
        descripcion = str(datos.get("descripcion") or "").strip()
        if not descripcion:
            raise ValidationError(
                {"descripcion": "La linea sin item requiere descripcion."}
            )
        return {
            "item": None,
            "descripcion": descripcion,
            "unidad_medida": unidad_medida,
            "tratamiento_iva": datos.get("tratamiento_iva"),
            "alicuota_iva": alicuota_iva,
        }

    item = _item_vendible(empresa=empresa, item=item)
    return {
        "item": item,
        "descripcion": datos.get("descripcion") or item.nombre,
        "unidad_medida": item.unidad_medida,
        "tratamiento_iva": item.tratamiento_iva,
        "alicuota_iva": item.alicuota_iva,
    }


def _calcular_linea(*, tratamiento_iva, alicuota_iva, cantidad, precio_unitario, descuento):
    bruto = _decimal(cantidad) * _decimal(precio_unitario)
    descuento_importe = bruto * _decimal(descuento) / Decimal("100")
    neto = _dinero(bruto - descuento_importe)

    subtotal_gravado = Decimal("0.00")
    subtotal_no_gravado = Decimal("0.00")
    subtotal_exento = Decimal("0.00")
    iva_importe = Decimal("0.00")

    if tratamiento_iva == Item.TratamientoIVA.GRAVADO:
        subtotal_gravado = neto
        iva_importe = _dinero(neto * alicuota_iva.porcentaje / Decimal("100"))
    elif tratamiento_iva == Item.TratamientoIVA.EXENTO:
        subtotal_exento = neto
    else:
        subtotal_no_gravado = neto

    return {
        "subtotal_gravado": subtotal_gravado,
        "subtotal_no_gravado": subtotal_no_gravado,
        "subtotal_exento": subtotal_exento,
        "iva_importe": iva_importe,
        "total_linea": _dinero(neto + iva_importe),
    }


def _crear_lineas(*, comprobante, lineas):
    if not lineas:
        raise ValidationError("El comprobante requiere al menos una linea.")

    creadas = []
    for indice, datos in enumerate(lineas, start=1):
        base = _datos_linea_desde_item(
            empresa=comprobante.empresa,
            datos=datos,
        )
        cantidad = _decimal(datos.get("cantidad"))
        precio_unitario = _decimal(datos.get("precio_unitario"))
        descuento = _decimal(datos.get("descuento_porcentaje", "0"))
        calculos = _calcular_linea(
            tratamiento_iva=base["tratamiento_iva"],
            alicuota_iva=base["alicuota_iva"],
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            descuento=descuento,
        )
        linea = ComprobanteVentaLinea(
            comprobante=comprobante,
            numero_linea=indice,
            item=base["item"],
            descripcion=base["descripcion"],
            unidad_medida=base["unidad_medida"],
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            descuento_porcentaje=descuento,
            tratamiento_iva=base["tratamiento_iva"],
            alicuota_iva=base["alicuota_iva"],
            **calculos,
        )
        linea.full_clean()
        linea.save()
        creadas.append(linea)
    return creadas


def _recalcular_totales(comprobante):
    lineas = list(comprobante.lineas.select_related("alicuota_iva"))
    comprobante.subtotal_gravado = sum(
        (linea.subtotal_gravado for linea in lineas),
        Decimal("0.00"),
    )
    comprobante.subtotal_no_gravado = sum(
        (linea.subtotal_no_gravado for linea in lineas),
        Decimal("0.00"),
    )
    comprobante.subtotal_exento = sum(
        (linea.subtotal_exento for linea in lineas),
        Decimal("0.00"),
    )
    comprobante.total_iva = sum(
        (linea.iva_importe for linea in lineas),
        Decimal("0.00"),
    )
    comprobante.total_tributos = sum(
        (tributo.importe for tributo in comprobante.tributos.all()),
        Decimal("0.00"),
    )
    comprobante.total = (
        comprobante.subtotal_gravado
        + comprobante.subtotal_no_gravado
        + comprobante.subtotal_exento
        + comprobante.total_iva
        + comprobante.total_tributos
    )
    comprobante.full_clean()
    comprobante.save(
        update_fields=[
            "subtotal_gravado",
            "subtotal_no_gravado",
            "subtotal_exento",
            "total_iva",
            "total_tributos",
            "total",
            "actualizado_en",
        ]
    )

    ComprobanteVentaIVA.objects.filter(comprobante=comprobante).delete()
    totales = {}
    for linea in lineas:
        if not linea.alicuota_iva_id:
            continue
        total = totales.setdefault(
            linea.alicuota_iva_id,
            {
                "alicuota_iva": linea.alicuota_iva,
                "base_imponible": Decimal("0.00"),
                "importe_iva": Decimal("0.00"),
            },
        )
        total["base_imponible"] += linea.subtotal_gravado
        total["importe_iva"] += linea.iva_importe

    for total in totales.values():
        ComprobanteVentaIVA.objects.create(
            comprobante=comprobante,
            alicuota_iva=total["alicuota_iva"],
            base_imponible=total["base_imponible"],
            importe_iva=total["importe_iva"],
        )
    return comprobante


@transaction.atomic
def crear_borrador_venta(
    *,
    empresa,
    sucursal,
    punto_venta,
    tipo_comprobante,
    fecha,
    fecha_vencimiento,
    cliente,
    lineas,
    observaciones="",
    request=None,
):
    empresa = _empresa_activa(empresa)
    sucursal = _sucursal_activa(empresa=empresa, sucursal=sucursal)
    punto_venta = _punto_venta_activo(
        empresa=empresa,
        sucursal=sucursal,
        punto_venta=punto_venta,
    )
    tipo_comprobante = _tipo_comprobante_activo(tipo_comprobante)
    cliente = _cliente_activo(empresa=empresa, cliente=cliente)

    comprobante = ComprobanteVenta(
        empresa=empresa,
        sucursal=sucursal,
        punto_venta=punto_venta,
        tipo_comprobante=tipo_comprobante,
        fecha=fecha,
        fecha_vencimiento=fecha_vencimiento,
        cliente=cliente,
        estado=ComprobanteVenta.Estado.BORRADOR,
        observaciones=observaciones or "",
        **_snapshot_cliente(cliente),
    )
    comprobante.full_clean()
    comprobante.save()
    _crear_lineas(comprobante=comprobante, lineas=lineas)
    comprobante = _recalcular_totales(comprobante)

    _auditar(
        empresa=empresa,
        objeto=comprobante,
        accion=Auditoria.Accion.INSERT,
        anteriores=None,
        nuevos=datos_comprobante_venta(comprobante),
        request=request,
    )
    return comprobante


@transaction.atomic
def validar_comprobante_venta(*, empresa, comprobante, request=None):
    empresa = _empresa_activa(empresa)
    comprobante = (
        ComprobanteVenta.objects.select_for_update()
        .filter(
            pk=getattr(comprobante, "pk", None),
            empresa=empresa,
            estado=ComprobanteVenta.Estado.BORRADOR,
        )
        .first()
    )
    if comprobante is None:
        raise ValidationError(
            "El comprobante no pertenece a la empresa o no esta en borrador."
        )
    if not comprobante.lineas.exists():
        raise ValidationError("El comprobante requiere al menos una linea.")
    if comprobante.punto_venta_id is None:
        raise ValidationError("El comprobante requiere punto de venta.")
    if comprobante.tipo_comprobante.requiere_comprobante_asociado:
        if not comprobante.asociaciones.exists():
            raise ValidationError(
                "El tipo de comprobante requiere comprobante asociado."
            )

    anteriores = datos_comprobante_venta(comprobante)
    comprobante = _recalcular_totales(comprobante)
    comprobante.estado = ComprobanteVenta.Estado.VALIDADO
    comprobante.full_clean()
    comprobante.save(update_fields=["estado", "actualizado_en"])
    _auditar(
        empresa=empresa,
        objeto=comprobante,
        accion=Auditoria.Accion.UPDATE,
        anteriores=anteriores,
        nuevos=datos_comprobante_venta(comprobante),
        request=request,
    )
    return comprobante


@transaction.atomic
def anular_comprobante_venta(*, empresa, comprobante, request=None):
    empresa = _empresa_activa(empresa)
    comprobante = (
        ComprobanteVenta.objects.select_for_update()
        .filter(
            pk=getattr(comprobante, "pk", None),
            empresa=empresa,
        )
        .exclude(estado=ComprobanteVenta.Estado.ANULADO)
        .first()
    )
    if comprobante is None:
        raise ValidationError(
            "El comprobante no pertenece a la empresa o ya esta anulado."
        )
    if comprobante.estado == ComprobanteVenta.Estado.EMITIDO:
        raise ValidationError(
            "Un comprobante emitido no se anula en forma destructiva."
        )

    anteriores = datos_comprobante_venta(comprobante)
    comprobante.estado = ComprobanteVenta.Estado.ANULADO
    comprobante.full_clean()
    comprobante.save(update_fields=["estado", "actualizado_en"])
    _auditar(
        empresa=empresa,
        objeto=comprobante,
        accion=Auditoria.Accion.UPDATE,
        anteriores=anteriores,
        nuevos=datos_comprobante_venta(comprobante),
        request=request,
    )
    return comprobante
