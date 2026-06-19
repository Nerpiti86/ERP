# Helpers de permisos funcionales del ERP.

from .models import UsuarioEmpresa, UsuarioRolEmpresa


def normalizar_codigo_permiso(codigo_permiso):
    if not isinstance(codigo_permiso, str):
        return ""

    return codigo_permiso.strip().lower()


def normalizar_codigos_permisos(codigos_permisos):
    if isinstance(codigos_permisos, str):
        codigos_permisos = (codigos_permisos,)

    return tuple(
        dict.fromkeys(
            codigo
            for codigo in (
                normalizar_codigo_permiso(item)
                for item in (codigos_permisos or ())
            )
            if codigo
        )
    )


def usuario_tiene_alguno_de_permisos(
    usuario,
    empresa,
    codigos_permisos,
):
    codigos = normalizar_codigos_permisos(codigos_permisos)

    if not codigos or not usuario or not empresa:
        return False

    if not getattr(usuario, "is_active", False):
        return False

    if not getattr(empresa, "activa", False):
        return False

    if getattr(usuario, "is_superuser", False):
        return True

    tiene_acceso_empresa = UsuarioEmpresa.objects.filter(
        usuario=usuario,
        empresa=empresa,
        activo=True,
    ).exists()

    if not tiene_acceso_empresa:
        return False

    return UsuarioRolEmpresa.objects.filter(
        usuario=usuario,
        empresa=empresa,
        activo=True,
        rol__activo=True,
        rol__permisos_asignados__activo=True,
        rol__permisos_asignados__permiso__codigo__in=codigos,
        rol__permisos_asignados__permiso__activo=True,
    ).exists()


def usuario_tiene_permiso(usuario, empresa, codigo_permiso):
    return usuario_tiene_alguno_de_permisos(
        usuario,
        empresa,
        (codigo_permiso,),
    )
