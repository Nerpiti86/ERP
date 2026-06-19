"""Servicios para resolver la sucursal activa de una sesión."""

from django.core.exceptions import PermissionDenied

from .models import Sucursal, UsuarioEmpresa


SESSION_SUCURSAL_ACTIVA_ID = "nucleo_sucursal_activa_id"


def sucursales_disponibles_para_usuario(usuario, empresa):
    """Devuelve sucursales activas y habilitadas dentro de una empresa."""

    if (
        usuario is None
        or not getattr(usuario, "is_authenticated", False)
        or not getattr(usuario, "is_active", False)
        or empresa is None
        or not getattr(empresa, "activa", False)
    ):
        return Sucursal.objects.none()

    sucursales = Sucursal.objects.filter(
        empresa=empresa,
        activa=True,
    )

    if usuario.is_superuser:
        return sucursales.order_by("codigo", "nombre", "id")

    tiene_acceso_empresa = UsuarioEmpresa.objects.filter(
        usuario=usuario,
        empresa=empresa,
        activo=True,
    ).exists()

    if not tiene_acceso_empresa:
        return Sucursal.objects.none()

    return (
        sucursales.filter(
            usuarios_asignados__usuario=usuario,
            usuarios_asignados__activo=True,
        )
        .distinct()
        .order_by("codigo", "nombre", "id")
    )


def obtener_sucursal_activa(
    request,
    *,
    empresa_activa,
    sucursales_disponibles=None,
    auto_seleccionar_unica=True,
):
    """Resuelve la sucursal activa y limpia selecciones inválidas."""

    if empresa_activa is None:
        limpiar_sucursal_activa(request)
        return None

    if sucursales_disponibles is None:
        sucursales_disponibles = sucursales_disponibles_para_usuario(
            request.user,
            empresa_activa,
        )

    sucursal_id = request.session.get(SESSION_SUCURSAL_ACTIVA_ID)

    if sucursal_id is not None:
        sucursal = sucursales_disponibles.filter(pk=sucursal_id).first()

        if sucursal is not None:
            return sucursal

        limpiar_sucursal_activa(request)

    if auto_seleccionar_unica:
        ids_disponibles = list(
            sucursales_disponibles.values_list("pk", flat=True)[:2]
        )

        if len(ids_disponibles) == 1:
            sucursal = sucursales_disponibles.get(pk=ids_disponibles[0])
            request.session[SESSION_SUCURSAL_ACTIVA_ID] = sucursal.pk
            request.session.modified = True
            return sucursal

    return None


def seleccionar_sucursal_para_sesion(request, sucursal_id):
    """Guarda una sucursal autorizada de la empresa activa."""

    empresa_activa = getattr(request, "empresa_activa", None)

    if empresa_activa is None:
        raise PermissionDenied(
            "Debe seleccionar una empresa antes de elegir una sucursal."
        )

    sucursales_disponibles = sucursales_disponibles_para_usuario(
        request.user,
        empresa_activa,
    )

    try:
        sucursal = sucursales_disponibles.get(pk=sucursal_id)
    except (Sucursal.DoesNotExist, TypeError, ValueError) as exc:
        raise PermissionDenied(
            "El usuario no puede seleccionar la sucursal solicitada."
        ) from exc

    request.session[SESSION_SUCURSAL_ACTIVA_ID] = sucursal.pk
    request.session.modified = True
    return sucursal


def limpiar_sucursal_activa(request):
    """Elimina la sucursal activa de la sesión."""

    request.session.pop(SESSION_SUCURSAL_ACTIVA_ID, None)
    request.session.modified = True
