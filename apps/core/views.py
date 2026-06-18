from django.shortcuts import render

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
