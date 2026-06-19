"""Servicios para resolver la empresa activa de una sesión."""

from django.core.exceptions import PermissionDenied

from .models import Empresa


SESSION_EMPRESA_ACTIVA_ID = "nucleo_empresa_activa_id"


def empresas_disponibles_para_usuario(usuario):
    """Devuelve las empresas activas que un usuario puede seleccionar."""

    if (
        usuario is None
        or not getattr(usuario, "is_authenticated", False)
        or not getattr(usuario, "is_active", False)
    ):
        return Empresa.objects.none()

    empresas = Empresa.objects.filter(activa=True)

    if usuario.is_superuser:
        return empresas.order_by("razon_social", "id")

    return (
        empresas.filter(
            usuarios_asignados__usuario=usuario,
            usuarios_asignados__activo=True,
        )
        .distinct()
        .order_by("razon_social", "id")
    )


def obtener_empresa_activa(
    request,
    *,
    empresas_disponibles=None,
    auto_seleccionar_unica=True,
):
    """Resuelve la empresa activa y limpia selecciones que ya no son válidas."""

    if empresas_disponibles is None:
        empresas_disponibles = empresas_disponibles_para_usuario(request.user)

    empresa_id = request.session.get(SESSION_EMPRESA_ACTIVA_ID)

    if empresa_id is not None:
        empresa = empresas_disponibles.filter(pk=empresa_id).first()

        if empresa is not None:
            return empresa

        request.session.pop(SESSION_EMPRESA_ACTIVA_ID, None)
        request.session.modified = True

    if auto_seleccionar_unica:
        ids_disponibles = list(
            empresas_disponibles.values_list("pk", flat=True)[:2]
        )

        if len(ids_disponibles) == 1:
            empresa = empresas_disponibles.get(pk=ids_disponibles[0])
            request.session[SESSION_EMPRESA_ACTIVA_ID] = empresa.pk
            request.session.modified = True
            return empresa

    return None


def seleccionar_empresa_para_sesion(request, empresa_id):
    """Guarda en sesión una empresa que el usuario tenga habilitada."""

    empresas_disponibles = empresas_disponibles_para_usuario(request.user)

    try:
        empresa = empresas_disponibles.get(pk=empresa_id)
    except (Empresa.DoesNotExist, TypeError, ValueError) as exc:
        raise PermissionDenied(
            "El usuario no puede seleccionar la empresa solicitada."
        ) from exc

    request.session[SESSION_EMPRESA_ACTIVA_ID] = empresa.pk
    request.session.modified = True
    return empresa


def limpiar_empresa_activa(request):
    """Elimina la empresa activa de la sesión."""

    request.session.pop(SESSION_EMPRESA_ACTIVA_ID, None)
    request.session.modified = True
