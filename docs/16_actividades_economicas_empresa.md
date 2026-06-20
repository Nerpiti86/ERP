# Actividades económicas por empresa

Estado: implementado por la TAREA 0006.

## 1. Objetivo

Administrar las actividades económicas de cada empresa dentro de
Configuración de empresa, utilizando exclusivamente el catálogo oficial
ARCA-CLAE sincronizado localmente.

## 2. Separación de responsabilidades

`ActividadEconomica` representa el catálogo oficial global.

`EmpresaActividad` representa la asignación histórica y funcional de una
actividad a una empresa.

Una actividad del catálogo puede estar vinculada con muchas empresas. Una
empresa puede tener cualquier cantidad de actividades.

## 3. Instantánea histórica

Cada relación conserva al momento del alta:

- nomenclador
- código
- descripción
- SHA-256 de la fuente oficial

La relación sigue apuntando al catálogo vigente, pero la instantánea no se
modifica cuando ARCA cambia posteriormente la descripción.

## 4. Campos de EmpresaActividad

- empresa
- actividad
- principal
- activa
- orden de visualización
- vigencia desde
- vigencia hasta
- observaciones
- nomenclador registrado
- código registrado
- descripción registrada
- SHA-256 registrado
- fechas de creación y actualización

## 5. Reglas

- una empresa puede tener cualquier cantidad de actividades
- como máximo una actividad principal activa por empresa
- una actividad no puede estar duplicada activamente en la misma empresa
- una relación principal debe estar activa
- la vigencia hasta no puede ser anterior a la vigencia desde
- una nueva relación solo puede usar una actividad activa del catálogo
- una relación histórica puede conservar una actividad que ARCA retire
- la actividad y la instantánea de una relación existente son inmutables
- la baja es lógica y no elimina la relación

Las restricciones principales se validan en aplicación y en PostgreSQL.

## 6. Servicios transaccionales

Las operaciones se concentran en:

- `crear_empresa_actividad`
- `actualizar_empresa_actividad`
- `inactivar_empresa_actividad`

El cambio de actividad principal se realiza dentro de una transacción. La
principal anterior se desmarca antes de confirmar la nueva.

## 7. Auditoría

Las altas, modificaciones, cambios de principal e inactivaciones generan
registros en `Auditoria`.

La auditoría conserva:

- empresa
- usuario
- acción
- relación afectada
- datos anteriores
- datos nuevos
- IP
- agente de usuario

## 8. Permisos

Permisos funcionales:

- `actividades.ver`
- `actividades.crear`
- `actividades.editar`

Matriz inicial:

- `ADMIN`: ver, crear y editar
- `CONTADOR`: ver, crear y editar
- `AUDITOR`: ver
- `SOLO_LECTURA`: ver
- `OPERADOR`: sin acceso

## 9. Interfaz

Rutas:

```text
/nucleo/configuracion/actividades/
/nucleo/configuracion/actividades/nueva/
/nucleo/configuracion/actividades/<id>/editar/
/nucleo/configuracion/actividades/<id>/inactivar/
/nucleo/configuracion/actividades/catalogo/buscar/
```

La selección usa búsqueda por código o descripción. No se carga un selector
con las 958 actividades completas.

La validación final siempre se realiza en backend.

## 10. Catálogo vacío

La migración crea las tablas, pero los registros del catálogo no forman
parte del repositorio.

Una instalación nueva debe ejecutar la sincronización CLAE.

Mientras el catálogo no tenga actividades activas:

- el listado muestra una advertencia
- el alta queda bloqueada
- la portada indica que el catálogo no está disponible

## 11. Configuración base

La sección de actividades se considera completa cuando:

- existe al menos una actividad activa
- existe una actividad principal activa

La portada general incorpora este estado al cálculo de configuración base.

## 12. Administración técnica

`ActividadEconomica`, `ImportacionCatalogoActividad` y `EmpresaActividad`
son de solo lectura en Django Admin.

Las modificaciones funcionales deben pasar por el sincronizador oficial o
por los servicios transaccionales del ERP.
