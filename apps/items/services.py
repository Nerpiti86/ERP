from django.core.exceptions import ValidationError
from django.db import transaction

from apps.nucleo.models import Auditoria, Empresa

from .models import AlicuotaIVA, CategoriaItem, Item, Marca, UnidadMedida


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


def datos_item(item):
    return {
        "empresa_id": item.empresa_id,
        "codigo": item.codigo,
        "nombre": item.nombre,
        "descripcion": item.descripcion,
        "tipo": item.tipo,
        "categoria_id": item.categoria_id,
        "marca_id": item.marca_id,
        "unidad_medida_id": item.unidad_medida_id,
        "se_compra": item.se_compra,
        "se_vende": item.se_vende,
        "controla_stock": item.controla_stock,
        "tratamiento_iva": item.tratamiento_iva,
        "alicuota_iva_id": item.alicuota_iva_id,
        "activo": item.activo,
        "observaciones": item.observaciones,
    }


def _empresa_activa(empresa):
    bloqueada = (
        Empresa.objects.select_for_update()
        .filter(pk=getattr(empresa, "pk", None), activa=True)
        .first()
    )
    if bloqueada is None:
        raise ValidationError("La empresa no existe o está inactiva.")
    return bloqueada


def _catalogo_empresa_activo(modelo, *, empresa, objeto, campo):
    if objeto is None:
        return None

    encontrado = (
        modelo.objects.select_for_update()
        .filter(
            pk=getattr(objeto, "pk", None),
            empresa=empresa,
            activo=True,
        )
        .first()
    )
    if encontrado is None:
        raise ValidationError(
            {campo: "El valor no pertenece a la empresa activa o está inactivo."}
        )
    return encontrado


def _catalogo_global_activo(modelo, *, objeto, campo):
    encontrado = (
        modelo.objects.select_for_update()
        .filter(pk=getattr(objeto, "pk", None), activo=True)
        .first()
    )
    if encontrado is None:
        raise ValidationError({campo: "El valor seleccionado está inactivo o no existe."})
    return encontrado


def _resolver_alicuota(*, tratamiento_iva, alicuota_iva):
    if tratamiento_iva == Item.TratamientoIVA.GRAVADO:
        if alicuota_iva is None:
            raise ValidationError(
                {"alicuota_iva": "Un ítem gravado requiere alícuota de IVA."}
            )
        return _catalogo_global_activo(
            AlicuotaIVA,
            objeto=alicuota_iva,
            campo="alicuota_iva",
        )

    if alicuota_iva is not None:
        raise ValidationError(
            {
                "alicuota_iva": (
                    "Los ítems exentos o no gravados no deben informar "
                    "alícuota de IVA."
                )
            }
        )
    return None


def _resolver_catalogos(
    *,
    empresa,
    categoria,
    marca,
    unidad_medida,
    tratamiento_iva,
    alicuota_iva,
):
    categoria = _catalogo_empresa_activo(
        CategoriaItem,
        empresa=empresa,
        objeto=categoria,
        campo="categoria",
    )
    marca = _catalogo_empresa_activo(
        Marca,
        empresa=empresa,
        objeto=marca,
        campo="marca",
    )
    unidad_medida = _catalogo_global_activo(
        UnidadMedida,
        objeto=unidad_medida,
        campo="unidad_medida",
    )
    alicuota_iva = _resolver_alicuota(
        tratamiento_iva=tratamiento_iva,
        alicuota_iva=alicuota_iva,
    )
    return categoria, marca, unidad_medida, alicuota_iva


@transaction.atomic
def crear_item(
    *,
    empresa,
    codigo,
    nombre,
    descripcion,
    tipo,
    categoria,
    marca,
    unidad_medida,
    se_compra,
    se_vende,
    controla_stock,
    tratamiento_iva,
    alicuota_iva,
    observaciones,
    request=None,
):
    empresa = _empresa_activa(empresa)
    categoria, marca, unidad_medida, alicuota_iva = _resolver_catalogos(
        empresa=empresa,
        categoria=categoria,
        marca=marca,
        unidad_medida=unidad_medida,
        tratamiento_iva=tratamiento_iva,
        alicuota_iva=alicuota_iva,
    )

    item = Item(
        empresa=empresa,
        codigo=codigo,
        nombre=nombre,
        descripcion=descripcion or "",
        tipo=tipo,
        categoria=categoria,
        marca=marca,
        unidad_medida=unidad_medida,
        se_compra=bool(se_compra),
        se_vende=bool(se_vende),
        controla_stock=bool(controla_stock),
        tratamiento_iva=tratamiento_iva,
        alicuota_iva=alicuota_iva,
        activo=True,
        observaciones=observaciones or "",
    )
    item.full_clean()
    item.save()

    _auditar(
        empresa=empresa,
        objeto=item,
        accion=Auditoria.Accion.INSERT,
        anteriores=None,
        nuevos=datos_item(item),
        request=request,
    )
    return item


@transaction.atomic
def actualizar_item(
    *,
    empresa,
    item,
    nombre,
    descripcion,
    tipo,
    categoria,
    marca,
    unidad_medida,
    se_compra,
    se_vende,
    controla_stock,
    tratamiento_iva,
    alicuota_iva,
    observaciones,
    request=None,
):
    empresa = _empresa_activa(empresa)
    item = (
        Item.objects.select_for_update()
        .filter(
            pk=getattr(item, "pk", None),
            empresa=empresa,
            activo=True,
        )
        .first()
    )
    if item is None:
        raise ValidationError(
            "El ítem no pertenece a la empresa activa o está inactivo."
        )

    categoria, marca, unidad_medida, alicuota_iva = _resolver_catalogos(
        empresa=empresa,
        categoria=categoria,
        marca=marca,
        unidad_medida=unidad_medida,
        tratamiento_iva=tratamiento_iva,
        alicuota_iva=alicuota_iva,
    )

    anteriores = datos_item(item)
    item.nombre = nombre
    item.descripcion = descripcion or ""
    item.tipo = tipo
    item.categoria = categoria
    item.marca = marca
    item.unidad_medida = unidad_medida
    item.se_compra = bool(se_compra)
    item.se_vende = bool(se_vende)
    item.controla_stock = bool(controla_stock)
    item.tratamiento_iva = tratamiento_iva
    item.alicuota_iva = alicuota_iva
    item.observaciones = observaciones or ""
    item.full_clean()
    item.save()

    _auditar(
        empresa=empresa,
        objeto=item,
        accion=Auditoria.Accion.UPDATE,
        anteriores=anteriores,
        nuevos=datos_item(item),
        request=request,
    )
    return item


@transaction.atomic
def inactivar_item(*, empresa, item, request=None):
    empresa = _empresa_activa(empresa)
    item = (
        Item.objects.select_for_update()
        .filter(
            pk=getattr(item, "pk", None),
            empresa=empresa,
            activo=True,
        )
        .first()
    )
    if item is None:
        raise ValidationError(
            "El ítem no pertenece a la empresa activa o ya está inactivo."
        )

    anteriores = datos_item(item)
    item.activo = False
    item.full_clean()
    item.save(update_fields=["activo", "actualizado_en"])

    _auditar(
        empresa=empresa,
        objeto=item,
        accion=Auditoria.Accion.UPDATE,
        anteriores=anteriores,
        nuevos=datos_item(item),
        request=request,
    )
    return item
