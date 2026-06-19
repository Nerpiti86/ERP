from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .autorizacion import (
    contexto_operativo_requerido,
    permiso_funcional_alguno_requerido,
    permiso_funcional_requerido,
)
from .forms import ConfiguracionEmpresaForm
from .parametros_empresa import (
    PARAMETROS_EMPRESA_ESTANDAR,
    guardar_configuracion_empresa,
    inicializar_parametros_empresa,
    obtener_datos_configuracion_empresa,
    obtener_estado_parametros_empresa,
)
from .permisos import usuario_tiene_permiso


PERMISOS_CONSULTA_CONFIGURACION = (
    "parametros.ver",
    "parametros.editar",
)


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_alguno_requerido(
    *PERMISOS_CONSULTA_CONFIGURACION
)
def configuracion_empresa(request):
    empresa = request.empresa_activa
    puede_editar = usuario_tiene_permiso(
        request.user,
        empresa,
        "parametros.editar",
    )

    if request.method == "POST" and not puede_editar:
        raise PermissionDenied

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

        if not puede_editar:
            for campo in form.fields.values():
                campo.disabled = True

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
            "puede_editar": puede_editar,
        },
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("parametros.editar")
@require_POST
def inicializar_configuracion_empresa(request):
    empresa = request.empresa_activa
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
