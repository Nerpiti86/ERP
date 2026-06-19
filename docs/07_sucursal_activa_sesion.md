# Sucursal activa para la sesión

Estado: implementado al cierre de la Tarea 45.

## 1. Objetivo

Definir una única sucursal de trabajo activa dentro de la empresa activa de la sesión.

La sucursal activa representa el punto operativo desde el que se ejecutarán operaciones futuras.

## 2. Dependencia de empresa

No puede existir una sucursal activa válida sin empresa activa.

Toda sucursal seleccionada debe:

- estar activa
- pertenecer a la empresa activa
- estar habilitada para el usuario
- conservar acceso activo a la empresa

## 3. Almacenamiento

La sesión guarda únicamente:

```text
nucleo_sucursal_activa_id
```

No se almacena el objeto completo.

## 4. Usuario normal

Puede seleccionar sucursales que cumplan:

- `Sucursal.activa = True`
- `Sucursal.empresa = request.empresa_activa`
- relación `UsuarioSucursal` activa
- relación `UsuarioEmpresa` activa
- usuario autenticado y activo

## 5. Superusuario

Puede seleccionar cualquier sucursal activa de la empresa activa.

No puede seleccionar:

- sucursales inactivas
- sucursales de otra empresa distinta de la activa

## 6. Selección automática

Si existe exactamente una sucursal disponible dentro de la empresa activa, se selecciona automáticamente.

Si existen varias, el usuario debe elegir.

## 7. Selección manual

Ruta:

```text
/sucursal/seleccionar/
```

La vista:

- requiere autenticación
- exige empresa activa
- lista únicamente sucursales permitidas
- valida el POST nuevamente en backend
- admite retorno seguro mediante `next`

Si no hay empresa activa, redirige primero al selector de empresa.

## 8. Cambio de empresa

Al cambiar de empresa se elimina inmediatamente la sucursal anterior.

En el siguiente request:

- se selecciona automáticamente una sucursal única de la nueva empresa
- o se solicita selección manual si hay varias
- o queda sin sucursal si no hay opciones

Nunca se conserva una sucursal perteneciente a otra empresa.

## 9. Middleware y contexto

El middleware existente resuelve en este orden:

```text
1. empresas disponibles
2. empresa activa
3. sucursales disponibles
4. sucursal activa
```

Atributos disponibles:

```text
request.empresa_activa
request.empresas_disponibles
request.sucursal_activa
request.sucursales_disponibles
```

Variables equivalentes quedan disponibles en plantillas.

## 10. Invalidación automática

La sucursal se elimina de la sesión si:

- fue desactivada
- se desactivó el acceso `UsuarioSucursal`
- se perdió el acceso a la empresa
- cambió la empresa activa
- dejó de pertenecer a la empresa activa
- el usuario quedó inactivo
- el registro dejó de existir

## 11. Seguridad

El selector visual no reemplaza controles backend.

Cada módulo futuro deberá validar:

- empresa del objeto
- sucursal del objeto cuando corresponda
- permisos funcionales del usuario

La sucursal activa no modifica todavía el modelo de permisos, que continúa definido por empresa.

## 12. Fuera de alcance

Esta tarea no implementa:

- login propio del ERP
- obligatoriedad global de sucursal activa
- permisos específicos por sucursal
- `UsuarioRolSucursal`
- filtrado automático de todos los módulos
- auditoría del cambio de sucursal
- persistencia fuera de la sesión
- migraciones o tablas nuevas

## 13. Próximo paso

```text
TAREA 46 — Definir autenticación propia del ERP
```
