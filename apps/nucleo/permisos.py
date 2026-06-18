# Helpers de permisos funcionales del ERP.

from .models import PermisoFuncional, UsuarioEmpresa, UsuarioRolEmpresa


def normalizar_codigo_permiso(codigo_permiso):
    if not isinstance(codigo_permiso, str):
        return ""

    return codigo_permiso.strip().lower()


def usuario_tiene_permiso(usuario, empresa, codigo_permiso):
    codigo = normalizar_codigo_permiso(codigo_permiso)

    if not codigo or not usuario or not empresa:
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

    permiso_activo = PermisoFuncional.objects.filter(
        codigo=codigo,
        activo=True,
    ).exists()

    if not permiso_activo:
        return False

    return UsuarioRolEmpresa.objects.filter(
        usuario=usuario,
        empresa=empresa,
        activo=True,
        rol__activo=True,
        rol__permisos_asignados__activo=True,
        rol__permisos_asignados__permiso__codigo=codigo,
        rol__permisos_asignados__permiso__activo=True,
    ).exists()
