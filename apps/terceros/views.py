from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from apps.nucleo.autorizacion import (
    contexto_operativo_requerido,
    permiso_funcional_alguno_requerido,
    permiso_funcional_requerido,
)
from apps.nucleo.permisos import usuario_tiene_permiso

from .forms import (
    ContactoTerceroForm,
    DomicilioTerceroForm,
    GrupoTerceroForm,
    TerceroForm,
)
from .models import (
    ContactoTercero,
    DomicilioTercero,
    GrupoTercero,
    Tercero,
    TerceroRol,
)
from .services import (
    actualizar_contacto,
    actualizar_domicilio,
    actualizar_grupo_tercero,
    actualizar_tercero,
    asegurar_grupos_generales,
    crear_contacto,
    crear_domicilio,
    crear_grupo_tercero,
    crear_tercero,
    inactivar_contacto,
    inactivar_domicilio,
    inactivar_grupo_tercero,
    inactivar_tercero,
)


PERMISOS_TERCEROS = (
    "terceros.ver",
    "terceros.crear",
    "terceros.editar",
)


def _agregar_errores(form, error):
    if hasattr(error, "message_dict"):
        for campo, mensajes in error.message_dict.items():
            destino = campo if campo in form.fields else None
            for mensaje in mensajes:
                form.add_error(destino, mensaje)
        return

    for mensaje in error.messages:
        form.add_error(None, mensaje)


def _obtener_tercero(empresa, tercero_id, *, activo=None):
    consulta = (
        Tercero.objects.filter(pk=tercero_id, empresa=empresa)
        .select_related("empresa", "tipo_documento", "condicion_iva")
        .prefetch_related(
            Prefetch(
                "roles",
                queryset=TerceroRol.objects.select_related("grupo").order_by(
                    "-activo",
                    "rol",
                    "pk",
                ),
            ),
            Prefetch(
                "domicilios",
                queryset=DomicilioTercero.objects.order_by(
                    "-activo",
                    "tipo",
                    "-principal",
                    "pk",
                ),
            ),
            Prefetch(
                "contactos",
                queryset=ContactoTercero.objects.order_by(
                    "-activo",
                    "-principal",
                    "nombre",
                    "pk",
                ),
            ),
        )
    )

    if activo is not None:
        consulta = consulta.filter(activo=activo)

    return get_object_or_404(consulta)


GRUPOS_CONFIG = {
    GrupoTercero.Tipo.CLIENTE: {
        "titulo": "Grupos de clientes",
        "singular": "grupo de cliente",
        "lista_url": "terceros:grupo_cliente_list",
        "crear_url": "terceros:grupo_cliente_create",
        "editar_url": "terceros:grupo_cliente_edit",
        "inactivar_url": "terceros:grupo_cliente_deactivate",
    },
    GrupoTercero.Tipo.PROVEEDOR: {
        "titulo": "Grupos de proveedores",
        "singular": "grupo de proveedor",
        "lista_url": "terceros:grupo_proveedor_list",
        "crear_url": "terceros:grupo_proveedor_create",
        "editar_url": "terceros:grupo_proveedor_edit",
        "inactivar_url": "terceros:grupo_proveedor_deactivate",
    },
}


def _obtener_grupo(empresa, grupo_id, *, tipo, activo=None):
    consulta = GrupoTercero.objects.filter(
        pk=grupo_id,
        empresa=empresa,
        tipo=tipo,
    )
    if activo is not None:
        consulta = consulta.filter(activo=activo)
    return get_object_or_404(consulta)


def _grupo_list(request, *, tipo):
    empresa = request.empresa_activa
    asegurar_grupos_generales(empresa)
    config = GRUPOS_CONFIG[tipo]
    busqueda = request.GET.get("q", "").strip()
    estado = request.GET.get("estado", "activos").strip().lower()

    grupos = GrupoTercero.objects.filter(
        empresa=empresa,
        tipo=tipo,
    ).annotate(
        cantidad_asignaciones=Count(
            "roles_terceros",
            filter=Q(roles_terceros__activo=True),
            distinct=True,
        )
    )

    if busqueda:
        grupos = grupos.filter(
            Q(codigo__icontains=busqueda)
            | Q(nombre__icontains=busqueda)
            | Q(observaciones__icontains=busqueda)
        )

    if estado == "inactivos":
        grupos = grupos.filter(activo=False)
    elif estado == "todos":
        pass
    else:
        estado = "activos"
        grupos = grupos.filter(activo=True)

    grupos = grupos.order_by("nombre", "codigo")

    return render(
        request,
        "terceros/grupo_tercero_list.html",
        {
            "empresa": empresa,
            "grupos": grupos,
            "cantidad_resultados": grupos.count(),
            "tipo": tipo,
            **config,
            "filtros": {"q": busqueda, "estado": estado},
            "hay_filtros": bool(busqueda or estado != "activos"),
            "puede_crear": usuario_tiene_permiso(
                request.user,
                empresa,
                "terceros.crear",
            ),
            "puede_editar": usuario_tiene_permiso(
                request.user,
                empresa,
                "terceros.editar",
            ),
        },
    )


def _grupo_form(request, *, tipo, grupo=None):
    empresa = request.empresa_activa
    config = GRUPOS_CONFIG[tipo]
    form = GrupoTerceroForm(
        request.POST if request.method == "POST" else None,
        grupo=grupo,
    )

    if request.method == "POST" and form.is_valid():
        try:
            if grupo is None:
                guardado = crear_grupo_tercero(
                    empresa=empresa,
                    tipo=tipo,
                    codigo=form.cleaned_data["codigo"],
                    nombre=form.cleaned_data["nombre"],
                    observaciones=form.cleaned_data["observaciones"],
                    request=request,
                )
                accion = "creado"
            else:
                guardado = actualizar_grupo_tercero(
                    empresa=empresa,
                    grupo=grupo,
                    nombre=form.cleaned_data["nombre"],
                    observaciones=form.cleaned_data["observaciones"],
                    request=request,
                )
                accion = "actualizado"
        except ValidationError as error:
            _agregar_errores(form, error)
        else:
            messages.success(
                request,
                f"Grupo {guardado.codigo} {accion} correctamente.",
            )
            return redirect(config["lista_url"])

    return render(
        request,
        "terceros/grupo_tercero_form.html",
        {
            "empresa": empresa,
            "form": form,
            "grupo": grupo,
            "tipo": tipo,
            "titulo": (
                f"Nuevo {config['singular']}"
                if grupo is None
                else f"Editar {config['singular']}"
            ),
            "lista_url": config["lista_url"],
            "modo_creacion": grupo is None,
        },
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_alguno_requerido(*PERMISOS_TERCEROS)
@require_GET
def grupo_cliente_list(request):
    return _grupo_list(request, tipo=GrupoTercero.Tipo.CLIENTE)


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_alguno_requerido(*PERMISOS_TERCEROS)
@require_GET
def grupo_proveedor_list(request):
    return _grupo_list(request, tipo=GrupoTercero.Tipo.PROVEEDOR)


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("terceros.crear")
def grupo_cliente_create(request):
    return _grupo_form(request, tipo=GrupoTercero.Tipo.CLIENTE)


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("terceros.crear")
def grupo_proveedor_create(request):
    return _grupo_form(request, tipo=GrupoTercero.Tipo.PROVEEDOR)


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("terceros.editar")
def grupo_cliente_edit(request, grupo_id):
    grupo = _obtener_grupo(
        request.empresa_activa,
        grupo_id,
        tipo=GrupoTercero.Tipo.CLIENTE,
        activo=True,
    )
    return _grupo_form(
        request,
        tipo=GrupoTercero.Tipo.CLIENTE,
        grupo=grupo,
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("terceros.editar")
def grupo_proveedor_edit(request, grupo_id):
    grupo = _obtener_grupo(
        request.empresa_activa,
        grupo_id,
        tipo=GrupoTercero.Tipo.PROVEEDOR,
        activo=True,
    )
    return _grupo_form(
        request,
        tipo=GrupoTercero.Tipo.PROVEEDOR,
        grupo=grupo,
    )


def _grupo_deactivate(request, *, grupo):
    try:
        grupo = inactivar_grupo_tercero(
            empresa=request.empresa_activa,
            grupo=grupo,
            request=request,
        )
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(
            request,
            f"Grupo {grupo.codigo} inactivado correctamente.",
        )
    return redirect(GRUPOS_CONFIG[grupo.tipo]["lista_url"])


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("terceros.editar")
@require_POST
def grupo_cliente_deactivate(request, grupo_id):
    grupo = _obtener_grupo(
        request.empresa_activa,
        grupo_id,
        tipo=GrupoTercero.Tipo.CLIENTE,
    )
    return _grupo_deactivate(request, grupo=grupo)


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("terceros.editar")
@require_POST
def grupo_proveedor_deactivate(request, grupo_id):
    grupo = _obtener_grupo(
        request.empresa_activa,
        grupo_id,
        tipo=GrupoTercero.Tipo.PROVEEDOR,
    )
    return _grupo_deactivate(request, grupo=grupo)


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_alguno_requerido(*PERMISOS_TERCEROS)
@require_GET
def tercero_list(request):
    empresa = request.empresa_activa
    asegurar_grupos_generales(empresa)
    busqueda = request.GET.get("q", "").strip()
    rol = request.GET.get("rol", "").strip().upper()
    grupo_id = request.GET.get("grupo", "").strip()
    estado = request.GET.get("estado", "activos").strip().lower()

    terceros = (
        Tercero.objects.filter(empresa=empresa)
        .select_related("tipo_documento", "condicion_iva")
        .prefetch_related(
            Prefetch(
                "roles",
                queryset=(
                    TerceroRol.objects.filter(activo=True)
                    .select_related("grupo")
                    .order_by("rol", "pk")
                ),
                to_attr="roles_activos_precargados",
            )
        )
        .order_by("denominacion", "codigo")
    )

    if busqueda:
        terceros = terceros.filter(
            Q(codigo__icontains=busqueda)
            | Q(numero_documento__icontains=busqueda)
            | Q(denominacion__icontains=busqueda)
            | Q(nombre_fantasia__icontains=busqueda)
            | Q(email__icontains=busqueda)
        )

    if rol not in set(TerceroRol.Rol.values):
        rol = ""

    grupo = None
    if grupo_id.isdigit():
        grupo = GrupoTercero.objects.filter(
            pk=int(grupo_id),
            empresa=empresa,
            activo=True,
        ).first()
    if grupo is None:
        grupo_id = ""

    filtros_roles = {"roles__activo": True}
    if rol:
        filtros_roles["roles__rol"] = rol
    if grupo is not None:
        filtros_roles["roles__grupo"] = grupo

    if rol or grupo is not None:
        terceros = terceros.filter(**filtros_roles).distinct()

    if estado == "inactivos":
        terceros = terceros.filter(activo=False)
    elif estado == "todos":
        pass
    else:
        estado = "activos"
        terceros = terceros.filter(activo=True)

    terceros = list(terceros)
    cantidad_resultados = len(terceros)
    grupos_cliente = GrupoTercero.objects.filter(
        empresa=empresa,
        tipo=GrupoTercero.Tipo.CLIENTE,
        activo=True,
    ).order_by("nombre", "codigo")
    grupos_proveedor = GrupoTercero.objects.filter(
        empresa=empresa,
        tipo=GrupoTercero.Tipo.PROVEEDOR,
        activo=True,
    ).order_by("nombre", "codigo")

    return render(
        request,
        "terceros/tercero_list.html",
        {
            "empresa": empresa,
            "terceros": terceros,
            "cantidad_resultados": cantidad_resultados,
            "roles_opciones": TerceroRol.Rol.choices,
            "grupos_cliente": grupos_cliente,
            "grupos_proveedor": grupos_proveedor,
            "filtros": {
                "q": busqueda,
                "rol": rol,
                "grupo": grupo_id,
                "estado": estado,
            },
            "hay_filtros": any(
                (busqueda, rol, grupo_id, estado != "activos")
            ),
            "puede_crear": usuario_tiene_permiso(
                request.user,
                empresa,
                "terceros.crear",
            ),
            "puede_editar": usuario_tiene_permiso(
                request.user,
                empresa,
                "terceros.editar",
            ),
        },
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_alguno_requerido(*PERMISOS_TERCEROS)
@require_GET
def tercero_detail(request, tercero_id):
    empresa = request.empresa_activa
    tercero = _obtener_tercero(empresa, tercero_id)

    return render(
        request,
        "terceros/tercero_detail.html",
        {
            "empresa": empresa,
            "tercero": tercero,
            "puede_editar": usuario_tiene_permiso(
                request.user,
                empresa,
                "terceros.editar",
            ),
        },
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("terceros.crear")
def tercero_create(request):
    empresa = request.empresa_activa
    asegurar_grupos_generales(empresa)
    form = TerceroForm(
        request.POST if request.method == "POST" else None,
        empresa=empresa,
        initial={
            "tipo_persona": Tercero.TipoPersona.PERSONA_JURIDICA,
            "es_cliente": True,
        },
    )

    if request.method == "POST" and form.is_valid():
        try:
            tercero = crear_tercero(
                empresa=empresa,
                codigo=form.cleaned_data["codigo"],
                tipo_persona=form.cleaned_data["tipo_persona"],
                tipo_documento=form.cleaned_data["tipo_documento"],
                numero_documento=form.cleaned_data["numero_documento"],
                denominacion=form.cleaned_data["denominacion"],
                nombre_fantasia=form.cleaned_data["nombre_fantasia"],
                condicion_iva=form.cleaned_data["condicion_iva"],
                telefono=form.cleaned_data["telefono"],
                email=form.cleaned_data["email"],
                sitio_web=form.cleaned_data["sitio_web"],
                fecha_alta=form.cleaned_data["fecha_alta"],
                roles=form.roles_seleccionados,
                grupos_por_rol=form.grupos_por_rol,
                observaciones=form.cleaned_data["observaciones"],
                request=request,
            )
        except ValidationError as error:
            _agregar_errores(form, error)
        else:
            messages.success(
                request,
                f"Tercero {tercero.codigo} — {tercero.denominacion} creado.",
            )
            return redirect(
                "terceros:tercero_detail",
                tercero_id=tercero.pk,
            )

    return render(
        request,
        "terceros/tercero_form.html",
        {
            "empresa": empresa,
            "form": form,
            "tercero": None,
            "titulo": "Nuevo cliente o proveedor",
            "modo_creacion": True,
        },
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("terceros.editar")
def tercero_edit(request, tercero_id):
    empresa = request.empresa_activa
    asegurar_grupos_generales(empresa)
    tercero = _obtener_tercero(empresa, tercero_id, activo=True)

    if request.method == "POST":
        form = TerceroForm(
            request.POST,
            empresa=empresa,
            tercero=tercero,
        )
    else:
        form = TerceroForm(
            empresa=empresa,
            tercero=tercero,
        )

    if request.method == "POST" and form.is_valid():
        try:
            tercero = actualizar_tercero(
                empresa=empresa,
                tercero=tercero,
                tipo_persona=form.cleaned_data["tipo_persona"],
                tipo_documento=form.cleaned_data["tipo_documento"],
                numero_documento=form.cleaned_data["numero_documento"],
                denominacion=form.cleaned_data["denominacion"],
                nombre_fantasia=form.cleaned_data["nombre_fantasia"],
                condicion_iva=form.cleaned_data["condicion_iva"],
                telefono=form.cleaned_data["telefono"],
                email=form.cleaned_data["email"],
                sitio_web=form.cleaned_data["sitio_web"],
                fecha_alta=form.cleaned_data["fecha_alta"],
                roles=form.roles_seleccionados,
                grupos_por_rol=form.grupos_por_rol,
                observaciones=form.cleaned_data["observaciones"],
                request=request,
            )
        except ValidationError as error:
            _agregar_errores(form, error)
        else:
            messages.success(
                request,
                f"Tercero {tercero.codigo} actualizado correctamente.",
            )
            return redirect(
                "terceros:tercero_detail",
                tercero_id=tercero.pk,
            )

    return render(
        request,
        "terceros/tercero_form.html",
        {
            "empresa": empresa,
            "form": form,
            "tercero": tercero,
            "titulo": "Editar cliente/proveedor",
            "modo_creacion": False,
        },
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("terceros.editar")
@require_POST
def tercero_deactivate(request, tercero_id):
    empresa = request.empresa_activa
    tercero = _obtener_tercero(empresa, tercero_id)

    try:
        tercero = inactivar_tercero(
            empresa=empresa,
            tercero=tercero,
            request=request,
        )
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(
            request,
            f"Tercero {tercero.codigo} inactivado correctamente.",
        )

    return redirect("terceros:tercero_list")


def _relacion_form(
    request,
    *,
    tercero,
    objeto,
    form_class,
    servicio,
    template,
    titulo,
):
    form = form_class(
        request.POST if request.method == "POST" else None,
        **({"domicilio": objeto} if template == "domicilio" else {"contacto": objeto}),
    )

    if request.method == "POST" and form.is_valid():
        try:
            relacion = servicio(
                empresa=request.empresa_activa,
                request=request,
                **(
                    {"tercero": tercero}
                    if objeto is None
                    else {template: objeto}
                ),
                **form.cleaned_data,
            )
        except ValidationError as error:
            _agregar_errores(form, error)
        else:
            messages.success(request, f"{titulo} guardado correctamente.")
            return redirect(
                "terceros:tercero_detail",
                tercero_id=relacion.tercero_id,
            )

    return render(
        request,
        f"terceros/{template}_form.html",
        {
            "empresa": request.empresa_activa,
            "tercero": tercero,
            template: objeto,
            "form": form,
            "titulo": titulo,
        },
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("terceros.editar")
def domicilio_create(request, tercero_id):
    tercero = _obtener_tercero(
        request.empresa_activa,
        tercero_id,
        activo=True,
    )
    return _relacion_form(
        request,
        tercero=tercero,
        objeto=None,
        form_class=DomicilioTerceroForm,
        servicio=crear_domicilio,
        template="domicilio",
        titulo="Nuevo domicilio",
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("terceros.editar")
def domicilio_edit(request, domicilio_id):
    domicilio = get_object_or_404(
        DomicilioTercero.objects.select_related("tercero"),
        pk=domicilio_id,
        tercero__empresa=request.empresa_activa,
        tercero__activo=True,
        activo=True,
    )
    return _relacion_form(
        request,
        tercero=domicilio.tercero,
        objeto=domicilio,
        form_class=DomicilioTerceroForm,
        servicio=actualizar_domicilio,
        template="domicilio",
        titulo="Editar domicilio",
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("terceros.editar")
@require_POST
def domicilio_deactivate(request, domicilio_id):
    domicilio = get_object_or_404(
        DomicilioTercero.objects.select_related("tercero"),
        pk=domicilio_id,
        tercero__empresa=request.empresa_activa,
    )
    tercero_id = domicilio.tercero_id

    try:
        inactivar_domicilio(
            empresa=request.empresa_activa,
            domicilio=domicilio,
            request=request,
        )
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(request, "Domicilio inactivado correctamente.")

    return redirect("terceros:tercero_detail", tercero_id=tercero_id)


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("terceros.editar")
def contacto_create(request, tercero_id):
    tercero = _obtener_tercero(
        request.empresa_activa,
        tercero_id,
        activo=True,
    )
    return _relacion_form(
        request,
        tercero=tercero,
        objeto=None,
        form_class=ContactoTerceroForm,
        servicio=crear_contacto,
        template="contacto",
        titulo="Nuevo contacto",
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("terceros.editar")
def contacto_edit(request, contacto_id):
    contacto = get_object_or_404(
        ContactoTercero.objects.select_related("tercero"),
        pk=contacto_id,
        tercero__empresa=request.empresa_activa,
        tercero__activo=True,
        activo=True,
    )
    return _relacion_form(
        request,
        tercero=contacto.tercero,
        objeto=contacto,
        form_class=ContactoTerceroForm,
        servicio=actualizar_contacto,
        template="contacto",
        titulo="Editar contacto",
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("terceros.editar")
@require_POST
def contacto_deactivate(request, contacto_id):
    contacto = get_object_or_404(
        ContactoTercero.objects.select_related("tercero"),
        pk=contacto_id,
        tercero__empresa=request.empresa_activa,
    )
    tercero_id = contacto.tercero_id

    try:
        inactivar_contacto(
            empresa=request.empresa_activa,
            contacto=contacto,
            request=request,
        )
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(request, "Contacto inactivado correctamente.")

    return redirect("terceros:tercero_detail", tercero_id=tercero_id)
