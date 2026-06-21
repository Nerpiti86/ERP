# Sucursales y domicilios estructurados

Estado: implementado por la TAREA 0004.

## 1. Objetivo

Administrar establecimientos físicos de cada empresa con domicilio
estructurado y funciones operativas, legales y fiscales.

## 2. Principio funcional

Todo domicilio físico utilizado por la empresa se administra como una
sucursal o establecimiento.

La misma sucursal puede ser simultáneamente:

- casa central
- domicilio fiscal nacional
- domicilio fiscal provincial
- domicilio legal
- principal lugar de actividades
- local comercial
- oficina administrativa

Las jurisdicciones impositivas de Ingresos Brutos no se confunden con
sucursales físicas.

## 3. Domicilio estructurado

La sucursal contiene:

- calle
- número
- sector
- torre
- piso
- departamento
- barrio
- localidad
- código postal
- partido o departamento
- provincia
- país

El campo anterior `domicilio` permanece disponible como respaldo de datos
históricos.

No se realiza migración automática desde texto libre porque no existe una
forma confiable de separar calle, número y complementos sin intervención
humana.

## 4. Funciones exclusivas

Entre sucursales activas de una misma empresa debe existir como máximo una
con cada función:

- casa central
- domicilio fiscal nacional
- domicilio fiscal provincial
- domicilio legal
- principal lugar de actividades

La exclusividad se valida en formulario, modelo y base de datos.

## 5. Funciones no exclusivas

Pueden existir varias sucursales activas como:

- depósito
- local comercial
- oficina administrativa
- otras funciones descriptivas

## 6. Estado de completitud

La portada considera completa la configuración de sucursales cuando:

1. Existe al menos una sucursal activa.
2. Todas las sucursales activas tienen domicilio estructurado completo.
3. Existe una casa central activa.

El domicilio estructurado mínimo requiere:

- calle
- número
- localidad
- código postal
- provincia
- país

## 7. Pantallas

Listado:

`/nucleo/configuracion/sucursales/`

Alta:

`/nucleo/configuracion/sucursales/nueva/`

Edición:

`/nucleo/configuracion/sucursales/<id>/editar/`

No se implementa eliminación física.

## 8. Permisos

Consulta:

`sucursales.ver`

Alta:

`sucursales.crear`

Edición y activación o desactivación:

`sucursales.editar`

Un usuario que posea cualquiera de estos permisos puede acceder a la
portada integrada de configuración, pero cada acción conserva su permiso
específico.

## 9. Multiempresa

Todas las consultas se filtran por empresa activa.

Una sucursal perteneciente a otra empresa devuelve 404 en la pantalla de
edición, incluso si el usuario conoce su identificador.

## 10. Migración

La migración agrega campos opcionales para no romper registros existentes.

No se asigna automáticamente:

- casa central
- domicilio fiscal
- domicilio legal
- principal lugar de actividades

La carga real se completa desde la pantalla funcional.


## Relación con puntos de venta

Desde la TAREA 0008 una sucursal puede tener cero, uno o varios puntos de
venta.

Reglas:

- un punto activo requiere una sucursal activa
- no se puede inactivar una sucursal mientras conserve puntos activos
- el domicilio del punto se obtiene de la sucursal
- el punto de venta no duplica los campos del domicilio estructurado
- la baja del punto conserva su relación histórica con la sucursal
