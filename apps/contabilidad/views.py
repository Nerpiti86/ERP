from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from apps.nucleo.autorizacion import (
    contexto_operativo_requerido,
    permiso_funcional_alguno_requerido,
    permiso_funcional_requerido,
)
from apps.nucleo.permisos import usuario_tiene_permiso

from .forms import CuentaContableCrearForm
from .models import CuentaContable


PERMISOS_CONSULTA_PLAN = (
    "contabilidad.ver",
    "contabilidad.editar",
)


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_alguno_requerido(*PERMISOS_CONSULTA_PLAN)
@require_http_methods(["GET"])
def plan_cuentas(request):
    empresa = request.empresa_activa
    base = CuentaContable.objects.filter(empresa=empresa)

    busqueda = request.GET.get("q", "").strip()
    tipo_contable = request.GET.get("tipo", "").strip()
    estado = request.GET.get("estado", "").strip()
    clase = request.GET.get("clase", "").strip()

    cuentas = base.select_related("parent").order_by("codigo")

    if busqueda:
        cuentas = cuentas.filter(
            Q(codigo__icontains=busqueda)
            | Q(nombre__icontains=busqueda)
            | Q(descripcion__icontains=busqueda)
        )

    if tipo_contable in set(CuentaContable.TipoContable.values):
        cuentas = cuentas.filter(tipo_contable=tipo_contable)
    else:
        tipo_contable = ""

    if estado == "habilitadas":
        cuentas = cuentas.filter(habilitada=True)
    elif estado == "deshabilitadas":
        cuentas = cuentas.filter(habilitada=False)
    else:
        estado = ""

    if clase == "agrupadoras":
        cuentas = cuentas.filter(codigo__endswith=".000")
    elif clase == "imputables":
        cuentas = cuentas.exclude(codigo__endswith=".000")
    else:
        clase = ""

    cuentas = list(cuentas)
    cantidad_resultados = len(cuentas)

    puede_crear = usuario_tiene_permiso(
        request.user,
        empresa,
        "contabilidad.editar",
    )

    return render(
        request,
        "contabilidad/plan_cuentas.html",
        {
            "empresa": empresa,
            "cuentas": cuentas,
            "cantidad_resultados": cantidad_resultados,
            "puede_crear": puede_crear,
            "tipo_opciones": CuentaContable.TipoContable.choices,
            "filtros": {
                "q": busqueda,
                "tipo": tipo_contable,
                "estado": estado,
                "clase": clase,
            },
            "hay_filtros": any(
                (busqueda, tipo_contable, estado, clase)
            ),
        },
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("contabilidad.editar")
@require_http_methods(["GET", "POST"])
def crear_cuenta(request):
    empresa = request.empresa_activa
    form = CuentaContableCrearForm(
        request.POST if request.method == "POST" else None
    )

    if request.method == "POST" and form.is_valid():
        cuenta = form.crear(empresa=empresa)

        if cuenta is not None:
            messages.success(
                request,
                f"Cuenta {cuenta.codigo} — {cuenta.nombre} creada.",
            )
            destino = reverse("contabilidad:plan_cuentas")
            return redirect(
                f"{destino}?{urlencode({'q': cuenta.codigo})}"
            )

    codigo = form.data.get("codigo", "").strip() if form.is_bound else ""
    codigo_padre_esperado = (
        CuentaContable.codigo_padre_desde_codigo(codigo)
        if codigo
        else None
    )
    cuenta_superior_esperada = None

    if codigo_padre_esperado:
        cuenta_superior_esperada = (
            CuentaContable.objects.filter(
                empresa=empresa,
                codigo=codigo_padre_esperado,
            )
            .only("codigo", "nombre")
            .first()
        )

    return render(
        request,
        "contabilidad/cuenta_form.html",
        {
            "empresa": empresa,
            "form": form,
            "codigo_padre_esperado": codigo_padre_esperado,
            "cuenta_superior_esperada": cuenta_superior_esperada,
        },
    )
