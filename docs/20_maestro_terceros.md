# Maestro base de terceros

<!-- BEGIN ESTADO_VERIFICADO_TERCEROS_TAREA_0016 -->
## Estado verificado del maestro de terceros — TAREA 0016

```text
Aplicación: apps.terceros
Modelos: 6
Última migración: 0002_catalogos_iniciales
Pruebas ejecutadas para la app: 52
Plantillas detectadas: 5
```

La primera versión funcional está implementada y permanece sujeta a aislamiento por empresa, permisos backend, servicios transaccionales y auditoría.

No incorpora todavía relaciones comerciales específicas con ítems, condiciones de compra ni cuentas corrientes.

El detalle de modelos, rutas, migraciones y pruebas se encuentra en `docs/22_estado_real_integral_erp.md`.
<!-- END ESTADO_VERIFICADO_TERCEROS_TAREA_0016 -->


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
