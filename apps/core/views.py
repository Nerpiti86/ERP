from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from apps.nucleo.empresa_activa import seleccionar_empresa_para_sesion
from apps.nucleo.models import Empresa, EjercicioFiscal, PeriodoContable, Sucursal
from apps.nucleo.sucursal_activa import seleccionar_sucursal_para_sesion


def home(request):
    contexto = {
        "metricas": {
            "empresas": Empresa.objects.count(),
            "sucursales": Sucursal.objects.count(),
            "ejercicios": EjercicioFiscal.objects.count(),
            "periodos": PeriodoContable.objects.count(),
        }
    }

    return render(request, "core/home.html", contexto)


def _redireccion_segura_o_inicio(request, next_url):
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)

    return redirect("core:home")


@login_required(login_url="/admin/login/")
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


@login_required(login_url="/admin/login/")
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
