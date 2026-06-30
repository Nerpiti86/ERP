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
from apps.terceros.models import TerceroRol

from .forms import (
    CategoriaItemForm,
    ItemForm,
    ItemProveedorForm,
    MarcaForm,
)
from .models import (
    AlicuotaIVA,
    CategoriaItem,
    Item,
    ItemProveedor,
    Marca,
    UnidadMedida,
)
from .services import (
    actualizar_categoria,
    actualizar_item,
    actualizar_marca,
    crear_categoria,
    crear_item,
    crear_marca,
    inactivar_categoria,
    inactivar_item,
    inactivar_item_proveedor,
    inactivar_marca,
    crear_item_proveedor,
    actualizar_item_proveedor,
    reactivar_item,
    reactivar_item_proveedor,
)


PERMISOS_ITEMS = (
    "items.ver",
    "items.crear",
    "items.editar",
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


def _obtener_item(empresa, item_id, *, activo=None):
    consulta = Item.objects.filter(
        pk=item_id,
        empresa=empresa,
    ).select_related(
        "empresa",
        "categoria",
        "marca",
        "unidad_medida",
        "alicuota_iva",
    )
    if activo is not None:
        consulta = consulta.filter(activo=activo)
    return get_object_or_404(consulta)


def _obtener_catalogo(modelo, empresa, catalogo_id, *, activo=None):
    consulta = modelo.objects.filter(
        pk=catalogo_id,
        empresa=empresa,
    )
    if activo is not None:
        consulta = consulta.filter(activo=activo)
    return get_object_or_404(consulta)


def _consulta_relaciones_proveedores():
    roles = TerceroRol.objects.filter(
        rol=TerceroRol.Rol.PROVEEDOR,
        activo=True,
    ).select_related("grupo")
    return (
        ItemProveedor.objects.select_related(
            "empresa",
            "item",
            "proveedor",
        )
        .prefetch_related(
            Prefetch(
                "proveedor__roles",
                queryset=roles,
                to_attr="roles_proveedor_activos_precargados",
            )
        )
    )


def _obtener_relacion_proveedor(
    empresa,
    item,
    relacion_id,
    *,
    activo=None,
):
    consulta = _consulta_relaciones_proveedores().filter(
        pk=relacion_id,
        empresa=empresa,
        item=item,
    )
    if activo is not None:
        consulta = consulta.filter(activo=activo)
    return get_object_or_404(consulta)


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_alguno_requerido(*PERMISOS_ITEMS)
@require_GET
def item_list(request):
    empresa = request.empresa_activa
    items = Item.objects.filter(empresa=empresa).select_related(
        "categoria",
        "marca",
        "unidad_medida",
        "alicuota_iva",
    )

    busqueda = request.GET.get("q", "").strip()
    tipo = request.GET.get("tipo", "").strip().upper()
    operacion = request.GET.get("operacion", "").strip().lower()
    stock = request.GET.get("stock", "").strip().lower()
    estado = request.GET.get("estado", "activos").strip().lower()

    if busqueda:
        items = items.filter(
            Q(codigo__icontains=busqueda)
            | Q(nombre__icontains=busqueda)
            | Q(descripcion__icontains=busqueda)
            | Q(categoria__nombre__icontains=busqueda)
            | Q(marca__nombre__icontains=busqueda)
        )

    if tipo in set(Item.Tipo.values):
        items = items.filter(tipo=tipo)
    else:
        tipo = ""

    if operacion == "compra":
        items = items.filter(se_compra=True)
    elif operacion == "venta":
        items = items.filter(se_vende=True)
    elif operacion == "ambos":
        items = items.filter(se_compra=True, se_vende=True)
    else:
        operacion = ""

    if stock == "si":
        items = items.filter(controla_stock=True)
    elif stock == "no":
        items = items.filter(controla_stock=False)
    else:
        stock = ""

    if estado == "inactivos":
        items = items.filter(activo=False)
    elif estado == "todos":
        pass
    else:
        estado = "activos"
        items = items.filter(activo=True)

    items = items.order_by("nombre", "codigo")
    cantidad_resultados = items.count()

    return render(
        request,
        "items/item_list.html",
        {
            "empresa": empresa,
            "items": items,
            "cantidad_resultados": cantidad_resultados,
            "tipos": Item.Tipo.choices,
            "filtros": {
                "q": busqueda,
                "tipo": tipo,
                "operacion": operacion,
                "stock": stock,
                "estado": estado,
            },
            "hay_filtros": any(
                (
                    busqueda,
                    tipo,
                    operacion,
                    stock,
                    estado != "activos",
                )
            ),
            "puede_crear": usuario_tiene_permiso(
                request.user,
                empresa,
                "items.crear",
            ),
            "puede_editar": usuario_tiene_permiso(
                request.user,
                empresa,
                "items.editar",
            ),
        },
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_alguno_requerido(*PERMISOS_ITEMS)
@require_GET
def item_detail(request, item_id):
    empresa = request.empresa_activa
    item = _obtener_item(empresa, item_id)
    relaciones_proveedores = list(
        _consulta_relaciones_proveedores()
        .filter(empresa=empresa, item=item)
        .order_by("-activo", "proveedor__denominacion", "proveedor__codigo")
    )
    return render(
        request,
        "items/item_detail.html",
        {
            "empresa": empresa,
            "item": item,
            "relaciones_proveedores": relaciones_proveedores,
            "puede_editar": usuario_tiene_permiso(
                request.user,
                empresa,
                "items.editar",
            ),
        },
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("items.editar")
def item_proveedor_create(request, item_id):
    empresa = request.empresa_activa
    item = _obtener_item(empresa, item_id, activo=True)

    if not item.se_compra:
        messages.error(
            request,
            "El ítem no está habilitado para compra.",
        )
        return redirect("items:item_detail", item_id=item.pk)

    form = ItemProveedorForm(
        request.POST if request.method == "POST" else None,
        empresa=empresa,
        item=item,
    )
    if request.method == "POST" and form.is_valid():
        try:
            relacion = crear_item_proveedor(
                empresa=empresa,
                item=item,
                proveedor=form.cleaned_data["proveedor"],
                codigo_proveedor=form.cleaned_data["codigo_proveedor"],
                observaciones=form.cleaned_data["observaciones"],
                request=request,
            )
        except ValidationError as error:
            _agregar_errores(form, error)
        else:
            messages.success(
                request,
                f"Proveedor {relacion.proveedor.denominacion} asociado.",
            )
            return redirect("items:item_detail", item_id=item.pk)

    return render(
        request,
        "items/item_proveedor_form.html",
        {
            "empresa": empresa,
            "item": item,
            "relacion": None,
            "form": form,
            "titulo": "Asociar proveedor",
        },
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("items.editar")
def item_proveedor_edit(request, item_id, relacion_id):
    empresa = request.empresa_activa
    item = _obtener_item(empresa, item_id)
    relacion = _obtener_relacion_proveedor(
        empresa,
        item,
        relacion_id,
        activo=True,
    )

    if not relacion.disponible_operativamente:
        messages.error(
            request,
            "La relación no está disponible para edición. "
            "Restablecé sus dependencias o inactivala.",
        )
        return redirect("items:item_detail", item_id=item.pk)

    form = ItemProveedorForm(
        request.POST if request.method == "POST" else None,
        empresa=empresa,
        item=item,
        relacion=relacion,
    )
    if request.method == "POST" and form.is_valid():
        try:
            relacion = actualizar_item_proveedor(
                empresa=empresa,
                relacion=relacion,
                codigo_proveedor=form.cleaned_data["codigo_proveedor"],
                observaciones=form.cleaned_data["observaciones"],
                request=request,
            )
        except ValidationError as error:
            _agregar_errores(form, error)
        else:
            messages.success(request, "Relación con proveedor actualizada.")
            return redirect("items:item_detail", item_id=item.pk)

    return render(
        request,
        "items/item_proveedor_form.html",
        {
            "empresa": empresa,
            "item": item,
            "relacion": relacion,
            "form": form,
            "titulo": "Editar proveedor asociado",
        },
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("items.editar")
@require_POST
def item_proveedor_deactivate(request, item_id, relacion_id):
    empresa = request.empresa_activa
    item = _obtener_item(empresa, item_id)
    relacion = _obtener_relacion_proveedor(
        empresa,
        item,
        relacion_id,
        activo=True,
    )
    try:
        inactivar_item_proveedor(
            empresa=empresa,
            relacion=relacion,
            request=request,
        )
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(request, "Relación con proveedor inactivada.")
    return redirect("items:item_detail", item_id=item.pk)


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("items.editar")
@require_POST
def item_proveedor_reactivate(request, item_id, relacion_id):
    empresa = request.empresa_activa
    item = _obtener_item(empresa, item_id)
    relacion = _obtener_relacion_proveedor(
        empresa,
        item,
        relacion_id,
        activo=False,
    )
    try:
        reactivar_item_proveedor(
            empresa=empresa,
            relacion=relacion,
            request=request,
        )
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(request, "Relación con proveedor reactivada.")
    return redirect("items:item_detail", item_id=item.pk)


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("items.crear")
def item_create(request):
    empresa = request.empresa_activa
    unidad_inicial = UnidadMedida.objects.filter(
        codigo="UNIDAD",
        activo=True,
    ).first()
    iva_inicial = AlicuotaIVA.objects.filter(
        codigo="IVA_21",
        activo=True,
    ).first()

    form = ItemForm(
        request.POST if request.method == "POST" else None,
        empresa=empresa,
        initial={
            "tipo": Item.Tipo.PRODUCTO,
            "unidad_medida": unidad_inicial,
            "se_vende": True,
            "tratamiento_iva": Item.TratamientoIVA.GRAVADO,
            "alicuota_iva": iva_inicial,
        },
    )

    if request.method == "POST" and form.is_valid():
        try:
            item = crear_item(
                empresa=empresa,
                codigo=form.cleaned_data["codigo"],
                nombre=form.cleaned_data["nombre"],
                descripcion=form.cleaned_data["descripcion"],
                tipo=form.cleaned_data["tipo"],
                categoria=form.cleaned_data["categoria"],
                marca=form.cleaned_data["marca"],
                unidad_medida=form.cleaned_data["unidad_medida"],
                se_compra=form.cleaned_data["se_compra"],
                se_vende=form.cleaned_data["se_vende"],
                controla_stock=form.cleaned_data["controla_stock"],
                tratamiento_iva=form.cleaned_data["tratamiento_iva"],
                alicuota_iva=form.cleaned_data["alicuota_iva"],
                observaciones=form.cleaned_data["observaciones"],
                request=request,
            )
        except ValidationError as error:
            _agregar_errores(form, error)
        else:
            messages.success(
                request,
                f"Ítem {item.codigo} — {item.nombre} creado.",
            )
            return redirect("items:item_detail", item_id=item.pk)

    return render(
        request,
        "items/item_form.html",
        {
            "empresa": empresa,
            "form": form,
            "item": None,
            "titulo": "Nuevo producto o servicio",
            "modo_creacion": True,
        },
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("items.editar")
def item_edit(request, item_id):
    empresa = request.empresa_activa
    item = _obtener_item(empresa, item_id, activo=True)
    form = ItemForm(
        request.POST if request.method == "POST" else None,
        empresa=empresa,
        item=item,
    )

    if request.method == "POST" and form.is_valid():
        try:
            item = actualizar_item(
                empresa=empresa,
                item=item,
                nombre=form.cleaned_data["nombre"],
                descripcion=form.cleaned_data["descripcion"],
                tipo=form.cleaned_data["tipo"],
                categoria=form.cleaned_data["categoria"],
                marca=form.cleaned_data["marca"],
                unidad_medida=form.cleaned_data["unidad_medida"],
                se_compra=form.cleaned_data["se_compra"],
                se_vende=form.cleaned_data["se_vende"],
                controla_stock=form.cleaned_data["controla_stock"],
                tratamiento_iva=form.cleaned_data["tratamiento_iva"],
                alicuota_iva=form.cleaned_data["alicuota_iva"],
                observaciones=form.cleaned_data["observaciones"],
                request=request,
            )
        except ValidationError as error:
            _agregar_errores(form, error)
        else:
            messages.success(
                request,
                f"Ítem {item.codigo} actualizado correctamente.",
            )
            return redirect("items:item_detail", item_id=item.pk)

    return render(
        request,
        "items/item_form.html",
        {
            "empresa": empresa,
            "form": form,
            "item": item,
            "titulo": "Editar producto o servicio",
            "modo_creacion": False,
        },
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("items.editar")
@require_POST
def item_reactivate(request, item_id):
    empresa = request.empresa_activa
    item = _obtener_item(empresa, item_id)
    try:
        item = reactivar_item(
            empresa=empresa,
            item=item,
            request=request,
        )
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(
            request,
            f"Ítem {item.codigo} reactivado correctamente.",
        )
    return redirect("items:item_detail", item_id=item.pk)


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("items.editar")
@require_POST
def item_deactivate(request, item_id):
    empresa = request.empresa_activa
    item = _obtener_item(empresa, item_id)
    try:
        item = inactivar_item(
            empresa=empresa,
            item=item,
            request=request,
        )
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(
            request,
            f"Ítem {item.codigo} inactivado correctamente.",
        )
    return redirect("items:item_list")


def _catalogo_list(
    request,
    *,
    modelo,
    titulo,
    singular,
    crear_url,
    editar_url,
    inactivar_url,
    muestra_descripcion,
):
    empresa = request.empresa_activa
    objetos = modelo.objects.filter(empresa=empresa)
    busqueda = request.GET.get("q", "").strip()
    estado = request.GET.get("estado", "activos").strip().lower()

    if busqueda:
        consulta = Q(codigo__icontains=busqueda) | Q(
            nombre__icontains=busqueda
        )
        if muestra_descripcion:
            consulta |= Q(descripcion__icontains=busqueda)
        objetos = objetos.filter(consulta)

    if estado == "inactivos":
        objetos = objetos.filter(activo=False)
    elif estado == "todos":
        pass
    else:
        estado = "activos"
        objetos = objetos.filter(activo=True)

    objetos = objetos.order_by("nombre", "codigo")
    cantidad_resultados = objetos.count()

    return render(
        request,
        "items/catalogo_list.html",
        {
            "empresa": empresa,
            "objetos": objetos,
            "cantidad_resultados": cantidad_resultados,
            "titulo": titulo,
            "singular": singular,
            "crear_url": crear_url,
            "editar_url": editar_url,
            "inactivar_url": inactivar_url,
            "muestra_descripcion": muestra_descripcion,
            "filtros": {"q": busqueda, "estado": estado},
            "hay_filtros": bool(busqueda or estado != "activos"),
            "puede_crear": usuario_tiene_permiso(
                request.user,
                empresa,
                "items.crear",
            ),
            "puede_editar": usuario_tiene_permiso(
                request.user,
                empresa,
                "items.editar",
            ),
        },
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_alguno_requerido(*PERMISOS_ITEMS)
@require_GET
def categoria_list(request):
    return _catalogo_list(
        request,
        modelo=CategoriaItem,
        titulo="Categorías de productos y servicios",
        singular="categoría",
        crear_url="items:categoria_create",
        editar_url="items:categoria_edit",
        inactivar_url="items:categoria_deactivate",
        muestra_descripcion=True,
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_alguno_requerido(*PERMISOS_ITEMS)
@require_GET
def marca_list(request):
    return _catalogo_list(
        request,
        modelo=Marca,
        titulo="Marcas",
        singular="marca",
        crear_url="items:marca_create",
        editar_url="items:marca_edit",
        inactivar_url="items:marca_deactivate",
        muestra_descripcion=False,
    )


def _catalogo_form(
    request,
    *,
    objeto,
    form_class,
    servicio,
    titulo,
    lista_url,
    tipo_objeto,
):
    empresa = request.empresa_activa
    kwargs = {tipo_objeto: objeto} if objeto is not None else {}
    form = form_class(
        request.POST if request.method == "POST" else None,
        **kwargs,
    )

    if request.method == "POST" and form.is_valid():
        argumentos = {
            "empresa": empresa,
            "nombre": form.cleaned_data["nombre"],
            "request": request,
        }
        if objeto is None:
            argumentos["codigo"] = form.cleaned_data["codigo"]
        else:
            argumentos[tipo_objeto] = objeto
        if tipo_objeto == "categoria":
            argumentos["descripcion"] = form.cleaned_data["descripcion"]

        try:
            guardado = servicio(**argumentos)
        except ValidationError as error:
            _agregar_errores(form, error)
        else:
            accion = "creada" if objeto is None else "actualizada"
            messages.success(
                request,
                f"{guardado._meta.verbose_name.capitalize()} "
                f"{guardado.codigo} {accion} correctamente.",
            )
            return redirect(lista_url)

    return render(
        request,
        "items/catalogo_form.html",
        {
            "empresa": empresa,
            "form": form,
            "catalogo": objeto,
            "titulo": titulo,
            "lista_url": lista_url,
            "modo_creacion": objeto is None,
        },
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("items.crear")
def categoria_create(request):
    return _catalogo_form(
        request,
        objeto=None,
        form_class=CategoriaItemForm,
        servicio=crear_categoria,
        titulo="Nueva categoría",
        lista_url="items:categoria_list",
        tipo_objeto="categoria",
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("items.editar")
def categoria_edit(request, categoria_id):
    categoria = _obtener_catalogo(
        CategoriaItem,
        request.empresa_activa,
        categoria_id,
        activo=True,
    )
    return _catalogo_form(
        request,
        objeto=categoria,
        form_class=CategoriaItemForm,
        servicio=actualizar_categoria,
        titulo="Editar categoría",
        lista_url="items:categoria_list",
        tipo_objeto="categoria",
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("items.editar")
@require_POST
def categoria_deactivate(request, categoria_id):
    categoria = _obtener_catalogo(
        CategoriaItem,
        request.empresa_activa,
        categoria_id,
    )
    try:
        categoria = inactivar_categoria(
            empresa=request.empresa_activa,
            categoria=categoria,
            request=request,
        )
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(
            request,
            f"Categoría {categoria.codigo} inactivada correctamente.",
        )
    return redirect("items:categoria_list")


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("items.crear")
def marca_create(request):
    return _catalogo_form(
        request,
        objeto=None,
        form_class=MarcaForm,
        servicio=crear_marca,
        titulo="Nueva marca",
        lista_url="items:marca_list",
        tipo_objeto="marca",
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("items.editar")
def marca_edit(request, marca_id):
    marca = _obtener_catalogo(
        Marca,
        request.empresa_activa,
        marca_id,
        activo=True,
    )
    return _catalogo_form(
        request,
        objeto=marca,
        form_class=MarcaForm,
        servicio=actualizar_marca,
        titulo="Editar marca",
        lista_url="items:marca_list",
        tipo_objeto="marca",
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("items.editar")
@require_POST
def marca_deactivate(request, marca_id):
    marca = _obtener_catalogo(
        Marca,
        request.empresa_activa,
        marca_id,
    )
    try:
        marca = inactivar_marca(
            empresa=request.empresa_activa,
            marca=marca,
            request=request,
        )
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(
            request,
            f"Marca {marca.codigo} inactivada correctamente.",
        )
    return redirect("items:marca_list")
