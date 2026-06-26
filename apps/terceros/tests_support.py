from django.contrib.auth import get_user_model
from django.test import RequestFactory

from apps.nucleo.models import (
    Empresa,
    RolFuncional,
    UsuarioEmpresa,
    UsuarioRolEmpresa,
)
from apps.nucleo.roles_iniciales import cargar_roles_permisos_iniciales

from .models import (
    CondicionIVA,
    GrupoTercero,
    TerceroRol,
    TipoDocumento,
)
from .services import crear_tercero


def crear_empresa(
    *,
    cuit="30711915695",
    razon_social="Empresa Uno SA",
):
    return Empresa.objects.create(
        cuit=cuit,
        razon_social=razon_social,
        condicion_iva=Empresa.CondicionIVA.RESPONSABLE_INSCRIPTO,
        activa=True,
    )


def obtener_catalogos():
    return {
        "cuit": TipoDocumento.objects.get(codigo="CUIT"),
        "dni": TipoDocumento.objects.get(codigo="DNI"),
        "sin_documento": TipoDocumento.objects.get(
            codigo="SIN_IDENTIFICAR"
        ),
        "ri": CondicionIVA.objects.get(
            codigo="IVA_RESPONSABLE_INSCRIPTO"
        ),
        "cf": CondicionIVA.objects.get(codigo="CONSUMIDOR_FINAL"),
    }


def crear_usuario(
    *,
    username="operador",
    password="clave-segura",
    superuser=False,
):
    usuario_modelo = get_user_model()

    if superuser:
        return usuario_modelo.objects.create_superuser(
            username=username,
            email=f"{username}@example.com",
            password=password,
        )

    return usuario_modelo.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password=password,
    )


def asignar_rol(*, usuario, empresa, codigo_rol):
    cargar_roles_permisos_iniciales()
    UsuarioEmpresa.objects.get_or_create(
        usuario=usuario,
        empresa=empresa,
        defaults={"activo": True},
    )
    rol = RolFuncional.objects.get(codigo=codigo_rol)
    relacion, _ = UsuarioRolEmpresa.objects.get_or_create(
        usuario=usuario,
        empresa=empresa,
        rol=rol,
        defaults={"activo": True},
    )
    if not relacion.activo:
        relacion.activo = True
        relacion.save(update_fields=["activo", "actualizado_en"])
    return relacion


def crear_request(usuario):
    request = RequestFactory().post("/")
    request.user = usuario
    request.META["REMOTE_ADDR"] = "127.0.0.1"
    request.META["HTTP_USER_AGENT"] = "Tests ERP"
    return request


def crear_tercero_prueba(
    *,
    empresa,
    codigo="",
    numero_documento="30711915695",
    denominacion="Cliente de Prueba SA",
    roles=None,
    grupos_por_rol=None,
    request=None,
):
    catalogos = obtener_catalogos()

    if roles is None:
        roles = {TerceroRol.Rol.CLIENTE}

    return crear_tercero(
        empresa=empresa,
        codigo=codigo,
        tipo_persona="PERSONA_JURIDICA",
        tipo_documento=catalogos["cuit"],
        numero_documento=numero_documento,
        denominacion=denominacion,
        nombre_fantasia="",
        condicion_iva=catalogos["ri"],
        telefono="3415550000",
        email="administracion@example.com",
        sitio_web="",
        fecha_alta="2026-06-21",
        roles=roles,
        grupos_por_rol=grupos_por_rol,
        observaciones="",
        request=request,
    )
