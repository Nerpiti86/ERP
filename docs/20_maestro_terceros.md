# Maestro base de terceros

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
