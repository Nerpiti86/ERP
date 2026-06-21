from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.http import JsonResponse
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
    ConfiguracionIIBBEmpresaForm,
    EmpresaActividadCrearForm,
    EmpresaActividadEditarForm,
    EmpresaJurisdiccionIIBBCrearForm,
    EmpresaJurisdiccionIIBBEditarForm,
    SucursalForm,
)
from .models import (
    ActividadEconomica,
    ConfiguracionIIBBEmpresa,
    EmpresaActividad,
    EmpresaJurisdiccionIIBB,
    ImportacionCatalogoActividad,
    JurisdiccionFiscal,
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
from .servicios_actividades import (
    actualizar_empresa_actividad,
    crear_empresa_actividad,
    inactivar_empresa_actividad,
)
from .servicios_iibb import (
    actualizar_configuracion_iibb,
    actualizar_jurisdiccion_iibb,
    crear_configuracion_iibb,
    crear_jurisdiccion_iibb,
    inactivar_configuracion_iibb,
    inactivar_jurisdiccion_iibb,
)


PERMISOS_CONSULTA_CONFIGURACION = (
    "empresas.ver",
    "empresas.editar",
    "sucursales.ver",
    "sucursales.crear",
    "sucursales.editar",
    "actividades.ver",
    "actividades.crear",
    "actividades.editar",
    "iibb.ver",
    "iibb.crear",
    "iibb.editar",
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


PERMISOS_ACTIVIDADES = (
    "actividades.ver",
    "actividades.crear",
    "actividades.editar",
)


PERMISOS_IIBB = (
    "iibb.ver",
    "iibb.crear",
    "iibb.editar",
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


def _resumen_actividades(actividades):
    activas = [
        relacion
        for relacion in actividades
        if relacion.activa
    ]
    principal = next(
        (
            relacion
            for relacion in activas
            if relacion.principal
        ),
        None,
    )

    return {
        "total": len(actividades),
        "activas": len(activas),
        "secundarias_activas": len(
            [
                relacion
                for relacion in activas
                if not relacion.principal
            ]
        ),
        "principal": principal,
        "completa": bool(activas and principal is not None),
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
    puede_ver_actividades = usuario_tiene_alguno_de_permisos(
        request.user,
        empresa,
        PERMISOS_ACTIVIDADES,
    )
    puede_ver_iibb = usuario_tiene_alguno_de_permisos(
        request.user,
        empresa,
        PERMISOS_IIBB,
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

    actividades = list(
        EmpresaActividad.objects.filter(
            empresa=empresa,
        )
        .select_related("actividad")
        .order_by(
            "-activa",
            "-principal",
            "orden",
            "codigo_registrado",
        )
    )
    resumen_actividades = _resumen_actividades(actividades)
    catalogo_actividades_disponible = (
        ActividadEconomica.objects.filter(
            nomenclador=ActividadEconomica.Nomenclador.ARCA_CLAE,
            activa=True,
        ).exists()
    )

    resumen_iibb = _resumen_iibb_empresa(empresa)

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
        and resumen_actividades["completa"]
        and resumen_iibb["completa"]
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
            "puede_ver_actividades": puede_ver_actividades,
            "actividades_empresa": actividades,
            "resumen_actividades": resumen_actividades,
            "catalogo_actividades_disponible": (
                catalogo_actividades_disponible
            ),
            "puede_ver_iibb": puede_ver_iibb,
            "resumen_iibb": resumen_iibb,
            "estado_parametros": estado_parametros,
            "datos_parametros": datos_parametros,
            "advertencias_parametros": advertencias_parametros,
            "configuracion_base_lista": configuracion_base_lista,
            "resumen": {
                "sucursales_total": resumen_sucursales["total"],
                "sucursales_activas": resumen_sucursales["activas"],
                "actividades_activas": resumen_actividades["activas"],
                "jurisdicciones_iibb_activas": (
                    resumen_iibb["jurisdicciones_total"]
                ),
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


def _agregar_errores_validacion(form, error):
    if hasattr(error, "message_dict"):
        for campo, mensajes in error.message_dict.items():
            destino = campo

            if campo == "actividad" and "actividad_texto" in form.fields:
                destino = "actividad_texto"

            if destino not in form.fields:
                destino = None

            for mensaje in mensajes:
                form.add_error(destino, mensaje)

        return

    for mensaje in error.messages:
        form.add_error(None, mensaje)


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_alguno_requerido(*PERMISOS_ACTIVIDADES)
@require_GET
def actividades_empresa(request):
    empresa = request.empresa_activa
    relaciones = list(
        EmpresaActividad.objects.filter(
            empresa=empresa,
        )
        .select_related("actividad")
        .order_by(
            "-activa",
            "-principal",
            "orden",
            "codigo_registrado",
            "pk",
        )
    )
    catalogo_total = ActividadEconomica.objects.filter(
        nomenclador=ActividadEconomica.Nomenclador.ARCA_CLAE,
        activa=True,
    ).count()
    ultima_importacion = (
        ImportacionCatalogoActividad.objects.filter(
            nomenclador=ActividadEconomica.Nomenclador.ARCA_CLAE,
        )
        .order_by("-importada_en", "-pk")
        .first()
    )

    return render(
        request,
        "nucleo/actividades_empresa.html",
        {
            "empresa": empresa,
            "actividades_empresa": relaciones,
            "resumen": _resumen_actividades(relaciones),
            "catalogo_total": catalogo_total,
            "catalogo_disponible": catalogo_total > 0,
            "ultima_importacion": ultima_importacion,
            "puede_crear": usuario_tiene_permiso(
                request.user,
                empresa,
                "actividades.crear",
            ),
            "puede_editar": usuario_tiene_permiso(
                request.user,
                empresa,
                "actividades.editar",
            ),
        },
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("actividades.crear")
def actividad_empresa_crear(request):
    empresa = request.empresa_activa

    if not ActividadEconomica.objects.filter(
        nomenclador=ActividadEconomica.Nomenclador.ARCA_CLAE,
        activa=True,
    ).exists():
        messages.error(
            request,
            (
                "El catálogo ARCA-CLAE todavía no fue sincronizado. "
                "No es posible asignar actividades."
            ),
        )
        return redirect("nucleo:actividades_empresa")

    if request.method == "POST":
        form = EmpresaActividadCrearForm(
            request.POST,
            empresa=empresa,
        )

        if form.is_valid():
            try:
                relacion = crear_empresa_actividad(
                    empresa=empresa,
                    actividad=form.actividad,
                    principal=form.cleaned_data["principal"],
                    orden=form.cleaned_data["orden"],
                    vigencia_desde=(
                        form.cleaned_data["vigencia_desde"]
                    ),
                    vigencia_hasta=(
                        form.cleaned_data["vigencia_hasta"]
                    ),
                    observaciones=(
                        form.cleaned_data["observaciones"]
                    ),
                    request=request,
                )
            except ValidationError as error:
                _agregar_errores_validacion(form, error)
            else:
                messages.success(
                    request,
                    (
                        f"Actividad {relacion.codigo_registrado} "
                        "asignada correctamente."
                    ),
                )
                return redirect("nucleo:actividades_empresa")
    else:
        form = EmpresaActividadCrearForm(
            empresa=empresa,
        )

    return render(
        request,
        "nucleo/actividad_empresa_form.html",
        {
            "empresa": empresa,
            "form": form,
            "empresa_actividad": None,
            "modo_creacion": True,
            "titulo": "Nueva actividad económica",
        },
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("actividades.editar")
def actividad_empresa_editar(request, empresa_actividad_id):
    empresa = request.empresa_activa
    relacion = get_object_or_404(
        EmpresaActividad.objects.select_related("actividad"),
        pk=empresa_actividad_id,
        empresa=empresa,
        activa=True,
    )

    if request.method == "POST":
        form = EmpresaActividadEditarForm(
            request.POST,
            empresa=empresa,
            empresa_actividad=relacion,
        )

        if form.is_valid():
            try:
                relacion = actualizar_empresa_actividad(
                    empresa=empresa,
                    empresa_actividad=relacion,
                    principal=form.cleaned_data["principal"],
                    orden=form.cleaned_data["orden"],
                    vigencia_desde=(
                        form.cleaned_data["vigencia_desde"]
                    ),
                    vigencia_hasta=(
                        form.cleaned_data["vigencia_hasta"]
                    ),
                    observaciones=(
                        form.cleaned_data["observaciones"]
                    ),
                    request=request,
                )
            except ValidationError as error:
                _agregar_errores_validacion(form, error)
            else:
                messages.success(
                    request,
                    (
                        f"Actividad {relacion.codigo_registrado} "
                        "actualizada correctamente."
                    ),
                )
                return redirect("nucleo:actividades_empresa")
    else:
        form = EmpresaActividadEditarForm(
            empresa=empresa,
            empresa_actividad=relacion,
        )

    return render(
        request,
        "nucleo/actividad_empresa_form.html",
        {
            "empresa": empresa,
            "form": form,
            "empresa_actividad": relacion,
            "modo_creacion": False,
            "titulo": "Editar actividad económica",
        },
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("actividades.editar")
@require_POST
def actividad_empresa_inactivar(request, empresa_actividad_id):
    empresa = request.empresa_activa
    relacion = get_object_or_404(
        EmpresaActividad,
        pk=empresa_actividad_id,
        empresa=empresa,
    )

    try:
        relacion = inactivar_empresa_actividad(
            empresa=empresa,
            empresa_actividad=relacion,
            request=request,
        )
    except ValidationError as error:
        messages.error(
            request,
            " ".join(error.messages),
        )
    else:
        messages.success(
            request,
            (
                f"Actividad {relacion.codigo_registrado} "
                "inactivada correctamente."
            ),
        )

    return redirect("nucleo:actividades_empresa")


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_alguno_requerido(*PERMISOS_ACTIVIDADES)
@require_GET
def catalogo_actividades_buscar(request):
    termino = request.GET.get("q", "").strip()

    if len(termino) < 2:
        return JsonResponse({"results": []})

    empresa = request.empresa_activa
    actividades = (
        ActividadEconomica.objects.filter(
            nomenclador=ActividadEconomica.Nomenclador.ARCA_CLAE,
            activa=True,
        )
        .filter(
            Q(codigo__icontains=termino)
            | Q(descripcion__icontains=termino)
        )
        .exclude(
            asignaciones_empresa__empresa=empresa,
            asignaciones_empresa__activa=True,
        )
        .order_by("codigo")[:20]
    )

    return JsonResponse(
        {
            "results": [
                {
                    "id": actividad.pk,
                    "codigo": actividad.codigo,
                    "descripcion": actividad.descripcion,
                    "text": (
                        f"{actividad.codigo} - "
                        f"{actividad.descripcion}"
                    ),
                }
                for actividad in actividades
            ]
        }
    )

def _resumen_iibb_empresa(empresa):
    configuraciones = list(
        ConfiguracionIIBBEmpresa.objects.filter(
            empresa=empresa,
        ).order_by(
            "-activa",
            "-creada_en",
            "-pk",
        )
    )
    configuracion_activa = next(
        (
            configuracion
            for configuracion in configuraciones
            if configuracion.activa
        ),
        None,
    )

    jurisdicciones_activas = []
    sede = None

    jurisdicciones_historicas = list(
        EmpresaJurisdiccionIIBB.objects.filter(
            configuracion__empresa=empresa,
            activa=False,
        )
        .select_related(
            "configuracion",
            "jurisdiccion",
        )
        .order_by(
            "-fecha_baja",
            "-actualizada_en",
            "codigo_registrado",
        )
    )

    if configuracion_activa is not None:
        jurisdicciones_activas = list(
            EmpresaJurisdiccionIIBB.objects.filter(
                configuracion=configuracion_activa,
                activa=True,
            )
            .select_related("jurisdiccion")
            .order_by(
                "-sede",
                "jurisdiccion__orden",
                "codigo_registrado",
            )
        )
        sede = next(
            (
                relacion
                for relacion in jurisdicciones_activas
                if relacion.sede
            ),
            None,
        )

    return {
        "configuraciones": configuraciones,
        "configuracion_activa": configuracion_activa,
        "jurisdicciones_activas": jurisdicciones_activas,
        "jurisdicciones_historicas": jurisdicciones_historicas,
        "jurisdicciones_total": len(jurisdicciones_activas),
        "sede": sede,
        "completa": bool(
            configuracion_activa is not None
            and configuracion_activa.esta_completa
        ),
    }


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_alguno_requerido(*PERMISOS_IIBB)
@require_GET
def ingresos_brutos(request):
    empresa = request.empresa_activa
    resumen = _resumen_iibb_empresa(empresa)

    return render(
        request,
        "nucleo/ingresos_brutos.html",
        {
            "empresa": empresa,
            "resumen": resumen,
            "catalogo_total": JurisdiccionFiscal.objects.filter(
                activa=True
            ).count(),
            "puede_crear": usuario_tiene_permiso(
                request.user,
                empresa,
                "iibb.crear",
            ),
            "puede_editar": usuario_tiene_permiso(
                request.user,
                empresa,
                "iibb.editar",
            ),
        },
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("iibb.crear")
def configuracion_iibb_crear(request):
    empresa = request.empresa_activa

    if ConfiguracionIIBBEmpresa.objects.filter(
        empresa=empresa,
        activa=True,
    ).exists():
        messages.warning(
            request,
            "La empresa ya tiene una configuración de IIBB activa.",
        )
        return redirect("nucleo:ingresos_brutos")

    if request.method == "POST":
        form = ConfiguracionIIBBEmpresaForm(
            request.POST,
            empresa=empresa,
        )

        if form.is_valid():
            try:
                configuracion = crear_configuracion_iibb(
                    empresa=empresa,
                    regimen=form.cleaned_data["regimen"],
                    tratamiento_general=(
                        form.cleaned_data["tratamiento_general"]
                    ),
                    numero_inscripcion=(
                        form.cleaned_data["numero_inscripcion"]
                    ),
                    fecha_alta=form.cleaned_data["fecha_alta"],
                    observaciones=form.cleaned_data["observaciones"],
                    request=request,
                )
            except ValidationError as error:
                _agregar_errores_validacion(form, error)
            else:
                messages.success(
                    request,
                    (
                        "Configuración de Ingresos Brutos creada "
                        f"como {configuracion.get_regimen_display()}."
                    ),
                )
                return redirect("nucleo:ingresos_brutos")
    else:
        form = ConfiguracionIIBBEmpresaForm(
            empresa=empresa,
        )

    return render(
        request,
        "nucleo/configuracion_iibb_form.html",
        {
            "empresa": empresa,
            "form": form,
            "configuracion": None,
            "titulo": "Nueva configuración de Ingresos Brutos",
        },
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("iibb.editar")
def configuracion_iibb_editar(request, configuracion_id):
    empresa = request.empresa_activa
    configuracion = get_object_or_404(
        ConfiguracionIIBBEmpresa,
        pk=configuracion_id,
        empresa=empresa,
        activa=True,
    )

    if request.method == "POST":
        form = ConfiguracionIIBBEmpresaForm(
            request.POST,
            empresa=empresa,
            configuracion=configuracion,
        )

        if form.is_valid():
            try:
                configuracion = actualizar_configuracion_iibb(
                    empresa=empresa,
                    configuracion=configuracion,
                    regimen=form.cleaned_data["regimen"],
                    tratamiento_general=(
                        form.cleaned_data["tratamiento_general"]
                    ),
                    numero_inscripcion=(
                        form.cleaned_data["numero_inscripcion"]
                    ),
                    fecha_alta=form.cleaned_data["fecha_alta"],
                    observaciones=form.cleaned_data["observaciones"],
                    request=request,
                )
            except ValidationError as error:
                _agregar_errores_validacion(form, error)
            else:
                messages.success(
                    request,
                    "Configuración de Ingresos Brutos actualizada.",
                )
                return redirect("nucleo:ingresos_brutos")
    else:
        form = ConfiguracionIIBBEmpresaForm(
            empresa=empresa,
            configuracion=configuracion,
        )

    return render(
        request,
        "nucleo/configuracion_iibb_form.html",
        {
            "empresa": empresa,
            "form": form,
            "configuracion": configuracion,
            "titulo": "Editar configuración de Ingresos Brutos",
        },
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("iibb.editar")
@require_POST
def configuracion_iibb_inactivar(request, configuracion_id):
    empresa = request.empresa_activa
    configuracion = get_object_or_404(
        ConfiguracionIIBBEmpresa,
        pk=configuracion_id,
        empresa=empresa,
    )

    try:
        inactivar_configuracion_iibb(
            empresa=empresa,
            configuracion=configuracion,
            request=request,
        )
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(
            request,
            "Configuración de Ingresos Brutos inactivada.",
        )

    return redirect("nucleo:ingresos_brutos")


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("iibb.crear")
def jurisdiccion_iibb_crear(request, configuracion_id):
    empresa = request.empresa_activa
    configuracion = get_object_or_404(
        ConfiguracionIIBBEmpresa,
        pk=configuracion_id,
        empresa=empresa,
        activa=True,
    )

    if (
        configuracion.regimen
        == ConfiguracionIIBBEmpresa.Regimen.NO_INSCRIPTO
    ):
        messages.warning(
            request,
            "Una empresa no inscripta no admite jurisdicciones.",
        )
        return redirect("nucleo:ingresos_brutos")

    if request.method == "POST":
        form = EmpresaJurisdiccionIIBBCrearForm(
            request.POST,
            configuracion=configuracion,
        )

        if form.is_valid():
            try:
                relacion = crear_jurisdiccion_iibb(
                    empresa=empresa,
                    configuracion=configuracion,
                    jurisdiccion=form.cleaned_data["jurisdiccion"],
                    numero_inscripcion=(
                        form.cleaned_data["numero_inscripcion"]
                    ),
                    sede=form.cleaned_data["sede"],
                    tratamiento=form.cleaned_data["tratamiento"],
                    fecha_alta=form.cleaned_data["fecha_alta"],
                    observaciones=form.cleaned_data["observaciones"],
                    request=request,
                )
            except ValidationError as error:
                _agregar_errores_validacion(form, error)
            else:
                messages.success(
                    request,
                    (
                        f"Jurisdicción {relacion.codigo_registrado} "
                        "agregada correctamente."
                    ),
                )
                return redirect("nucleo:ingresos_brutos")
    else:
        form = EmpresaJurisdiccionIIBBCrearForm(
            configuracion=configuracion,
        )

    return render(
        request,
        "nucleo/jurisdiccion_iibb_form.html",
        {
            "empresa": empresa,
            "configuracion": configuracion,
            "relacion": None,
            "form": form,
            "titulo": "Agregar jurisdicción de Ingresos Brutos",
        },
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("iibb.editar")
def jurisdiccion_iibb_editar(request, relacion_id):
    empresa = request.empresa_activa
    relacion = get_object_or_404(
        EmpresaJurisdiccionIIBB.objects.select_related(
            "configuracion",
            "jurisdiccion",
        ),
        pk=relacion_id,
        configuracion__empresa=empresa,
        activa=True,
    )
    configuracion = relacion.configuracion

    if request.method == "POST":
        form = EmpresaJurisdiccionIIBBEditarForm(
            request.POST,
            configuracion=configuracion,
            relacion=relacion,
        )

        if form.is_valid():
            try:
                relacion = actualizar_jurisdiccion_iibb(
                    empresa=empresa,
                    relacion=relacion,
                    numero_inscripcion=(
                        form.cleaned_data["numero_inscripcion"]
                    ),
                    sede=form.cleaned_data["sede"],
                    tratamiento=form.cleaned_data["tratamiento"],
                    fecha_alta=form.cleaned_data["fecha_alta"],
                    observaciones=form.cleaned_data["observaciones"],
                    request=request,
                )
            except ValidationError as error:
                _agregar_errores_validacion(form, error)
            else:
                messages.success(
                    request,
                    (
                        f"Jurisdicción {relacion.codigo_registrado} "
                        "actualizada correctamente."
                    ),
                )
                return redirect("nucleo:ingresos_brutos")
    else:
        form = EmpresaJurisdiccionIIBBEditarForm(
            configuracion=configuracion,
            relacion=relacion,
        )

    return render(
        request,
        "nucleo/jurisdiccion_iibb_form.html",
        {
            "empresa": empresa,
            "configuracion": configuracion,
            "relacion": relacion,
            "form": form,
            "titulo": "Editar jurisdicción de Ingresos Brutos",
        },
    )


@login_required
@contexto_operativo_requerido(requiere_sucursal=False)
@permiso_funcional_requerido("iibb.editar")
@require_POST
def jurisdiccion_iibb_inactivar(request, relacion_id):
    empresa = request.empresa_activa
    relacion = get_object_or_404(
        EmpresaJurisdiccionIIBB,
        pk=relacion_id,
        configuracion__empresa=empresa,
    )

    try:
        relacion = inactivar_jurisdiccion_iibb(
            empresa=empresa,
            relacion=relacion,
            request=request,
        )
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(
            request,
            (
                f"Jurisdicción {relacion.codigo_registrado} "
                "inactivada correctamente."
            ),
        )

    return redirect("nucleo:ingresos_brutos")
