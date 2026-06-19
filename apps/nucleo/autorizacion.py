from functools import wraps
from urllib.parse import urlencode

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse

from .permisos import (
    usuario_tiene_alguno_de_permisos,
    usuario_tiene_permiso,
)


def _redirigir_a_selector(request, nombre_url, mensaje):
    messages.warning(request, mensaje)
    selector = reverse(nombre_url)
    next_url = request.get_full_path()
    return redirect(
        f"{selector}?{urlencode({'next': next_url})}"
    )


def empresa_activa_requerida(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if getattr(request, "empresa_activa", None) is None:
            return _redirigir_a_selector(
                request,
                "core:seleccionar_empresa",
                "Primero tenés que seleccionar una empresa.",
            )

        return view_func(request, *args, **kwargs)

    return wrapper


def sucursal_activa_requerida(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if getattr(request, "empresa_activa", None) is None:
            return _redirigir_a_selector(
                request,
                "core:seleccionar_empresa",
                "Primero tenés que seleccionar una empresa.",
            )

        if getattr(request, "sucursal_activa", None) is None:
            return _redirigir_a_selector(
                request,
                "core:seleccionar_sucursal",
                "Primero tenés que seleccionar una sucursal.",
            )

        return view_func(request, *args, **kwargs)

    return wrapper


def contexto_operativo_requerido(
    view_func=None,
    *,
    requiere_sucursal=True,
):
    # Exige empresa y, por defecto, sucursal activas.

    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if getattr(request, "empresa_activa", None) is None:
                return _redirigir_a_selector(
                    request,
                    "core:seleccionar_empresa",
                    "Primero tenés que seleccionar una empresa.",
                )

            if (
                requiere_sucursal
                and getattr(request, "sucursal_activa", None) is None
            ):
                return _redirigir_a_selector(
                    request,
                    "core:seleccionar_sucursal",
                    "Primero tenés que seleccionar una sucursal.",
                )

            return func(request, *args, **kwargs)

        return wrapper

    if view_func is None:
        return decorator

    return decorator(view_func)


def permiso_funcional_alguno_requerido(*codigos_permisos):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not usuario_tiene_alguno_de_permisos(
                request.user,
                request.empresa_activa,
                codigos_permisos,
            ):
                raise PermissionDenied

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def permiso_funcional_requerido(codigo_permiso):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not usuario_tiene_permiso(
                request.user,
                request.empresa_activa,
                codigo_permiso,
            ):
                raise PermissionDenied

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
