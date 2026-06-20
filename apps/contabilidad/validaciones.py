from django.core.exceptions import ValidationError


def normalizar_campos(cuenta):
    cuenta.codigo = (cuenta.codigo or "").strip()
    cuenta.nombre = " ".join((cuenta.nombre or "").split())
    cuenta.descripcion = (cuenta.descripcion or "").strip()
    cuenta.naturaleza = cuenta.naturaleza or None


def _validar_raiz(cuenta, errores):
    if cuenta.parent_id is not None:
        errores["parent"] = "Una cuenta raiz no puede tener superior."

    codigo_esperado = cuenta.CODIGOS_RAIZ_POR_TIPO.get(
        cuenta.tipo_contable
    )
    if codigo_esperado is not None and cuenta.codigo != codigo_esperado:
        errores["codigo"] = (
            "El codigo raiz no corresponde al tipo contable seleccionado."
        )
    elif (
        cuenta.tipo_contable == cuenta.TipoContable.ORDEN
        and cuenta.codigo in cuenta.CODIGOS_RAIZ_POR_TIPO.values()
    ):
        errores["codigo"] = (
            "Los codigos raiz 1 a 5 estan reservados para los tipos "
            "contables operativos."
        )


def _validar_superior(cuenta, errores):
    if cuenta.parent_id is None:
        errores["parent"] = "La cuenta superior es obligatoria."
        return

    try:
        parent = cuenta.parent
    except cuenta.__class__.DoesNotExist:
        errores["parent"] = "La cuenta superior indicada no existe."
        return

    if parent.empresa_id != cuenta.empresa_id:
        errores["parent"] = (
            "La cuenta superior debe pertenecer a la misma empresa."
        )
    elif parent.codigo != cuenta.codigo_padre_esperado:
        errores["parent"] = (
            "La cuenta superior no coincide con el codigo de la cuenta."
        )
    elif parent.tipo_contable != cuenta.tipo_contable:
        errores["tipo_contable"] = (
            "La cuenta debe conservar el tipo contable de su superior."
        )
    elif parent.imputable:
        errores["parent"] = (
            "Una cuenta imputable no puede tener descendientes."
        )
    elif cuenta.habilitada and not parent.habilitada:
        errores["parent"] = (
            "Una cuenta habilitada no puede depender de una superior "
            "deshabilitada."
        )

    if cuenta.pk is None:
        return

    ancestro = parent
    visitados = set()
    while ancestro is not None and ancestro.pk not in visitados:
        if ancestro.pk == cuenta.pk:
            errores["parent"] = (
                "Una cuenta no puede ubicarse dentro de su propia rama."
            )
            break
        visitados.add(ancestro.pk)
        ancestro = ancestro.parent


def _validar_naturaleza(cuenta, nivel, errores):
    if nivel == 5:
        if cuenta.pk is not None and cuenta.get_children().exists():
            errores["codigo"] = (
                "Una cuenta con descendientes no puede convertirse "
                "directamente en imputable."
            )
        if cuenta.naturaleza not in cuenta.Naturaleza.values:
            errores["naturaleza"] = (
                "La naturaleza es obligatoria para una cuenta imputable."
            )
    elif cuenta.naturaleza is not None:
        errores["naturaleza"] = (
            "Las cuentas agrupadoras no deben tener naturaleza."
        )


def _validar_modificacion(cuenta, errores):
    if cuenta.pk is None:
        return

    original = cuenta.__class__.objects.filter(pk=cuenta.pk).first()
    if original is None:
        return

    if original.empresa_id != cuenta.empresa_id:
        errores["empresa"] = (
            "Una cuenta existente no puede trasladarse a otra empresa."
        )

    cambio_estructural = (
        original.codigo != cuenta.codigo
        or original.parent_id != cuenta.parent_id
        or original.tipo_contable != cuenta.tipo_contable
    )
    if cambio_estructural and cuenta.get_descendant_count() > 0:
        errores["codigo"] = (
            "Una rama con descendientes debe modificarse mediante "
            "el servicio transaccional de renumeracion."
        )

    if not cuenta.habilitada and any(
        descendiente.habilitada
        for descendiente in cuenta.get_descendants()
    ):
        errores["habilitada"] = (
            "No se puede deshabilitar una cuenta con descendientes "
            "habilitados."
        )


def validar_cuenta(cuenta):
    normalizar_campos(cuenta)
    errores = {}
    nivel = cuenta.nivel

    if not cuenta.nombre:
        errores["nombre"] = "El nombre es obligatorio."

    if nivel is None:
        errores["codigo"] = (
            "El codigo debe respetar la mascara y no puede contener "
            "niveles informados despues de un nivel en cero."
        )
    elif nivel == 1:
        _validar_raiz(cuenta, errores)
    else:
        _validar_superior(cuenta, errores)

    _validar_naturaleza(cuenta, nivel, errores)
    _validar_modificacion(cuenta, errores)

    if errores:
        raise ValidationError(errores)
