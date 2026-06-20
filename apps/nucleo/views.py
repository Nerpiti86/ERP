from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from .autorizacion import (
    contexto_operativo_requerido,
    permiso_funcional_alguno_requerido,
    permiso_funcional_requerido,
)
from .forms import (
    ConfiguracionEmpresaForm,
    DatosContribuyenteForm,
    SucursalForm,
)
from .models import (
    PerfilFiscalEmpresa,
    Sucursal,
    UsuarioEmpresa,
    UsuarioRolEmpresa,
)
from .parametros_empresa import (
    PARAMETROS_EMPRESA_ESTANDAR,
    guardar_configuracion_empresa,
    inicializar_parametros_empresa,
    obtener_datos_configuracion_empresa,
    obtener_estado_parametros_empresa,
)
from .permisos import (
    usuario_tiene_alguno_de_permisos,
    usuario_tiene_permiso,
)


PERMISOS_CONSULTA_CONFIGURACION = (
    "empresas.ver",
    "empresas.editar",
    "sucursales.ver",
    "sucursales.crear",
    "sucursales.editar",
    "parametros.ver",
    "parametros.editar",
)

PERMISOS_DATOS_CONTRIBUYENTE = (
    "empresas.ver",
    "empresas.editar",
)

PERMISOS_SUCURSALES = (
    "sucursales.ver",
    "sucursales.crear",
    "sucursales.editar",
)


def _obtener_perfil_fiscal(empresa):
    try:
        return empresa.perfil_fiscal
    except PerfilFiscalEmpresa.DoesNotExist:
        return None


def _datos_contribuyente_completos(empresa, perfil):
    return bool(
        empresa.nombre_fantasia.strip()
        and perfil is not None
        and perfil.esta_completo
    )


def _resumen_sucursales(sucursales):
    activas = [
        sucursal
        for sucursal in sucursales
        if sucursal.activa
    ]
    completas = [
        sucursal
        for sucursal in activas
        if sucursal.domicilio_estructurado_completo
    ]
    casa_central = next(
        (
            sucursal
            for sucursal in activas
            if sucursal.es_casa_central
        ),
        None,
    )

    return {
        "total": len(sucursales),
        "activas": len(activas),
        "domicilios_completos": len(completas),
        "casa_central": casa_central,
        "completa": bool(
            activas
            and len(completas) == len(activas)
            and casa_central is not None
        ),
    }


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_alguno_requerido(
    *PERMISOS_CONSULTA_CONFIGURACION
)
@require_GET
def configuracion_empresa(request):
    empresa = request.empresa_activa
    perfil_fiscal = _obtener_perfil_fiscal(empresa)
    datos_contribuyente_completos = _datos_contribuyente_completos(
        empresa,
        perfil_fiscal,
    )
    puede_editar_datos_contribuyente = usuario_tiene_permiso(
        request.user,
        empresa,
        "empresas.editar",
    )
    puede_ver_sucursales = usuario_tiene_alguno_de_permisos(
        request.user,
        empresa,
        PERMISOS_SUCURSALES,
    )

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
    resumen_sucursales = _resumen_sucursales(sucursales)

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
        and datos_contribuyente_completos
        and resumen_sucursales["completa"]
        and estado_parametros["completa"]
        and not advertencias_parametros
    )

    return render(
        request,
        "nucleo/configuracion_empresa.html",
        {
            "empresa": empresa,
            "perfil_fiscal": perfil_fiscal,
            "datos_contribuyente_completos": (
                datos_contribuyente_completos
            ),
            "puede_editar_datos_contribuyente": (
                puede_editar_datos_contribuyente
            ),
            "puede_ver_sucursales": puede_ver_sucursales,
            "sucursales": sucursales,
            "resumen_sucursales": resumen_sucursales,
            "estado_parametros": estado_parametros,
            "datos_parametros": datos_parametros,
            "advertencias_parametros": advertencias_parametros,
            "configuracion_base_lista": configuracion_base_lista,
            "resumen": {
                "sucursales_total": resumen_sucursales["total"],
                "sucursales_activas": resumen_sucursales["activas"],
                "usuarios_activos": usuarios_activos,
                "roles_asignados": roles_asignados,
            },
        },
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_alguno_requerido(
    *PERMISOS_DATOS_CONTRIBUYENTE
)
def datos_contribuyente(request):
    empresa = request.empresa_activa
    perfil = _obtener_perfil_fiscal(empresa)
    puede_editar = usuario_tiene_permiso(
        request.user,
        empresa,
        "empresas.editar",
    )

    if request.method == "POST" and not puede_editar:
        raise PermissionDenied

    if request.method == "POST":
        form = DatosContribuyenteForm(
            request.POST,
            empresa=empresa,
            perfil=perfil,
        )

        if form.is_valid():
            empresa, perfil = form.save()
            messages.success(
                request,
                (
                    f"Datos del contribuyente {empresa.razon_social} "
                    "guardados correctamente."
                ),
            )
            return redirect("nucleo:datos_contribuyente")
    else:
        form = DatosContribuyenteForm(
            empresa=empresa,
            perfil=perfil,
        )

    if not puede_editar:
        for campo in form.fields.values():
            campo.disabled = True

    return render(
        request,
        "nucleo/datos_contribuyente.html",
        {
            "empresa": empresa,
            "perfil": perfil,
            "form": form,
            "puede_editar": puede_editar,
        },
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_alguno_requerido(*PERMISOS_SUCURSALES)
@require_GET
def sucursales(request):
    empresa = request.empresa_activa
    registros = list(
        Sucursal.objects.filter(empresa=empresa).order_by(
            "-activa",
            "codigo",
            "nombre",
        )
    )

    return render(
        request,
        "nucleo/sucursales.html",
        {
            "empresa": empresa,
            "sucursales": registros,
            "resumen": _resumen_sucursales(registros),
            "puede_crear": usuario_tiene_permiso(
                request.user,
                empresa,
                "sucursales.crear",
            ),
            "puede_editar": usuario_tiene_permiso(
                request.user,
                empresa,
                "sucursales.editar",
            ),
        },
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("sucursales.crear")
def sucursal_crear(request):
    empresa = request.empresa_activa

    if request.method == "POST":
        form = SucursalForm(
            request.POST,
            empresa=empresa,
        )

        if form.is_valid():
            sucursal = form.save()
            messages.success(
                request,
                (
                    f"Sucursal {sucursal.codigo} · {sucursal.nombre} "
                    "creada correctamente."
                ),
            )
            return redirect("nucleo:sucursales")
    else:
        form = SucursalForm(empresa=empresa)

    return render(
        request,
        "nucleo/sucursal_form.html",
        {
            "empresa": empresa,
            "form": form,
            "sucursal": None,
            "titulo": "Nueva sucursal",
        },
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("sucursales.editar")
def sucursal_editar(request, sucursal_id):
    empresa = request.empresa_activa
    sucursal = get_object_or_404(
        Sucursal,
        pk=sucursal_id,
        empresa=empresa,
    )

    if request.method == "POST":
        form = SucursalForm(
            request.POST,
            instance=sucursal,
            empresa=empresa,
        )

        if form.is_valid():
            sucursal = form.save()
            messages.success(
                request,
                (
                    f"Sucursal {sucursal.codigo} · {sucursal.nombre} "
                    "actualizada correctamente."
                ),
            )
            return redirect("nucleo:sucursales")
    else:
        form = SucursalForm(
            instance=sucursal,
            empresa=empresa,
        )

    return render(
        request,
        "nucleo/sucursal_form.html",
        {
            "empresa": empresa,
            "form": form,
            "sucursal": sucursal,
            "titulo": "Editar sucursal",
        },
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_alguno_requerido(
    "parametros.ver",
    "parametros.editar",
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
