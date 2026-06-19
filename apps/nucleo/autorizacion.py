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


def empresa_activa_requerida(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if getattr(request, "empresa_activa", None) is None:
            messages.warning(
                request,
                "Primero tenés que seleccionar una empresa.",
            )
            selector = reverse("core:seleccionar_empresa")
            next_url = request.get_full_path()
            return redirect(
                f"{selector}?{urlencode({'next': next_url})}"
            )

        return view_func(request, *args, **kwargs)

    return wrapper


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
