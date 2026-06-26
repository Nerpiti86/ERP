from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.nucleo.models import Auditoria, Empresa

from .models import (
    CondicionIVA,
    ContactoTercero,
    DomicilioTercero,
    GrupoTercero,
    Tercero,
    TerceroRol,
    TipoDocumento,
)


def _valor_json(valor):
    return valor.isoformat() if hasattr(valor, "isoformat") else valor


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


def datos_tercero(tercero):
    return {
        "empresa_id": tercero.empresa_id,
        "codigo": tercero.codigo,
        "tipo_persona": tercero.tipo_persona,
        "tipo_documento_id": tercero.tipo_documento_id,
        "numero_documento": tercero.numero_documento,
        "denominacion": tercero.denominacion,
        "nombre_fantasia": tercero.nombre_fantasia,
        "condicion_iva_id": tercero.condicion_iva_id,
        "telefono": tercero.telefono,
        "email": tercero.email,
        "sitio_web": tercero.sitio_web,
        "fecha_alta": _valor_json(tercero.fecha_alta),
        "fecha_baja": _valor_json(tercero.fecha_baja),
        "activo": tercero.activo,
        "observaciones": tercero.observaciones,
        "roles": list(
            tercero.roles.filter(activo=True)
            .order_by("rol")
            .values_list("rol", flat=True)
        ),
        "grupos_roles": {
            relacion.rol: relacion.grupo_id
            for relacion in tercero.roles.filter(activo=True).order_by("rol")
        },
    }


def datos_domicilio(domicilio):
    return {
        "tercero_id": domicilio.tercero_id,
        "tipo": domicilio.tipo,
        "nombre": domicilio.nombre,
        "calle": domicilio.calle,
        "numero": domicilio.numero,
        "sector": domicilio.sector,
        "torre": domicilio.torre,
        "piso": domicilio.piso,
        "departamento": domicilio.departamento,
        "barrio": domicilio.barrio,
        "localidad": domicilio.localidad,
        "codigo_postal": domicilio.codigo_postal,
        "partido_departamento": domicilio.partido_departamento,
        "provincia": domicilio.provincia,
        "pais": domicilio.pais,
        "principal": domicilio.principal,
        "activo": domicilio.activo,
        "fecha_alta": _valor_json(domicilio.fecha_alta),
        "fecha_baja": _valor_json(domicilio.fecha_baja),
        "observaciones": domicilio.observaciones,
    }


def datos_contacto(contacto):
    return {
        "tercero_id": contacto.tercero_id,
        "nombre": contacto.nombre,
        "cargo": contacto.cargo,
        "area": contacto.area,
        "telefono": contacto.telefono,
        "email": contacto.email,
        "principal": contacto.principal,
        "activo": contacto.activo,
        "fecha_alta": _valor_json(contacto.fecha_alta),
        "fecha_baja": _valor_json(contacto.fecha_baja),
        "observaciones": contacto.observaciones,
    }


def _fecha_baja(fecha_alta):
    hoy = timezone.localdate()
    return fecha_alta if fecha_alta and hoy < fecha_alta else hoy


def _empresa_activa(empresa):
    bloqueada = (
        Empresa.objects.select_for_update()
        .filter(pk=empresa.pk, activa=True)
        .first()
    )
    if bloqueada is None:
        raise ValidationError("La empresa no existe o está inactiva.")
    return bloqueada


def _catalogo_activo(modelo, objeto, campo):
    encontrado = (
        modelo.objects.select_for_update()
        .filter(pk=objeto.pk, activo=True)
        .first()
    )
    if encontrado is None:
        raise ValidationError({campo: "El valor seleccionado está inactivo."})
    return encontrado


GRUPOS_GENERALES = {
    TerceroRol.Rol.CLIENTE: {
        "codigo": "CLIENTES_GENERALES",
        "nombre": "Clientes generales",
    },
    TerceroRol.Rol.PROVEEDOR: {
        "codigo": "PROVEEDORES_GENERALES",
        "nombre": "Proveedores generales",
    },
}


def datos_grupo_tercero(grupo):
    return {
        "empresa_id": grupo.empresa_id,
        "tipo": grupo.tipo,
        "codigo": grupo.codigo,
        "nombre": grupo.nombre,
        "observaciones": grupo.observaciones,
        "activo": grupo.activo,
    }


@transaction.atomic
def asegurar_grupos_generales(empresa):
    empresa = _empresa_activa(empresa)
    grupos = {}

    for tipo, datos in GRUPOS_GENERALES.items():
        grupo, _ = GrupoTercero.objects.get_or_create(
            empresa=empresa,
            tipo=tipo,
            codigo=datos["codigo"],
            defaults={
                "nombre": datos["nombre"],
                "observaciones": "Grupo general creado por el sistema.",
                "activo": True,
            },
        )
        if not grupo.activo:
            grupo.activo = True
            grupo.save(update_fields=["activo", "actualizado_en"])
        grupos[tipo] = grupo

    return grupos


def _grupo_editable(*, empresa, grupo, tipo=None):
    consulta = GrupoTercero.objects.select_for_update().filter(
        pk=getattr(grupo, "pk", None),
        empresa=empresa,
        activo=True,
    )
    if tipo is not None:
        consulta = consulta.filter(tipo=tipo)

    bloqueado = consulta.first()
    if bloqueado is None:
        raise ValidationError(
            "El grupo no pertenece a la empresa activa, "
            "no coincide con el tipo o está inactivo."
        )
    return bloqueado


@transaction.atomic
def crear_grupo_tercero(
    *,
    empresa,
    tipo,
    codigo,
    nombre,
    observaciones,
    request=None,
):
    empresa = _empresa_activa(empresa)
    grupo = GrupoTercero(
        empresa=empresa,
        tipo=tipo,
        codigo=codigo,
        nombre=nombre,
        observaciones=observaciones or "",
        activo=True,
    )
    grupo.full_clean()
    grupo.save()
    _auditar(
        empresa=empresa,
        objeto=grupo,
        accion=Auditoria.Accion.INSERT,
        anteriores=None,
        nuevos=datos_grupo_tercero(grupo),
        request=request,
    )
    return grupo


@transaction.atomic
def actualizar_grupo_tercero(
    *,
    empresa,
    grupo,
    nombre,
    observaciones,
    request=None,
):
    empresa = _empresa_activa(empresa)
    grupo = _grupo_editable(
        empresa=empresa,
        grupo=grupo,
        tipo=grupo.tipo,
    )
    anteriores = datos_grupo_tercero(grupo)
    grupo.nombre = nombre
    grupo.observaciones = observaciones or ""
    grupo.full_clean()
    grupo.save()
    _auditar(
        empresa=empresa,
        objeto=grupo,
        accion=Auditoria.Accion.UPDATE,
        anteriores=anteriores,
        nuevos=datos_grupo_tercero(grupo),
        request=request,
    )
    return grupo


@transaction.atomic
def inactivar_grupo_tercero(*, empresa, grupo, request=None):
    empresa = _empresa_activa(empresa)
    grupo = _grupo_editable(
        empresa=empresa,
        grupo=grupo,
        tipo=grupo.tipo,
    )

    general = GRUPOS_GENERALES.get(grupo.tipo)
    if general and grupo.codigo == general["codigo"]:
        raise ValidationError(
            "El grupo general del tipo no puede inactivarse."
        )

    if grupo.roles_terceros.filter(activo=True).exists():
        raise ValidationError(
            "No se puede inactivar un grupo utilizado por roles activos."
        )

    anteriores = datos_grupo_tercero(grupo)
    grupo.activo = False
    grupo.full_clean()
    grupo.save(update_fields=["activo", "actualizado_en"])
    _auditar(
        empresa=empresa,
        objeto=grupo,
        accion=Auditoria.Accion.UPDATE,
        anteriores=anteriores,
        nuevos=datos_grupo_tercero(grupo),
        request=request,
    )
    return grupo


def _roles_validos(roles):
    validos = set(TerceroRol.Rol.values)
    seleccionados = {
        str(rol).strip().upper()
        for rol in (roles or ())
        if str(rol).strip()
    }
    desconocidos = seleccionados - validos

    if desconocidos:
        raise ValidationError(
            {"roles": "Roles desconocidos: " + ", ".join(sorted(desconocidos))}
        )
    if not seleccionados:
        raise ValidationError(
            {"roles": "El tercero debe ser cliente, proveedor o ambos."}
        )

    return seleccionados


def _siguiente_codigo(empresa):
    maximo = 0
    codigos = (
        Tercero.objects.filter(
            empresa=empresa,
            codigo__regex=r"^T[0-9]{6}$",
        )
        .order_by("codigo")
        .values_list("codigo", flat=True)
    )
    for codigo in codigos:
        maximo = max(maximo, int(codigo[1:]))

    if maximo >= 999999:
        raise ValidationError(
            {"codigo": "Se agotó la numeración automática de terceros."}
        )
    return f"T{maximo + 1:06d}"


def _resolver_grupos_por_rol(
    *,
    tercero,
    roles,
    grupos_por_rol=None,
):
    seleccionados = _roles_validos(roles)
    informados = {
        str(rol).strip().upper(): grupo
        for rol, grupo in (grupos_por_rol or {}).items()
    }

    sobrantes = set(informados) - seleccionados
    if sobrantes:
        raise ValidationError(
            {
                "grupos": (
                    "Se informaron grupos para roles no seleccionados: "
                    + ", ".join(sorted(sobrantes))
                )
            }
        )

    generales = asegurar_grupos_generales(tercero.empresa)
    resueltos = {}

    for rol in seleccionados:
        grupo = informados.get(rol) or generales[rol]
        encontrado = (
            GrupoTercero.objects.select_for_update()
            .filter(
                pk=getattr(grupo, "pk", None),
                empresa=tercero.empresa,
                tipo=rol,
                activo=True,
            )
            .first()
        )
        if encontrado is None:
            raise ValidationError(
                {
                    "grupos": (
                        f"El grupo del rol {rol} no pertenece a la "
                        "empresa, no coincide con el tipo o está inactivo."
                    )
                }
            )
        resueltos[rol] = encontrado

    return seleccionados, resueltos


def _sincronizar_roles(
    *,
    tercero,
    roles,
    grupos_por_rol=None,
):
    seleccionados, grupos = _resolver_grupos_por_rol(
        tercero=tercero,
        roles=roles,
        grupos_por_rol=grupos_por_rol,
    )
    actuales = {
        relacion.rol: relacion
        for relacion in (
            TerceroRol.objects.select_for_update()
            .filter(tercero=tercero, activo=True)
            .select_related("grupo")
            .order_by("pk")
        )
    }

    for rol, relacion in actuales.items():
        if rol not in seleccionados:
            relacion.activo = False
            relacion.fecha_baja = _fecha_baja(relacion.fecha_alta)
            relacion.full_clean()
            relacion.save(
                update_fields=["activo", "fecha_baja", "actualizado_en"]
            )
            continue

        grupo = grupos[rol]
        if relacion.grupo_id != grupo.pk:
            relacion.grupo = grupo
            relacion.full_clean()
            relacion.save(update_fields=["grupo", "actualizado_en"])

    for rol in sorted(seleccionados - set(actuales)):
        relacion = TerceroRol(
            tercero=tercero,
            grupo=grupos[rol],
            rol=rol,
            fecha_alta=timezone.localdate(),
            activo=True,
        )
        relacion.full_clean()
        relacion.save()


@transaction.atomic
def crear_tercero(
    *,
    empresa,
    codigo,
    tipo_persona,
    tipo_documento,
    numero_documento,
    denominacion,
    nombre_fantasia,
    condicion_iva,
    telefono,
    email,
    sitio_web,
    fecha_alta,
    roles,
    observaciones,
    grupos_por_rol=None,
    request=None,
):
    empresa = _empresa_activa(empresa)
    tipo_documento = _catalogo_activo(
        TipoDocumento,
        tipo_documento,
        "tipo_documento",
    )
    condicion_iva = _catalogo_activo(
        CondicionIVA,
        condicion_iva,
        "condicion_iva",
    )
    roles = _roles_validos(roles)
    codigo = (codigo or "").strip().upper() or _siguiente_codigo(empresa)

    tercero = Tercero(
        empresa=empresa,
        codigo=codigo,
        tipo_persona=tipo_persona,
        tipo_documento=tipo_documento,
        numero_documento=numero_documento or "",
        denominacion=denominacion,
        nombre_fantasia=nombre_fantasia or "",
        condicion_iva=condicion_iva,
        telefono=telefono or "",
        email=email or "",
        sitio_web=sitio_web or "",
        fecha_alta=fecha_alta,
        fecha_baja=None,
        activo=True,
        observaciones=observaciones or "",
    )
    tercero.full_clean()
    tercero.save()
    _sincronizar_roles(
        tercero=tercero,
        roles=roles,
        grupos_por_rol=grupos_por_rol,
    )
    tercero.refresh_from_db()

    _auditar(
        empresa=empresa,
        objeto=tercero,
        accion=Auditoria.Accion.INSERT,
        anteriores=None,
        nuevos=datos_tercero(tercero),
        request=request,
    )
    return tercero


@transaction.atomic
def actualizar_tercero(
    *,
    empresa,
    tercero,
    tipo_persona,
    tipo_documento,
    numero_documento,
    denominacion,
    nombre_fantasia,
    condicion_iva,
    telefono,
    email,
    sitio_web,
    fecha_alta,
    roles,
    observaciones,
    grupos_por_rol=None,
    request=None,
):
    empresa = _empresa_activa(empresa)
    tercero = (
        Tercero.objects.select_for_update()
        .filter(pk=tercero.pk, empresa=empresa, activo=True)
        .first()
    )
    if tercero is None:
        raise ValidationError(
            "El tercero no pertenece a la empresa activa o está inactivo."
        )

    anteriores = datos_tercero(tercero)
    tercero.tipo_documento = _catalogo_activo(
        TipoDocumento,
        tipo_documento,
        "tipo_documento",
    )
    tercero.condicion_iva = _catalogo_activo(
        CondicionIVA,
        condicion_iva,
        "condicion_iva",
    )
    tercero.tipo_persona = tipo_persona
    tercero.numero_documento = numero_documento or ""
    tercero.denominacion = denominacion
    tercero.nombre_fantasia = nombre_fantasia or ""
    tercero.telefono = telefono or ""
    tercero.email = email or ""
    tercero.sitio_web = sitio_web or ""
    tercero.fecha_alta = fecha_alta
    tercero.observaciones = observaciones or ""
    tercero.full_clean()
    tercero.save()
    _sincronizar_roles(
        tercero=tercero,
        roles=roles,
        grupos_por_rol=grupos_por_rol,
    )
    tercero.refresh_from_db()

    _auditar(
        empresa=empresa,
        objeto=tercero,
        accion=Auditoria.Accion.UPDATE,
        anteriores=anteriores,
        nuevos=datos_tercero(tercero),
        request=request,
    )
    return tercero


@transaction.atomic
def inactivar_tercero(*, empresa, tercero, request=None):
    empresa = _empresa_activa(empresa)
    tercero = (
        Tercero.objects.select_for_update()
        .filter(pk=tercero.pk, empresa=empresa, activo=True)
        .first()
    )
    if tercero is None:
        raise ValidationError(
            "El tercero no pertenece a la empresa activa o ya está inactivo."
        )

    anteriores = datos_tercero(tercero)
    baja = _fecha_baja(tercero.fecha_alta)
    ahora = timezone.now()

    TerceroRol.objects.select_for_update().filter(
        tercero=tercero,
        activo=True,
    ).update(activo=False, fecha_baja=baja, actualizado_en=ahora)
    DomicilioTercero.objects.select_for_update().filter(
        tercero=tercero,
        activo=True,
    ).update(
        activo=False,
        principal=False,
        fecha_baja=baja,
        actualizado_en=ahora,
    )
    ContactoTercero.objects.select_for_update().filter(
        tercero=tercero,
        activo=True,
    ).update(
        activo=False,
        principal=False,
        fecha_baja=baja,
        actualizado_en=ahora,
    )

    tercero.activo = False
    tercero.fecha_baja = baja
    tercero.full_clean()
    tercero.save(
        update_fields=["activo", "fecha_baja", "actualizado_en"]
    )
    _auditar(
        empresa=empresa,
        objeto=tercero,
        accion=Auditoria.Accion.UPDATE,
        anteriores=anteriores,
        nuevos=datos_tercero(tercero),
        request=request,
    )
    return tercero


def _tercero_activo(*, empresa, tercero):
    bloqueado = (
        Tercero.objects.select_for_update()
        .filter(pk=tercero.pk, empresa=empresa, activo=True)
        .first()
    )
    if bloqueado is None:
        raise ValidationError(
            "El tercero no pertenece a la empresa activa o está inactivo."
        )
    return bloqueado


def _desmarcar_domicilios(*, tercero, tipo, excluir_id=None):
    consulta = DomicilioTercero.objects.select_for_update().filter(
        tercero=tercero,
        tipo=tipo,
        activo=True,
        principal=True,
    )
    if excluir_id is not None:
        consulta = consulta.exclude(pk=excluir_id)
    consulta.update(principal=False, actualizado_en=timezone.now())


def _asegurar_domicilio_principal(*, tercero, tipo):
    if DomicilioTercero.objects.filter(
        tercero=tercero,
        tipo=tipo,
        activo=True,
        principal=True,
    ).exists():
        return

    domicilio = (
        DomicilioTercero.objects.select_for_update()
        .filter(tercero=tercero, tipo=tipo, activo=True)
        .order_by("fecha_alta", "pk")
        .first()
    )
    if domicilio is not None:
        domicilio.principal = True
        domicilio.full_clean()
        domicilio.save(
            update_fields=["principal", "actualizado_en"]
        )


@transaction.atomic
def crear_domicilio(*, empresa, tercero, request=None, **datos):
    empresa = _empresa_activa(empresa)
    tercero = _tercero_activo(empresa=empresa, tercero=tercero)
    tipo = datos["tipo"]
    existen = DomicilioTercero.objects.select_for_update().filter(
        tercero=tercero,
        tipo=tipo,
        activo=True,
    ).exists()
    principal = bool(datos["principal"]) or not existen

    if principal:
        _desmarcar_domicilios(tercero=tercero, tipo=tipo)

    domicilio = DomicilioTercero(
        tercero=tercero,
        activo=True,
        fecha_baja=None,
        **{**datos, "principal": principal},
    )
    domicilio.full_clean()
    domicilio.save()
    _auditar(
        empresa=empresa,
        objeto=domicilio,
        accion=Auditoria.Accion.INSERT,
        anteriores=None,
        nuevos=datos_domicilio(domicilio),
        request=request,
    )
    return domicilio


@transaction.atomic
def actualizar_domicilio(*, empresa, domicilio, request=None, **datos):
    empresa = _empresa_activa(empresa)
    domicilio = (
        DomicilioTercero.objects.select_for_update()
        .select_related("tercero")
        .filter(
            pk=domicilio.pk,
            tercero__empresa=empresa,
            tercero__activo=True,
            activo=True,
        )
        .first()
    )
    if domicilio is None:
        raise ValidationError(
            "El domicilio no pertenece a la empresa activa o está inactivo."
        )

    anteriores = datos_domicilio(domicilio)
    tipo_anterior = domicilio.tipo
    era_principal = domicilio.principal
    tipo_nuevo = datos["tipo"]
    otros = DomicilioTercero.objects.select_for_update().filter(
        tercero=domicilio.tercero,
        tipo=tipo_nuevo,
        activo=True,
    ).exclude(pk=domicilio.pk)
    principal = bool(datos["principal"]) or not otros.exists()

    if principal:
        _desmarcar_domicilios(
            tercero=domicilio.tercero,
            tipo=tipo_nuevo,
            excluir_id=domicilio.pk,
        )

    for campo, valor in datos.items():
        setattr(domicilio, campo, valor)
    domicilio.principal = principal
    domicilio.full_clean()
    domicilio.save()

    if era_principal and tipo_anterior != tipo_nuevo:
        _asegurar_domicilio_principal(
            tercero=domicilio.tercero,
            tipo=tipo_anterior,
        )
    _asegurar_domicilio_principal(
        tercero=domicilio.tercero,
        tipo=tipo_nuevo,
    )

    _auditar(
        empresa=empresa,
        objeto=domicilio,
        accion=Auditoria.Accion.UPDATE,
        anteriores=anteriores,
        nuevos=datos_domicilio(domicilio),
        request=request,
    )
    return domicilio


@transaction.atomic
def inactivar_domicilio(*, empresa, domicilio, request=None):
    empresa = _empresa_activa(empresa)
    domicilio = (
        DomicilioTercero.objects.select_for_update()
        .select_related("tercero")
        .filter(pk=domicilio.pk, tercero__empresa=empresa, activo=True)
        .first()
    )
    if domicilio is None:
        raise ValidationError(
            "El domicilio no pertenece a la empresa activa o ya está inactivo."
        )

    anteriores = datos_domicilio(domicilio)
    era_principal = domicilio.principal
    tipo = domicilio.tipo
    domicilio.activo = False
    domicilio.principal = False
    domicilio.fecha_baja = _fecha_baja(domicilio.fecha_alta)
    domicilio.full_clean()
    domicilio.save(
        update_fields=[
            "activo",
            "principal",
            "fecha_baja",
            "actualizado_en",
        ]
    )
    if era_principal:
        _asegurar_domicilio_principal(
            tercero=domicilio.tercero,
            tipo=tipo,
        )

    _auditar(
        empresa=empresa,
        objeto=domicilio,
        accion=Auditoria.Accion.UPDATE,
        anteriores=anteriores,
        nuevos=datos_domicilio(domicilio),
        request=request,
    )
    return domicilio


def _desmarcar_contactos(*, tercero, excluir_id=None):
    consulta = ContactoTercero.objects.select_for_update().filter(
        tercero=tercero,
        activo=True,
        principal=True,
    )
    if excluir_id is not None:
        consulta = consulta.exclude(pk=excluir_id)
    consulta.update(principal=False, actualizado_en=timezone.now())


def _asegurar_contacto_principal(*, tercero):
    if ContactoTercero.objects.filter(
        tercero=tercero,
        activo=True,
        principal=True,
    ).exists():
        return

    contacto = (
        ContactoTercero.objects.select_for_update()
        .filter(tercero=tercero, activo=True)
        .order_by("fecha_alta", "pk")
        .first()
    )
    if contacto is not None:
        contacto.principal = True
        contacto.full_clean()
        contacto.save(
            update_fields=["principal", "actualizado_en"]
        )


@transaction.atomic
def crear_contacto(*, empresa, tercero, request=None, **datos):
    empresa = _empresa_activa(empresa)
    tercero = _tercero_activo(empresa=empresa, tercero=tercero)
    existen = ContactoTercero.objects.select_for_update().filter(
        tercero=tercero,
        activo=True,
    ).exists()
    principal = bool(datos["principal"]) or not existen

    if principal:
        _desmarcar_contactos(tercero=tercero)

    contacto = ContactoTercero(
        tercero=tercero,
        activo=True,
        fecha_baja=None,
        **{**datos, "principal": principal},
    )
    contacto.full_clean()
    contacto.save()
    _auditar(
        empresa=empresa,
        objeto=contacto,
        accion=Auditoria.Accion.INSERT,
        anteriores=None,
        nuevos=datos_contacto(contacto),
        request=request,
    )
    return contacto


@transaction.atomic
def actualizar_contacto(*, empresa, contacto, request=None, **datos):
    empresa = _empresa_activa(empresa)
    contacto = (
        ContactoTercero.objects.select_for_update()
        .select_related("tercero")
        .filter(
            pk=contacto.pk,
            tercero__empresa=empresa,
            tercero__activo=True,
            activo=True,
        )
        .first()
    )
    if contacto is None:
        raise ValidationError(
            "El contacto no pertenece a la empresa activa o está inactivo."
        )

    anteriores = datos_contacto(contacto)
    otros = ContactoTercero.objects.select_for_update().filter(
        tercero=contacto.tercero,
        activo=True,
    ).exclude(pk=contacto.pk)
    principal = bool(datos["principal"]) or not otros.exists()

    if principal:
        _desmarcar_contactos(
            tercero=contacto.tercero,
            excluir_id=contacto.pk,
        )

    for campo, valor in datos.items():
        setattr(contacto, campo, valor)
    contacto.principal = principal
    contacto.full_clean()
    contacto.save()
    _asegurar_contacto_principal(tercero=contacto.tercero)

    _auditar(
        empresa=empresa,
        objeto=contacto,
        accion=Auditoria.Accion.UPDATE,
        anteriores=anteriores,
        nuevos=datos_contacto(contacto),
        request=request,
    )
    return contacto


@transaction.atomic
def inactivar_contacto(*, empresa, contacto, request=None):
    empresa = _empresa_activa(empresa)
    contacto = (
        ContactoTercero.objects.select_for_update()
        .select_related("tercero")
        .filter(pk=contacto.pk, tercero__empresa=empresa, activo=True)
        .first()
    )
    if contacto is None:
        raise ValidationError(
            "El contacto no pertenece a la empresa activa o ya está inactivo."
        )

    anteriores = datos_contacto(contacto)
    era_principal = contacto.principal
    contacto.activo = False
    contacto.principal = False
    contacto.fecha_baja = _fecha_baja(contacto.fecha_alta)
    contacto.full_clean()
    contacto.save(
        update_fields=[
            "activo",
            "principal",
            "fecha_baja",
            "actualizado_en",
        ]
    )
    if era_principal:
        _asegurar_contacto_principal(tercero=contacto.tercero)

    _auditar(
        empresa=empresa,
        objeto=contacto,
        accion=Auditoria.Accion.UPDATE,
        anteriores=anteriores,
        nuevos=datos_contacto(contacto),
        request=request,
    )
    return contacto
