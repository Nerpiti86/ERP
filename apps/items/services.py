from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.nucleo.models import Auditoria, Empresa
from apps.terceros.models import Tercero, TerceroRol

from .models import (
    AlicuotaIVA,
    CategoriaItem,
    Item,
    ItemProveedor,
    Marca,
    UnidadMedida,
)


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

    if (
        item.se_compra
        and not bool(se_compra)
        and item.relaciones_proveedores.filter(activo=True).exists()
    ):
        raise ValidationError(
            {
                "se_compra": (
                    "Primero inactivá las relaciones activas con proveedores."
                )
            }
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
def reactivar_item(*, empresa, item, request=None):
    empresa = _empresa_activa(empresa)
    item = (
        Item.objects.select_for_update()
        .filter(
            pk=getattr(item, "pk", None),
            empresa=empresa,
            activo=False,
        )
        .first()
    )
    if item is None:
        raise ValidationError(
            "El ítem no pertenece a la empresa activa o ya está activo."
        )

    anteriores = datos_item(item)
    item.activo = True
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


def datos_categoria(categoria):
    return {
        "empresa_id": categoria.empresa_id,
        "codigo": categoria.codigo,
        "nombre": categoria.nombre,
        "descripcion": categoria.descripcion,
        "activo": categoria.activo,
    }


def datos_marca(marca):
    return {
        "empresa_id": marca.empresa_id,
        "codigo": marca.codigo,
        "nombre": marca.nombre,
        "activo": marca.activo,
    }


def _datos_catalogo(catalogo):
    if isinstance(catalogo, CategoriaItem):
        return datos_categoria(catalogo)
    return datos_marca(catalogo)


def _catalogo_empresa_editable(modelo, *, empresa, catalogo, etiqueta):
    bloqueado = (
        modelo.objects.select_for_update()
        .filter(
            pk=getattr(catalogo, "pk", None),
            empresa=empresa,
            activo=True,
        )
        .first()
    )
    if bloqueado is None:
        raise ValidationError(
            f"La {etiqueta} no pertenece a la empresa activa o está inactiva."
        )
    return bloqueado


@transaction.atomic
def crear_categoria(
    *,
    empresa,
    codigo,
    nombre,
    descripcion,
    request=None,
):
    empresa = _empresa_activa(empresa)
    categoria = CategoriaItem(
        empresa=empresa,
        codigo=codigo,
        nombre=nombre,
        descripcion=descripcion or "",
        activo=True,
    )
    categoria.full_clean()
    categoria.save()
    _auditar(
        empresa=empresa,
        objeto=categoria,
        accion=Auditoria.Accion.INSERT,
        anteriores=None,
        nuevos=datos_categoria(categoria),
        request=request,
    )
    return categoria


@transaction.atomic
def actualizar_categoria(
    *,
    empresa,
    categoria,
    nombre,
    descripcion,
    request=None,
):
    empresa = _empresa_activa(empresa)
    categoria = _catalogo_empresa_editable(
        CategoriaItem,
        empresa=empresa,
        catalogo=categoria,
        etiqueta="categoría",
    )
    anteriores = datos_categoria(categoria)
    categoria.nombre = nombre
    categoria.descripcion = descripcion or ""
    categoria.full_clean()
    categoria.save()
    _auditar(
        empresa=empresa,
        objeto=categoria,
        accion=Auditoria.Accion.UPDATE,
        anteriores=anteriores,
        nuevos=datos_categoria(categoria),
        request=request,
    )
    return categoria


@transaction.atomic
def inactivar_categoria(*, empresa, categoria, request=None):
    empresa = _empresa_activa(empresa)
    categoria = _catalogo_empresa_editable(
        CategoriaItem,
        empresa=empresa,
        catalogo=categoria,
        etiqueta="categoría",
    )
    if categoria.items.filter(activo=True).exists():
        raise ValidationError(
            "No se puede inactivar una categoría utilizada por ítems activos."
        )

    anteriores = datos_categoria(categoria)
    categoria.activo = False
    categoria.full_clean()
    categoria.save(update_fields=["activo", "actualizado_en"])
    _auditar(
        empresa=empresa,
        objeto=categoria,
        accion=Auditoria.Accion.UPDATE,
        anteriores=anteriores,
        nuevos=datos_categoria(categoria),
        request=request,
    )
    return categoria


@transaction.atomic
def crear_marca(*, empresa, codigo, nombre, request=None):
    empresa = _empresa_activa(empresa)
    marca = Marca(
        empresa=empresa,
        codigo=codigo,
        nombre=nombre,
        activo=True,
    )
    marca.full_clean()
    marca.save()
    _auditar(
        empresa=empresa,
        objeto=marca,
        accion=Auditoria.Accion.INSERT,
        anteriores=None,
        nuevos=datos_marca(marca),
        request=request,
    )
    return marca


@transaction.atomic
def actualizar_marca(
    *,
    empresa,
    marca,
    nombre,
    request=None,
):
    empresa = _empresa_activa(empresa)
    marca = _catalogo_empresa_editable(
        Marca,
        empresa=empresa,
        catalogo=marca,
        etiqueta="marca",
    )
    anteriores = datos_marca(marca)
    marca.nombre = nombre
    marca.full_clean()
    marca.save()
    _auditar(
        empresa=empresa,
        objeto=marca,
        accion=Auditoria.Accion.UPDATE,
        anteriores=anteriores,
        nuevos=datos_marca(marca),
        request=request,
    )
    return marca


@transaction.atomic
def inactivar_marca(*, empresa, marca, request=None):
    empresa = _empresa_activa(empresa)
    marca = _catalogo_empresa_editable(
        Marca,
        empresa=empresa,
        catalogo=marca,
        etiqueta="marca",
    )
    if marca.items.filter(activo=True).exists():
        raise ValidationError(
            "No se puede inactivar una marca utilizada por ítems activos."
        )

    anteriores = datos_marca(marca)
    marca.activo = False
    marca.full_clean()
    marca.save(update_fields=["activo", "actualizado_en"])
    _auditar(
        empresa=empresa,
        objeto=marca,
        accion=Auditoria.Accion.UPDATE,
        anteriores=anteriores,
        nuevos=datos_marca(marca),
        request=request,
    )
    return marca

def _valor_json(valor):
    return valor.isoformat() if hasattr(valor, "isoformat") else valor


def datos_item_proveedor(relacion):
    return {
        "empresa_id": relacion.empresa_id,
        "item_id": relacion.item_id,
        "proveedor_id": relacion.proveedor_id,
        "codigo_proveedor": relacion.codigo_proveedor,
        "activo": relacion.activo,
        "fecha_alta": _valor_json(relacion.fecha_alta),
        "fecha_baja": _valor_json(relacion.fecha_baja),
        "observaciones": relacion.observaciones,
        "disponible_operativamente": relacion.disponible_operativamente,
        "motivo_indisponibilidad": relacion.motivo_indisponibilidad,
    }


def _fecha_baja_relacion(fecha_alta):
    hoy = timezone.localdate()
    return fecha_alta if fecha_alta and hoy < fecha_alta else hoy


def _item_comprable(*, empresa, item):
    encontrado = (
        Item.objects.select_for_update()
        .filter(
            pk=getattr(item, "pk", None),
            empresa=empresa,
            activo=True,
            se_compra=True,
        )
        .first()
    )
    if encontrado is None:
        raise ValidationError(
            {
                "item": (
                    "El ítem no pertenece a la empresa activa, está inactivo "
                    "o no está habilitado para compra."
                )
            }
        )
    return encontrado


def _proveedor_valido(*, empresa, proveedor):
    encontrado = (
        Tercero.objects.select_for_update()
        .filter(
            pk=getattr(proveedor, "pk", None),
            empresa=empresa,
            activo=True,
        )
        .first()
    )
    if encontrado is None:
        raise ValidationError(
            {
                "proveedor": (
                    "El proveedor no pertenece a la empresa activa "
                    "o está inactivo."
                )
            }
        )

    rol = (
        TerceroRol.objects.select_for_update()
        .filter(
            tercero=encontrado,
            rol=TerceroRol.Rol.PROVEEDOR,
            activo=True,
        )
        .first()
    )
    if rol is None:
        raise ValidationError(
            {"proveedor": "El tercero no tiene un rol PROVEEDOR activo."}
        )
    return encontrado


def _relacion_item_proveedor(*, empresa, relacion, activo=None):
    consulta = (
        ItemProveedor.objects.select_for_update()
        .select_related("empresa", "item", "proveedor")
        .filter(
            pk=getattr(relacion, "pk", None),
            empresa=empresa,
        )
    )
    if activo is not None:
        consulta = consulta.filter(activo=activo)

    encontrada = consulta.first()
    if encontrada is None:
        estado = (
            " o no coincide con el estado requerido"
            if activo is not None
            else ""
        )
        raise ValidationError(
            f"La relación no pertenece a la empresa activa{estado}."
        )
    return encontrada


def _guardar_relacion(relacion):
    try:
        relacion.full_clean()
        relacion.save()
    except IntegrityError as error:
        raise ValidationError(
            "La relación o el código del proveedor ya están registrados."
        ) from error
    return relacion


@transaction.atomic
def crear_item_proveedor(
    *,
    empresa,
    item,
    proveedor,
    codigo_proveedor,
    observaciones,
    request=None,
):
    empresa = _empresa_activa(empresa)
    item = _item_comprable(empresa=empresa, item=item)
    proveedor = _proveedor_valido(empresa=empresa, proveedor=proveedor)

    existente = (
        ItemProveedor.objects.select_for_update()
        .filter(empresa=empresa, item=item, proveedor=proveedor)
        .first()
    )
    if existente is not None:
        accion = "reactivarla" if not existente.activo else "editarla"
        raise ValidationError(
            {
                "proveedor": (
                    "Ya existe una relación histórica con este proveedor; "
                    f"corresponde {accion}."
                )
            }
        )

    relacion = ItemProveedor(
        empresa=empresa,
        item=item,
        proveedor=proveedor,
        codigo_proveedor=codigo_proveedor or "",
        observaciones=observaciones or "",
        activo=True,
        fecha_alta=timezone.localdate(),
        fecha_baja=None,
    )
    _guardar_relacion(relacion)
    _auditar(
        empresa=empresa,
        objeto=relacion,
        accion=Auditoria.Accion.INSERT,
        anteriores=None,
        nuevos=datos_item_proveedor(relacion),
        request=request,
    )
    return relacion


@transaction.atomic
def actualizar_item_proveedor(
    *,
    empresa,
    relacion,
    codigo_proveedor,
    observaciones,
    request=None,
):
    empresa = _empresa_activa(empresa)
    relacion = _relacion_item_proveedor(
        empresa=empresa,
        relacion=relacion,
        activo=True,
    )
    _item_comprable(empresa=empresa, item=relacion.item)
    _proveedor_valido(empresa=empresa, proveedor=relacion.proveedor)

    anteriores = datos_item_proveedor(relacion)
    relacion.codigo_proveedor = codigo_proveedor or ""
    relacion.observaciones = observaciones or ""
    _guardar_relacion(relacion)
    _auditar(
        empresa=empresa,
        objeto=relacion,
        accion=Auditoria.Accion.UPDATE,
        anteriores=anteriores,
        nuevos=datos_item_proveedor(relacion),
        request=request,
    )
    return relacion


@transaction.atomic
def inactivar_item_proveedor(*, empresa, relacion, request=None):
    empresa = _empresa_activa(empresa)
    relacion = _relacion_item_proveedor(
        empresa=empresa,
        relacion=relacion,
        activo=True,
    )
    anteriores = datos_item_proveedor(relacion)
    relacion.activo = False
    relacion.fecha_baja = _fecha_baja_relacion(relacion.fecha_alta)
    _guardar_relacion(relacion)
    _auditar(
        empresa=empresa,
        objeto=relacion,
        accion=Auditoria.Accion.UPDATE,
        anteriores=anteriores,
        nuevos=datos_item_proveedor(relacion),
        request=request,
    )
    return relacion


@transaction.atomic
def reactivar_item_proveedor(*, empresa, relacion, request=None):
    empresa = _empresa_activa(empresa)
    relacion = _relacion_item_proveedor(
        empresa=empresa,
        relacion=relacion,
        activo=False,
    )
    _item_comprable(empresa=empresa, item=relacion.item)
    _proveedor_valido(empresa=empresa, proveedor=relacion.proveedor)

    anteriores = datos_item_proveedor(relacion)
    relacion.activo = True
    relacion.fecha_baja = None
    _guardar_relacion(relacion)
    _auditar(
        empresa=empresa,
        objeto=relacion,
        accion=Auditoria.Accion.UPDATE,
        anteriores=anteriores,
        nuevos=datos_item_proveedor(relacion),
        request=request,
    )
    return relacion
