from django.core.exceptions import ValidationError
from django.db import transaction

from .models import CuentaContable


@transaction.atomic
def crear_cuenta_contable(
    *,
    empresa,
    codigo,
    nombre,
    tipo_contable,
    naturaleza=None,
    descripcion="",
    habilitada=True,
):
    """Crea una cuenta usando el superior derivado de su codigo."""
    codigo = (codigo or "").strip()
    nivel = CuentaContable.nivel_desde_codigo(codigo)
    codigo_padre = CuentaContable.codigo_padre_desde_codigo(codigo)

    datos = {
        "empresa": empresa,
        "codigo": codigo,
        "nombre": nombre,
        "descripcion": descripcion,
        "tipo_contable": tipo_contable,
        "naturaleza": naturaleza,
        "habilitada": habilitada,
    }

    if nivel is None:
        raise ValidationError(
            {"codigo": "El codigo no representa una jerarquia contable valida."}
        )

    if nivel == 1:
        return CuentaContable.add_root(**datos)

    if codigo_padre is None:
        raise ValidationError(
            {"codigo": "No se pudo determinar la cuenta superior esperada."}
        )

    try:
        parent = CuentaContable.objects.select_for_update().get(
            empresa=empresa,
            codigo=codigo_padre,
        )
    except CuentaContable.DoesNotExist as exc:
        raise ValidationError(
            {
                "parent": (
                    "No existe la cuenta superior esperada "
                    f"{codigo_padre} en la empresa."
                )
            }
        ) from exc

    return parent.add_child(**datos)
