# Ventas sin factura electronica

Estado: base inicial de arquitectura.

## Objetivo

Implementar ventas con una estructura compatible con comprobantes fiscales, sin
integrar todavia la autorizacion electronica de ARCA.

## Alcance inicial

- Catalogo local de tipos de comprobante de venta.
- Cabecera de comprobante.
- Lineas con snapshot operativo del item o carga manual.
- Totales por tratamiento de IVA.
- Totales de IVA por alicuota.
- Tributos/percepciones como estructura separada.
- Comprobantes asociados para notas de credito, notas de debito y futuras
  referencias fiscales.
- Servicios transaccionales para crear borrador, validar y anular.

## Fuera de alcance

- WSFEv1.
- CAE y CAEA.
- Certificados, claves privadas y autenticacion remota.
- Consulta remota de parametros ARCA.
- Numeracion sincronizada contra ARCA.
- QR fiscal.
- Factura de credito electronica MiPyME.
- Contabilizacion automatica.
- Cobranza.
- Stock.
- Libro IVA ventas definitivo.

## Deuda explicita

La factura electronica debe entrar como una tarea separada. Esa tarea tiene que
resolver al menos:

- Parametros oficiales de ARCA por web service.
- Compatibilidad entre tipo de comprobante, condicion fiscal del emisor,
  receptor y punto de venta.
- Ultimo comprobante autorizado por punto de venta y tipo.
- Solicitud de CAE.
- Registro de request, response, errores y reintentos.
- Inmutabilidad de comprobantes autorizados.
- Flujo fiscal de anulacion mediante comprobante inverso cuando corresponda.

## Criterio de diseno

La app de ventas no duplica empresa, sucursal, punto de venta, terceros, items,
unidades, alicuotas ni cuentas contables. Usa los modelos existentes del ERP y
solo agrega la capa propia del comprobante de venta.
