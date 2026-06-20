from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST

from .autorizacion import (
    contexto_operativo_requerido,
    permiso_funcional_alguno_requerido,
    permiso_funcional_requerido,
)
from .forms import ConfiguracionEmpresaForm
from .models import UsuarioEmpresa, UsuarioRolEmpresa
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
@require_GET
def configuracion_empresa(request):
    empresa = request.empresa_activa
    estado_parametros = obtener_estado_parametros_empresa(empresa)
    datos_parametros = {}
    advertencias_parametros = ()

    if estado_parametros["completa"]:
        (
            datos_parametros,
            advertencias_parametros,
        ) = obtener_datos_configuracion_empresa(empresa)

    sucursales = list(
        empresa.sucursales.order_by(
            "-activa",
            "codigo",
            "nombre",
        )
    )
    sucursales_activas = sum(
        1 for sucursal in sucursales if sucursal.activa
    )
    usuarios_activos = (
        UsuarioEmpresa.objects.filter(
            empresa=empresa,
            activo=True,
            usuario__is_active=True,
        )
        .values("usuario_id")
        .distinct()
        .count()
    )
    roles_asignados = UsuarioRolEmpresa.objects.filter(
        empresa=empresa,
        activo=True,
        usuario__is_active=True,
        rol__activo=True,
    ).count()

    configuracion_base_lista = (
        empresa.activa
        and sucursales_activas > 0
        and estado_parametros["completa"]
        and not advertencias_parametros
    )

    return render(
        request,
        "nucleo/configuracion_empresa.html",
        {
            "empresa": empresa,
            "sucursales": sucursales,
            "estado_parametros": estado_parametros,
            "datos_parametros": datos_parametros,
            "advertencias_parametros": advertencias_parametros,
            "configuracion_base_lista": configuracion_base_lista,
            "resumen": {
                "sucursales_total": len(sucursales),
                "sucursales_activas": sucursales_activas,
                "usuarios_activos": usuarios_activos,
                "roles_asignados": roles_asignados,
            },
        },
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_alguno_requerido(
    *PERMISOS_CONSULTA_CONFIGURACION
)
def parametros_operativos(request):
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
                return redirect("nucleo:parametros_operativos")
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
        return redirect("nucleo:parametros_operativos")

    return render(
        request,
        "nucleo/parametros_operativos.html",
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

    return redirect("nucleo:parametros_operativos")
