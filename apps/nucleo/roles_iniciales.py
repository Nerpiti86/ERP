"""Definiciones y carga idempotente de roles y permisos iniciales."""

from django.db import transaction

from .models import PermisoFuncional, RolFuncional, RolPermiso


ROLES_INICIALES = {
    "ADMIN": {
        "nombre": "Administrador",
        "descripcion": "Administracion funcional amplia dentro de una empresa.",
    },
    "CONTADOR": {
        "nombre": "Contador",
        "descripcion": "Acceso contable, documental y de consulta operativa.",
    },
    "OPERADOR": {
        "nombre": "Operador",
        "descripcion": "Carga y operacion diaria del ERP.",
    },
    "AUDITOR": {
        "nombre": "Auditor",
        "descripcion": "Consulta de auditoria, eventos y reportes sin operacion.",
    },
    "SOLO_LECTURA": {
        "nombre": "Solo lectura",
        "descripcion": "Consulta general sin permisos de modificacion.",
    },
}


PERMISOS_INICIALES = {
    "empresas.ver": "Consultar empresas.",
    "empresas.crear": "Crear empresas.",
    "empresas.editar": "Editar empresas.",
    "empresas.desactivar": "Desactivar empresas.",
    "sucursales.ver": "Consultar sucursales.",
    "sucursales.crear": "Crear sucursales.",
    "sucursales.editar": "Editar sucursales.",
    "actividades.ver": "Consultar actividades económicas.",
    "actividades.crear": "Asignar actividades económicas.",
    "actividades.editar": "Editar o inactivar actividades económicas.",
    "iibb.ver": "Consultar Ingresos Brutos y jurisdicciones.",
    "iibb.crear": "Crear configuraciones y jurisdicciones de IIBB.",
    "iibb.editar": "Editar o inactivar datos de IIBB.",
    "usuarios.ver": "Consultar usuarios y accesos.",
    "usuarios.crear": "Crear usuarios y accesos.",
    "usuarios.editar": "Editar usuarios y accesos.",
    "parametros.ver": "Consultar parametros del sistema.",
    "parametros.editar": "Editar parametros del sistema.",
    "auditoria.ver": "Consultar registros de auditoria.",
    "eventos.ver": "Consultar eventos de negocio.",
    "documentos.ver": "Consultar documentos adjuntos.",
    "documentos.adjuntar": "Adjuntar documentos.",
    "documentos.desactivar": "Desactivar documentos adjuntos.",
    "contabilidad.ver": "Consultar informacion contable.",
    "contabilidad.editar": "Crear o modificar informacion contable.",
    "ventas.ver": "Consultar ventas.",
    "ventas.crear": "Crear operaciones de venta.",
    "compras.ver": "Consultar compras.",
    "compras.crear": "Crear operaciones de compra.",
    "tesoreria.ver": "Consultar tesoreria.",
    "tesoreria.operar": "Registrar operaciones de tesoreria.",
}


PERMISOS_POR_ROL = {
    "ADMIN": tuple(PERMISOS_INICIALES),
    "CONTADOR": (
        "empresas.ver",
        "sucursales.ver",
        "parametros.ver",
        "documentos.ver",
        "documentos.adjuntar",
        "contabilidad.ver",
        "contabilidad.editar",
        "ventas.ver",
        "compras.ver",
        "tesoreria.ver",
        "actividades.ver",
        "actividades.crear",
        "actividades.editar",
        "iibb.ver",
        "iibb.crear",
        "iibb.editar",
    ),
    "OPERADOR": (
        "empresas.ver",
        "sucursales.ver",
        "documentos.ver",
        "documentos.adjuntar",
        "ventas.ver",
        "ventas.crear",
        "compras.ver",
        "compras.crear",
        "tesoreria.ver",
        "tesoreria.operar",
    ),
    "AUDITOR": (
        "empresas.ver",
        "sucursales.ver",
        "usuarios.ver",
        "parametros.ver",
        "auditoria.ver",
        "eventos.ver",
        "documentos.ver",
        "contabilidad.ver",
        "ventas.ver",
        "compras.ver",
        "tesoreria.ver",
        "actividades.ver",
        "iibb.ver",
    ),
    "SOLO_LECTURA": (
        "empresas.ver",
        "sucursales.ver",
        "parametros.ver",
        "documentos.ver",
        "contabilidad.ver",
        "ventas.ver",
        "compras.ver",
        "tesoreria.ver",
        "actividades.ver",
        "iibb.ver",
    ),
}


def _validar_definiciones():
    roles_definidos = set(ROLES_INICIALES)
    roles_mapeados = set(PERMISOS_POR_ROL)

    if roles_definidos != roles_mapeados:
        faltantes = sorted(roles_definidos - roles_mapeados)
        sobrantes = sorted(roles_mapeados - roles_definidos)
        raise RuntimeError(
            "La matriz de roles no coincide con las definiciones. "
            f"Faltantes={faltantes}; sobrantes={sobrantes}"
        )

    permisos_definidos = set(PERMISOS_INICIALES)

    for codigo_rol, permisos in PERMISOS_POR_ROL.items():
        desconocidos = sorted(set(permisos) - permisos_definidos)
        if desconocidos:
            raise RuntimeError(
                f"El rol {codigo_rol} referencia permisos desconocidos: "
                f"{desconocidos}"
            )


@transaction.atomic
def cargar_roles_permisos_iniciales():
    """Crea o actualiza la matriz inicial sin eliminar datos adicionales."""

    _validar_definiciones()

    resumen = {
        "roles_creados": 0,
        "roles_existentes": 0,
        "permisos_creados": 0,
        "permisos_existentes": 0,
        "relaciones_creadas": 0,
        "relaciones_activadas": 0,
        "relaciones_sin_cambios": 0,
    }

    roles = {}

    for codigo, datos in ROLES_INICIALES.items():
        rol, creado = RolFuncional.objects.get_or_create(
            codigo=codigo,
            defaults={
                "nombre": datos["nombre"],
                "descripcion": datos["descripcion"],
                "activo": True,
                "sistema": True,
            },
        )

        cambio = False
        for campo, valor in {
            "nombre": datos["nombre"],
            "descripcion": datos["descripcion"],
            "activo": True,
            "sistema": True,
        }.items():
            if getattr(rol, campo) != valor:
                setattr(rol, campo, valor)
                cambio = True

        rol.full_clean()
        if creado or cambio:
            rol.save()

        resumen["roles_creados" if creado else "roles_existentes"] += 1
        roles[codigo] = rol

    permisos = {}

    for codigo, descripcion in PERMISOS_INICIALES.items():
        modulo, accion = codigo.split(".", 1)

        permiso, creado = PermisoFuncional.objects.get_or_create(
            codigo=codigo,
            defaults={
                "modulo": modulo,
                "accion": accion,
                "descripcion": descripcion,
                "activo": True,
            },
        )

        cambio = False
        for campo, valor in {
            "modulo": modulo,
            "accion": accion,
            "descripcion": descripcion,
            "activo": True,
        }.items():
            if getattr(permiso, campo) != valor:
                setattr(permiso, campo, valor)
                cambio = True

        permiso.full_clean()
        if creado or cambio:
            permiso.save()

        resumen[
            "permisos_creados" if creado else "permisos_existentes"
        ] += 1
        permisos[codigo] = permiso

    for codigo_rol, codigos_permisos in PERMISOS_POR_ROL.items():
        rol = roles[codigo_rol]

        for codigo_permiso in codigos_permisos:
            permiso = permisos[codigo_permiso]
            relacion, creada = RolPermiso.objects.get_or_create(
                rol=rol,
                permiso=permiso,
                defaults={"activo": True},
            )

            if creada:
                relacion.full_clean()
                relacion.save()
                resumen["relaciones_creadas"] += 1
            elif not relacion.activo:
                relacion.activo = True
                relacion.full_clean()
                relacion.save()
                resumen["relaciones_activadas"] += 1
            else:
                resumen["relaciones_sin_cambios"] += 1

    return resumen


def verificar_roles_permisos_iniciales():
    """Devuelve errores de consistencia de la matriz inicial cargada."""

    _validar_definiciones()
    errores = []

    for codigo, datos in ROLES_INICIALES.items():
        rol = RolFuncional.objects.filter(codigo=codigo).first()

        if rol is None:
            errores.append(f"Falta rol: {codigo}")
            continue

        if not rol.activo:
            errores.append(f"Rol inactivo: {codigo}")
        if not rol.sistema:
            errores.append(f"Rol no marcado como sistema: {codigo}")
        if rol.nombre != datos["nombre"]:
            errores.append(f"Nombre incorrecto para rol: {codigo}")

    for codigo, descripcion in PERMISOS_INICIALES.items():
        permiso = PermisoFuncional.objects.filter(codigo=codigo).first()

        if permiso is None:
            errores.append(f"Falta permiso: {codigo}")
            continue

        modulo, accion = codigo.split(".", 1)

        if not permiso.activo:
            errores.append(f"Permiso inactivo: {codigo}")
        if permiso.modulo != modulo or permiso.accion != accion:
            errores.append(f"Modulo/accion incorrectos: {codigo}")
        if permiso.descripcion != descripcion:
            errores.append(f"Descripcion incorrecta: {codigo}")

    for codigo_rol, codigos_permisos in PERMISOS_POR_ROL.items():
        for codigo_permiso in codigos_permisos:
            existe = RolPermiso.objects.filter(
                rol__codigo=codigo_rol,
                permiso__codigo=codigo_permiso,
                rol__activo=True,
                permiso__activo=True,
                activo=True,
            ).exists()

            if not existe:
                errores.append(
                    f"Falta relacion activa: {codigo_rol} -> {codigo_permiso}"
                )

    return errores
