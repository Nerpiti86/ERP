# Maestro base de terceros

<!-- BEGIN ESTADO_VERIFICADO_TERCEROS -->
## Estado verificado del maestro de terceros — TAREA 0023

```text
Aplicación: apps.terceros
Modelos: 7
Última migración: 0003_grupos_terceros
Pruebas ejecutadas para la app: 72
Plantillas detectadas: 7
```

La primera versión funcional está implementada con identidad compartida,
roles CLIENTE/PROVEEDOR, grupos obligatorios por rol, domicilios, contactos,
aislamiento por empresa, permisos backend, servicios y auditoría.

Incorpora relaciones persistentes con ítems mediante `ItemProveedor`.
Condiciones de compra, precios y cuentas corrientes continúan pendientes.
El contrato e implementación se documentan en
`docs/24_relacion_items_proveedores.md`. El estado técnico vigente está en
`docs/22_estado_real_integral_erp.md`.
<!-- END ESTADO_VERIFICADO_TERCEROS -->


Estado: implementado por TAREA 0009.

## Objetivo

Incorporar una identidad única para clientes y proveedores por empresa,
preparada para ventas, compras, cuentas corrientes e impuestos.

No se crean identidades separadas de cliente y proveedor. Un `Tercero`
recibe uno o ambos roles mediante `TerceroRol`.

## App y modelos

```text
apps/terceros
```

Modelos:

- `TipoDocumento`
- `CondicionIVA`
- `GrupoTercero`
- `Tercero`
- `TerceroRol`
- `DomicilioTercero`
- `ContactoTercero`

## Reglas

- código único por empresa
- generación automática `T000001`
- documento único por empresa, tipo y número
- CUIT y CUIL normalizados y validados
- empresa y código inmutables
- baja lógica
- un domicilio principal activo por tercero y tipo
- un contacto principal activo
- aislamiento obligatorio por empresa activa
- auditoría mediante servicios transaccionales
- grupo obligatorio por cada rol activo
- grupos separados por empresa y tipo CLIENTE o PROVEEDOR
- inactivación bloqueada cuando el grupo posee roles activos

## Grupos de clientes y proveedores

`GrupoTercero` clasifica cada rol comercial sin duplicar la identidad del
tercero. La relación se almacena en `TerceroRol.grupo`.

Un tercero que sea cliente y proveedor puede pertenecer a grupos diferentes:

```text
CLIENTE   → Odontólogos
PROVEEDOR → Importadores
```

La migración 0003 crea por empresa:

- `CLIENTES_GENERALES`;
- `PROVEEDORES_GENERALES`.

Todos los roles históricos son asignados automáticamente según su tipo antes de
volver obligatorio el campo.

La interfaz incorpora ABM, búsqueda, baja lógica, cantidades asignadas, filtros
en el maestro y visualización en listado y detalle.

## Relación con ítems

`ItemProveedor` referencia `Tercero` y comprueba como condición operativa la
existencia de un rol activo `PROVEEDOR`.

La inactivación del tercero o del rol no borra la relación comercial: la vuelve
temporalmente no disponible y conserva su historia.

El contrato e implementación están en
`docs/24_relacion_items_proveedores.md`.

## Catálogos iniciales

Se incorporan ocho tipos documentales y once condiciones frente al IVA
con sus códigos ARCA de referencia.

Estos datos son una base local. La futura integración WSFEv1 deberá
consultar los métodos oficiales de parámetros antes de emitir.

## Permisos

```text
terceros.ver
terceros.crear
terceros.editar
```

ADMIN, CONTADOR y OPERADOR pueden consultar, crear y editar.
AUDITOR y SOLO_LECTURA pueden consultar.

## Fuera de alcance

- cuentas corrientes
- crédito
- bancos
- condiciones de venta y pago
- retenciones y percepciones
- productos y servicios
- comprobantes
- consulta automática de padrones
