from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import ConfiguracionEmpresaForm
from .parametros_empresa import (
    PARAMETROS_EMPRESA_ESTANDAR,
    guardar_configuracion_empresa,
    inicializar_parametros_empresa,
    obtener_datos_configuracion_empresa,
    obtener_estado_parametros_empresa,
)


def _resolver_empresa_para_configuracion(request):
    if not request.user.is_staff:
        raise PermissionDenied

    if request.empresa_activa is not None:
        return request.empresa_activa, None

    selector = reverse("core:seleccionar_empresa")
    next_url = request.get_full_path()
    messages.warning(
        request,
        "Primero tenés que seleccionar una empresa.",
    )
    return None, redirect(
        f"{selector}?{urlencode({'next': next_url})}"
    )


@login_required
def configuracion_empresa(request):
    empresa, respuesta = _resolver_empresa_para_configuracion(request)

    if respuesta is not None:
        return respuesta

    estado = obtener_estado_parametros_empresa(empresa)
    form = None
    advertencias = ()

    if estado["completa"]:
        datos_iniciales, advertencias = obtener_datos_configuracion_empresa(
            empresa
        )

        if request.method == "POST":
            form = ConfiguracionEmpresaForm(request.POST)

            if form.is_valid():
                resultado = guardar_configuracion_empresa(
                    empresa,
                    form.cleaned_data,
                )
                total = (
                    len(resultado["creados"])
                    + len(resultado["actualizados"])
                )
                messages.success(
                    request,
                    (
                        f"Configuración de {empresa.razon_social} guardada. "
                        f"Parámetros procesados: {total}."
                    ),
                )
                return redirect("nucleo:configuracion_empresa")
        else:
            form = ConfiguracionEmpresaForm(initial=datos_iniciales)
    elif request.method == "POST":
        messages.warning(
            request,
            "Inicializá la configuración antes de editarla.",
        )
        return redirect("nucleo:configuracion_empresa")

    return render(
        request,
        "nucleo/configuracion_empresa.html",
        {
            "empresa": empresa,
            "estado": estado,
            "form": form,
            "advertencias": advertencias,
            "definiciones": PARAMETROS_EMPRESA_ESTANDAR,
        },
    )


@login_required
@require_POST
def inicializar_configuracion_empresa(request):
    empresa, respuesta = _resolver_empresa_para_configuracion(request)

    if respuesta is not None:
        return respuesta

    resultado = inicializar_parametros_empresa(empresa)
    creados = len(resultado["creados"])
    reactivados = len(resultado["reactivados"])
    existentes = len(resultado["existentes"])

    if creados or reactivados:
        messages.success(
            request,
            (
                f"Configuración inicializada para {empresa.razon_social}. "
                f"Creados: {creados}; reactivados: {reactivados}; "
                f"ya existentes: {existentes}."
            ),
        )
    else:
        messages.info(
            request,
            "La empresa ya tenía todos los parámetros estándar activos.",
        )

    return redirect("nucleo:configuracion_empresa")
