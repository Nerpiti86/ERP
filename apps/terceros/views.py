from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from apps.nucleo.autorizacion import (
    contexto_operativo_requerido,
    permiso_funcional_alguno_requerido,
    permiso_funcional_requerido,
)
from apps.nucleo.permisos import usuario_tiene_permiso

from .forms import ContactoTerceroForm, DomicilioTerceroForm, TerceroForm
from .models import ContactoTercero, DomicilioTercero, Tercero, TerceroRol
from .services import (
    actualizar_contacto,
    actualizar_domicilio,
    actualizar_tercero,
    crear_contacto,
    crear_domicilio,
    crear_tercero,
    inactivar_contacto,
    inactivar_domicilio,
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
                queryset=TerceroRol.objects.order_by("-activo", "rol", "pk"),
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


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_alguno_requerido(*PERMISOS_TERCEROS)
@require_GET
def tercero_list(request):
    empresa = request.empresa_activa
    base = Tercero.objects.filter(empresa=empresa)
    busqueda = request.GET.get("q", "").strip()
    rol = request.GET.get("rol", "").strip().upper()
    estado = request.GET.get("estado", "activos").strip().lower()

    terceros = (
        base.select_related("tipo_documento", "condicion_iva")
        .prefetch_related(
            Prefetch(
                "roles",
                queryset=TerceroRol.objects.filter(activo=True).order_by(
                    "rol",
                    "pk",
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

    if rol in set(TerceroRol.Rol.values):
        terceros = terceros.filter(
            roles__rol=rol,
            roles__activo=True,
        ).distinct()
    else:
        rol = ""

    if estado == "inactivos":
        terceros = terceros.filter(activo=False)
    elif estado == "todos":
        pass
    else:
        estado = "activos"
        terceros = terceros.filter(activo=True)

    resumen = {
        "total": base.count(),
        "activos": base.filter(activo=True).count(),
        "clientes": base.filter(
            activo=True,
            roles__rol=TerceroRol.Rol.CLIENTE,
            roles__activo=True,
        ).distinct().count(),
        "proveedores": base.filter(
            activo=True,
            roles__rol=TerceroRol.Rol.PROVEEDOR,
            roles__activo=True,
        ).distinct().count(),
    }

    return render(
        request,
        "terceros/tercero_list.html",
        {
            "empresa": empresa,
            "terceros": list(terceros),
            "resumen": resumen,
            "roles_opciones": TerceroRol.Rol.choices,
            "filtros": {"q": busqueda, "rol": rol, "estado": estado},
            "hay_filtros": any(
                (busqueda, rol, estado != "activos")
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
