from django.core.exceptions import ImproperlyConfigured, PermissionDenied


def _contexto_activo(request, atributo, etiqueta):
    contexto = getattr(request, atributo, None)

    if contexto is None or not getattr(contexto, "activa", False):
        raise PermissionDenied(
            f"Se requiere {etiqueta} activa para operar."
        )

    return contexto


def _resolver_atributo(objeto, ruta):
    if not ruta:
        raise ImproperlyConfigured(
            "La ruta del atributo de contexto no puede estar vacía."
        )

    valor = objeto
    try:
        for segmento in ruta.split("."):
            valor = getattr(valor, segmento)
    except AttributeError as exc:
        raise ImproperlyConfigured(
            f"El objeto no expone el atributo de contexto '{ruta}'."
        ) from exc

    return valor


def _normalizar_identificador(valor):
    return getattr(valor, "pk", valor)


def filtrar_queryset_por_empresa_activa(
    request,
    queryset,
    *,
    campo_empresa="empresa_id",
):
    empresa = _contexto_activo(
        request,
        "empresa_activa",
        "una empresa",
    )
    return queryset.filter(**{campo_empresa: empresa.pk})


def filtrar_queryset_por_contexto_operativo(
    request,
    queryset,
    *,
    campo_empresa="empresa_id",
    campo_sucursal="sucursal_id",
):
    empresa = _contexto_activo(
        request,
        "empresa_activa",
        "una empresa",
    )
    sucursal = _contexto_activo(
        request,
        "sucursal_activa",
        "una sucursal",
    )

    return queryset.filter(
        **{
            campo_empresa: empresa.pk,
            campo_sucursal: sucursal.pk,
        }
    )


def validar_objeto_en_empresa_activa(
    request,
    objeto,
    *,
    atributo_empresa="empresa_id",
):
    empresa = _contexto_activo(
        request,
        "empresa_activa",
        "una empresa",
    )
    empresa_objeto = _normalizar_identificador(
        _resolver_atributo(objeto, atributo_empresa)
    )

    if empresa_objeto != empresa.pk:
        raise PermissionDenied(
            "El objeto solicitado no pertenece a la empresa activa."
        )

    return objeto


def validar_objeto_en_contexto_operativo(
    request,
    objeto,
    *,
    atributo_empresa="empresa_id",
    atributo_sucursal="sucursal_id",
):
    validar_objeto_en_empresa_activa(
        request,
        objeto,
        atributo_empresa=atributo_empresa,
    )
    sucursal = _contexto_activo(
        request,
        "sucursal_activa",
        "una sucursal",
    )
    sucursal_objeto = _normalizar_identificador(
        _resolver_atributo(objeto, atributo_sucursal)
    )

    if sucursal_objeto != sucursal.pk:
        raise PermissionDenied(
            "El objeto solicitado no pertenece a la sucursal activa."
        )

    return objeto
