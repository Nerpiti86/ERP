from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from apps.nucleo.empresa_activa import seleccionar_empresa_para_sesion
from apps.nucleo.models import Empresa, EjercicioFiscal, PeriodoContable, Sucursal


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

            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)

            return redirect("core:home")

    return render(
        request,
        "core/seleccionar_empresa.html",
        {
            "empresas": empresas,
            "next": next_url,
        },
    )
