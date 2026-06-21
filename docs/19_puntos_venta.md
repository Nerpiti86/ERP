# Puntos de venta por sucursal

Estado: implementado por la TAREA 0008.

## 1. Objetivo

Administrar los puntos de venta de cada empresa sin confundirlos con:

- parámetros generales de empresa
- sucursales físicas
- secuencias internas de comprobantes
- credenciales de facturación electrónica
- autorización de comprobantes mediante CAE o CAEA

Cada punto de venta pertenece a una empresa y a una sucursal. Una sucursal
puede tener cero, uno o varios puntos de venta.

## 2. Fuente y criterio registral

La administración registral de ARCA vincula el punto de venta con un sistema
de emisión y con un domicilio previamente declarado.

Los puntos utilizados por Web Services deben distinguirse de los utilizados
por otros sistemas de emisión. La numeración de comprobantes mantiene
correlatividad por punto de venta y tipo de comprobante.

Fuentes oficiales consultadas:

- https://www.arca.gob.ar/fe/emision-autorizacion/solicitud-autorizacion.asp
- https://www.arca.gob.ar/monotributo/ayuda/facturacion.asp
- https://www.afip.gob.ar/ws/documentacion/manuales/manual-desarrollador-ARCA-COMPG.pdf

La TAREA 0008 modela la configuración registral local. No consulta ni modifica
los puntos de venta de ARCA.

## 3. Modelo PuntoVenta

Campos:

- empresa
- sucursal
- número entre 1 y 99998
- nombre de fantasía opcional
- sistema de emisión
- descripción exacta observada en ARCA, opcional
- actividad económica predeterminada, opcional
- jurisdicción de IIBB predeterminada, opcional
- punto predeterminado para la sucursal
- bloqueo informado por ARCA
- fecha de alta
- fecha de baja
- estado activo
- observaciones
- fechas técnicas

El número se guarda como entero y se presenta con cinco posiciones:

```text
1 -> 00001
27 -> 00027
```

## 4. Sistemas de emisión iniciales

Valores iniciales:

- Web Services
- Comprobantes en línea
- Controlador fiscal
- Facturador
- comprobantes manuales
- otro sistema

La descripción observada en ARCA permite conservar una denominación más
específica sin convertirla en una enumeración rígida del ERP.

## 5. Reglas

- el número es único dentro de la empresa
- un número dado de baja no puede reutilizarse
- la sucursal debe pertenecer a la empresa
- un punto activo requiere una sucursal activa
- una actividad predeterminada debe ser una actividad activa de la empresa
- una jurisdicción predeterminada debe ser una relación IIBB activa de la empresa
- como máximo existe un punto predeterminado activo por sucursal
- el primer punto activo de una sucursal se convierte en predeterminado
- cambiar el predeterminado desmarca al anterior dentro de una transacción
- inactivar el predeterminado promueve otro punto activo cuando existe
- el número y la empresa de un punto existente son inmutables
- la fecha de baja no puede preceder a la fecha de alta
- la baja es lógica y conserva historia

Las invariantes principales se validan en formulario, modelo, servicio y
PostgreSQL.

## 6. Servicios transaccionales

Operaciones:

- `crear_punto_venta`
- `actualizar_punto_venta`
- `inactivar_punto_venta`

Los servicios:

- validan pertenencia a empresa
- bloquean registros relevantes
- mantienen un predeterminado coherente por sucursal
- preservan historia
- registran auditoría
- revierten la operación ante un error

## 7. Parámetro anterior

El parámetro técnico:

```text
punto_venta_default
```

deja de formar parte de los parámetros estándar de empresa.

No se elimina ni se convierte automáticamente porque no identifica:

- sucursal
- sistema de emisión
- fecha de alta
- estado registral real

Cuando existe un valor anterior válido y todavía no existen puntos de venta,
la nueva pantalla lo muestra como sugerencia de carga manual.

## 8. Permisos

Permisos funcionales:

```text
puntos_venta.ver
puntos_venta.crear
puntos_venta.editar
```

Matriz inicial:

- `ADMIN`: ver, crear y editar
- `CONTADOR`: ver, crear y editar
- `AUDITOR`: ver
- `SOLO_LECTURA`: ver
- `OPERADOR`: sin acceso

## 9. Interfaz

Rutas:

```text
/nucleo/configuracion/puntos-venta/
/nucleo/configuracion/puntos-venta/nuevo/
/nucleo/configuracion/puntos-venta/<id>/editar/
/nucleo/configuracion/puntos-venta/<id>/inactivar/
```

La portada de Configuración de empresa muestra:

- puntos activos y totales
- sucursales con puntos activos
- cantidad de predeterminados
- estado de completitud

La sección se considera completa cuando:

- existe al menos un punto activo
- cada sucursal que tenga puntos activos tiene exactamente un punto predeterminado activo
- una sucursal activa puede no tener puntos de venta cuando no emite comprobantes

## 10. Administración técnica

`PuntoVenta` queda visible en Django Admin como consulta de solo lectura.

Las modificaciones deben pasar por la interfaz funcional y los servicios
transaccionales.

## 11. Fuera de alcance

La TAREA 0008 no implementa:

- conexión con WSFEv1
- consulta automática de `FEParamGetPtosVenta`
- alta, baja o modificación remota en ARCA
- certificados y claves privadas
- CAE o CAEA
- secuencias de comprobantes por tipo
- CBU para Factura de Crédito Electrónica
- sistema de circulación de Factura de Crédito
- configuraciones particulares de comprobantes clase A
- controladores fiscales
- importación automática de puntos existentes
- copia automática del parámetro anterior
