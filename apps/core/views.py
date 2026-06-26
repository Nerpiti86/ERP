from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.nucleo.empresa_activa import (
    empresas_disponibles_para_usuario,
    limpiar_empresa_activa,
    seleccionar_empresa_para_sesion,
)
from apps.nucleo.models import Empresa, EjercicioFiscal, PeriodoContable, Sucursal
from apps.nucleo.sucursal_activa import (
    seleccionar_sucursal_para_sesion,
    sucursales_disponibles_para_usuario,
)

from .forms import ERPAuthenticationForm


def _url_interna_segura(request, url):
    return bool(
        url
        and url_has_allowed_host_and_scheme(
            url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        )
    )


def _redireccion_segura_o_inicio(request, next_url):
    if _url_interna_segura(request, next_url):
        return redirect(next_url)

    return redirect("core:home")


def _destino_inicial_usuario(request, usuario):
    empresas = empresas_disponibles_para_usuario(usuario)
    empresa_ids = list(empresas.values_list("pk", flat=True)[:2])

    if len(empresa_ids) == 0:
        return "core:home"

    if len(empresa_ids) > 1:
        return "core:seleccionar_empresa"

    empresa = seleccionar_empresa_para_sesion(
        request,
        empresa_ids[0],
    )
    request.empresa_activa = empresa

    sucursales = sucursales_disponibles_para_usuario(
        usuario,
        empresa,
    )
    sucursal_ids = list(sucursales.values_list("pk", flat=True)[:2])

    if len(sucursal_ids) > 1:
        return "core:seleccionar_sucursal"

    return "core:home"


def iniciar_sesion(request):
    if request.user.is_authenticated:
        return redirect("core:home")

    next_url = request.POST.get("next") or request.GET.get("next") or ""
    form = ERPAuthenticationForm(
        request=request,
        data=request.POST if request.method == "POST" else None,
    )

    if request.method == "POST" and form.is_valid():
        usuario = form.get_user()
        auth_login(request, usuario)
        limpiar_empresa_activa(request)

        messages.success(
            request,
            f"Bienvenido, {usuario.get_username()}.",
        )

        if _url_interna_segura(request, next_url):
            return redirect(next_url)

        return redirect(_destino_inicial_usuario(request, usuario))

    return render(
        request,
        "core/login.html",
        {
            "form": form,
            "next": next_url,
        },
    )


@login_required
@require_POST
def cerrar_sesion(request):
    auth_logout(request)
    messages.success(request, "La sesión se cerró correctamente.")
    return redirect("core:login")


@login_required
def home(request):
    modo = getattr(settings, "ERP_APP_MODE", "integrado")
    plantillas = {
        "gestion": "core/home_gestion.html",
        "contabilidad": "core/home_contabilidad.html",
    }
    plantilla = plantillas.get(modo, "core/home.html")
    contexto = {}

    if modo == "integrado":
        empresa = request.empresa_activa

        if empresa is None:
            metricas = {
                "empresas": request.empresas_disponibles.count(),
                "sucursales": 0,
                "ejercicios": 0,
                "periodos": 0,
            }
        else:
            metricas = {
                "empresas": 1,
                "sucursales": request.sucursales_disponibles.count(),
                "ejercicios": EjercicioFiscal.objects.filter(
                    empresa=empresa,
                ).count(),
                "periodos": PeriodoContable.objects.filter(
                    ejercicio__empresa=empresa,
                ).count(),
            }

        contexto["metricas"] = metricas

    return render(request, plantilla, contexto)


@login_required
def seleccionar_empresa(request):
    empresas = list(request.empresas_disponibles)
    next_url = request.POST.get("next") or request.GET.get("next") or ""

    if request.method == "POST":
        empresa_id = request.POST.get("empresa_id")

        if not empresa_id:
            messages.error(request, "Tenés que seleccionar una empresa.")
        else:
            try:
                empresa = seleccionar_empresa_para_sesion(
                    request,
                    empresa_id,
                )
            except PermissionDenied:
                raise

            messages.success(
                request,
                f"Empresa activa: {empresa.razon_social}.",
            )
            return _redireccion_segura_o_inicio(request, next_url)

    return render(
        request,
        "core/seleccionar_empresa.html",
        {
            "empresas": empresas,
            "next": next_url,
        },
    )


@login_required
def seleccionar_sucursal(request):
    if request.empresa_activa is None:
        messages.warning(
            request,
            "Primero tenés que seleccionar una empresa.",
        )
        selector_empresa = reverse("core:seleccionar_empresa")
        next_url = request.get_full_path()
        return redirect(
            f"{selector_empresa}?{urlencode({'next': next_url})}"
        )

    sucursales = list(request.sucursales_disponibles)
    next_url = request.POST.get("next") or request.GET.get("next") or ""

    if request.method == "POST":
        sucursal_id = request.POST.get("sucursal_id")

        if not sucursal_id:
            messages.error(request, "Tenés que seleccionar una sucursal.")
        else:
            try:
                sucursal = seleccionar_sucursal_para_sesion(
                    request,
                    sucursal_id,
                )
            except PermissionDenied:
                raise

            messages.success(
                request,
                f"Sucursal activa: {sucursal.nombre}.",
            )
            return _redireccion_segura_o_inicio(request, next_url)

    return render(
        request,
        "core/seleccionar_sucursal.html",
        {
            "sucursales": sucursales,
            "next": next_url,
        },
    )
